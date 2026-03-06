# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QTabWidget, QPlainTextEdit
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QTextCursor

# =====================================================================
# CLASE: TerminalManager (SISTEMA DE SALIDA Y CONSOLA INTERACTIVA)
# Esta clase actúa como el componente de retroalimentación principal del IDE.
# Hereda de QTabWidget para organizar la salida del compilador en
# diferentes etapas lógicas (Terminal, Léxico, Sintáctico, etc.).
#
# Arquitectura:
# - Implementa una consola interactiva real mediante QProcess.
# - Gestiona buffers de texto independientes para cada fase del análisis.
# - Actúa como sumidero de datos (Data Sink) para los resultados del backend.
# =====================================================================
class TerminalManager(QTabWidget):

    # =====================================================================
    # MÉTODO: __init__
    # Qué hace: Constructor de la clase que inicializa la estructura de pestañas.
    # Qué componentes usa: QPlainTextEdit para cada vista de salida.
    # Cómo interactúa: Define el objeto 'bottomTabs' para la aplicación de
    # estilos CSS y establece la pestaña interactiva principal (PowerShell).
    # =====================================================================
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("bottomTabs")

        # Inicialización de la consola interactiva de sistema
        self.terminal_edit = QPlainTextEdit()
        self.setup_terminal()
        self.addTab(self.terminal_edit, "Terminal")

        # Inicialización de vistas de solo lectura para el compilador
        self.lexico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.lexico_output, "Esperando ejecución para análisis léxico...\n")
        self.addTab(self.lexico_output, "Análisis Léxico")

        self.sintactico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.sintactico_output, "Esperando ejecución para análisis sintáctico...\n")
        self.addTab(self.sintactico_output, "Análisis Sintáctico")

        self.semantico_output = QPlainTextEdit()
        self.setup_analysis_tab(self.semantico_output, "Esperando ejecución para análisis semántico...\n")
        self.addTab(self.semantico_output, "Análisis Semántico")

        self.codigo_intermedio = QPlainTextEdit()
        self.setup_analysis_tab(self.codigo_intermedio, "Esperando ejecución para código intermedio...\n")
        self.addTab(self.codigo_intermedio, "Código Intermedio")

        # Inyección de lógica personalizada para el manejo de teclado
        self.terminal_edit.keyPressEvent = self.terminal_keyPressEvent


    # =====================================================================
    # MÉTODO: setup_analysis_tab
    # Qué hace: Configura el estado inicial y permisos de las pestañas de análisis.
    # Qué componentes usa: QPlainTextEdit (Widget de texto).
    # Cómo interactúa: Bloquea la edición manual del usuario para proteger
    # la integridad de los resultados generados por el compilador.
    # =====================================================================
    def setup_analysis_tab(self, widget, initial_text):
        """Aplica configuraciones de solo lectura a las pestañas de análisis."""
        widget.setReadOnly(True)
        widget.appendPlainText(initial_text)


    # =====================================================================
    # MÉTODO: setup_terminal (NÚCLEO DE PROCESAMIENTO)
    # Qué hace: Spawnea un subproceso de sistema (PowerShell) y conecta los pipes.
    # Qué componentes usa: QProcess, Pipes de Entrada/Salida Estándar.
    # Cómo interactúa: Permite al IDE ejecutar comandos de consola como
    # 'python' u 'openssl' integrando la terminal de Windows en la UI.
    # =====================================================================
    def setup_terminal(self):
        """Inicializa el proceso de PowerShell para la terminal principal."""
        self.terminal_edit.setReadOnly(False)

        # Configuración del motor de subprocesos asíncronos
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

        self.interactive_position = 0

        # Inicio del shell con forzado de codificación UTF-8 para evitar caracteres erróneos
        self.process.start("powershell.exe", ["-NoExit", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"])


    # =====================================================================
    # MÉTODOS: handle_stdout / handle_stderr
    # Qué hace: Escuchan y redirigen el flujo de datos del subproceso a la UI.
    # Qué componentes usa: QProcess.readAllStandardOutput/Error, QTextCursor.
    # Cómo interactúa: Actualiza la vista en tiempo real y mantiene el control
    # de la 'posición interactiva' para proteger el historial de la terminal.
    # =====================================================================
    def handle_stdout(self):
        """Escribe la salida estándar de PowerShell en la interfaz."""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')

        # Gestión del cursor para auto-scroll y posicionamiento al final del buffer
        cursor = self.terminal_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal_edit.setTextCursor(cursor)
        self.terminal_edit.insertPlainText(text)

        # Actualización de la marca de agua para evitar ediciones en el historial
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()

    def handle_stderr(self):
        """Escribe los errores de PowerShell en la interfaz."""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        self.terminal_edit.insertPlainText(text)
        self.interactive_position = self.terminal_edit.textCursor().position()
        self.terminal_edit.ensureCursorVisible()


    # =====================================================================
    # MÉTODO: terminal_keyPressEvent (INTERCEPTOR DE ENTRADA)
    # Qué hace: Valida y procesa la entrada de teclado del usuario en la consola.
    # Qué componentes usa: QKeyEvent, QProcess.write.
    # Cómo interactúa: Implementa la lógica de 'Shell Emulator', enviando
    # comandos al subproceso solo al presionar 'Enter' y bloqueando el
    # borrado del prompt mediante la validación de 'interactive_position'.
    # =====================================================================
    def terminal_keyPressEvent(self, event):
        """Controla la entrada de teclado interactiva en la terminal."""
        # Protección del prompt: evita borrar o mover el cursor a zonas de historial
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.terminal_edit.textCursor().position() <= self.interactive_position:
                return

        # Procesamiento de comandos al presionar Enter
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.terminal_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.terminal_edit.setTextCursor(cursor)

            # Extracción del texto ingresado por el usuario desde la última marca
            cursor.setPosition(self.interactive_position, QTextCursor.KeepAnchor)
            command = cursor.selectedText().strip()

            # Gestión de comandos internos de la interfaz (Clear)
            if command.lower() in ['clear', 'cls']:
                self.terminal_edit.clear()
                self.process.write(b"\n")
                return

            cursor.clearSelection()
            self.terminal_edit.setTextCursor(cursor)
            self.terminal_edit.insertPlainText("\n")

            # Envío de la cadena de comando al flujo de entrada de PowerShell
            self.process.write((command + "\n").encode('utf-8'))
            return

        # Delegación de teclas estándar al comportamiento base de QPlainTextEdit
        QPlainTextEdit.keyPressEvent(self.terminal_edit, event)


    # =====================================================================
    # SECCIÓN: FUNCIONES DE INTERCEPCIÓN DEL COMPILADOR
    # Estos métodos actúan como la API pública del TerminalManager para
    # recibir datos de los analizadores externos (Backend).
    #
    # Flujo:
    # 1. Cambian el índice de pestaña al módulo correspondiente.
    # 2. Limpian el buffer anterior.
    # 3. Renderizan el nuevo resultado (Léxico, Sintáctico, etc.).
    # =====================================================================

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

        # Simulación de salida de tokens
        resultado_simulado = f"=== RESULTADO LÉXICO ===\nProcesando:\n{source_code}"
        self.lexico_output.setPlainText(resultado_simulado)

    def execute_syntactic(self, source_code):
        """Procesa el código y actualiza la pestaña Sintáctica."""
        self.setCurrentIndex(2)
        self.show()
        self.sintactico_output.clear()

        # Simulación de estructura de árbol AST
        resultado_simulado = f"=== RESULTADO SINTÁCTICO ===\nÁrbol AST para:\n{source_code}"
        self.sintactico_output.setPlainText(resultado_simulado)

    def execute_semantic(self, source_code):
        """Procesa el código y actualiza la pestaña Semántica."""
        self.setCurrentIndex(3)
        self.show()
        self.semantico_output.clear()

        # Simulación de validación de tipos y ámbitos
        resultado_simulado = f"=== RESULTADO SEMÁNTICO ===\nValidación para:\n{source_code}"
        self.semantico_output.setPlainText(resultado_simulado)

    def execute_intermediate(self, source_code):
        """Genera y muestra el código intermedio."""
        self.setCurrentIndex(4)
        self.show()
        self.codigo_intermedio.clear()

        # Simulación de generación de código de tres direcciones o cuádruplos
        resultado_simulado = f"=== CÓDIGO INTERMEDIO ===\nCuádruplos generados para:\n{source_code}"
        self.codigo_intermedio.setPlainText(resultado_simulado)
