from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir

class TreeManager:
    def __init__(self, tree_view):
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
