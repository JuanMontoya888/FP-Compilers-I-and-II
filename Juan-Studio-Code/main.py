import sys
import os
import traceback
from PySide6.QtWidgets import QApplication

# Add root to sys.path to allow imports to work seamlessly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide.core.widget import Widget

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        widget = Widget()
        widget.showMaximized()
        sys.exit(app.exec())
    except Exception:
        # Diagnostic display for catastrophic errors
        print("\n" + "="*60)
        print("CRITICAL ERROR: THE APPLICATION FAILED TO START")
        print("="*60)
        traceback.print_exc()
        print("="*60 + "\n")
        input("System Failure. Press Enter to exit...")

