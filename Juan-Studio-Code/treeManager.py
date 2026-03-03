from PySide6.QtWidgets import QFileSystemModel, QFileDialog, QMenu, QTextEdit
from PySide6.QtGui import QAction
from PySide6.QtCore import QDir, QModelIndex
import os


class TreeManager:
    def __init__(self, tree_view, file_button, tab):
        # Guardamos la referencia al TreeView (ahora Model-Based)
        self.tree = tree_view

        # Creamos el modelo que gestiona los archivos automáticamente
        self.model = QFileSystemModel()

        # Establecemos la ruta raíz (C: o tu carpeta de proyectos)
        path_gen = QDir.rootPath() # Por defecto la raíz del sistema
        # a ella podemos concatenar nuestra ruta mas adelante
        #path_gen = path_gen + "\\Users\\Juan\\Documentos Desktop\\UNI"
        self.model.setRootPath(path_gen)

        # Conectamos el modelo a la vista
        self.tree.setModel(self.model)

        # Hacemos que la vista se sitúe en la ruta raíz
        self.tree.setRootIndex(self.model.index(path_gen))

        # MEJORA VISUAL: Ocultar columnas innecesarias para un IDE
        # Columna 1: Tamaño, 2: Tipo, 3: Fecha modificación
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        # Ajustar el ancho de la columna del nombre automáticamente
        self.tree.header().setStretchLastSection(True)

        #PARA EL FILE BUTTON
        # Guardamos la referencia al file_button
        self.button = file_button
        #Menu despegable
        self.setup_button_menu()

        #PARA TAB
        #Guardamos la referencia al editText
        self.text_edit = tab
        self.tree.doubleClicked.connect(self.on_file_selected)


    def on_file_selected(self, index: QModelIndex):
            # Obtenemos la ruta absoluta desde el modelo usando el índice
            file_path = self.model.filePath(index)

            # Verificamos si es un archivo (y no una carpeta)
            if os.path.isfile(file_path):
                try:
                    # Intentamos leer el archivo (usando utf-8 por seguridad)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.text_edit.setPlainText(content)

                    print(f"Archivo cargado: {file_path}")
                except Exception as e:
                    print(f"No se pudo leer el archivo: {e}")
            else:
                # Si es una carpeta, el comportamiento por defecto de QTreeView
                # ya expande la rama, así que no solemos hacer nada aquí.
                pass

    def setup_button_menu(self):
        #Creamos el objeto menu
        self.menu = QMenu()

        #Opciones del menu
        new_file = QAction("New File", self.button)
        open_file = QAction("Open File...", self.button)
        open_dir = QAction("Open Directory...", self.button)
        save_file = QAction("Save File...", self.button)

        #funciones correspondientes
        new_file.triggered.connect(self.new_file_action)
        open_file.triggered.connect(self.open_file_action)
        open_dir.triggered.connect(self.open_dir_action)
        #save_file.triggered.connect(self.save_file_action)

        #Añadimos las acciones al menú
        self.menu.addAction(new_file)
        self.menu.addAction(open_file)
        self.menu.addAction(open_dir)
        self.menu.addSeparator()
        self.menu.addAction(save_file)

        #Asignamos el menu al boton
        self.button.setMenu(self.menu)
        #Abrir el menu al hacer click
        self.button.setPopupMode(self.button.ToolButtonPopupMode.InstantPopup)
        #Para quitarle la flecha
        self.button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

    def open_file_action(self):
        #Archivo en blanco
        file_path, _  = QFileDialog.getOpenFileName(
                None,
                'Select a file',
                os.getcwd(),
                "All Files (*)"
        )
        #Si el filepaht tiene contenido\
        if file_path:
                try:
                        #Creamos el archivo
                        with open(file_path, 'w') as f:
                                f.write("")
                        #Actualizamos el TreeView
                        dir_path = os.path.dirname(file_path)
                        self.tree.setRootIndex(self.model.index(dir_path))
                except Exceptionn as e:
                        #Valio verga
                        print("Error al crear el archivo:  {e} ")


    def new_file_action(self):
        #abrimos el explorador de archivos
        file_path, _ = QFileDialog.getSaveFileName(
                None,
                'Create New File',
                os.getcwd(),
                "All Files (*);;Python Files (*.py);;Text Files (*.txt)"
        )

        #Si el filepaht tiene contenido\
        if file_path:
                try:
                        #Creamos el archivo
                        with open(file_path, 'w') as f:
                                f.write("")
                        #Actualizamos el TreeView
                        dir_path = os.path.dirname(file_path)
                        self.tree.setRootIndex(self.model.index(dir_path))
                except Exceptionn as e:
                        #Valio verga
                        print("Error al crear el archivo:  {e} ")

    def open_dir_action(self):
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Directory', os.getcwd())
        if dir_path:
                # Si el usuario selecciona una carpeta, actualizamos el TreeView
                self.tree.setRootIndex(self.model.index(dir_path))
