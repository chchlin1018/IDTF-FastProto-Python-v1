import sys
from PySide6.QtWidgets import QApplication
from .main_window import NDHCpMainWindow

def main():
    app = QApplication(sys.argv)
    window = NDHCpMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

