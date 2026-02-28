# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget

# Asegúrate de haber ejecutado: pyside6-uic form.ui -o ui_form.py
from ui_form import Ui_Widget
from treeManager import TreeManager

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Configuración del Splitter para que el editor crezca más
        self.ui.splitter.setStretchFactor(0, 0) # Panel izquierdo fijo
        self.ui.splitter.setStretchFactor(1, 1) # Panel derecho expansible

        # Instanciamos el manager pasando el treeView de la UI
        self.explorer = TreeManager(self.ui.treeView)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.showMaximized()
    sys.exit(app.exec())
