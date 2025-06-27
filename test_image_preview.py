import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from aichat.ui.file_upload_widget import FileUploadWidget

def create_test_images(directory):
    """Create test images in the specified directory."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    os.makedirs(directory, exist_ok=True)
    
    # Create 3 test images with different colors and text
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
    ]
    
    img_paths = []
    for i, color in enumerate(colors):
        # Create a simple image with color and text
        img = Image.new('RGB', (400, 300), color=color)
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        d.text((50, 50), f"Test Image {i+1}", fill=(255, 255, 255), font=font)
        
        # Save the image
        img_path = os.path.join(directory, f"test_image_{i+1}.png")
        img.save(img_path)
        img_paths.append(img_path)
    
    return img_paths

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Preview Test")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Instructions
        instructions = QLabel(
            "<h3>Image Preview Test</h3>"
            "<p>Test the following features:</p>"
            "<ul>"
            "<li>Drag and drop images or use the file dialog</li>"
            "<li>Navigate between images using arrow buttons</li>"
            "<li>Use zoom controls (+/-/100%)</li>"
            "<li>Rotate images (↺/↻)</li>"
            "<li>Close preview with '✕ Close'</li>"
            "</ul>"
        )
        instructions.setTextFormat(Qt.RichText)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create file upload widget
        self.upload_widget = FileUploadWidget(allowed_extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp'])
        layout.addWidget(self.upload_widget, 1)  # Allow widget to expand
        
        # Add some test buttons
        test_btn_layout = QHBoxLayout()
        
        btn_add_files = QPushButton("Add Test Images")
        btn_add_files.clicked.connect(self.add_test_images)
        test_btn_layout.addWidget(btn_add_files)
        
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.upload_widget.clear_files)
        test_btn_layout.addWidget(btn_clear)
        
        btn_zoom_in = QPushButton("Test Zoom In")
        btn_zoom_in.clicked.connect(lambda: getattr(self.upload_widget, 'zoom_in', lambda: None)())
        test_btn_layout.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton("Test Zoom Out")
        btn_zoom_out.clicked.connect(lambda: getattr(self.upload_widget, 'zoom_out', lambda: None)())
        test_btn_layout.addWidget(btn_zoom_out)
        
        btn_rotate_left = QPushButton("Test Rotate Left")
        btn_rotate_left.clicked.connect(lambda: getattr(self.upload_widget, 'rotate_left', lambda: None)())
        test_btn_layout.addWidget(btn_rotate_left)
        
        btn_rotate_right = QPushButton("Test Rotate Right")
        btn_rotate_right.clicked.connect(lambda: getattr(self.upload_widget, 'rotate_right', lambda: None)())
        test_btn_layout.addWidget(btn_rotate_right)
        
        layout.addLayout(test_btn_layout)
        
        # Create test images
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_images")
        self.test_images = []
        
        # Add some initial test images
        self.add_test_images()
    
    def add_test_images(self):
        """Add test images to the upload widget."""
        # Create test images if they don't exist
        if not os.path.exists(self.test_dir) or not os.listdir(self.test_dir):
            self.test_images = create_test_images(self.test_dir)
        
        # Add files to the widget
        if self.test_images:
            self.upload_widget.add_files(self.test_images)
            # Show the first image in preview if not already showing
            if not hasattr(self.upload_widget, 'current_preview_path') or not self.upload_widget.current_preview_path:
                self.upload_widget.show_preview(self.test_images[0])

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
