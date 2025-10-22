#!/usr/bin/env python3
"""
IADL Designer - Main Application
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import IADLDesignerMainWindow


def main():
    """Main entry point for IADL Designer."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setApplicationName("IADL Designer")
    app.setOrganizationName("IDTF")
    
    # Create and show main window
    window = IADLDesignerMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

