"""Voice input/output widget for speech-to-text and text-to-speech functionality."""
import os
import tempfile
from pathlib import Path
from typing import Optional, Callable

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QProgressBar
)
from PyQt5.QtGui import QIcon, QPixmap, QColor

from multimodal import MultiModalProcessor


class VoiceInputThread(QThread):
    """Thread for handling voice input processing."""
    finished = pyqtSignal(str, bool)  # text, success
    
    def __init__(self, processor: MultiModalProcessor, language: str = 'en-US'):
        super().__init__()
        self.processor = processor
        self.language = language
        self.is_recording = False
        self.stop_requested = False
        
    def run(self):
        """Run the voice recognition in a separate thread."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Record audio
            self.is_recording = True
            with sr.Microphone() as source:
                self.processor.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.processor.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                if self.stop_requested:
                    self.finished.emit("", False)
                    return
                    
                # Save audio to temporary file
                with open(temp_path, "wb") as f:
                    f.write(audio.get_wav_data())
            
            # Convert speech to text
            text = self.processor.speech_to_text(temp_path, self.language)
            os.unlink(temp_path)  # Clean up temp file
            
            if text.startswith("Error"):
                self.finished.emit(text, False)
            else:
                self.finished.emit(text, True)
                
        except Exception as e:
            self.finished.emit(f"Error during voice recognition: {str(e)}", False)
        finally:
            self.is_recording = False
    
    def stop(self):
        """Stop the recording process."""
        if self.is_recording:
            self.stop_requested = True


class VoiceInputWidget(QWidget):
    """Widget for voice input and output controls."""
    
    voice_input_received = pyqtSignal(str)  # Emitted when voice input is received
    
    def __init__(self, parent=None, processor: Optional[MultiModalProcessor] = None, 
                 language: str = 'en-US'):
        """Initialize the voice input widget.
        
        Args:
            parent: Parent widget
            processor: MultiModalProcessor instance for voice processing
            language: Language code for speech recognition (default: 'en-US')
        """
        super().__init__(parent)
        self.processor = processor or MultiModalProcessor()
        self.language = language
        self.recording_thread = None
        self.is_recording = False
        
        # UI Setup
        self.init_ui()
        
        # Animation timer for recording indicator
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_recording_animation)
        self.animation_frame = 0
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main button layout
        button_layout = QHBoxLayout()
        
        # Voice input button
        self.voice_button = QPushButton()
        self.voice_button.setIcon(self.style().standardIcon(
            getattr(self.style(), 'SP_MediaPlay')
        ))
        self.voice_button.setToolTip("Start/Stop Voice Input")
        self.voice_button.setFixedSize(40, 40)
        self.voice_button.setCheckable(True)
        self.voice_button.clicked.connect(self.toggle_voice_input)
        
        # Status label
        self.status_label = QLabel("Tap to speak")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Progress bar for recording level
        self.level_meter = QProgressBar()
        self.level_meter.setTextVisible(False)
        self.level_meter.setRange(0, 100)
        self.level_meter.setValue(0)
        self.level_meter.setFixedHeight(4)
        
        # Assemble layout
        button_layout.addWidget(self.voice_button)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.level_meter)
        
        # Set initial state
        self.set_recording_state(False)
    
    def toggle_voice_input(self):
        """Toggle voice input on/off."""
        if self.is_recording:
            self.stop_voice_input()
        else:
            self.start_voice_input()
    
    def start_voice_input(self):
        """Start voice input recording."""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.set_recording_state(True)
        
        # Start animation
        self.animation_frame = 0
        self.animation_timer.start(100)  # Update every 100ms
        
        # Start recording in a separate thread
        self.recording_thread = VoiceInputThread(self.processor, self.language)
        self.recording_thread.finished.connect(self.on_voice_input_finished)
        self.recording_thread.start()
    
    def stop_voice_input(self):
        """Stop voice input recording."""
        if not self.is_recording or not self.recording_thread:
            return
            
        # Stop animation
        self.animation_timer.stop()
        self.level_meter.setValue(0)
        
        # Stop the recording thread
        if self.recording_thread.isRunning():
            self.recording_thread.stop()
            self.recording_thread.wait()
        
        self.set_recording_state(False)
    
    def on_voice_input_finished(self, text: str, success: bool):
        """Handle completion of voice input processing."""
        self.animation_timer.stop()
        self.level_meter.setValue(0)
        self.set_recording_state(False)
        
        if success and text:
            self.voice_input_received.emit(text)
            self.status_label.setText("Voice input received")
        elif text:  # Error message
            self.status_label.setText(text)
        
        # Reset button state
        self.voice_button.setChecked(False)
    
    def set_recording_state(self, recording: bool):
        """Update UI elements based on recording state."""
        self.is_recording = recording
        
        if recording:
            self.voice_button.setIcon(self.style().standardIcon(
                getattr(self.style(), 'SP_MediaStop')
            ))
            self.voice_button.setToolTip("Stop Recording")
            self.status_label.setText("Listening...")
            self.status_label.setStyleSheet("color: #ff6b6b;")
        else:
            self.voice_button.setIcon(self.style().standardIcon(
                getattr(self.style(), 'SP_MediaPlay')
            ))
            self.voice_button.setToolTip("Start Voice Input")
            self.status_label.setText("Tap to speak")
            self.status_label.setStyleSheet("")
    
    def update_recording_animation(self):
        """Update the recording animation."""
        if not self.is_recording:
            return
            
        # Simple animation: cycle through different levels
        self.animation_frame = (self.animation_frame + 1) % 10
        level = abs(5 - self.animation_frame) * 20  # 0-100 in a wave pattern
        self.level_meter.setValue(level)
    
    def set_language(self, language: str):
        """Set the language for speech recognition.
        
        Args:
            language: Language code (e.g., 'en-US', 'es-ES')
        """
        self.language = language
    
    def set_processor(self, processor: MultiModalProcessor):
        """Set the MultiModalProcessor instance to use.
        
        Args:
            processor: MultiModalProcessor instance
        """
        self.processor = processor
