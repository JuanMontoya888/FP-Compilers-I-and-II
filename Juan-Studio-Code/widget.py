# This Python file uses the following encoding: utf-8
import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QWidget, QSplitter
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ui_form import Ui_Widget
from treeManager import TreeManager
from codeEditorManager import CodeEditorManager
from shortcuts import Shortcuts
from terminalManager import TerminalManager

# =====================================================================
# MAIN ARCHITECTURE: Widget Class (IDE Orchestrator)
# This class serves as the central "Heart" of the application. It is
# responsible for the coordinated initialization of the User Interface
# (UI) and the synchronous integration of all backend managers.
#
# Design Patterns & Roles:
# - Mediator: Manages communication between the File Tree, Editor, and Terminal.
# - Orchestrator: Ensures resources (icons, layouts) are loaded in order.
# - Dependency Hub: Injects references across different manager instances.
# =====================================================================
class Widget(QWidget):

    # ============================================================
    # METHOD: __init__
    # What it does: Class constructor and entry point for the Widget.
    # What components it uses: Ui_Widget, os module.
    # How it interacts: Initializes the UI form and sets up global
    # state variables (paths/selections) before triggering the
    # specialized configuration sequence.
    # ============================================================
    def __init__(self, parent=None):
        """
        Initializes the main window and state variables.
        """
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # Global state tracking for the current workspace
        self.current_path =  "C:/Users/Juan/Desktop/" or os.getcwd()
        self.current_file_selected = None

        # Execute organized setup sequence
        self.setup_icons()
        self.setup_layout()
        self.setup_components()
        self.setup_connections()


    # ============================================================
    # METHOD: setup_icons (ASSET MANAGEMENT)
    # What it does: Resolves resource paths and assigns SVG icons.
    # What components it uses: QIcon, QSize, Absolute path resolution.
    # How it interacts: Links local physical assets to the toolbar
    # buttons defined in the UI form, providing visual identity.
    # ============================================================
    def setup_icons(self):
        """
        Locates SVG resources and maps them to the sidebar buttons.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")
        icon_size = QSize(24, 24)

        # Mapping SVG assets to specific toolbar functionality
        self.ui.lexicoButton.setIcon(QIcon(os.path.join(icons_dir, "lexico.svg")))
        self.ui.lexicoButton.setIconSize(icon_size)

        self.ui.sintacticoButton.setIcon(QIcon(os.path.join(icons_dir, "sintactico.svg")))
        self.ui.sintacticoButton.setIconSize(icon_size)

        self.ui.semanticoButton.setIcon(QIcon(os.path.join(icons_dir, "semantico.svg")))
        self.ui.semanticoButton.setIconSize(icon_size)

        self.ui.codIntButton.setIcon(QIcon(os.path.join(icons_dir, "intermedio.svg")))
        self.ui.codIntButton.setIconSize(icon_size)

        self.ui.runButton_.setIcon(QIcon(os.path.join(icons_dir, "play.svg")))
        self.ui.runButton_.setIconSize(icon_size)

        self.ui.errorButton.setIcon(QIcon(os.path.join(icons_dir, "bug.svg")))
        self.ui.errorButton.setIconSize(icon_size)

        self.ui.tablaSimbolosButton.setIcon(QIcon(os.path.join(icons_dir, "table.svg")))
        self.ui.tablaSimbolosButton.setIconSize(icon_size)

        self.ui.saveAsFileButton.setIcon(QIcon(os.path.join(icons_dir, "save_as.svg")))
        self.ui.saveAsFileButton.setIconSize(icon_size)

        self.ui.saveFileButton.setIcon(QIcon(os.path.join(icons_dir, "save.svg")))
        self.ui.saveFileButton.setIconSize(icon_size)

        self.ui.newDirectoryButton.setIcon(QIcon(os.path.join(icons_dir, "new_folder.svg")))
        self.ui.newDirectoryButton.setIconSize(icon_size)

        # Accessibility: Defining tooltips for the button interface
        self.ui.saveFileButton.setToolTip("Save current file")
        self.ui.saveAsFileButton.setToolTip("Save file as...")
        self.ui.newDirectoryButton.setToolTip("Open directory")
        self.ui.runButton_.setToolTip("Run / Open Terminal")
        self.ui.lexicoButton.setToolTip("Lexical Analysis")
        self.ui.sintacticoButton.setToolTip("Syntax Analysis")
        self.ui.semanticoButton.setToolTip("Semantic Analysis")
        self.ui.codIntButton.setToolTip("Intermediate Code")
        self.ui.tablaSimbolosButton.setToolTip("View Symbol Table")
        self.ui.errorButton.setToolTip("View Error Console")


    # ============================================================
    # METHOD: setup_components (LOGICAL BRAIN INITIALIZATION)
    # What it does: Instantiates specialized managers and links them.
    # What components it uses: CodeEditorManager, TreeManager, Shortcuts.
    # How it interacts: Performs dependency injection by cross-referencing
    # managers (e.g., Tree knows about Editor) to enable integrated workflows.
    # ============================================================
    def setup_components(self):
        """
        Initializes logic controllers and registers global hotkeys.
        """
        # Orchestrate tab and text editing logic
        self.editor_manager = CodeEditorManager(self.ui.tabWidget, self)

        # Orchestrate File System interaction linked to the editor and terminal
        self.explorer = TreeManager(self.ui.treeView, self.ui, self.editor_manager, self.terminal_manager, self)

        # Attach keyboard shortcut listeners to the window
        self.atajos = Shortcuts(self, self.explorer, self.editor_manager)

        # Final cross-reference injection
        self.editor_manager.tree_manager = self.explorer


    # ============================================================
    # METHOD: setup_layout (UI GEOMETRY & PANEL HIERARCHY)
    # What it does: Configures splitters and embeds the TerminalManager.
    # What components it uses: QSplitter, TerminalManager.
    # How it interacts: Defines the elastic behavior of the workspace,
    # ensuring the editor has priority while keeping the terminal
    # collapsible at the bottom.
    # ============================================================
    def setup_layout(self):
        """
        Defines the visual architecture and initial visibility states.
        """
        # Horizontal Splitter: [Sidebar Explorer | Main Workspace]
        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        # Vertical Splitter: [Code Editor Tabs | Output Consoles]
        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.ui.tabWidget)

        # Terminal injection
        self.terminal_manager = TerminalManager(main_app=self)
        self.v_splitter.addWidget(self.terminal_manager)

        # Initialize with collapsed console
        self.terminal_manager.hide()

        # Layout Priorities: Editor consumes 100% of available vertical space by default
        self.v_splitter.setStretchFactor(0, 1)
        self.v_splitter.setStretchFactor(1, 0)

        # Final integration into the main layout container
        self.ui.splitter.addWidget(self.v_splitter)
        self.ui.splitter.setSizes([200, 800])


    # ============================================================
    # METHOD: setup_connections (EVENT ROUTING)
    # What it does: Establishes the Signal and Slot system for the UI.
    # What components it uses: PySide6 Signal/Slot mechanism.
    # How it interacts: Routes toolbar clicks to the appropriate
    # terminal tab or file system action.
    # ============================================================
    def setup_connections(self):
        """
        Binds interface events to controller logic.
        """
        # Routing Activity Bar clicks to the bottom console switcher
        self.ui.runButton_.clicked.connect(lambda: self.open_bottom_panel(0))
        self.ui.lexicoButton.clicked.connect(lambda: self.open_bottom_panel(1))
        self.ui.sintacticoButton.clicked.connect(lambda: self.open_bottom_panel(2))
        self.ui.semanticoButton.clicked.connect(lambda: self.open_bottom_panel(3))
        self.ui.codIntButton.clicked.connect(lambda: self.open_bottom_panel(4))
        self.ui.tablaSimbolosButton.clicked.connect(lambda: self.open_bottom_panel(5))
        self.ui.errorButton.clicked.connect(lambda: self.open_bottom_panel(6))

        # Connecting file action buttons to the TreeManager API
        self.ui.saveAsFileButton.clicked.connect(self.explorer.save_as_file_action)
        self.ui.saveFileButton.clicked.connect(self.explorer.save_file_action)
        self.ui.newDirectoryButton.clicked.connect(self.explorer.open_dir_action)


    # ============================================================
    # METHOD: open_bottom_panel (VIEW CONTROLLER)
    # What it does: Manages visibility and context of the console area.
    # What components it uses: TerminalManager, Match/Case logic.
    # How it interacts: Triggers backend analysis (Lexical, etc.) based
    # on the active index and forces UI focus on the bottom area.
    # ============================================================
    def open_bottom_panel(self, tab_index):
        """
        Switches console tabs and triggers corresponding compiler logic.
        """
        # Execution Switch: Trigger backend task based on requested view
        match(tab_index):
            case 1:
                # Trigger background lexical processing
                self.terminal_manager.execute_lexical(self.current_file_selected)

        # Switch tab index and ensure the widget is visible to the user
        self.terminal_manager.setCurrentIndex(tab_index)
        if not self.terminal_manager.isVisible():
            self.terminal_manager.show()


# =====================================================================
# BLOCK: MAIN EXECUTION (APPLICATION ENTRY POINT)
# Initializes the global Qt application context and provides a
# high-level exception handler for debugging unexpected crashes.
# =====================================================================
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
