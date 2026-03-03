# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QTextCursor

class TerminalManager(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Propiedad para poder escribir
        self.setReadOnly(False)

        # 2. Tus estilos nivel Dios
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #181818;
                color: #cccccc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: none;
                border-top: 2px solid #007acc;
                padding: 10px;
                selection-background-color: #264f78;
            }
            QScrollBar:vertical {
                border: none;
                background: #181818;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # ==========================================
        # LÓGICA DE QPROCESS (CONEXIÓN A POWERSHELL)
        # ==========================================
        self.process = QProcess(self)

        # Conectamos las "orejas" del proceso para escuchar lo que dice PowerShell
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

        # Variable para saber dónde termina el texto de la consola y dónde empieza a escribir el usuario
        self.interactive_position = 0

        # Iniciamos PowerShell
        self.process.start("powershell.exe", ["-NoExit", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"])

    def handle_stdout(self):
        """Escucha la salida normal de PowerShell y la imprime."""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')

        # Movemos el cursor al final y escribimos la respuesta
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertPlainText(text)

        # Actualizamos la posición segura (el usuario no puede borrar antes de esto)
        self.interactive_position = self.textCursor().position()
        self.ensureCursorVisible()

    def handle_stderr(self):
        """Escucha los errores de PowerShell (letras rojas en una consola normal)."""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        self.insertPlainText(text)
        self.interactive_position = self.textCursor().position()
        self.ensureCursorVisible()

    def keyPressEvent(self, event):
        """Interceptamos las teclas para comportarnos como una terminal real."""
        # 1. Evitamos que el usuario borre el historial o el prompt (Backspace o Flecha Izquierda)
        if event.key() in (Qt.Key_Backspace, Qt.Key_Left):
            if self.textCursor().position() <= self.interactive_position:
                return # Ignoramos la tecla si intenta borrar más allá del límite

        # 2. Si presiona Enter, capturamos el comando y lo enviamos
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

            # Seleccionamos todo lo que el usuario escribió desde el prompt hasta el final
            cursor.setPosition(self.interactive_position, QTextCursor.KeepAnchor)
            command = cursor.selectedText()

            # Quitamos la selección e insertamos el salto de línea visual
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self.insertPlainText("\n")

            # Le enviamos el comando a PowerShell con un salto de línea (\n) para que lo ejecute
            self.process.write((command + "\n").encode('utf-8'))
            return # Evitamos el comportamiento de Enter por defecto

        # Para cualquier otra tecla, dejamos que el QPlainTextEdit funcione normal
        super().keyPressEvent(event)

    def run_python_file(self, file_path):
        """Función lista para cuando programemos el botón RUN."""
        if file_path:
            comando = f'python "{file_path}"\n'
            self.process.write(comando.encode('utf-8'))
