import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Test GUI")
window.setGeometry(100, 100, 400, 200)

label = QLabel("If you can see this, PyQt5 is working!", window)
label.move(50, 50)

window.show()
sys.exit(app.exec_())
