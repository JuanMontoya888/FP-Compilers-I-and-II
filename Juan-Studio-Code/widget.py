# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QSplitter
from PySide6.QtCore import Qt

from ui_form import Ui_Widget

# Importamos nuestros módulos personalizados
from treeManager import TreeManager
from codeEditorManager import CodeEditorManager
from shortcuts import Shortcuts
from terminalManager import TerminalManager

class Widget(QWidget):

    def __init__(self, parent=None):
        ''' ------ Configuraciones generales de la app --------'''
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Configuramos el comportamiento del QSplitter principal (Horizontal)
        self.ui.splitter.setStretchFactor(0, 0) # Panel izquierdo (Explorador)
        self.ui.splitter.setStretchFactor(1, 1) # Panel derecho (Lo que sea que esté aquí)

        ''' ------ Configuraciones de componentes ------ '''
        # Instanciamos el manager de las PESTAÑAS.
        self.editor_manager = CodeEditorManager(self.ui.tabWidget)

        # Instanciamos el manager del EXPLORADOR DE ARCHIVOS.
        self.explorer = TreeManager(self.ui.treeView, self.ui.fileButton, self.editor_manager)

        ''' ------ Configuraciones de la Terminal y Splitter Vertical ------ '''
        # Creamos un nuevo Splitter VERTICAL
        self.v_splitter = QSplitter(Qt.Vertical)

        # Metemos el tabWidget al splitter vertical
        self.v_splitter.addWidget(self.ui.tabWidget)

        # Instanciamos la Terminal y la metemos debajo del tabWidget
        self.terminal = TerminalManager()
        self.v_splitter.addWidget(self.terminal)

        # La ocultamos
        self.terminal.hide()

        # Ajustamos las proporciones
        self.v_splitter.setStretchFactor(0, 1) # Editor se estira
        self.v_splitter.setStretchFactor(1, 0) # Terminal mantiene su tamaño

        # Insertamos el bloque vertical en el panel derecho del splitter horizontal
        self.ui.splitter.addWidget(self.v_splitter)

        # definimos tam
        self.ui.splitter.setSizes([200, 800])

        ''' ------ Instanciamos atajos ------ '''
        # Le pasamos el self (parent) para que atajos.py pueda acceder a self.terminal
        self.atajos = Shortcuts(self, self.explorer, self.editor_manager)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.showMaximized()
    sys.exit(app.exec())
