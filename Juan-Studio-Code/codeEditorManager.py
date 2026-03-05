# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget, QTextEdit
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
# GESTIÓN DE PESTAÑAS Y ARCHIVOS
# =====================================================================
class CodePage(QWidget):
    """Representa una sola pestaña/archivo abierto."""
    def __init__(self, content="", file_path="", parent=None):
        super().__init__(parent)
        self.file_path = file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = CodeEditor()
        self.editor.setPlainText(content)

        layout.addWidget(self.editor)

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

    def close_page(self, index):
        if self.tabs.count() > 0:
            self.tabs.removeTab(index)

    def save_current_page(self):
        """Guarda el contenido de la pestaña activa en su archivo físico."""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            if current_page.file_path:
                try:
                    content = current_page.editor.toPlainText()
                    with open(current_page.file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Éxito: Archivo guardado en {current_page.file_path}")
                except Exception as e:
                    print(f"Error al guardar el archivo: {e}")
            else:
                print("Este archivo no tiene una ruta asignada aún.")
