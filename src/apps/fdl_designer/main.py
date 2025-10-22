"""
FDL Designer - Main Application Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from .main_window import FDLDesignerMainWindow


def main():
    app = QApplication(sys.argv)
    window = FDLDesignerMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

