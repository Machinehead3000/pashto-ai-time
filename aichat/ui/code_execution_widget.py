"""
Widget for executing Python code and displaying results.
"""
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QTabWidget, QSplitter, QSizePolicy, QFileDialog, QMessageBox,
    QComboBox, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QProcess, QTimer
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextFormat

from code_interpreter import CodeInterpreter

class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""
    
    # Python keywords
    keywords = [
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
        'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'None', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'True', 'try', 'while', 'with', 'yield'
    ]
    
    # Python operators
    operators = [
        '=', '==', '!=', '<', '<=', '>', '>=', '\\',
        '\\*', '\\+', '-', '\\^', '\\[', '\\]', '\\{', '\\}', '\\(', '\\)',
        '\\*\\*', '\\*', '\\+', '-', '\\^', '\\~', '\\|', '&', '//', '/',
        '\\%', '\\<\\<', '\\>\\>'
    ]
    
    # Python braces
    braces = [
        '\\{', '\\}', '\\[', '\\]', '\\(', '\\)'
    ]
    
    def __init__(self, document):
        super().__init__(document)
        
        # Multi-line strings (expression, flag, style)
        self.tri_single = (QRegExp("'''"), 1, self.styles['string2'])
        self.tri_double = (QRegExp('"""'), 2, self.styles['string2'])
        
        rules = []
        
        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, self.styles['keyword']) for w in self.keywords]
        rules += [(r'%s' % o, 0, self.styles['operator']) for o in self.operators]
        rules += [(r'%s' % b, 0, self.styles['brace']) for b in self.braces]
        
        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, self.styles['self']),
            
            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, self.styles['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, self.styles['string']),
            
            # From 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, self.styles['defclass']),
            # From 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, self.styles['defclass']),
            
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, self.styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, self.styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, self.styles['numbers']),
            
            # Comments
            (r'#[^\n]*', 0, self.styles['comment']),
        ]
        
        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
    
    # Styles for different syntax elements
    styles = {
        'keyword': QTextCharFormat(),
        'operator': QTextCharFormat(),
        'brace': QTextCharFormat(),
        'defclass': QTextCharFormat(),
        'string': QTextCharFormat(),
        'string2': QTextCharFormat(),
        'comment': QTextCharFormat(),
        'self': QTextCharFormat(),
        'numbers': QTextCharFormat(),
    }
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        # Apply syntax highlighting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        
        self.setCurrentBlockState(0)
        
        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)
    
    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings."""
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()
        
        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the closing delimiter
            end = delimiter.indexIn(text, start + add)
            # Closing delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)
        
        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False

class CodeExecutionWidget(QWidget):
    """
    Widget for executing Python code and displaying results.
    """
    # Signal emitted when code execution starts
    execution_started = pyqtSignal()
    
    # Signal emitted when code execution finishes
    execution_finished = pyqtSignal(dict)  # Result dictionary
    
    def __init__(self, parent=None):
        """Initialize the code execution widget."""
        super().__init__(parent)
        
        # Initialize code interpreter
        self.interpreter = CodeInterpreter()
        
        # Setup UI
        self.setup_ui()
        
        # Execution process
        self.process = None
        self.execution_timer = QTimer(self)
        self.execution_timer.setSingleShot(True)
        self.execution_timer.timeout.connect(self.kill_long_running_process)
    
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Enter Python code here and click 'Run' or press Shift+Enter to execute...")
        self.code_editor.setAcceptRichText(False)
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #e0e0ff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #3a3a5a;
            }
        """)
        
        # Set up syntax highlighting
        self.highlighter = PythonHighlighter(self.code_editor.document())
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # Run button
        self.run_btn = QPushButton("Run (Shift+Enter)")
        self.run_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_MediaPlay')))
        self.run_btn.clicked.connect(self.execute_code)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_TrashIcon')))
        self.clear_btn.clicked.connect(self.clear_editor)
        
        # Add buttons to toolbar
        toolbar.addWidget(self.run_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        
        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 9))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        # Add widgets to layout
        layout.addLayout(toolbar)
        layout.addWidget(self.code_editor, 1)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output_area, 1)
    
    def execute_code(self):
        """Execute the Python code in the editor."""
        code = self.code_editor.toPlainText().strip()
        if not code:
            return
        
        # Clear previous output
        self.output_area.clear()
        
        # Emit signal that execution has started
        self.execution_started.emit()
        
        try:
            # Execute the code
            result = self.interpreter.execute_code(code)
            
            # Display the output
            if result['output']:
                self.append_output(result['output'])
            
            # Display any plots that were generated
            for plot_path in result.get('plots', []):
                self.append_output(f"\n[Generated plot: {os.path.basename(plot_path)}]")
            
            # Display any errors
            if not result['success'] and result.get('error'):
                self.append_output(f"\nError: {result['error']}", color="#ff6b6b")
                if result.get('traceback'):
                    self.append_output(f"\n{result['traceback']}", color="#ff6b6b")
            
            # Emit signal that execution has finished
            self.execution_finished.emit(result)
            
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}\n{traceback.format_exc()}"
            self.append_output(error_msg, color="#ff6b6b")
            self.execution_finished.emit({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
    
    def append_output(self, text: str, color: str = "#e0e0ff"):
        """
        Append text to the output area.
        
        Args:
            text: Text to append
            color: Text color (hex code)
        """
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set text color
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)
        
        # Insert text
        cursor.insertText(text + "\n")
        
        # Scroll to bottom
        self.output_area.ensureCursorVisible()
    
    def clear_editor(self):
        """Clear the code editor and output area."""
        self.code_editor.clear()
        self.output_area.clear()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Run code on Shift+Enter
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
            self.execute_code()
        else:
            super().keyPressEvent(event)
    
    def kill_long_running_process(self):
        """Kill a process that's been running too long."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.append_output("\nProcess terminated: Execution time limit exceeded", color="#ff6b6b")
