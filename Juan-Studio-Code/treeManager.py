# This Python file uses the following encoding: utf-8
import os
from PySide6.QtWidgets import QFileSystemModel, QFileDialog, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QDir, QModelIndex

# =====================================================================
# CLASS: TreeManager (NAVIGATION AND MENU SYSTEM)
# This class acts as the primary controller for the interaction between
# the OS file system and the application interface.
#
# Architecture:
# - Model-View: Implements QFileSystemModel to mirror the physical storage.
# - Menu Factory: Imperatively constructs the context-aware top menus.
# - Controller/Proxy: Bridges the file explorer, code editor, and terminal.
# =====================================================================
class TreeManager:

    # =====================================================================
    # METHOD: __init__
    # What it does: Sets up the file system model and binds tree view properties.
    # What components it uses: QFileSystemModel, QTreeView, main_app state.
    # How it interacts: Maps the current working directory to the lateral
    # explorer and binds toolbar buttons to the setup_buttons logic.
    # ============================================================
    def __init__(self, tree_view, ui, editor_manager, terminal_manager, main_app):
        self.tree = tree_view
        self.editor_manager = editor_manager
        self.terminal_manager = terminal_manager
        self.main_app = main_app

        # System file model configuration
        self.model = QFileSystemModel()
        self.model.setRootPath(self.main_app.current_path)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.main_app.current_path))

        # UI Refinement: Hide technical metadata columns for a clean look
        self.tree.setColumnHidden(1, True) # Hide Size
        self.tree.setColumnHidden(2, True) # Hide Type
        self.tree.setColumnHidden(3, True) # Hide Date Modified
        self.tree.header().setStretchLastSection(True)

        # Reference toolbar buttons from the UI form
        self.btn_file = ui.fileButton
        self.btn_edit = ui.editButton
        self.btn_compile = ui.compileButton
        self.btn_terminal = ui.terminalButton

        self.setup_buttons()
        self.tree.doubleClicked.connect(self.on_file_selected)


    # =====================================================================
    # METHOD: on_file_selected
    # What it does: Triggers the "Open File" logic when a user interacts
    # with the tree view.
    # What components it uses: QModelIndex, Python File I/O, editor_manager.
    # How it interacts: Converts the tree index into a physical path,
    # reads the content, and instructs the editor_manager to create a new tab.
    # ============================================================
    def on_file_selected(self, index: QModelIndex):
        """Processes the double-click event on the file explorer tree."""
        file_path = self.model.filePath(index)
        self.main_app.current_file_selected = file_path

        if os.path.isfile(file_path):
            try:
                # Use latin-1 to maintain compatibility with original file encodings
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    file_name = self.model.fileName(index)
                    self.editor_manager.add_new_page(file_name, content, file_path)
            except Exception as e:
                print(f"CRITICAL: Could not read the file: {e}")


    # =====================================================================
    # METHOD: setup_buttons (MENU ORCHESTRATION)
    # What it does: Dynamically populates the toolbar buttons with QMenu objects.
    # What components it uses: QMenu, QAction, QKeySequence.
    # How it interacts: Defines the global action system of the IDE,
    # connecting visual menu items to the functional methods of the class.
    # ============================================================
    def setup_buttons(self):
        """Instantiates and configures the dropdown menus for the top toolbar."""
        # Initialize menu containers
        self.menu_file = QMenu()
        self.menu_edit = QMenu()
        self.menu_compile = QMenu()
        self.menu_terminal = QMenu()

        # ------------------------------------------------------------
        # FILE MENU CONFIGURATION
        # ------------------------------------------------------------
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

        self.menu_file.addActions([new_file, open_file, open_dir])
        self.menu_file.addSeparator()
        self.menu_file.addActions([save_file, save_as_file])
        self.menu_file.addSeparator()
        self.menu_file.addAction(exit_tab)
        self.btn_file.setMenu(self.menu_file)

        # ------------------------------------------------------------
        # EDIT MENU CONFIGURATION
        # ------------------------------------------------------------
        copy_data = QAction("Copy\tCtrl+C", self.btn_edit)
        paste_data = QAction("Paste\tCtrl+V", self.btn_edit)

        copy_data.triggered.connect(self.copy_action)
        paste_data.triggered.connect(self.paste_action)

        self.menu_edit.addActions([copy_data, paste_data])
        self.btn_edit.setMenu(self.menu_edit)

        # ------------------------------------------------------------
        # COMPILE MENU CONFIGURATION
        # ------------------------------------------------------------
        lexico_act = QAction("Lexical Analysis", self.btn_compile)
        sintactico_act = QAction("Syntax Analysis", self.btn_compile)
        semantico_act = QAction("Semantic Analysis", self.btn_compile)
        codigo_intermedio = QAction("Intermediate Code", self.btn_compile)
        ejecutar_act = QAction("Run\tF5", self.btn_compile)

        # Route triggered signals to the terminal manager's tab indices
        lexico_act.triggered.connect(lambda: self.open_terminal_tab(1, True))
        sintactico_act.triggered.connect(lambda: self.open_terminal_tab(2, True))
        semantico_act.triggered.connect(lambda: self.open_terminal_tab(3, True))
        codigo_intermedio.triggered.connect(lambda: self.open_terminal_tab(4, True))
        ejecutar_act.triggered.connect(lambda: self.open_terminal_tab(0, True))

        self.menu_compile.addActions([lexico_act, sintactico_act, semantico_act, codigo_intermedio])
        self.menu_compile.addSeparator()
        self.menu_compile.addAction(ejecutar_act)
        self.btn_compile.setMenu(self.menu_compile)

        # ------------------------------------------------------------
        # TERMINAL MENU CONFIGURATION
        # ------------------------------------------------------------
        toggle_view = QAction("Show/Hide Panel\tCtrl+`", self.btn_terminal)
        clear_cons = QAction("Clear Console", self.btn_terminal)
        kill_proc = QAction("Stop Current Process", self.btn_terminal)

        toggle_view.triggered.connect(self.toggle_terminal_action)
        clear_cons.triggered.connect(self.clear_terminal_action)
        kill_proc.triggered.connect(self.kill_process_action)

        self.menu_terminal.addAction(toggle_view)
        self.menu_terminal.addSeparator()
        self.menu_terminal.addActions([clear_cons, kill_proc])
        self.btn_terminal.setMenu(self.menu_terminal)

        # Visual cleanup: Use professional 'InstantPopup' style
        for btn in [self.btn_file, self.btn_edit, self.btn_compile, self.btn_terminal]:
            btn.setPopupMode(btn.ToolButtonPopupMode.InstantPopup)
            btn.setStyleSheet("QToolButton::menu-indicator { image: none; }")


    # =====================================================================
    # SECTION: INTEGRATED TERMINAL LOGIC
    # These methods manage the operational flow of the integrated shell,
    # including visibility toggles and sub-process lifecycle control.
    # ============================================================

    def toggle_terminal_action(self):
        """Switches terminal visibility state."""
        if self.terminal_manager.isVisible():
            self.terminal_manager.hide()
        else:
            self.terminal_manager.show()

    def clear_terminal_action(self):
        """Purges the terminal text buffer."""
        self.terminal_manager.terminal_edit.clear()
        self.terminal_manager.interactive_position = 0

    def kill_process_action(self):
        """Forces the termination of the active shell process."""
        if self.terminal_manager.process.state() != self.terminal_manager.process.NotRunning:
            self.terminal_manager.process.kill()
            self.terminal_manager.terminal_edit.appendPlainText("\n[PROCESS TERMINATED BY USER]\n")
            self.terminal_manager.interactive_position = self.terminal_manager.terminal_edit.textCursor().position()

    def open_terminal_tab(self, index, execute_analysis=False):
        """Switches focus to a specific console phase (Lexical, Syntax, etc)."""
        if execute_analysis:
            match(index):


                case 1:
                    self.terminal_manager.execute_lexical(self.main_app.current_file_selected)


        self.terminal_manager.setCurrentIndex(index)
        if not self.terminal_manager.isVisible():
            self.terminal_manager.show()


    # =====================================================================
    # SECTION: EDITING AND PERSISTENCE LOGIC
    # These methods act as command wrappers that bridge UI requests to
    # the CodeEditorManager's core logic.
    # ============================================================

    def copy_action(self):
        """Delegates copy command to the active editor instance."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor_manager.tabs.widget(current_index)
            current_page.editor.copy()

    def paste_action(self):
        """Delegates paste command to the active editor instance."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor_manager.tabs.widget(current_index)
            current_page.editor.paste()

    def exit_file_action(self):
        """Requests closure of the current tab buffer."""
        current_index = self.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            self.editor_manager.close_page(current_index)

    def save_file_action(self):
        """Triggers direct file save."""
        self.editor_manager.save_current_page()

    def save_as_file_action(self):
        """Triggers save as dialog."""
        self.editor_manager.save_as_current_page()

    def open_file_action(self):
        """Launches native file selector and updates workspace context."""
        file_path, _ = QFileDialog.getOpenFileName(None, 'Open File', self.main_app.current_path, "All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                file_name = os.path.basename(file_path)
                self.editor_manager.add_new_page(file_name, content, file_path)
                # Synchronize tree to the file's parent folder
                self.tree.setRootIndex(self.model.index(os.path.dirname(file_path)))
            except Exception as e:
                print(f"FILE SYSTEM ERROR: {e}")

    def new_file_action(self):
        """Initializes a blank document in the editor."""
        self.editor_manager.add_new_page("Untitled*", "", "")

    def open_dir_action(self):
        """Changes the root of the file explorer to a new folder selection."""
        dir_path = QFileDialog.getExistingDirectory(None, 'Select Directory', self.main_app.current_path)
        if dir_path:
            self.tree.setRootIndex(self.model.index(dir_path))
