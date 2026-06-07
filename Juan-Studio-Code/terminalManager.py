from PySide6.QtWidgets import QTabWidget, QPlainTextEdit, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import QProcess, Qt, QThread, Signal
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
import os, sys, re

# =====================================================================
# BACKEND MODULE INTEGRATION
# This section ensures that the 'Analizador_Lexico' directory is
# accessible to the Python interpreter, allowing the import of the
# custom SCANNER component.
# =====================================================================
sys.path.append(os.path.join(os.getcwd(), 'Analizador_Lexico'))
from SCAN import SCANNER


# =====================================================================
# MULTI-THREADING COMPONENT: LexerWorker
# This class implements a worker thread to execute the lexical scanner
# in a separate CPU core.
#
# Responsibilities:
# - Isolate heavy lexical analysis from the Main UI Thread.
# - Prevent UI freezing/hanging during large file processing.
# - Emit results via Qt Signals once the background task is complete.
# =====================================================================
class LexerWorker(QThread):
    # Signal that sends the list of tokens and an error message: (tokens_list, error_message)
    finished_signal = Signal(list, str)

    def __init__(self, source_code):
        super().__init__()
        self.source_code = source_code

    def run(self):
        """This method executes automatically in the background."""
        try:
            # Instantiate and execute the scanner logic
            scanner = SCANNER(self.source_code)
            scanner.get_token()

            # Emit successful result with the actual tokens list
            self.finished_signal.emit(scanner.list_tokens, "")
        except Exception as e:
            # Catch unexpected exceptions and propagate the error message
            self.finished_signal.emit([], str(e))


# =====================================================================
# UI COMPONENT: TerminalManager (OUTPUT SYSTEM & INTERACTIVE CONSOLE)
# This class serves as the primary feedback component for the IDE.
# It inherits from QTabWidget to organize compiler output into
# distinct logical stages (Terminal, Lexical, Syntactic, etc.).
#
# Architecture:
# - Implements a real interactive console via QProcess.
# - Manages independent text buffers for each compilation phase.
# - Acts as a Data Sink for backend analysis results.
# =====================================================================
class TerminalManager(QTabWidget):

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
        self.terminal_edit = QPlainTextEdit()
        self.setup_terminal()
        self.addTab(self.terminal_edit, "Terminal")

        # Initialize read-only views for compiler stages
        self.lexico_output = QTreeWidget()
        self.lexico_output.setHeaderLabels(["Token Type", "Lexeme", "Line/Column"])
        self.lexico_output.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333333;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #333333;
                padding: 4px;
            }
        """)
        self.addTab(self.lexico_output, "Lexical Analysis")

        self.sintactico_output = QTreeWidget()
        self.sintactico_output.setHeaderLabels(["Syntax Node", "Value / Code", "Line/Column"])
        self.sintactico_output.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333333;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #333333;
                padding: 4px;
            }
        """)
        self.addTab(self.sintactico_output, "Syntax Analysis")

        self.semantico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.semantico_output, "Waiting for semantic analysis execution...\n")
        self.addTab(self.semantico_output, "Semantic Analysis")

        self.codigo_intermedio = QPlainTextEdit()
        self.setup_analysis_tab(self.codigo_intermedio, "Waiting for intermediate code execution...\n")
        self.addTab(self.codigo_intermedio, "Intermediate Code")

        self.tabla = QPlainTextEdit()
        self.setup_analysis_tab(self.tabla, "Symbol Table...\n")
        self.addTab(self.tabla, "Symbol Table")

        self.errores = QTreeWidget()
        self.errores.setObjectName("errorTreeWidget")
        self.errores.setHeaderLabels(["Error Type / Description", "Position"])
        self.addTab(self.errores, "Errors")
        self.errores.itemDoubleClicked.connect(self.jump_to_error_tree)
        self.terminal_edit.keyPressEvent = self.terminal_keyPressEvent

        # Corner widgets setup
        from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        self.corner_container = QWidget()
        self.corner_layout = QHBoxLayout(self.corner_container)
        self.corner_layout.setContentsMargins(0, 0, 0, 0)
        self.corner_layout.setSpacing(5)

        self.btn_visualize_ast = QPushButton("Visualize Graphical AST")
        self.btn_visualize_ast.setCursor(Qt.PointingHandCursor)
        self.btn_visualize_ast.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d; color: #cccccc; border: 1px solid #333333; padding: 2px 10px; border-radius: 2px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """)
        self.btn_visualize_ast.clicked.connect(self.show_ast_visualization)
        self.btn_visualize_ast.setVisible(False)  # Hidden by default

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
        self.corner_layout.addWidget(self.btn_copy_terminal)

        self.setCornerWidget(self.corner_container, Qt.TopRightCorner)
        self.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        # Only show AST Visualization button when Syntax Analysis is the active tab
        is_syntax_tab = (self.widget(index) == self.sintactico_output)
        self.btn_visualize_ast.setVisible(is_syntax_tab)

    def copy_current_tab(self):
        """Copia el contenido de la pestaña actual al portapapeles."""
        from PySide6.QtWidgets import QApplication
        current_widget = self.currentWidget()
        
        texto_copiar = ""
        if isinstance(current_widget, QPlainTextEdit):
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
        
        if not hasattr(self, 'current_ast') or not self.current_ast:
            QMessageBox.warning(self, "No AST Available", "AST tree not found in memory. Please run a successful Syntax Analysis first.")
            return
            
        try:
            # Import visualization logic
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), 'Analizador_Sintactico'))
            
            # Make sure astVisualizer is importable
            from astVisualizer import ASTHtmlGenerator, ASTVisualizerDialog
            
            # Generate the HTML
            html_content = ASTHtmlGenerator.arbol_a_html(self.current_ast, getattr(self, 'current_syntax_errors', []))
            
            # Instantiate and display the dialog persistently
            if not hasattr(self, '_ast_visualizer_dialog') or self._ast_visualizer_dialog is None:
                self._ast_visualizer_dialog = ASTVisualizerDialog(self)
                
            self._ast_visualizer_dialog.load_html_content(html_content)
            self._ast_visualizer_dialog.show()
            self._ast_visualizer_dialog.raise_()
            self._ast_visualizer_dialog.activateWindow()
            
        except ImportError as e:
            QMessageBox.critical(self, "Module Error", f"Could not load visualization module: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Visualization Error", f"Error launching AST visualizer: {e}")

    # =====================================================================
    # UTILITY METHOD: setup_analysis_tab
    # What it does: Configures the initial state and permissions of analysis tabs.
    # What components it uses: QPlainTextEdit (Text widget).
    # How it interacts: Locks manual user editing to protect the integrity
    # of the data generated by the compiler.
    # =====================================================================
    def setup_analysis_tab(self, widget, initial_text):
        """Applies read-only configurations to the analysis tabs."""
        widget.setReadOnly(True)
        widget.appendPlainText(initial_text)


    # =====================================================================
    # METHOD: setup_terminal (INTERACTIVE PROCESSING CORE)
    # What it does: Spawns a system sub-process (PowerShell) and connects pipes.
    # What components it uses: QProcess, Standard Input/Output Pipes.
    # How it interacts: Enables the IDE to run console commands like 'python'
    # or 'openssl' by integrating the Windows shell directly into the UI.
    # =====================================================================
    def setup_terminal(self):
        """Initializes the PowerShell process for the main terminal."""
        self.terminal_edit.setReadOnly(False)

        # Asynchronous sub-process engine configuration
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

        self.interactive_position = 0

        # Start shell with UTF-8 encoding forced to avoid encoding artifacts
        self.process.start("powershell.exe", ["-NoExit", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"])


    # =====================================================================
    # PIPE READING METHODS: handle_stdout / handle_stderr
    # What it does: Listens to and redirects the sub-process data flow to the UI.
    # What components it uses: QProcess Standard Read methods, QTextCursor.
    # How it interacts: Updates the view in real-time and maintains the
    # 'interactive position' marker to protect terminal history.
    # =====================================================================
    def handle_stdout(self):
        """Writes PowerShell standard output to the interface."""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')

        # Cursor management for auto-scrolling and buffer positioning
        cursor = self.terminal_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal_edit.setTextCursor(cursor)
        self.terminal_edit.insertPlainText(text)

        # Update watermark to prevent editing of previous shell history
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()

    def handle_stderr(self):
        """Writes PowerShell error stream to the interface."""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')

        self.terminal_edit.insertPlainText(text)
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()


    # =====================================================================
    # METHOD: terminal_keyPressEvent (INPUT INTERCEPTOR)
    # What it does: Validates and processes user keyboard input in the console.
    # What components it uses: QKeyEvent, QProcess.write.
    # How it interacts: Implements 'Shell Emulator' logic, sending commands
    # to the sub-process only on 'Enter' and blocking deletions beyond the
    # current prompt via 'interactive_position' validation.
    # =====================================================================
    def terminal_keyPressEvent(self, event):
        """Controls interactive keyboard input in the terminal."""
        # Prompt protection: prevents deleting or moving cursor into history zones
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.terminal_edit.textCursor().position() <= self.interactive_position:
                return

        # Process commands when Enter is pressed
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.terminal_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.terminal_edit.setTextCursor(cursor)

            # Extract user input text from the last watermark position
            cursor.setPosition(self.interactive_position, QTextCursor.KeepAnchor)
            command = cursor.selectedText().strip()

            # Handle internal UI commands (Clear Screen)
            if command.lower() in ['clear', 'cls']:
                self.terminal_edit.clear()
                self.process.write(b"\n")
                return

            # ---> LA MAGIA SUCEDE AQUÍ <---
            # Eliminamos lo que el usuario escribió en la UI para evitar el duplicado.
            # PowerShell nos devolverá el comando como "Eco", así que aparecerá de nuevo
            # de forma natural y con el salto de línea correcto.
            cursor.removeSelectedText()

            # Send the command string to the PowerShell input stream
            self.process.write((command + "\n").encode('utf-8'))
            return

        # Delegate standard keys to base QPlainTextEdit behavior
        QPlainTextEdit.keyPressEvent(self.terminal_edit, event)

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
    # ASYNCHRONOUS MANAGEMENT: execute_lexical and on_lexical_finished
    # What it does: Initializes the scanner worker and handles its callback.
    # =====================================================================
    def execute_lexical(self, source_code):
            """Processes code using a background thread."""
            self.setCurrentIndex(1)
            self.show()
            self.lexico_output.clear()

            if not source_code:
                item = QTreeWidgetItem(self.lexico_output)
                item.setText(0, "ERROR")
                item.setText(1, "No file selected. Open or save a file first.")
                return

            item = QTreeWidgetItem(self.lexico_output)
            item.setText(0, "INFO")
            item.setText(1, f"Executing lexical analysis...")

            # Prepare worker by passing the file path/source
            self.lexer_thread = LexerWorker(source_code)

            # Connect completion signal to the UI update callback
            self.lexer_thread.finished_signal.connect(self.on_lexical_finished)

            # Start the background worker!
            self.lexer_thread.start()

    def on_lexical_finished(self, tokens_list, error):
        """This function is called automatically when LexerWorker finishes."""
        self.lexico_output.clear()
        
        # Early return if there is some problem
        if error:
            item = QTreeWidgetItem(self.lexico_output)
            item.setText(0, "CRITICAL ERROR")
            item.setText(1, error)
            return
            
        # Resolver problema de Enum y separar errores léxicos
        errors = [t for t in tokens_list if hasattr(t[0], 'name') and t[0].name == "ERROR"]
        valid_tokens = [t for t in tokens_list if not (hasattr(t[0], 'name') and t[0].name in ["ERROR", "COMMENT_LINE", "COMMENT_BLOCK"])]
        
        # Poblar QTreeWidget de errores
        if len(errors) > 0:
            from PySide6.QtGui import QColor
            error_color = QColor("#ff5555")
            for t in errors:
                line = t[2] if len(t) > 2 else "?"
                col = t[3] if len(t) > 3 else "?"
                item = QTreeWidgetItem(self.errores)
                item.setText(0, f"Lexical Error: Unexpected Token ('{t[1]}')")
                item.setText(1, f"Ln {line}, Col {col}")
                item.setForeground(0, error_color)
                item.setForeground(1, error_color)
        
        # Poblar pestaña de Léxico SÓLO con tokens válidos
        for t in valid_tokens:
            item = QTreeWidgetItem(self.lexico_output)
            item.setText(0, str(t[0].name) if hasattr(t[0], 'name') else str(t[0]))
            item.setText(1, str(t[1]))
            line = t[2] if len(t) > 2 else "?"
            col = t[3] if len(t) > 3 else "?"
            item.setText(2, f"Ln {line}, Col {col}")


    def execute_syntactic(self, source_code):
        """Processes code and updates the Syntactic tab."""
        self.setCurrentIndex(2)
        self.show()
        self.sintactico_output.clear()

        if not source_code:
            return

        import sys
        sys.path.append(os.path.join(os.getcwd(), 'Analizador_Sintactico'))
        from analizador_sintactico import Parser, ParserSignals
        
        # Initialize memory storage for AST Visualization
        self.current_ast = None
        self.current_syntax_errors = []
        
        # 1. Run scanner
        scanner = SCANNER(source_code)
        scanner.get_token()
        
        # 2. Setup signals
        signals = ParserSignals()
        
        self.errores.clear()
        
        def handle_error(mensaje, linea, columna):
            from PySide6.QtWidgets import QTreeWidgetItem
            from PySide6.QtGui import QColor
            
            error_text = f"Syntax Error: {mensaje} (Ln {linea}, Col {columna})"
            self.current_syntax_errors.append(error_text)
            
            item = QTreeWidgetItem(self.errores)
            item.setText(0, f"Syntax Error: {mensaje}")
            item.setText(1, f"Ln {linea}, Col {columna}")
            error_color = QColor("#ff5555")
            item.setForeground(0, error_color)
            item.setForeground(1, error_color)
            
        def handle_node(nombre, lexema):
            # La señal node_signal emite cada nodo conforme se crea.
            pass

        signals.error_signal.connect(handle_error)
        signals.node_signal.connect(handle_node)

        # 3. Run parser
        parser = Parser(scanner.list_tokens, signals=signals)
        ast_root = parser.parse()
        
        # Save to memory for visualization
        self.current_ast = ast_root
        
        # 4. Populate QTreeWidget
        def renderizar_ast_en_ui(self_ref, ast_root, tree_widget):
            tree_widget.clear() # Limpiar árbol anterior
            if not ast_root:
                return
                
            def construir_nodos_ui(nodo_datos, parent_ui):
                item = QTreeWidgetItem(parent_ui)
                item.setText(0, nodo_datos.name)
                item.setText(1, str(nodo_datos.value))
                line_str = f"Ln {nodo_datos.line}, Col {nodo_datos.col}" if str(nodo_datos.line).isdigit() else ""
                item.setText(2, line_str)
                
                for hijo in nodo_datos.children:
                    construir_nodos_ui(hijo, item)

            root_item = QTreeWidgetItem(tree_widget)
            root_item.setText(0, ast_root.name)
            root_item.setText(1, str(ast_root.value))
            line_str_root = f"Ln {ast_root.line}, Col {ast_root.col}" if str(ast_root.line).isdigit() else ""
            root_item.setText(2, line_str_root)
            
            for child in ast_root.children:
                construir_nodos_ui(child, root_item)
                
            tree_widget.expandAll()

        self.sintactico_output.setHeaderLabels(["Syntax Node", "Value / Code", "Line/Column"])
        renderizar_ast_en_ui(self, ast_root, self.sintactico_output)

    def execute_semantic(self, source_code):
        """Processes code and updates the Semantic tab."""
        self.setCurrentIndex(3)
        self.show()
        self.semantico_output.clear()

        # Simulated type and scope validation
        resultado_simulado = f"=== SEMANTIC RESULT ===\nValidation for:\n{source_code}"
        self.semantico_output.setPlainText(resultado_simulado)

    def execute_intermediate(self, source_code):
        """Generates and displays intermediate code."""
        self.setCurrentIndex(4)
        self.show()
        self.codigo_intermedio.clear()

        # Simulated 3-address code or quadruples generation
        resultado_simulado = f"=== INTERMEDIATE CODE ===\nQuadruples generated for:\n{source_code}"
        self.codigo_intermedio.setPlainText(resultado_simulado)
