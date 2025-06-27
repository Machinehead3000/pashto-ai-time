from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTextEdit, QLineEdit, QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from aichat.utils.prompt_library import PromptLibrary

class PromptLibraryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt Library")
        self.setMinimumSize(400, 350)
        self.library = PromptLibrary()
        self.selected_prompt = None
        self.setup_ui()
        self.load_prompts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.prompt_list = QListWidget()
        self.prompt_list.itemSelectionChanged.connect(self.on_prompt_selected)
        layout.addWidget(QLabel("Saved Prompts:"))
        layout.addWidget(self.prompt_list)

        # Prompt text area
        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        layout.addWidget(QLabel("Prompt Preview:"))
        layout.addWidget(self.prompt_text)

        # Buttons
        btn_layout = QHBoxLayout()
        self.insert_btn = QPushButton("Insert")
        self.insert_btn.clicked.connect(self.accept)
        self.insert_btn.setEnabled(False)
        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.add_prompt)
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_prompt)
        self.rename_btn.setEnabled(False)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_prompt)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.insert_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.rename_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

    def load_prompts(self):
        self.prompt_list.clear()
        for prompt in self.library.get_prompts():
            self.prompt_list.addItem(prompt["name"])

    def on_prompt_selected(self):
        items = self.prompt_list.selectedItems()
        if items:
            name = items[0].text()
            prompt = next((p for p in self.library.get_prompts() if p["name"] == name), None)
            if prompt:
                self.selected_prompt = prompt
                self.prompt_text.setPlainText(prompt["text"])
                self.insert_btn.setEnabled(True)
                self.rename_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
        else:
            self.selected_prompt = None
            self.prompt_text.clear()
            self.insert_btn.setEnabled(False)
            self.rename_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def add_prompt(self):
        name, ok = QInputDialog.getText(self, "Add Prompt", "Prompt name:")
        if ok and name:
            text, ok2 = QInputDialog.getMultiLineText(self, "Add Prompt", "Prompt text:")
            if ok2 and text:
                self.library.add_prompt(name, text)
                self.load_prompts()

    def rename_prompt(self):
        if not self.selected_prompt:
            return
        old_name = self.selected_prompt["name"]
        new_name, ok = QInputDialog.getText(self, "Rename Prompt", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.library.rename_prompt(old_name, new_name)
            self.load_prompts()

    def delete_prompt(self):
        if not self.selected_prompt:
            return
        name = self.selected_prompt["name"]
        reply = QMessageBox.question(self, "Delete Prompt", f"Delete prompt '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.library.delete_prompt(name)
            self.load_prompts()

    def get_selected_prompt_text(self):
        if self.selected_prompt:
            return self.selected_prompt["text"]
        return "" 