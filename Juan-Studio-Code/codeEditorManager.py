# This Python file uses the following encoding: utf-8
import os
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLabel, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QTextFormat

# ============================================================
# SECCIÓN: COMPONENTES GRÁFICOS DEL EDITOR
# Estos componentes extienden la funcionalidad base de PySide6
# para añadir características esenciales de un IDE, como el
# área de numeración de líneas y el resaltado visual.
# ============================================================

# ============================================================
# CLASE: LineNumberArea
# Qué hace: Actúa como un lienzo (Canvas) lateral vinculado al
# editor para dibujar los números de línea.
# Qué componentes usa: QWidget.
# Cómo interactúa: Es instanciado por 'CodeEditor'. Delega la
# responsabilidad del dibujo al editor principal mediante
# rellamadas (callbacks) en el evento de pintura.
# ============================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        # Define el ancho sugerido basado en el cálculo de dígitos del editor
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        # Redirige el control del dibujo al núcleo del editor
        self.code_editor.lineNumberAreaPaintEvent(event)


# ============================================================
# CLASE: CodeEditor (NÚCLEO DEL EDITOR)
# Qué hace: Extiende QPlainTextEdit para gestionar márgenes
# dinámicos, resaltado de línea actual y renderizado de numeración.
# Qué componentes usa: LineNumberArea, QPainter, QTextFormat.
# Cómo interactúa: Coordina eventos de scroll, cambio de cursor
# y redimensionamiento para mantener sincronizada el área lateral.
# ============================================================
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # Conexión de señales internas para la reactividad de la interfaz
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    #

    def line_number_area_width(self):
        """
        Qué hace: Calcula el ancho dinámico necesario para el margen izquierdo.
        Componentes: fontMetrics.
        Interacción: Escala el margen según la magnitud de líneas (1-9, 10-99, etc).
        """
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Ajusta el margen interno (Viewport) para dejar espacio a la numeración."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Maneja el desplazamiento vertical y la actualización parcial del widget lateral."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Sincroniza la geometría del área de números al cambiar el tamaño del editor."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        """
        Qué hace: Aplica un resaltado visual (ExtraSelection) a la línea activa.
        Componentes: QTextEdit.ExtraSelection, QColor.
        Interacción: Proporciona feedback visual inmediato sobre la posición del cursor.
        """
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2d2d30") # Color oscuro sutil para el fondo
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        """
        Qué hace: Ejecuta el bucle de renderizado para los números de línea.
        Componentes: QPainter, QTextBlock.
        Interacción: Itera solo sobre los bloques de texto visibles para optimizar el rendimiento.
        """
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        # Bucle de dibujo: mapea bloques de texto a coordenadas verticales
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


# ============================================================
# CLASE: CodePage (CONTENEDOR DE PESTAÑA)
# Qué hace: Encapsula el editor y la barra de estado en un solo widget.
# Qué componentes usa: CodeEditor, QLabel, QVBoxLayout.
# Cómo interactúa: Actúa como la unidad mínima que el 'CodeEditorManager'
# inserta en las pestañas del QTabWidget.
# ============================================================
class CodePage(QWidget):
    def __init__(self, content="", file_path="", parent=None):
        super().__init__(parent)
        self.file_path = file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = CodeEditor()
        self.editor.setPlainText(content)
        layout.addWidget(self.editor)

        # Configuración de la barra de indicadores inferior
        self.status_bar = QWidget()
        self.status_bar.setObjectName("editorStatusBar")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(15, 2, 15, 2)

        self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.lbl_encoding = QLabel("Latin-1")
        self.lbl_language = QLabel("txt")

        status_layout.addStretch()
        status_layout.addWidget(self.lbl_cursor)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_encoding)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_language)

        layout.addWidget(self.status_bar)

        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.update_cursor_position()

    def update_cursor_position(self):
        """Extrae la posición del cursor de texto para actualizar la barra de estado."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")


# ============================================================
# CLASE: CodeEditorManager (ORQUESTADOR DE DOCUMENTOS)
# Qué hace: Gestiona el ciclo de vida de los archivos abiertos (Tabs).
# Qué componentes usa: QTabWidget, QMessageBox, QFileDialog.
# Cómo interactúa: Centraliza el guardado, cierre y control de
# cambios (estado modificado '*') de todas las pestañas.
# ============================================================
class CodeEditorManager:
    def __init__(self, tab_widget):
        self.tabs = tab_widget
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_page)

    def add_new_page(self, title, content, file_path):
        """
        Qué hace: Instancia una nueva 'CodePage' y la añade al control de pestañas.
        Interacción: Vincula la señal 'textChanged' para detectar ediciones futuras.
        """
        new_page = CodePage(content, file_path)
        index = self.tabs.addTab(new_page, title)
        self.tabs.setCurrentIndex(index)

        # Activa el sistema de detección de cambios en tiempo real
        new_page.editor.textChanged.connect(lambda: self.mark_as_unsaved(new_page))

    def mark_as_unsaved(self, page):
        """Añade feedback visual (*) al título de la pestaña cuando hay cambios en el editor."""
        index = self.tabs.indexOf(page)
        if index >= 0:
            title = self.tabs.tabText(index)
            if not title.endswith("*"):
                self.tabs.setTabText(index, title + "*")

    def close_page(self, index):
        """
        Qué hace: Gestiona el flujo de cierre de un documento.
        Componentes: QMessageBox.
        Interacción: Intercepta el cierre para prevenir pérdida de datos si hay cambios (*).
        """
        title = self.tabs.tabText(index)

        if title.endswith("*"):
            # Lógica de diálogo de confirmación para archivos modificados
            respuesta = QMessageBox.question(
                self.tabs,
                "Guardar cambios",
                f"El archivo '{title[:-1]}' tiene cambios sin guardar.\n¿Deseas guardarlo antes de cerrar?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if respuesta == QMessageBox.Save:
                self.tabs.setCurrentIndex(index)
                self.save_current_page()
                if self.tabs.tabText(index).endswith("*"):
                    return
            elif respuesta == QMessageBox.Cancel:
                return

        if self.tabs.count() > 0:
            self.tabs.removeTab(index)

    def save_current_page(self):
        """
        Qué hace: Ejecuta la persistencia del archivo actual en disco.
        Componentes: Standard Python open/write.
        Interacción: Si el archivo es nuevo (sin ruta), redirige a 'save_as_current_page'.
        """
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            title = self.tabs.tabText(current_index)

            if current_page.file_path:
                try:
                    content = current_page.editor.toPlainText()
                    with open(current_page.file_path, 'w', encoding='latin-1') as f:
                        f.write(content)

                    # Limpieza del indicador de cambios tras guardado exitoso
                    if title.endswith("*"):
                        self.tabs.setTabText(current_index, title[:-1])

                    QMessageBox.information(self.tabs, "Éxito", "Archivo guardado correctamente.")
                except Exception as e:
                    QMessageBox.critical(self.tabs, "Error", f"Error al guardar el archivo:\n{e}")
            else:
                self.save_as_current_page()

    def save_as_current_page(self):
        """
        Qué hace: Gestiona la creación de nuevos archivos físicos mediante explorador.
        Componentes: QFileDialog.
        Interacción: Actualiza la ruta del objeto 'CodePage' y el título de la pestaña.
        """
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            start_path = current_page.file_path if current_page.file_path else os.getcwd()

            file_path, _ = QFileDialog.getSaveFileName(
                self.tabs,
                "Guardar como...",
                start_path,
                "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
            )

            if file_path:
                try:
                    content = current_page.editor.toPlainText()
                    with open(file_path, 'w', encoding='latin-1') as f:
                        f.write(content)

                    # Sincronización del estado interno con la nueva ubicación física
                    current_page.file_path = file_path
                    new_name = os.path.basename(file_path)
                    self.tabs.setTabText(current_index, new_name)

                    QMessageBox.information(self.tabs, "Éxito", f"Archivo guardado como:\n{new_name}")
                except Exception as e:
                    QMessageBox.critical(self.tabs, "Error", f"Error al guardar como:\n{e}")
