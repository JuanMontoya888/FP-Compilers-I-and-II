import os
from PySide6.QtWidgets import QFileSystemModel, QFileDialog, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QDir, QModelIndex

class TreeManager:
    def __init__(self, tree_view, file_button, editor_manager):
        self.tree = tree_view
        self.editor_manager = editor_manager

        self.model = QFileSystemModel()
        path_gen = QDir.rootPath()
        self.model.setRootPath(path_gen)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path_gen))

        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.header().setStretchLastSection(True)

        self.button = file_button
        self.setup_button_menu()
        self.tree.doubleClicked.connect(self.on_file_selected)

    def on_file_selected(self, index: QModelIndex):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_name = self.model.fileName(index)
                    self.editor_manager.add_new_page(file_name, content, file_path)
                print(f"Archivo cargado en pestaña: {file_path}")
            except Exception as e:
                print(f"No se pudo leer el archivo: {e}")

    def setup_button_menu(self):
        self.menu = QMenu()
        new_file = QAction("New File", self.button)
        open_file = QAction("Open File...", self.button)
        open_dir = QAction("Open Directory...", self.button)
        save_file = QAction("Save File...", self.button)

        new_file.triggered.connect(self.new_file_action)
        open_file.triggered.connect(self.open_file_action)
        open_dir.triggered.connect(self.open_dir_action)

        # --- NUEVA CONEXIÓN ---
        save_file.triggered.connect(self.save_file_action)

        self.menu.addAction(new_file)
        self.menu.addAction(open_file)
        self.menu.addAction(open_dir)
        self.menu.addSeparator()
        self.menu.addAction(save_file)

        self.button.setMenu(self.menu)
        self.button.setPopupMode(self.button.ToolButtonPopupMode.InstantPopup)
        self.button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

    # --- NUEVA FUNCIÓN ---
    def save_file_action(self):
        # Delegamos el guardado al manager de pestañas
        self.editor_manager.save_current_page()


    # metodo para abrir un nuevo documento
    def open_file_action(self):
        file_path, _  = QFileDialog.getOpenFileName(None, 'Select a file', os.getcwd(), "All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_name = os.path.basename(file_path)
                self.editor_manager.add_new_page(file_name, content, file_path)
                dir_path = os.path.dirname(file_path)
                self.tree.setRootIndex(self.model.index(dir_path))
            except Exception as e:
                print(f"Error al abrir el archivo: {e}")

    # metodo para crear un nuevo archivo
    def new_file_action(self):
        file_path, _ = QFileDialog.getSaveFileName(None, 'Create New File', os.getcwd(), "All Files (*);;Python Files (*.py);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                file_name = os.path.basename(file_path)
                self.editor_manager.add_new_page(file_name, "", file_path)
                dir_path = os.path.dirname(file_path)
                self.tree.setRootIndex(self.model.index(dir_path))
            except Exception as e:
                # --- ARREGLADO EL CORTE AQUÍ ---
                print(f"Error al crear el archivo: {e}")

    # metodo para abrir un nuevo folder, o directorio
    def open_dir_action(self):
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Directory', os.getcwd())
        if dir_path:
            self.tree.setRootIndex(self.model.index(dir_path))
