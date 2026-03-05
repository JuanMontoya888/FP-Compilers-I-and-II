# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLabel, QMessageBox
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QTextFormat

# =====================================================================
# ÁREA DE NÚMEROS DE LÍNEA
# =====================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

# =====================================================================
# EDITOR DE CÓDIGO PERSONALIZADO
# =====================================================================
'''
Extiende de QPlainTextEdit para poder generar una pagina en blanco
'''
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2d2d30")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight | Qt.AlignVCenter, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

# =====================================================================
# GESTIÓN DE PESTAÑAS Y ARCHIVOS CON INDICADORES ---------------------
# =====================================================================
'''
Line, Column, Enconding, Languaje ---------------------------------------
'''
class CodePage(QWidget):
    """Representa una sola pestaña/archivo abierto."""
    def __init__(self, content="", file_path="", parent=None):
        super().__init__(parent)
        self.file_path = file_path

        # Layout principal de la pestaña (vertical)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0) # Quitamos el espacio para que la barra se pegue al editor

        # El editor de código
        self.editor = CodeEditor()
        self.editor.setPlainText(content)
        layout.addWidget(self.editor)

        # La barra de estado inferior
        self.status_bar = QWidget()
        self.status_bar.setObjectName("editorStatusBar")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(15, 2, 15, 2)

        # Indicadores
        self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.lbl_encoding = QLabel("Latin-1")
        self.lbl_language = QLabel("txt")

        # Empujamos los elementos hacia la derecha como en VS Code
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_cursor)

        # Agregamos espacios de separación visual
        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_encoding)

        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_language)

        layout.addWidget(self.status_bar)

        # Conectamos el movimiento del cursor para actualizar los indicadores
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.update_cursor_position() # Llamada inicial para establecer valores

    def update_cursor_position(self):
        """Calcula y actualiza la fila y columna actual del cursor."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")


class CodeEditorManager:
    """Gestiona el QTabWidget de la UI principal."""
    def __init__(self, tab_widget):
        self.tabs = tab_widget
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_page)

    def add_new_page(self, title, content, file_path):
        new_page = CodePage(content, file_path)
        index = self.tabs.addTab(new_page, title)
        self.tabs.setCurrentIndex(index)

        # Conectar el evento de escritura para poner el asterisco indicando cambios
        new_page.editor.textChanged.connect(lambda: self.mark_as_unsaved(new_page))

    def mark_as_unsaved(self, page):
        """Agrega un asterisco al nombre de la pestaña si el archivo es modificado."""
        index = self.tabs.indexOf(page)
        if index >= 0:
            title = self.tabs.tabText(index)
            if not title.endswith("*"):
                self.tabs.setTabText(index, title + "*")

    def close_page(self, index):
        """Verifica si hay cambios sin guardar antes de cerrar la pestaña."""
        title = self.tabs.tabText(index)

        # Si tiene asterisco, lanzamos un pop-up preguntando si desea guardar
        if title.endswith("*"):
            respuesta = QMessageBox.question(
                self.tabs,
                "Guardar cambios",
                f"El archivo '{title[:-1]}' tiene cambios sin guardar.\n¿Deseas guardarlo antes de cerrar?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if respuesta == QMessageBox.Save:
                self.tabs.setCurrentIndex(index)
                self.save_current_page()
                # Si después de intentar guardar falló (sigue con asterisco), detenemos el cierre
                if self.tabs.tabText(index).endswith("*"):
                    return
            elif respuesta == QMessageBox.Cancel:
                return # Aborta la acción de cerrar

        # Cierra la pestaña si el usuario seleccionó "Discard" o si no había cambios
        if self.tabs.count() > 0:
            self.tabs.removeTab(index)

    def save_current_page(self):
        """Guarda el archivo, quita el asterisco y muestra pop-ups de estado."""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            title = self.tabs.tabText(current_index)

            if current_page.file_path:
                try:
                    content = current_page.editor.toPlainText()
                    # Mantenemos el encoding latin-1 que solicitaste
                    with open(current_page.file_path, 'w', encoding='latin-1') as f:
                        f.write(content)

                    # Quitamos el asterisco de la pestaña
                    if title.endswith("*"):
                        self.tabs.setTabText(current_index, title[:-1])

                    # Pop-up de éxito
                    QMessageBox.information(self.tabs, "Éxito", "Archivo guardado correctamente.")

                except Exception as e:
                    # Pop-up de error
                    QMessageBox.critical(self.tabs, "Error", f"Error al guardar el archivo:\n{e}")
            else:
                # Pop-up de advertencia si es un archivo nuevo sin ruta
                QMessageBox.warning(self.tabs, "Aviso", "El archivo no tiene ruta. Usa la opción Guardar Como.")
