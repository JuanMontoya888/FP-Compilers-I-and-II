# This Python file uses the following encoding: utf-8
from PySide6.QtGui import QShortcut, QKeySequence

# =====================================================================
# CLASS: Shortcuts (KEYBOARD EVENT DISPATCHER)
# This class centralizes the management of keyboard shortcuts for the IDE.
# It serves as a bridge between user input gestures and the underlying
# functional logic of the file tree, editor tabs, and terminal.
#
# Architecture:
# - Decouples keyboard event handling from the main UI class.
# - Provides a unified registry for global hotkeys.
# - Manages cross-component interactions (UI toggles, file operations).
# =====================================================================
class Shortcuts:

    # =====================================================================
    # METHOD: __init__
    # What it does: Initializes the shortcut manager and stores references
    # to essential IDE components.
    # What components it uses: tree_manager, editor_manager.
    # How it interacts: Captures pointers to the main window and managers
    # to trigger their methods when a key sequence is detected.
    # =====================================================================
    def __init__(self, parent_widget, tree_manager, editor_manager):
        # Store references for interaction
        self.parent = parent_widget
        self.tree = tree_manager
        self.editor = editor_manager

        # Execute the configuration of all global shortcuts
        self.setup_shortcuts()


    # =====================================================================
    # METHOD: setup_shortcuts (HOTKEY REGISTRY)
    # What it does: Maps physical key sequences to specific function calls.
    # What components it uses: QShortcut, QKeySequence (PySide6).
    # How it interacts: Connects UI signals (activated) to logic defined
    # within the Editor, Tree, and Terminal systems.
    # =====================================================================
    def setup_shortcuts(self):
        # ==========================================
        # FILES AND DIRECTORIES
        # Logic related to I/O operations and app state.
        # ==========================================
        QShortcut(QKeySequence("Ctrl+S"), self.parent).activated.connect(self.editor.save_current_page)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self.parent).activated.connect(self.editor.save_as_current_page)
        QShortcut(QKeySequence("Ctrl+N"), self.parent).activated.connect(self.tree.new_file_action)
        QShortcut(QKeySequence("Ctrl+O"), self.parent).activated.connect(self.tree.open_file_action)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self.parent).activated.connect(self.tree.open_dir_action)
        QShortcut(QKeySequence("Ctrl+Q"), self.parent).activated.connect(self.parent.close)

        # ==========================================
        # TAB MANAGEMENT
        # Logic to manipulate the editor's workspace tabs.
        # ==========================================
        QShortcut(QKeySequence("Ctrl+W"), self.parent).activated.connect(self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self.parent).activated.connect(self.change_tab)

        # ==========================================
        # EDITOR SHORTCUTS
        # Logic related to text search and replace.
        # ==========================================
        QShortcut(QKeySequence("Ctrl+F"), self.parent).activated.connect(self.find_in_editor)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self.parent).activated.connect(self.replace_in_editor)

        # ==========================================
        # EXECUTION AND VISIBILITY
        # Hotkeys for workspace layout and code processing.
        # ==========================================
        QShortcut(QKeySequence("F5"), self.parent).activated.connect(self.run_code)
        QShortcut(QKeySequence("Ctrl+B"), self.parent).activated.connect(self.toggle_sidebar)

        # Show/Hide Terminal (Ctrl+` and Ctrl+J as alternative)
        QShortcut(QKeySequence("Ctrl+`"), self.parent).activated.connect(self.toggle_terminal)
        QShortcut(QKeySequence("Ctrl+J"), self.parent).activated.connect(self.toggle_terminal)

    # =====================================================================
    # METHOD:  change_tab
    # What it does: change the current tab to the next
    # How it interacts: Connects to the editor component
    # =====================================================================
    def change_tab(self):
        # Get current tabs
        count = self.editor.tabs.count()

        # if current tabs size is 1 there's no where to change
        if count <= 1:
            return

        # Get current tab and calculate next
        current = self.editor.tabs.currentIndex()
        next_index = (current + 1) % count

        # Set next index
        self.editor.tabs.setCurrentIndex(next_index)



    # =====================================================================
    # SECTION: HELPER LOGIC FOR SHORTCUTS
    # These methods implement specific UI behaviors that are triggered
    # by the hotkeys registered in setup_shortcuts.
    # =====================================================================

    # =====================================================================
    # METHOD: close_current_tab
    # What it does: Safely closes the currently focused editor tab.
    # What components it uses: QTabWidget (via editor_manager).
    # How it interacts: Queries the editor for the active index and
    # requests the close_page logic to handle save prompts or buffer removal.
    # =====================================================================
    def close_current_tab(self):
        """Closes the tab that is currently active."""
        current_index = self.editor.tabs.currentIndex()
        if current_index >= 0:
            self.editor.close_page(current_index)


    # =====================================================================
    # METHOD: find_in_editor
    # What it does: Triggers the find dialog on the active code editor.
    # =====================================================================
    def find_in_editor(self):
        """Opens the Find dialog for the current tab."""
        current_index = self.editor.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor.tabs.widget(current_index)
            if hasattr(current_page, 'editor'):
                current_page.editor.show_find_dialog()


    # =====================================================================
    # METHOD: replace_in_editor
    # What it does: Triggers the replace dialog on the active code editor.
    # =====================================================================
    def replace_in_editor(self):
        """Opens the Replace dialog for the current tab."""
        current_index = self.editor.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.editor.tabs.widget(current_index)
            if hasattr(current_page, 'editor'):
                current_page.editor.show_replace_dialog()


    # =====================================================================
    # METHOD: run_code
    # What it does: Trigger mechanism for the compilation/execution phase.
    # Interaction: Serves as a hook to connect the backend compiler.
    # =====================================================================
    def run_code(self):
        """Logic for the F5 shortcut."""
        print("F5 Shortcut pressed: Here we will connect the Python compiler!")
        # If you have a Run button, you can trigger it like this:
        # self.parent.ui.runButton.click()


    # =====================================================================
    # METHOD: toggle_sidebar
    # What it does: Dynamically hides or shows the left file explorer.
    # What components it uses: QSplitter (via parent UI).
    # How it interacts: Modifies the layout distribution (splitter sizes)
    # to expand or collapse the sidebar widget.
    # =====================================================================
    def toggle_sidebar(self):
        """Hides or shows the left panel with Ctrl+B."""
        sizes = self.parent.ui.splitter.sizes()
        if sizes[0] > 0:
            self.parent.ui.splitter.setSizes([0, sizes[1]])
        else:
            self.parent.ui.splitter.setSizes([250, sizes[1]])


    # =====================================================================
    # METHOD: toggle_terminal
    # What it does: Controls the visibility of the bottom terminal manager.
    # What components it uses: TerminalManager (widget).
    # How it interacts: Directly toggles the visibility state of the
    # output console area.
    # =====================================================================
    def toggle_terminal(self):
            """Hides or shows the entire bottom panel."""
            if self.parent.terminal_manager.isVisible():
                self.parent.terminal_manager.hide()
            else:
                self.parent.terminal_manager.show()
