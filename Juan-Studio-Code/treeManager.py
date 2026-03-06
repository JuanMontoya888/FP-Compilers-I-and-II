# This Python file uses the following encoding: utf-8
import os
from PySide6.QtWidgets import QFileSystemModel, QFileDialog, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QDir, QModelIndex

# ============================================================
# CLASE: TreeManager (SISTEMA DE NAVEGACIÓN Y MENÚS)
# Este manager actúa como el controlador principal para la
# interacción entre el sistema de archivos del SO y la interfaz.
#
# Arquitectura:
# - Implementa un modelo de vista (QFileSystemModel) para el árbol.
# - Orquesta la construcción de menús contextuales para la barra superior.
# - Actúa como puente (Proxy) entre el explorador, el editor y la terminal.
# ============================================================
class TreeManager:

    # ============================================================
    # MÉTODO: __init__
    # Qué hace: Configura el modelo de datos del sistema de archivos y
    # vincula los botones físicos de la interfaz con la lógica interna.
    #
    # Componentes:
    # - QFileSystemModel: Para mapear el almacenamiento local.
    # - QTreeView: Para la representación jerárquica.
    #
    # Cómo interactúa: Inyecta las referencias de 'editor_manager'
    # y 'terminal_manager' para permitir que el explorador dispare
    # acciones en otros subsistemas.
    # ============================================================
    def __init__(self, tree_view, ui, editor_manager, terminal_manager):
        self.tree = tree_view
        self.editor_manager = editor_manager
        self.terminal_manager = terminal_manager

        # Configuración del modelo de archivos del sistema
        self.model = QFileSystemModel()
        path_gen = QDir.rootPath()
        self.model.setRootPath(path_gen)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path_gen))

        # Ocultamos columnas técnicas para mantener una UI limpia de explorador
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.header().setStretchLastSection(True)

        # Vinculación de botones de la barra de herramientas superior
        self.btn_file = ui.fileButton
        self.btn_edit = ui.editButton
        self.btn_compile = ui.compileButton
        self.btn_terminal = ui.terminalButton

        self.setup_buttons()
        self.tree.doubleClicked.connect(self.on_file_selected)


    # ============================================================
    # MÉTODO: on_file_selected
    # Qué hace: Maneja el evento de apertura de archivos mediante
    # interacción directa con el árbol de directorios.
    #
    # Componentes:
    # - QModelIndex: Para identificar el nodo seleccionado.
    # - OS Path: Para validaciones de integridad de archivos.
    #
    # Cómo interactúa: Lee el contenido del disco con codificación Latin-1
    # y solicita al 'editor_manager' que cree una nueva página de edición.
    # ============================================================
    def on_file_selected(self, index: QModelIndex):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            try:
                # Apertura de archivo con manejo de codificación específica
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    file_name = self.model.fileName(index)
                    self.editor_manager.add_new_page(file_name, content, file_path)
            except Exception as e:
                print(f"No se pudo leer el archivo: {e}")


    # ============================================================
    # SECCIÓN: CONFIGURACIÓN DE MENÚS Y ACCIONES (TOOLBAR)
    # Este método realiza la construcción imperativa de los menús
    # desplegables para la barra de herramientas superior.
    #
    # Responsabilidades:
    # - Instanciar QMenus y QActions con sus respectivos shortcuts.
    # - Establecer el mapeo de señales (triggered) a los métodos lógicos.
    # - Aplicar el estilo visual 'InstantPopup' para emular un IDE profesional.
    # ============================================================
    def setup_buttons(self):
        # Inicialización de contenedores de menú para cada categoría
        self.menu_file = QMenu()
        self.menu_edit = QMenu()
        self.menu_compile = QMenu()
        self.menu_terminal = QMenu()

        # --------------------------------------- MENÚ FILE ---------------------------------------
        # Definición de acciones de persistencia y gestión de documentos
        new_file = QAction("New File\tCtrl+N", self.btn_file)
        open_file = QAction("Open File...\tCtrl+O", self.btn_file)
        open_dir = QAction("Open Directory...\tCtrl+Shift+O", self.btn_file)
        save_file = QAction("Save File\tCtrl+S", self.btn_file)
        save_as_file = QAction("Save As...\tCtrl+Shift+S", self.btn_file)
        exit_tab = QAction("Close Tab\tCtrl+W", self.btn_file)

        new_file.triggered.connect(self.new_file_action)
        open_file.triggered.connect(self.open_file_action)
        open_dir.triggered.connect(self.open_dir_action)
        save_file.triggered.connect(self.save_file_action)
        save_as_file.triggered.connect(self.save_as_file_action)
        exit_tab.triggered.connect(self.exit_file_action)

        self.menu_file.addAction(new_file)
        self.menu_file.addAction(open_file)
        self.menu_file.addAction(open_dir)
        self.menu_file.addSeparator()
        self.menu_file.addAction(save_file)
        self.menu_file.addAction(save_as_file)
        self.menu_file.addSeparator()
        self.menu_file.addAction(exit_tab)
        self.btn_file.setMenu(self.menu_file)

        # --------------------------------------- MENÚ EDIT ---------------------------------------
        # Integración de funciones estándar de manipulación de texto
        copy_data = QAction("Copy\tCtrl+C", self.btn_edit)
        paste_data = QAction("Paste\tCtrl+V", self.btn_edit)
        copy_data.triggered.connect(self.copy_action)
        paste_data.triggered.connect(self.paste_action)
        self.menu_edit.addAction(copy_data)
        self.menu_edit.addAction(paste_data)
        self.btn_edit.setMenu(self.menu_edit)

        # --------------------------------------- MENÚ COMPILE ---------------------------------------
        # Mapeo de herramientas de análisis léxico, sintáctico y semántico
        lexico_act = QAction("Análisis Léxico", self.btn_compile)
        sintactico_act = QAction("Análisis Sintáctico", self.btn_compile)
        semantico_act = QAction("Análisis Semántico", self.btn_compile)
        ejecutar_act = QAction("Ejecutar\tF5", self.btn_compile)

        # Conexión mediante lambdas para controlar el índice del panel inferior
        lexico_act.triggered.connect(lambda: self.open_terminal_tab(1))
        sintactico_act.triggered.connect(lambda: self.open_terminal_tab(2))
        semantico_act.triggered.connect(lambda: self.open_terminal_tab(3))
        ejecutar_act.triggered.connect(lambda: self.open_terminal_tab(0))

        self.menu_compile.addAction(lexico_act)
        self.menu_compile.addAction(sintactico_act)
        self.menu_compile.addAction(semantico_act)
        self.menu_compile.addSeparator()
        self.menu_compile.addAction(ejecutar_act)
        self.btn_compile.setMenu(self.menu_compile)

        # --------------------------------------- TERMINAL ---------------------------------------
        # Acciones de control de flujo y visibilidad de la consola integrada
        toggle_view = QAction("Mostrar/Ocultar Panel\tCtrl+`", self.btn_terminal)
        clear_cons = QAction("Limpiar Consola", self.btn_terminal)
        kill_proc = QAction("Detener Proceso Actual", self.btn_terminal)

        toggle_view.triggered.connect(self.toggle_terminal_action)
        clear_cons.triggered.connect(self.clear_terminal_action)
        kill_proc.triggered.connect(self.kill_process_action)

        self.menu_terminal.addAction(toggle_view)
        self.menu_terminal.addSeparator()
        self.menu_terminal.addAction(clear_cons)
        self.menu_terminal.addAction(kill_proc)

        self.btn_terminal.setMenu(self.menu_terminal)

        # Normalización estética: eliminamos el indicador de menú de Qt para un look minimalista
        for btn in [self.btn_file, self.btn_edit, self.btn_compile, self.btn_terminal]:
            btn.setPopupMode(btn.ToolButtonPopupMode.InstantPopup)
            btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")


    # ============================================================
    # SECCIÓN: LÓGICA DE LA TERMINAL INTEGRADA
    # Estos métodos controlan el ciclo de vida de la consola de comandos
    # y los procesos en ejecución (PowerShell/Python).
    # ============================================================

    def toggle_terminal_action(self):
        """Alterna la visibilidad del panel inferior dinámicamente."""
        if self.terminal_manager.isVisible():
            self.terminal_manager.hide()
        else:
            self.terminal_manager.show()

    def clear_terminal_action(self):
        """Limpia el buffer de texto de la terminal y resetea el puntero de entrada."""
        self.terminal_manager.terminal_edit.clear()
        self.terminal_manager.interactive_position = 0

    def kill_process_action(self):
        """Forza la finalización del proceso secundario actual para liberar recursos."""
        if self.terminal_manager.process.state() != self.terminal_manager.process.NotRunning:
            self.terminal_manager.process.kill()
            self.terminal_manager.terminal_edit.appendPlainText("\n[Proceso finalizado por el usuario]\n")
            # Restauramos el cursor para permitir nuevas entradas
            self.terminal_manager.interactive_position = self.terminal_manager.terminal_edit.textCursor().position()

    def open_terminal_tab(self, index):
        """Cambia el foco de la consola a la pestaña de análisis específica."""
        self.terminal_manager.setCurrentIndex(index)
        if not self.terminal_manager.isVisible():
            self.terminal_manager.show()


    # ============================================================
    # SECCIÓN: LÓGICA DE EDICIÓN Y PERSISTENCIA
    # Implementa las funciones de portapapeles y los diálogos de
    # guardado/apertura de archivos delegando al Editor Manager.
    # ============================================================

    def copy_action(self):
        """Accede al editor de la pestaña activa para ejecutar la copia."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor_manager.tabs.widget(current_index)
            current_page.editor.copy()

    def paste_action(self):
        """Accede al editor de la pestaña activa para ejecutar el pegado."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor_manager.tabs.widget(current_index)
            current_page.editor.paste()

    def exit_file_action(self):
        """Solicita el cierre controlado de la pestaña actual."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            self.editor_manager.close_page(current_index)

    def save_file_action(self):
        """Dispara la rutina de guardado estándar en el editor manager."""
        self.editor_manager.save_current_page()

    def save_as_file_action(self):
        """Dispara la rutina de 'Guardar como' con diálogo de selección."""
        self.editor_manager.save_as_current_page()

    def open_file_action(self):
        """Despliega el explorador nativo para importar un archivo al entorno."""
        file_path, _ = QFileDialog.getOpenFileName(None, 'Select a file', os.getcwd(), "All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                file_name = os.path.basename(file_path)
                self.editor_manager.add_new_page(file_name, content, file_path)
                # Sincronizamos el árbol de archivos con la ubicación del nuevo archivo
                self.tree.setRootIndex(self.model.index(os.path.dirname(file_path)))
            except Exception as e:
                print(f"Error al abrir: {e}")

    def new_file_action(self):
        """Instancia una nueva pestaña en memoria con estado 'Unsaved'."""
        self.editor_manager.add_new_page("Untitled*", "", "")

    def open_dir_action(self):
        """Actualiza la raíz del explorador lateral a un nuevo directorio."""
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Directory', os.getcwd())
        if dir_path:
            self.tree.setRootIndex(self.model.index(dir_path))
