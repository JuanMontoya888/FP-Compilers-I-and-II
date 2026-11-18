from PySide6.QtWidgets import (
    QTabWidget, QPlainTextEdit, QTreeWidget, QTreeWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QLabel,
    QMessageBox, QApplication,
)
from PySide6.QtCore import QProcess, Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor, QColor, QFont
import os, sys, re
from typing import Optional

# =====================================================================
# BACKEND MODULE INTEGRATION
# Uses the pure-Python CompilerPipeline and background CompilationWorker.
# =====================================================================
from compiler.pipeline import CompilationResult, CompilerPipeline
from ide.components.interactive_terminal import InteractiveTerminal
from ide.core.compiler_worker import CompilationWorker


# =====================================================================
# UI COMPONENT: TerminalManager (OUTPUT SYSTEM & INTERACTIVE CONSOLE)
# =====================================================================
class TerminalManager(QTabWidget):
    diagnostics_updated = Signal(list)
    compilation_completed = Signal(object, str, bool)

    # =====================================================================
    # METHOD: __init__
    # What it does: Constructor that initializes the tab structure and consoles.
    # What components it uses: QPlainTextEdit for each output view.
    # How it interacts: Sets the 'bottomTabs' object name for CSS styling
    # and initializes the main interactive shell (PowerShell) and
    # read-only tabs for compiler analysis phases.
    # =====================================================================
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        
        # reference to principal class
        self.main_app = main_app
        
        self.setObjectName("bottomTabs")

        # Initialize the interactive system terminal
        self.terminal_edit = InteractiveTerminal()
        self.setup_terminal()
        self.addTab(self.terminal_edit, "Terminal")

        # Initialize read-only views for compiler stages
        self.lexico_output = QTreeWidget()
        self.lexico_output.setHeaderLabels(["Token Type", "Lexeme", "Line/Column"])
        self.lexico_output.setAlternatingRowColors(True)
        self.lexico_output.setColumnWidth(0, 220)
        self.lexico_output.setColumnWidth(1, 260)
        self.addTab(self.lexico_output, "Lexical Analysis")

        self.sintactico_output = QTreeWidget()
        self.sintactico_output.setHeaderLabels(["Syntax Node", "Value / Code", "Line/Column"])
        self.sintactico_output.setAlternatingRowColors(True)
        self.sintactico_output.setColumnWidth(0, 260)
        self.sintactico_output.setColumnWidth(1, 260)
        self.addTab(self.sintactico_output, "Syntax Analysis")

        self.semantico_output = QTreeWidget()
        self.semantico_output.setHeaderLabels(["Semantic Node", "Value / Code", "Line/Column"])
        self.semantico_output.setAlternatingRowColors(True)
        self.semantico_output.setColumnWidth(0, 260)
        self.semantico_output.setColumnWidth(1, 260)
        self.setup_analysis_tab(self.semantico_output, "Waiting for semantic analysis execution...\n")
        self.addTab(self.semantico_output, "Semantic Analysis")

        # Tab 4: Intermediate Code (side-by-side .tm and .ci viewers)
        self.codigo_intermedio = QWidget()
        intermedio_layout = QVBoxLayout(self.codigo_intermedio)
        intermedio_layout.setContentsMargins(0, 0, 0, 0)
        intermedio_layout.setSpacing(0)

        self.intermediate_splitter = QSplitter(Qt.Horizontal)

        mono_font = QFont("Consolas", 10)
        mono_font.setStyleHint(QFont.Monospace)

        tm_panel = QWidget()
        tm_layout = QVBoxLayout(tm_panel)
        tm_layout.setContentsMargins(0, 0, 0, 0)
        tm_layout.setSpacing(0)
        self.lbl_tm_header = QLabel("  Código Objeto TM (.tm)")
        self.lbl_tm_header.setStyleSheet(
            "background-color: #1b3a4b; color: #4ec9b0; font-weight: bold; "
            "padding: 5px 8px; border-bottom: 1px solid #2a5a73;"
        )
        self.tm_code_edit = QPlainTextEdit()
        self.tm_code_edit.setFont(mono_font)
        self.tm_code_edit.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: none; }"
        )
        self.setup_analysis_tab(self.tm_code_edit, "Waiting for TM target code generation (.tm)...\n")
        tm_layout.addWidget(self.lbl_tm_header)
        tm_layout.addWidget(self.tm_code_edit)

        ci_panel = QWidget()
        ci_layout = QVBoxLayout(ci_panel)
        ci_layout.setContentsMargins(0, 0, 0, 0)
        ci_layout.setSpacing(0)
        self.lbl_ci_header = QLabel("  Código Intermedio de Tres Direcciones (.ci)")
        self.lbl_ci_header.setStyleSheet(
            "background-color: #2d2d2d; color: #dcdcaa; font-weight: bold; "
            "padding: 5px 8px; border-bottom: 1px solid #3c3c3c;"
        )
        self.ci_code_edit = QPlainTextEdit()
        self.ci_code_edit.setFont(mono_font)
        self.ci_code_edit.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: none; }"
        )
        self.setup_analysis_tab(self.ci_code_edit, "Waiting for three-address intermediate code generation (.ci)...\n")
        ci_layout.addWidget(self.lbl_ci_header)
        ci_layout.addWidget(self.ci_code_edit)

        self.intermediate_splitter.addWidget(tm_panel)
        self.intermediate_splitter.addWidget(ci_panel)
        self.intermediate_splitter.setStretchFactor(0, 1)
        self.intermediate_splitter.setStretchFactor(1, 1)
        self.intermediate_splitter.setSizes([500, 500])

        intermedio_layout.addWidget(self.intermediate_splitter)
        self.addTab(self.codigo_intermedio, "Intermediate Code")

        self.tabla = QTreeWidget()
        self.tabla.setHeaderLabels(["Name/Lexema", "Data Type", "Value", "Memory Offset", "Lines Referenced"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setColumnWidth(0, 180)
        self.tabla.setColumnWidth(1, 120)
        self.setup_analysis_tab(self.tabla, "Symbol Table...\n")
        self.addTab(self.tabla, "Symbol Table")

        self.errores = QTreeWidget()
        self.errores.setObjectName("errorTreeWidget")
        self.errores.setHeaderLabels(["Error Type / Description", "Position"])
        self.errores.setAlternatingRowColors(True)
        self.errores.setColumnWidth(0, 520)
        self.addTab(self.errores, "Errors")
        self.errores.itemDoubleClicked.connect(self.jump_to_error_tree)

        # Corner widgets setup
        self.corner_container = QWidget()
        self.corner_layout = QHBoxLayout(self.corner_container)
        self.corner_layout.setContentsMargins(0, 0, 0, 0)
        self.corner_layout.setSpacing(5)

        self.btn_visualize_ast = QPushButton("Visualizar AST (Qt)")
        self.btn_visualize_ast.setCursor(Qt.PointingHandCursor)
        self.btn_visualize_ast.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d; color: #cccccc; border: 1px solid #333333; padding: 2px 10px; border-radius: 2px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """)
        self.btn_visualize_ast.clicked.connect(self.show_ast_visualization)
        self.btn_visualize_ast.setVisible(False)  # Hidden by default

        self.btn_browser_ast = QPushButton("Abrir AST (Navegador)")
        self.btn_browser_ast.setCursor(Qt.PointingHandCursor)
        self.btn_browser_ast.setStyleSheet("""
            QPushButton {
                background-color: #1b3a4b; color: #4ec9b0; border: 1px solid #2a5a73; padding: 2px 10px; border-radius: 2px; font-weight: bold;
            }
            QPushButton:hover { background-color: #24526b; color: #ffffff; }
        """)
        self.btn_browser_ast.clicked.connect(self.show_html_ast_visualization)
        self.btn_browser_ast.setVisible(False)

        self.btn_copy_terminal = QPushButton("Copy Result")
        self.btn_copy_terminal.setCursor(Qt.PointingHandCursor)
        self.btn_copy_terminal.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d; color: #cccccc; border: 1px solid #333333; padding: 2px 10px; border-radius: 2px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """)
        self.btn_copy_terminal.clicked.connect(self.copy_current_tab)

        self.corner_layout.addWidget(self.btn_visualize_ast)
        self.corner_layout.addWidget(self.btn_browser_ast)
        self.corner_layout.addWidget(self.btn_copy_terminal)

        self.setCornerWidget(self.corner_container, Qt.TopRightCorner)
        self.currentChanged.connect(self._on_tab_changed)

        # Decoupled compiler pipeline & background worker state
        self.pipeline = CompilerPipeline(self._get_project_root())
        self._active_worker: Optional[CompilationWorker] = None
        self._running_workers: set[CompilationWorker] = set()
        self._pending_run_after_compile: bool = False
        self.current_tokens = []
        self.current_ast = None
        self.current_semantic_ast = None
        self.current_syntax_errors = []
        self.current_semantic_errors = []

    def _on_tab_changed(self, index):
        # Show AST Visualization buttons when Syntax Analysis or Semantic Analysis is the active tab
        is_ast_tab = (self.widget(index) == self.sintactico_output or self.widget(index) == self.semantico_output)
        self.btn_visualize_ast.setVisible(is_ast_tab)
        self.btn_browser_ast.setVisible(is_ast_tab)
        
        if self.widget(index) == self.errores:
            self.stop_error_blink()

    def get_current_editor(self):
        if not self.main_app: return None
        current_index = self.main_app.editor_manager.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.main_app.editor_manager.tabs.widget(current_index)
            if hasattr(current_page, 'editor'):
                return current_page.editor
        return None

    def alert_errors_tab(self):
        index = self.indexOf(self.errores)
        if self.currentIndex() == index:
            return
            
        if not hasattr(self, 'blink_timer'):
            from PySide6.QtCore import QTimer
            self.blink_timer = QTimer(self)
            self.blink_timer.timeout.connect(self._toggle_error_tab_color)
            
        self.blink_state = False
        self.blink_timer.start(500)

    def _toggle_error_tab_color(self):
        index = self.indexOf(self.errores)

        self.blink_state = not getattr(self, 'blink_state', False)
        color = QColor("#ff5555") if self.blink_state else QColor()
        self.tabBar().setTabTextColor(index, color)

    def stop_error_blink(self):
        if hasattr(self, 'blink_timer') and self.blink_timer.isActive():
            self.blink_timer.stop()
            index = self.indexOf(self.errores)

            self.tabBar().setTabTextColor(index, QColor())

    def copy_current_tab(self):
        """Copia el contenido de la pestaña actual al portapapeles."""
        from PySide6.QtWidgets import QApplication
        current_widget = self.currentWidget()
        
        texto_copiar = ""
        if current_widget == self.codigo_intermedio:
            tm_text = self.tm_code_edit.toPlainText()
            ci_text = self.ci_code_edit.toPlainText()
            texto_copiar = (
                "=== CÓDIGO OBJETO TM (.tm) ===\n"
                f"{tm_text}\n\n"
                "=== CÓDIGO INTERMEDIO DE TRES DIRECCIONES (.ci) ===\n"
                f"{ci_text}"
            )
        elif isinstance(current_widget, QPlainTextEdit):
            texto_copiar = current_widget.toPlainText()
        elif isinstance(current_widget, QTreeWidget):
            def recurse_tree(item, level=0):
                res = "  " * level + f"|-- {item.text(0)}: {item.text(1)} ({item.text(2)})\n"
                for i in range(item.childCount()):
                    res += recurse_tree(item.child(i), level + 1)
                return res
                
            for i in range(current_widget.topLevelItemCount()):
                texto_copiar += recurse_tree(current_widget.topLevelItem(i))
                
        if texto_copiar:
            QApplication.clipboard().setText(texto_copiar)

    def jump_to_error_tree(self, item, column):
        pos_str = item.text(1)
        import re
        match = re.search(r"Ln\s+(\d+),\s*Col\s+(\d+)", pos_str)
        
        if match and self.main_app:
            target_line = int(match.group(1)) - 1
            target_col = int(match.group(2)) - 1

            current_index = self.main_app.editor_manager.tabs.currentIndex() 
            if current_index >= 0:
                current_page = self.main_app.editor_manager.tabs.widget(current_index)
                editor = current_page.editor

                from PySide6.QtGui import QTextCursor
                editor_cursor = editor.textCursor()
                editor_cursor.movePosition(QTextCursor.Start)
                editor_cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, target_line)
                editor_cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, target_col)
                
                editor.setTextCursor(editor_cursor)
                editor.setFocus()
                editor.highlight_current_line()

    # =====================================================================
    # METHOD: show_ast_visualization
    # What it does: Slot triggered by the Visualize AST button. Uses the in-memory
    # AST object to generate and display a stylized HTML visualization dialog.
    # What components it uses: ASTHtmlGenerator, ASTVisualizerDialog.
    # How it interacts: Opens a pop-up window containing the graphical AST.
    # =====================================================================
    def show_ast_visualization(self):
        from PySide6.QtWidgets import QMessageBox
        
        is_semantic_tab = (self.currentWidget() == self.semantico_output)
        
        target_ast = getattr(self, 'current_semantic_ast', None) if is_semantic_tab else getattr(self, 'current_ast', None)
        target_errors = getattr(self, 'current_semantic_errors', []) if is_semantic_tab else getattr(self, 'current_syntax_errors', [])
        
        if not target_ast:
            QMessageBox.warning(self, "No AST Available", "AST tree not found in memory. Please run the analysis first.")
            return
            
        try:
            # Use the unified scalable graphical visualizer
            from ide.components.tree_visualizer import GraphicalTreeVisualizer
            
            title = "Semantic AST Visualization" if is_semantic_tab else "Syntactic AST Visualization"
            
            # Instantiate and display the dialog persistently
            if not hasattr(self, '_ast_visualizer_dialog') or self._ast_visualizer_dialog is None:
                self._ast_visualizer_dialog = GraphicalTreeVisualizer(self, title)
            else:
                self._ast_visualizer_dialog.setWindowTitle(title)
                
            self._ast_visualizer_dialog.render_tree(target_ast, target_errors)
            self._ast_visualizer_dialog.show()
            self._ast_visualizer_dialog.raise_()
            self._ast_visualizer_dialog.activateWindow()
            
        except ImportError as e:
            QMessageBox.critical(self, "Module Error", f"Could not load visualization module: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Visualization Error", f"Error launching AST visualizer: {e}")

    def show_html_ast_visualization(self):
        from PySide6.QtWidgets import QMessageBox
        from ide.components.html_tree_visualizer import open_ast_in_browser

        is_semantic_tab = (self.currentWidget() == self.semantico_output)
        target_ast = getattr(self, 'current_semantic_ast', None) if is_semantic_tab else getattr(self, 'current_ast', None)
        target_errors = getattr(self, 'current_semantic_errors', []) if is_semantic_tab else getattr(self, 'current_syntax_errors', [])
        title = "Semantic AST Visualization" if is_semantic_tab else "Syntactic AST Visualization"

        if not target_ast:
            target_ast = getattr(self, 'current_semantic_ast', None) or getattr(self, 'current_ast', None)
            target_errors = getattr(self, 'current_semantic_errors', []) or getattr(self, 'current_syntax_errors', [])

        if not target_ast:
            QMessageBox.warning(self, "No AST Available", "AST tree not found in memory. Please run the analysis first.")
            return

        try:
            open_ast_in_browser(target_ast, target_errors, title)
        except Exception as e:
            QMessageBox.critical(self, "Browser Visualization Error", f"Error opening HTML visualizer: {e}")

    # =====================================================================
    # UTILITY METHOD: setup_analysis_tab
    # What it does: Configures the initial state and permissions of analysis tabs.
    # What components it uses: QPlainTextEdit (Text widget).
    # How it interacts: Locks manual user editing to protect the integrity
    # of the data generated by the compiler.
    # =====================================================================
    def setup_analysis_tab(self, widget, initial_text):
        """Applies read-only configurations to the analysis tabs."""
        from PySide6.QtWidgets import QPlainTextEdit, QTreeWidget, QTreeWidgetItem
        if isinstance(widget, QPlainTextEdit):
            widget.setReadOnly(True)
            widget.appendPlainText(initial_text)
        elif isinstance(widget, QTreeWidget):
            item = QTreeWidgetItem(widget)
            item.setText(0, "INFO")
            item.setText(1, initial_text.strip())


    # =====================================================================
    # METHOD: setup_terminal (INTERACTIVE PROCESSING CORE)
    # =====================================================================
    def setup_terminal(self):
        """Initializes the PowerShell shell and managed TM runner process."""
        if hasattr(self, "process") and self.process is not None:
            try:
                self.process.readyReadStandardOutput.disconnect()
                self.process.readyReadStandardError.disconnect()
            except (RuntimeError, TypeError):
                pass
            if self.process.state() != QProcess.ProcessState.NotRunning:
                self.process.kill()

        if hasattr(self, "tm_process") and self.tm_process is not None:
            try:
                self.tm_process.readyReadStandardOutput.disconnect()
                self.tm_process.readyReadStandardError.disconnect()
                self.tm_process.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            if self.tm_process.state() != QProcess.ProcessState.NotRunning:
                self.tm_process.kill()

        self.terminal_edit.clear_terminal()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

        self.tm_process = QProcess(self)
        self.tm_process.readyReadStandardOutput.connect(self._handle_tm_stdout)
        self.tm_process.readyReadStandardError.connect(self._handle_tm_stderr)
        self.tm_process.finished.connect(self._on_tm_finished)

        if not getattr(self, "_terminal_signals_bound", False):
            self.terminal_edit.command_submitted.connect(self._on_terminal_command_submitted)
            self.terminal_edit.interrupt_requested.connect(self.interrupt_terminal_process)
            self.terminal_edit.clear_requested.connect(self.clear_terminal_view)
            self.terminal_edit.tab_completion_requested.connect(self.handle_tab_completion)
            self._terminal_signals_bound = True

        # Start shell with UTF-8 encoding forced to avoid encoding artifacts
        self.process.start(
            "powershell.exe",
            ["-NoExit", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"],
        )

    @property
    def interactive_position(self) -> int:
        return self.terminal_edit.interactive_position

    @interactive_position.setter
    def interactive_position(self, value: int) -> None:
        self.terminal_edit.interactive_position = value

    def handle_stdout(self):
        """Writes PowerShell standard output with ANSI color support."""
        data = bytes(self.process.readAllStandardOutput())
        self.terminal_edit.append_output_bytes(data, is_stderr=False)

    def handle_stderr(self):
        """Writes PowerShell error stream safely at the end of output."""
        data = bytes(self.process.readAllStandardError())
        self.terminal_edit.append_output_bytes(data, is_stderr=True)

    def _handle_tm_stdout(self):
        data = bytes(self.tm_process.readAllStandardOutput())
        self.terminal_edit.append_output_bytes(data, is_stderr=False)

    def _handle_tm_stderr(self):
        data = bytes(self.tm_process.readAllStandardError())
        self.terminal_edit.append_output_bytes(data, is_stderr=True)

    def _on_tm_finished(self, exit_code: int, _exit_status) -> None:
        self.terminal_edit.append_system_message(
            f"\n> Simulador TM finalizado (código {exit_code}).\n",
            color_hex="#569cd6" if exit_code == 0 else "#f48771",
        )
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.write(b"\n")

    def clear_terminal_view(self) -> None:
        self.terminal_edit.clear_terminal()
        if self.tm_process.state() == QProcess.ProcessState.NotRunning and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.write(b"\n")

    def interrupt_terminal_process(self) -> None:
        """Handles Ctrl+C cleanly without killing the entire IDE or freezing Qt."""
        if hasattr(self, "tm_process") and self.tm_process.state() != QProcess.ProcessState.NotRunning:
            self.tm_process.kill()
            self.terminal_edit.append_system_message(
                "\n^C [Simulación TM abortada por el usuario]\n",
                color_hex="#f48771",
            )
            return

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.terminal_edit.append_system_message("\n^C\n", color_hex="#f48771")
            self.setup_terminal()

    def _on_terminal_command_submitted(self, command: str) -> None:
        """Routes submitted input lines either to active TM process (cin) or PowerShell."""
        if hasattr(self, "tm_process") and self.tm_process.state() == QProcess.ProcessState.Running:
            self.tm_process.write((command + "\n").encode("utf-8"))
            return

        if command.strip().lower() in ("clear", "cls"):
            self.clear_terminal_view()
            return

        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.setup_terminal()

        self.process.write((command + "\n").encode("utf-8"))

        # Track working directory best-effort for tab completion
        if command.lower().startswith("cd "):
            target_dir = command[3:].strip().strip('"').strip("'")
            base_dir = getattr(self, "current_terminal_dir", os.getcwd())
            new_dir = os.path.normpath(os.path.join(base_dir, target_dir))
            if os.path.isdir(new_dir):
                self.current_terminal_dir = new_dir

    def terminal_keyPressEvent(self, event):
        """Backwards-compatible entry point delegating to InteractiveTerminal."""
        self.terminal_edit.keyPressEvent(event)

    def handle_tab_completion(self):
        """Implements PowerShell-like tab completion for files and directories."""
        cursor = self.terminal_edit.textCursor()
        
        # If we are already cycling through completions
        if getattr(self.terminal_edit, '_tab_completion_state', None):
            state = self.terminal_edit._tab_completion_state
            state['index'] = (state['index'] + 1) % len(state['matches'])
            
            # Replace current word with new match
            cursor.setPosition(state['start_pos'])
            cursor.setPosition(state['end_pos'], QTextCursor.KeepAnchor)
            
            match = state['matches'][state['index']]
            # Quote if contains space
            if ' ' in match: match = f'"{match}"'
            
            cursor.insertText(match)
            state['end_pos'] = state['start_pos'] + len(match)
            return

        # Start a new completion search
        cursor.setPosition(self.interactive_position, QTextCursor.KeepAnchor)
        input_text = cursor.selectedText()
        
        if not input_text:
            return
            
        # Find the last word being typed
        import shlex
        try:
            # Simple split by spaces, but ignoring spaces inside quotes
            # Fallback to simple split if shlex fails on unclosed quotes
            words = []
            current_word = ""
            in_quotes = False
            quote_char = ""
            for char in input_text:
                if char in ("'", '"'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = ""
                    current_word += char
                elif char == ' ' and not in_quotes:
                    words.append(current_word)
                    current_word = ""
                else:
                    current_word += char
            words.append(current_word)
            last_word = words[-1] if words else ""
        except:
            last_word = input_text.split()[-1] if input_text.split() else ""

        # Remove quotes for searching
        search_term = last_word.strip('"').strip("'")
        
        # Determine base directory and prefix from the prompt
        prompt_cursor = self.terminal_edit.textCursor()
        prompt_cursor.setPosition(self.interactive_position)
        prompt_cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        prompt_text = prompt_cursor.selectedText()
        import re
        match_prompt = re.search(r'PS (([a-zA-Z]:)?[^>]+)>', prompt_text)
        base_dir = match_prompt.group(1).strip() if match_prompt else getattr(self, 'current_terminal_dir', os.getcwd())
        
        if os.path.isabs(search_term):
            search_dir = os.path.dirname(search_term)
            prefix = os.path.basename(search_term)
            user_dir = search_dir
        else:
            search_dir = os.path.dirname(os.path.join(base_dir, search_term))
            prefix = os.path.basename(search_term)
            user_dir = os.path.dirname(search_term)
            
        if not search_dir:
            search_dir = base_dir
            
        if not os.path.exists(search_dir):
            return
            
        # Find matches
        try:
            matches = []
            for item in os.listdir(search_dir):
                if item.lower().startswith(prefix.lower()):
                    # Reconstruct the path relative to what user typed
                    if user_dir:
                        match_path = os.path.join(user_dir, item)
                    else:
                        match_path = ".\\" + item
                        
                    # Add trailing slash for directories
                    full_path = os.path.join(search_dir, item)
                    if os.path.isdir(full_path):
                        matches.append(match_path + "\\")
                    else:
                        matches.append(match_path)
            
            if matches:
                # Calculate positions to replace the word
                # the start_pos is current absolute position minus length of last_word
                end_pos = self.terminal_edit.textCursor().position()
                start_pos = end_pos - len(last_word)
                
                # Replace with first match
                match = matches[0]
                if ' ' in match: match = f'"{match}"'
                
                cursor = self.terminal_edit.textCursor()
                cursor.setPosition(start_pos)
                cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
                cursor.insertText(match)
                
                # Save state for consecutive tabs
                self.terminal_edit._tab_completion_state = {
                    'start_pos': start_pos,
                    'end_pos': start_pos + len(match),
                    'matches': matches,
                    'index': 0
                }
        except Exception as e:
            pass

    # =====================================================================
    # EXECUTION SECTION: COMPILER INTERFACE
    # These methods act as the TerminalManager's public API to receive
    # and trigger data processing from the Backend.
    #
    # General Flow:
    # 1. Switch UI focus to the corresponding tab.
    # 2. Clear previous buffers.
    # 3. Trigger the execution thread or render simulated output.
    # =====================================================================

    def run_python_file(self, file_path):
        """Standard execution in the system terminal."""
        self.setCurrentIndex(0)
        self.show()
        if file_path:
            command = f'python "{file_path}"\n'
            self.process.write(command.encode('utf-8'))

    # =====================================================================
    # ASYNCHRONOUS MANAGEMENT & UNIFIED COMPILER PIPELINE UI SINK
    # =====================================================================

    def _start_compilation_worker(
        self,
        source_code_or_path,
        target_stage: str = "full",
        silent: bool = False,
        run_after: bool = False,
    ) -> None:
        """Runs CompilerPipeline in a background QThread, safely cancelling any older in-flight worker."""
        prev_worker = self._active_worker
        self._active_worker = None
        if prev_worker is not None:
            try:
                if prev_worker.isRunning():
                    prev_worker.cancel()
            except RuntimeError:
                pass

        editor = self.get_current_editor()
        fallback_text = editor.toPlainText() if editor else ""
        self._pending_run_after_compile = run_after

        worker = CompilationWorker(
            source_code_or_path=source_code_or_path,
            fallback_text=fallback_text,
            target_stage=target_stage,
            silent=silent,
            run_after=run_after,
            project_root=self._get_project_root(),
            parent=self,
        )
        self._running_workers.add(worker)
        worker.compilation_finished.connect(self._on_worker_finished)
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self._active_worker = worker
        worker.start()

    def _cleanup_worker(self, worker: CompilationWorker) -> None:
        """Safely clears references before scheduling C++ object deletion."""
        self._running_workers.discard(worker)
        if self._active_worker is worker:
            self._active_worker = None
        try:
            worker.deleteLater()
        except RuntimeError:
            pass

    def _on_worker_finished(self, result: CompilationResult, target_stage: str, silent: bool) -> None:
        """Handles CompilationResult on the main UI thread."""
        sender = self.sender()
        if sender is not None and getattr(sender, "is_cancelled", False):
            return

        self._apply_compilation_result(result, target_stage=target_stage, silent=silent)
        self.compilation_completed.emit(result, target_stage, silent)

        should_run = getattr(sender, "run_after", False) if sender is not None else self._pending_run_after_compile
        if should_run:
            self._pending_run_after_compile = False
            self._launch_tm_execution(result)

    def _populate_lexical_tree(self, valid_tokens) -> None:
        self.lexico_output.clear()
        for t in valid_tokens:
            item = QTreeWidgetItem(self.lexico_output)
            item.setText(0, str(t[0].name) if hasattr(t[0], "name") else str(t[0]))
            item.setText(1, str(t[1]))
            line = t[2] if len(t) > 2 else "?"
            col = t[3] if len(t) > 3 else "?"
            item.setText(2, f"Ln {line}, Col {col}")

    def _apply_compilation_result(
        self,
        result: CompilationResult,
        target_stage: str = "full",
        silent: bool = False,
    ) -> None:
        """Single UI update sink for all compiler stages."""
        editor = self.get_current_editor()
        self.current_tokens = result.all_tokens

        if result.source_code == "" and any(d.phase == "General" for d in result.diagnostics):
            err_dicts = result.errors_as_dicts
            self._populate_errors_tab(err_dicts, editor)
            self.diagnostics_updated.emit(err_dicts)
            self._clear_generated_code_outputs("No source code available. Open or write a .jpp file first.")
            if not silent:
                if target_stage == "lexical":
                    self.lexico_output.clear()
                    item = QTreeWidgetItem(self.lexico_output)
                    item.setText(0, "ERROR")
                    item.setText(1, "No file selected. Open or save a file first.")
                elif target_stage == "syntactic":
                    self.sintactico_output.clear()
                    item = QTreeWidgetItem(self.sintactico_output)
                    item.setText(0, "ERROR")
                    item.setText(1, "No file selected. Open or save a file first.")
                elif target_stage == "semantic":
                    self.semantico_output.clear()
                    item = QTreeWidgetItem(self.semantico_output)
                    item.setText(0, "ERROR")
                    item.setText(1, "No AST found. Please run Syntax Analysis first.")
                self.alert_errors_tab()
            return

        if not silent:
            self._populate_lexical_tree(result.valid_tokens)

        if target_stage in ("syntactic", "semantic", "full"):
            self.current_ast = result.syntactic_ast
            self.current_syntax_errors = list(result.syntax_error_strings)
            if not silent:
                self._populate_ast_tree(result.syntactic_ast, self.sintactico_output)
                try:
                    from ide.components.html_tree_visualizer import export_ast_to_html
                    export_ast_to_html(result.syntactic_ast, self.current_syntax_errors, "Syntactic AST Visualization")
                except Exception:
                    pass

        if target_stage in ("semantic", "full") and result.semantic_ast is not None:
            self.current_semantic_ast = result.semantic_ast
            self.current_semantic_errors = list(result.semantic_error_strings)
            if not silent:
                self._populate_ast_tree(result.semantic_ast, self.semantico_output)
                try:
                    from ide.components.html_tree_visualizer import export_ast_to_html
                    export_ast_to_html(result.semantic_ast, self.current_semantic_errors, "Semantic AST Visualization")
                except Exception:
                    pass
            self._populate_symbol_table(result.symbols)

        err_dicts = result.errors_as_dicts
        self._populate_errors_tab(err_dicts, editor)
        self.diagnostics_updated.emit(err_dicts)

        if target_stage == "full":
            if not result.success or result.diagnostics:
                if not silent:
                    self.alert_errors_tab()
                summary = "\n".join(
                    f"• {d.message} (Ln {d.line}, Col {d.col})" for d in result.diagnostics
                )
                self._clear_generated_code_outputs(
                    "=== COMPILATION ABORTED ===\n"
                    "Fix the following errors before generating .tm / .ci code:\n\n"
                    f"{summary}"
                )
            else:
                self.tm_code_edit.setPlainText(result.tm_code)
                self.ci_code_edit.setPlainText(result.ci_code)
        elif result.diagnostics and not silent:
            self.alert_errors_tab()

    def execute_lexical(self, source_code):
        """Processes lexical analysis using the background CompilationWorker."""
        self.setCurrentIndex(1)
        self.show()
        self.lexico_output.clear()
        self.errores.clear()

        editor = self.get_current_editor()
        if editor:
            editor.clear_error_highlights()

        if not source_code and not (editor and editor.toPlainText().strip()):
            item = QTreeWidgetItem(self.lexico_output)
            item.setText(0, "ERROR")
            item.setText(1, "No file selected. Open or save a file first.")
            return

        item = QTreeWidgetItem(self.lexico_output)
        item.setText(0, "INFO")
        item.setText(1, "Executing lexical analysis...")
        self._start_compilation_worker(source_code, target_stage="lexical", silent=False)

    def execute_syntactic(self, source_code):
        """Processes syntax analysis asynchronously and updates the Syntactic tab."""
        self.setCurrentIndex(2)
        self.show()
        self.sintactico_output.clear()
        self.errores.clear()

        editor = self.get_current_editor()
        if editor:
            editor.clear_error_highlights()

        if not source_code and not (editor and editor.toPlainText().strip()):
            item = QTreeWidgetItem(self.sintactico_output)
            item.setText(0, "ERROR")
            item.setText(1, "No file selected. Open or save a file first.")
            return

        self.sintactico_output.setHeaderLabels(["Syntax Node", "Value / Code", "Line/Column"])
        self._start_compilation_worker(source_code, target_stage="syntactic", silent=False)

    def execute_semantic(self, source_code):
        """Processes semantic analysis asynchronously and updates Semantic & Symbol Table tabs."""
        self.setCurrentIndex(3)
        self.show()
        self.semantico_output.clear()
        self.errores.clear()

        editor = self.get_current_editor()
        if editor:
            editor.clear_error_highlights()

        if not source_code and not (editor and editor.toPlainText().strip()):
            item = QTreeWidgetItem(self.semantico_output)
            item.setText(0, "ERROR")
            item.setText(1, "No AST found. Please run Syntax Analysis first.")
            return

        self.semantico_output.setHeaderLabels(["Semantic Node", "Value / Code", "Line/Column"])
        self._start_compilation_worker(source_code, target_stage="semantic", silent=False)

    def _get_project_root(self) -> str:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(curr_dir))

    def _get_output_dir(self) -> str:
        out_dir = os.path.join(self._get_project_root(), "compiler_output")
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _resolve_source_and_path(self, source_code_or_path):
        """Delegates source resolution to CompilerPipeline."""
        editor = self.get_current_editor()
        fallback_text = editor.toPlainText() if editor else ""
        return self.pipeline.resolve_source(source_code_or_path, fallback_text=fallback_text)

    def _clear_generated_code_outputs(self, reason_msg: str):
        """Updates viewers and removes stale .tm/.ci files so invalid builds cannot be shown or run."""
        self.tm_code_edit.setPlainText(reason_msg)
        self.ci_code_edit.setPlainText(reason_msg)
        self.pipeline.clear_stale_artifacts()

    def _populate_ast_tree(self, ast_root, tree_widget):
        """Populates a QTreeWidget from an ASTNode tree."""
        tree_widget.clear()
        if not ast_root:
            return

        def build_item(node_data, parent_ui):
            item = QTreeWidgetItem(parent_ui)
            item.setText(0, node_data.name)
            item.setText(1, str(node_data.value) if node_data.value is not None else "")
            line_str = f"Ln {node_data.line}, Col {node_data.col}" if str(node_data.line).isdigit() else ""
            item.setText(2, line_str)
            for child in node_data.children:
                build_item(child, item)

        build_item(ast_root, tree_widget)
        tree_widget.expandAll()

    def _populate_symbol_table(self, symbols):
        """Populates the Symbol Table view from SymbolTable.all_symbols."""
        self.tabla.clear()
        for sym in symbols:
            item = QTreeWidgetItem(self.tabla)
            item.setText(0, sym.name)
            item.setText(1, sym.dtype)
            item.setText(2, str(sym.value) if getattr(sym, "value", None) is not None else "-")
            item.setText(3, str(sym.offset))
            item.setText(4, ", ".join(map(str, sym.lines)))

    def _populate_errors_tab(self, all_errors, editor=None):
        """Populates the Errors tab and underlines error locations in the active editor."""
        self.errores.clear()
        if editor:
            editor.clear_error_highlights()

        error_color = QColor("#ff5555")
        for err in all_errors:
            item = QTreeWidgetItem(self.errores)
            msg = err["msg"]
            line = err.get("line", "?")
            col = err.get("col", "?")
            item.setText(0, msg)
            item.setText(1, f"Ln {line}, Col {col}")
            item.setForeground(0, error_color)
            item.setForeground(1, error_color)

            if editor and str(line).isdigit() and str(col).isdigit():
                editor.add_error_highlight(max(0, int(line) - 1), max(0, int(col) - 1), msg)

    def compile_full_pipeline(self, source_code_or_path, silent: bool = False):
        """
        Synchronous wrapper around CompilerPipeline for immediate callers / tests.
        Returns (success: bool, tm_path: Optional[str], errors: list).
        """
        editor = self.get_current_editor()
        fallback_text = editor.toPlainText() if editor else ""
        result = self.pipeline.run(
            source_code_or_path,
            fallback_text=fallback_text,
            target_stage="full",
        )
        self._apply_compilation_result(result, target_stage="full", silent=silent)
        return result.success, result.tm_path, result.errors_as_dicts

    def execute_intermediate(self, source_code):
        """Compiles the full pipeline asynchronously and displays .tm and .ci side by side."""
        self.setCurrentIndex(4)
        self.show()
        self._start_compilation_worker(source_code, target_stage="full", silent=False)

    def _launch_tm_execution(self, result: CompilationResult) -> None:
        self.setCurrentIndex(0)
        self.show()

        if not result.success or not result.tm_path:
            self.terminal_edit.append_system_message(
                "\n[COMPILATION ABORTED] Fix the reported errors (see 'Errors' tab) before running in TM.\n",
                color_hex="#f48771",
            )
            self.alert_errors_tab()
            return

        if hasattr(self, "tm_process") and self.tm_process.state() != QProcess.ProcessState.NotRunning:
            self.tm_process.kill()
            self.tm_process.waitForFinished(300)

        tm_name = os.path.basename(result.tm_path)
        self.terminal_edit.append_system_message(
            f"\n> Ejecutando simulador TM ({tm_name})...\n",
            color_hex="#4ec9b0",
        )

        tm_script_path = os.path.join(self._get_project_root(), "compiler", "tm_simulator", "tm_simulator.py")
        self.tm_process.setWorkingDirectory(self._get_project_root())
        self.tm_process.start(sys.executable, ["-u", tm_script_path, result.tm_path])
        self.terminal_edit.setFocus()

    def execute_run(self, source_code):
        """Compiles the active file asynchronously and runs the generated .tm code inside Terminal."""
        self.setCurrentIndex(0)
        self.show()
        self._start_compilation_worker(source_code, target_stage="full", silent=False, run_after=True)

    def execute_silent_compilation(self, source_code_or_path, active_tab_index=3):
        """
        Runs full compilation asynchronously in a background QThread without stealing focus.
        Updates ASTs, errors, symbol table, and .tm / .ci outputs once finished.
        """
        if not source_code_or_path:
            return
        self._start_compilation_worker(source_code_or_path, target_stage="full", silent=True)
