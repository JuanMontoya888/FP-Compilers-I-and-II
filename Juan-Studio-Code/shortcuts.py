# This Python file uses the following encoding: utf-8
from PySide6.QtGui import QShortcut, QKeySequence

class Shortcuts:
    def __init__(self, parent_widget, tree_manager, editor_manager):
        # Guardamos las referencias
        self.parent = parent_widget
        self.tree = tree_manager
        self.editor = editor_manager

        # Llamamos a la función que configura todos los atajos
        self.setup_shortcuts()

    def setup_shortcuts(self):
        # ==========================================
        # ARCHIVOS Y CARPETAS
        # ==========================================
        QShortcut(QKeySequence("Ctrl+S"), self.parent).activated.connect(self.editor.save_current_page)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self.parent).activated.connect(self.editor.save_as_current_page)
        QShortcut(QKeySequence("Ctrl+N"), self.parent).activated.connect(self.tree.new_file_action)
        QShortcut(QKeySequence("Ctrl+O"), self.parent).activated.connect(self.tree.open_file_action)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self.parent).activated.connect(self.tree.open_dir_action)
        QShortcut(QKeySequence("Ctrl+Q"), self.parent).activated.connect(self.parent.close)

        # ==========================================
        # PESTAÑAS (TABS)
        # ==========================================
        QShortcut(QKeySequence("Ctrl+W"), self.parent).activated.connect(self.close_current_tab)

        # ==========================================
        # EJECUCIÓN Y VISIBILIDAD
        # ==========================================
        QShortcut(QKeySequence("F5"), self.parent).activated.connect(self.run_code)
        QShortcut(QKeySequence("Ctrl+B"), self.parent).activated.connect(self.toggle_sidebar)

        # Mostrar/Ocultar Terminal (Ctrl+` y Ctrl+J como alternativa)
        QShortcut(QKeySequence("Ctrl+`"), self.parent).activated.connect(self.toggle_terminal)
        QShortcut(QKeySequence("Ctrl+J"), self.parent).activated.connect(self.toggle_terminal)


    # -------------------------- Funciones auxiliares para los atajos --------------------------
    def close_current_tab(self):
        """Cierra la pestaña que esté activa en este momento."""
        current_index = self.editor.tabs.currentIndex()
        if current_index >= 0:
            self.editor.close_page(current_index)

    def run_code(self):
        """Lógica para el atajo F5."""
        print("Atajo F5 presionado: ¡Aquí conectaremos el compilador de Python!")
        # Si tienes un botón Run, lo puedes conectar así:
        # self.parent.ui.runButton.click()

    # Metodo para ocultar el panel izquierdo
    def toggle_sidebar(self):
        """Oculta o muestra el panel izquierdo con Ctrl+B."""
        sizes = self.parent.ui.splitter.sizes()
        if sizes[0] > 0:
            self.parent.ui.splitter.setSizes([0, sizes[1]])
        else:
            self.parent.ui.splitter.setSizes([250, sizes[1]])

    # Metodo para cerrar y abrir el tab widget
    def toggle_terminal(self):
            """Oculta o muestra el panel inferior completo."""
            if self.parent.terminal_manager.isVisible():
                self.parent.terminal_manager.hide()
            else:
                self.parent.terminal_manager.show()
