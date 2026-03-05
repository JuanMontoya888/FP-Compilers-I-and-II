# This Python file uses the following encoding: utf-8
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QSplitter
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ui_form import Ui_Widget
from treeManager import TreeManager
from codeEditorManager import CodeEditorManager
from shortcuts import Shortcuts
from terminalManager import TerminalManager

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Mantenemos el __init__ compacto llamando a los métodos de configuración
        self.setup_icons()
        self.setup_components()
        self.setup_layout()
        self.setup_connections() # método para conectar los botones

    def setup_icons(self):
        """ ------ CONFIGURACIÓN DE ÍCONOS DE LA ACTIVITY BAR ------ """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")
        icon_size = QSize(24, 24)

        # match word or regular expression
        self.ui.lexicoButton.setIcon(QIcon(os.path.join(icons_dir, "lexico.svg")))
        self.ui.lexicoButton.setIconSize(icon_size)

        # tree
        self.ui.sintacticoButton.setIcon(QIcon(os.path.join(icons_dir, "sintactico.svg")))
        self.ui.sintacticoButton.setIconSize(icon_size)

        # brain
        self.ui.semanticoButton.setIcon(QIcon(os.path.join(icons_dir, "semantico.svg")))
        self.ui.semanticoButton.setIconSize(icon_size)

        # Developer Mode TV
        self.ui.codIntButton.setIcon(QIcon(os.path.join(icons_dir, "intermedio.svg")))
        self.ui.codIntButton.setIconSize(icon_size)

        # play
        self.ui.runButton_.setIcon(QIcon(os.path.join(icons_dir, "play.svg")))
        self.ui.runButton_.setIconSize(icon_size)

        # bug
        self.ui.errorButton.setIcon(QIcon(os.path.join(icons_dir, "bug.svg")))
        self.ui.errorButton.setIconSize(icon_size)

    def setup_components(self):
        """ ------ Configuraciones de componentes y atajos ------ """
        self.editor_manager = CodeEditorManager(self.ui.tabWidget)
        self.explorer = TreeManager(self.ui.treeView, self.ui.fileButton, self.editor_manager)
        self.atajos = Shortcuts(self, self.explorer, self.editor_manager)

    def setup_layout(self):
        """ ------ Configuraciones de los splitters y la terminal ------ """
        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.ui.tabWidget)

        self.terminal_manager = TerminalManager()
        self.v_splitter.addWidget(self.terminal_manager)

        self.terminal_manager.hide()

        self.v_splitter.setStretchFactor(0, 1)
        self.v_splitter.setStretchFactor(1, 0)

        self.ui.splitter.addWidget(self.v_splitter)
        self.ui.splitter.setSizes([200, 800])


    def setup_connections(self):
        """ ------ Conexión de botones a sus respectivas acciones ------ """
        # Al hacer clic, llamamos a open_bottom_panel y le pasamos el índice de la pestaña
        self.ui.runButton_.clicked.connect(lambda: self.open_bottom_panel(0))      # Abre Terminal
        self.ui.lexicoButton.clicked.connect(lambda: self.open_bottom_panel(1))    # Abre Análisis Léxico
        self.ui.sintacticoButton.clicked.connect(lambda: self.open_bottom_panel(2))# Abre Análisis Sintáctico
        self.ui.semanticoButton.clicked.connect(lambda: self.open_bottom_panel(3)) # Abre Análisis Semántico
        self.ui.codIntButton.clicked.connect(lambda: self.open_bottom_panel(4)) # Abre Análisis Semántico


    def open_bottom_panel(self, tab_index):
        """Muestra el panel inferior y selecciona la pestaña indicada."""
        self.terminal_manager.setCurrentIndex(tab_index)
        if not self.terminal_manager.isVisible():
            self.terminal_manager.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.showMaximized()
    sys.exit(app.exec())
