"""Text-to-speech widget for converting text to speech."""
import os
import tempfile
from pathlib import Path
from typing import Optional, Callable

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox, 
    QSlider, QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from ..multimodal import MultiModalProcessor


class TTSThread(QThread):
    """Thread for handling text-to-speech conversion."""
    finished = pyqtSignal(str, bool)  # audio_path, success
    
    def __init__(
        self, 
        text: str, 
        processor: MultiModalProcessor, 
        language: str = 'en',
        speed: float = 1.0,
        use_cloud: bool = False
    ):
        super().__init__()
        self.text = text
        self.processor = processor
        self.language = language
        self.speed = speed
        self.use_cloud = use_cloud
        self.output_path = None
        
    def run(self):
        """Convert text to speech and save to a temporary file."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Convert text to speech
            result_path = self.processor.text_to_speech(
                text=self.text,
                output_path=output_path,
                lang=self.language
            )
            
            if result_path.startswith("Error"):
                self.finished.emit(result_path, False)
            else:
                self.output_path = result_path
                self.finished.emit(result_path, True)
                
        except Exception as e:
            self.finished.emit(f"Error in text-to-speech: {str(e)}", False)


class TTSWidget(QWidget):
    """Widget for text-to-speech functionality."""
    
    def __init__(self, parent=None, processor: Optional[MultiModalProcessor] = None):
        """Initialize the TTS widget.
        
        Args:
            parent: Parent widget
            processor: MultiModalProcessor instance for TTS
        """
        super().__init__(parent)
        self.processor = processor or MultiModalProcessor()
        self.media_player = QMediaPlayer()
        self.current_audio_path = None
        self.tts_thread = None
        
        # UI Setup
        self.init_ui()
        
        # Connect media player signals
        self.media_player.stateChanged.connect(self.on_media_state_changed)
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Spanish", "es")
        self.language_combo.addItem("French", "fr")
        self.language_combo.addItem("German", "de")
        self.language_combo.addItem("Italian", "it")
        self.language_combo.addItem("Japanese", "ja")
        self.language_combo.addItem("Chinese", "zh")
        self.language_combo.addItem("Russian", "ru")
        self.language_combo.addItem("Arabic", "ar")
        lang_layout.addWidget(self.language_combo)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)  # 50% to 200% speed
        self.speed_slider.setValue(100)  # 100% speed
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(25)
        
        self.speed_label = QLabel("1.0x")
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        
        # Cloud TTS option
        self.cloud_tts_check = QCheckBox("Use Cloud TTS (if available)")
        self.cloud_tts_check.setChecked(False)
        
        # Play button
        self.play_button = QPushButton("Speak")
        self.play_button.setIcon(self.style().standardIcon(
            getattr(self.style(), 'SP_MediaPlay')
        ))
        self.play_button.clicked.connect(self.toggle_playback)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Assemble layout
        layout.addLayout(lang_layout)
        layout.addLayout(speed_layout)
        layout.addWidget(self.cloud_tts_check)
        layout.addWidget(self.play_button)
        layout.addWidget(self.status_label)
    
    def speak_text(self, text: str):
        """Convert text to speech and play it.
        
        Args:
            text: The text to convert to speech
        """
        if not text.strip():
            self.status_label.setText("No text to speak")
            return
            
        self.current_text = text
        self.status_label.setText("Converting to speech...")
        
        # Start TTS in a separate thread
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.terminate()
            self.tts_thread.wait()
            
        self.tts_thread = TTSThread(
            text=text,
            processor=self.processor,
            language=self.language_combo.currentData(),
            speed=self.speed_slider.value() / 100.0,
            use_cloud=self.cloud_tts_check.isChecked()
        )
        self.tts_thread.finished.connect(self.on_tts_finished)
        self.tts_thread.start()
    
    def toggle_playback(self):
        """Toggle playback of the current audio."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(
                getattr(self.style(), 'SP_MediaPlay')
            ))
        else:
            if self.current_audio_path and os.path.exists(self.current_audio_path):
                self.media_player.play()
                self.play_button.setIcon(self.style().standardIcon(
                    getattr(self.style(), 'SP_MediaPause')
                ))
    
    def on_tts_finished(self, audio_path: str, success: bool):
        """Handle completion of TTS conversion."""
        if success:
            self.current_audio_path = audio_path
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(
                getattr(self.style(), 'SP_MediaPause')
            ))
            self.status_label.setText("Playing...")
        else:
            self.status_label.setText(audio_path)  # Show error message
    
    def on_media_state_changed(self, state):
        """Handle media player state changes."""
        if state == QMediaPlayer.StoppedState:
            self.play_button.setIcon(self.style().standardIcon(
                getattr(self.style(), 'SP_MediaPlay')
            ))
            self.status_label.setText("Ready")
    
    def on_speed_changed(self, value):
        """Handle speed slider value changes."""
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        
        # Update media player rate if supported
        if hasattr(self.media_player, 'setPlaybackRate'):
            self.media_player.setPlaybackRate(speed)
    
    def set_processor(self, processor: MultiModalProcessor):
        """Set the MultiModalProcessor instance to use.
        
        Args:
            processor: MultiModalProcessor instance
        """
        self.processor = processor
    
    def cleanup(self):
        """Clean up resources."""
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.terminate()
            self.tts_thread.wait()
            
        if hasattr(self, 'current_audio_path') and self.current_audio_path:
            try:
                if os.path.exists(self.current_audio_path):
                    os.unlink(self.current_audio_path)
            except Exception:
                pass
