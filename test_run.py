import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

def test_qt():
    app = QApplication(sys.argv)
    
    # Create a simple window
    window = QWidget()
    window.setWindowTitle('Test Window')
    window.setGeometry(100, 100, 400, 300)
    
    # Add a label
    layout = QVBoxLayout()
    label = QLabel('PyQt5 is working correctly!')
    layout.addWidget(label)
    window.setLayout(layout)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_qt()
