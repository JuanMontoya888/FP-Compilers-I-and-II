from PySide6.QtWidgets import QTabWidget, QPlainTextEdit
from PySide6.QtCore import QProcess, Qt, QThread, Signal
from PySide6.QtGui import QTextCursor
import os
import sys

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
    # Signal that sends two strings upon completion: (result_content, error_message)
    finished_signal = Signal(str, str)

    def __init__(self, source_code):
        super().__init__()
        self.source_code = source_code

    # =====================================================================
    # CORE EXECUTION METHOD: run
    # What it does: Serves as the entry point for the worker thread.
    # What components it uses: SCANNER class (from SCAN module) and File I/O.
    # How it interacts: It instantiates the scanner, triggers the token
    # generation, reads the resulting 'tokens.txt', and emits the
    # finished_signal back to the Main UI.
    # =====================================================================
    def run(self):
        """This method executes automatically in the background."""
        try:
            # Instantiate and execute the scanner logic
            scanner = SCANNER(self.source_code)
            scanner.get_token()

            # Read the resulting output file
            resultado_txt_path = "tokens.txt"
            if os.path.exists(resultado_txt_path):
                with open(resultado_txt_path, 'r', encoding='utf-8') as f:
                    resultado = f.read()
                # Emit successful result with an empty error string
                self.finished_signal.emit(resultado, "")
            else:
                self.finished_signal.emit("", "ERROR: The file 'tokens.txt' was not generated.")
        except Exception as e:
            # Catch unexpected exceptions and propagate the error message
            self.finished_signal.emit("", str(e))


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
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("bottomTabs")

        # Initialize the interactive system terminal
        self.terminal_edit = QPlainTextEdit()
        self.setup_terminal()
        self.addTab(self.terminal_edit, "Terminal")

        # Initialize read-only views for compiler stages
        self.lexico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.lexico_output, "Waiting for lexical analysis execution...\n")
        self.addTab(self.lexico_output, "Lexical Analysis")

        self.sintactico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.sintactico_output, "Waiting for syntax analysis execution...\n")
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

        self.errores = QPlainTextEdit()
        self.setup_analysis_tab(self.errores, "Error Console...\n")
        self.addTab(self.errores, "Errors")

        # Inject custom keyboard handling logic
        self.terminal_edit.keyPressEvent = self.terminal_keyPressEvent


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
                self.lexico_output.setPlainText("ERROR: No file selected. Open or save a file first.")
                return

            self.lexico_output.appendPlainText(f"Executing lexical analysis on: {source_code}...\n")

            # Prepare worker by passing the file path/source
            self.lexer_thread = LexerWorker(source_code)

            # Connect completion signal to the UI update callback
            self.lexer_thread.finished_signal.connect(self.on_lexical_finished)

            # Start the background worker!
            self.lexer_thread.start()

    def on_lexical_finished(self, resultado, error):
        """This function is called automatically when LexerWorker finishes."""
        
        # Early return if there is some problem
        if error:
            self.lexico_output.appendPlainText(f"\nCRITICAL ERROR DURING ANALYSIS:\n{error}")
            return
        
            
        # first split for lines
        li = resultado.split("\n")
        # get lines where exists errors
        errors = [lin for lin in li if lin.startswith("ERROR")]
        
        if len(errors) > 0:
            # First time it will clear terminal, when starts analyzing 
            # a new code, and then will append all errors
            self.errores.clear()
            self.errores.appendPlainText("\tError in lexical analysis ...\n")
            for err in errors:
                self.errores.appendPlainText(f"{err.strip()}")
        
        
        # Finally set all text to lexico_output
        self.lexico_output.appendPlainText(resultado)


    def execute_syntactic(self, source_code):
        """Processes code and updates the Syntactic tab."""
        self.setCurrentIndex(2)
        self.show()
        self.sintactico_output.clear()

        # Simulated AST tree structure
        resultado_simulado = f"=== SYNTACTIC RESULT ===\nAST Tree for:\n{source_code}"
        self.sintactico_output.setPlainText(resultado_simulado)

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
