# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QTabWidget, QPlainTextEdit
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QTextCursor

class TerminalManager(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("bottomTabs")

        # --- 1. Terminal ---
        self.terminal_edit = QPlainTextEdit()
        self.setup_terminal()
        self.addTab(self.terminal_edit, "Terminal")

        # --- 2. Léxico ---
        self.lexico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.lexico_output, "Esperando ejecución para análisis léxico...\n")
        self.addTab(self.lexico_output, "Análisis Léxico")

        # --- 3. Sintáctico ---
        self.sintactico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.sintactico_output, "Esperando ejecución para análisis sintáctico...\n")
        self.addTab(self.sintactico_output, "Análisis Sintáctico")

        # --- 4. Semántico ---
        self.semantico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.semantico_output, "Esperando ejecución para análisis semántico...\n")
        self.addTab(self.semantico_output, "Análisis Semántico")

        # --- 5. Código Intermedio ---
        self.codigo_intermedio = QPlainTextEdit()
        self.setup_analysis_tab(self.codigo_intermedio, "Esperando ejecución para código intermedio...\n")
        self.addTab(self.codigo_intermedio, "Código Intermedio")

        self.terminal_edit.keyPressEvent = self.terminal_keyPressEvent

    def setup_analysis_tab(self, widget, initial_text):
        """Aplica configuraciones de solo lectura a las pestañas de análisis."""
        widget.setReadOnly(True)
        widget.appendPlainText(initial_text)

    def setup_terminal(self):
        """Inicializa el proceso de PowerShell para la terminal principal."""
        self.terminal_edit.setReadOnly(False)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.interactive_position = 0
        self.process.start("powershell.exe", ["-NoExit", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"])

    def handle_stdout(self):
        """Escribe la salida estándar de PowerShell en la interfaz."""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        cursor = self.terminal_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal_edit.setTextCursor(cursor)
        self.terminal_edit.insertPlainText(text)
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()

    def handle_stderr(self):
        """Escribe los errores de PowerShell en la interfaz."""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        self.terminal_edit.insertPlainText(text)
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()

    def terminal_keyPressEvent(self, event):
        """Controla la entrada de teclado interactiva en la terminal."""
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.terminal_edit.textCursor().position() <= self.interactive_position:
                return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.terminal_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.terminal_edit.setTextCursor(cursor)

            cursor.setPosition(self.interactive_position, QTextCursor.KeepAnchor)
            command = cursor.selectedText().strip()

            if command.lower() in ['clear', 'cls']:
                self.terminal_edit.clear()
                self.process.write(b"\n")
                return

            cursor.clearSelection()
            self.terminal_edit.setTextCursor(cursor)
            self.terminal_edit.insertPlainText("\n")
            self.process.write((command + "\n").encode('utf-8'))
            return

        QPlainTextEdit.keyPressEvent(self.terminal_edit, event)

    # ==========================================
    # FUNCIONES DE INTERCEPCIÓN DEL COMPILADOR
    # ==========================================

    def run_python_file(self, file_path):
        """Ejecución estándar en terminal."""
        self.setCurrentIndex(0)
        self.show()
        if file_path:
            comando = f'python "{file_path}"\n'
            self.process.write(comando.encode('utf-8'))

    def execute_lexical(self, source_code):
        """Procesa el código y actualiza la pestaña Léxica."""
        self.setCurrentIndex(1)
        self.show()
        self.lexico_output.clear()

        # AQUÍ: analizador léxico real ------------------------------------------
        # resultado = mi_lexer.analizar(source_code)

        resultado_simulado = f"=== RESULTADO LÉXICO ===\nProcesando:\n{source_code}"
        self.lexico_output.setPlainText(resultado_simulado)

    def execute_syntactic(self, source_code):
        """Procesa el código y actualiza la pestaña Sintáctica."""
        self.setCurrentIndex(2)
        self.show()
        self.sintactico_output.clear()

        # AQUÍ:analizador sintáctico real ------------------------------------------

        resultado_simulado = f"=== RESULTADO SINTÁCTICO ===\nÁrbol AST para:\n{source_code}"
        self.sintactico_output.setPlainText(resultado_simulado)

    def execute_semantic(self, source_code):
        """Procesa el código y actualiza la pestaña Semántica."""
        self.setCurrentIndex(3)
        self.show()
        self.semantico_output.clear()

        # analizador semántico real ------------------------------------------

        resultado_simulado = f"=== RESULTADO SEMÁNTICO ===\nValidación para:\n{source_code}"
        self.semantico_output.setPlainText(resultado_simulado)


    def execute_intermediate(self, source_code):
        """Genera y muestra el código intermedio."""
        self.setCurrentIndex(4)
        self.show()
        self.codigo_intermedio.clear()

        # AQUÍ: generador de código intermedio ------------------------------------------

        resultado_simulado = f"=== CÓDIGO INTERMEDIO ===\nCuádruplos generados para:\n{source_code}"
        self.codigo_intermedio.setPlainText(resultado_simulado)
