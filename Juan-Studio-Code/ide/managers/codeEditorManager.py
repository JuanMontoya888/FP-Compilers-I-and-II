# This Python file uses the following encoding: utf-8
import os
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLabel, QMessageBox, QFileDialog, QMenu, QInputDialog, QToolTip
from PySide6.QtCore import Qt, QRect, QSize, QEvent
from PySide6.QtGui import QPainter, QColor, QTextFormat
from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor, QTextDocument
from PySide6.QtCore import QRegularExpression

from ide.components.theme import Theme
from ide.components.highlighter import Highlighter
from ide.components.search_replace import SearchReplaceWidget

# ============================================================
# ARCHITECTURE: GRAPHICAL EDITOR ENGINE
# This module contains the core components for the IDE's
# text manipulation, including syntax highlighting,
# line numbering gutters, and document lifecycle management.
# ============================================================

# =====================================================================
# CLASS: LineNumberArea (VISUAL GUTTER)
# This component acts as a side canvas linked to the editor to
# render line numbers.
#
# Responsibilities:
# - Provide a dedicated drawing area for line counts.
# - Synchronize its size with the editor's digit count.
# - Delegate paint events to the editor's coordinate system.
# =====================================================================
class LineNumberArea(QWidget):
    # ============================================================
    # METHOD: __init__
    # What it does: Initializes the gutter widget.
    # What components it uses: QWidget base class.
    # Interaction: Stores a reference to the parent CodeEditor to
    # access its font metrics and block counts.
    # ============================================================
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    # ============================================================
    # METHOD: sizeHint
    # What it does: Defines the recommended width for the gutter.
    # What components it uses: QSize.
    # Interaction: Calls the editor's internal width calculation logic.
    # ============================================================
    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    # ============================================================
    # METHOD: paintEvent
    # What it does: Triggered when the gutter needs to be redrawn.
    # Interaction: Passes the event context back to the CodeEditor
    # to handle the actual text rendering.
    # ============================================================
    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)





# =====================================================================
# CLASS: CodeEditor (MAIN EDITING WIDGET)
# A robust extension of QPlainTextEdit that integrates the gutter,
# line highlighting, and viewport synchronization.
#
# Components: LineNumberArea, QPainter, QTextFormat.
# Interaction: Connects text modification signals to UI update
# requests for the gutter and visual markers.
# =====================================================================
class CodeEditor(QPlainTextEdit):
    # ============================================================
    # METHOD: __init__
    # What it does: Sets up the visual editor properties.
    # Interaction: Instantiates the gutter and connects scrolling/cursor
    # signals to local handlers.
    # ============================================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # UI Preference: Code usually doesn't wrap in IDEs
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Signal-Slot connections for real-time reactivity
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.error_selections = []
        self.error_messages = []
        self.highlight_current_line()
        self.tree_manager = None

    # ============================================================
    # METHOD: line_number_area_width
    # What it does: Calculates horizontal space required by numbers.
    # Interaction: Uses current font metrics to ensure the gutter
    # grows as the file reaches 10, 100, or 1000 lines.
    # ============================================================
    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    # ============================================================
    # METHOD: update_line_number_area_width
    # What it does: Resizes the editor's left margin.
    # Interaction: Modifies the viewport margins to prevent text
    # from overlapping with the gutter.
    # ============================================================
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    # ============================================================
    # METHOD: update_line_number_area
    # What it does: Synchronizes gutter scrolling with the editor.
    # Interaction: Triggers partial UI updates to the LineNumberArea
    # during vertical scroll events.
    # ============================================================
    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    # ============================================================
    # METHOD: resizeEvent
    # What it does: Adjusts the gutter geometry when the window resizes.
    # ============================================================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        
        # Reposition the floating search widget if it's visible
        if hasattr(self, 'search_replace_widget') and self.search_replace_widget.isVisible():
            self.search_replace_widget.update_position()

    # ============================================================
    # METHOD: highlight_current_line
    # What it does: Highlights the background of the active line.
    # Components: ExtraSelection, QColor.
    # Interaction: Provides visual feedback on where the cursor is.
    # ============================================================
    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Theme.CURRENT_LINE_BG)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        extra_selections.extend(self.error_selections)
        self.setExtraSelections(extra_selections)

    # ============================================================
    # METHOD: add_error_highlight
    # What it does: Adds a red squiggly line under the specified word.
    # ============================================================
    def add_error_highlight(self, line, col, msg=""):
        selection = QTextEdit.ExtraSelection()
        format = QTextCharFormat()
        format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        format.setUnderlineColor(QColor(Theme.ERROR_SQUIGGLY))
        selection.format = format
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, col)
        
        # Calculate length to next space or semicolon to capture full expressions like 32.32
        block_text = cursor.block().text()[col:]
        import re
        match = re.search(r'[\s;]', block_text)
        length = match.start() if match else len(block_text)
        if length == 0:
            length = 1
            
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, length)
            
        selection.cursor = cursor
        self.error_selections.append(selection)
        
        # Guardar la información del error para el tooltip interactivo
        length = len(cursor.selectedText())
        if msg:
            self.error_messages.append({
                "line": line,
                "start_col": col,
                "end_col": col + length,
                "msg": msg
            })
            
        self.highlight_current_line()

    # ============================================================
    # METHOD: clear_error_highlights
    # What it does: Clears all red squiggly underlines and tooltips.
    # ============================================================
    def clear_error_highlights(self):
        self.error_selections.clear()
        self.error_messages.clear()
        self.highlight_current_line()

    # ============================================================
    # METHOD: event
    # What it does: Intercepts events, particularly ToolTip events,
    # to display error messages when hovering over red squiggly lines.
    # ============================================================
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            cursor = self.cursorForPosition(event.pos())
            line = cursor.blockNumber()
            col = cursor.positionInBlock()
            
            for err in self.error_messages:
                if err["line"] == line and err["start_col"] <= col <= err["end_col"]:
                    QToolTip.showText(event.globalPos(), err["msg"], self)
                    return True
                    
            QToolTip.hideText()
            
        return super().event(event)

    # ============================================================
    # METHOD: lineNumberAreaPaintEvent
    # What it does: The core drawing loop for the line numbers.
    # Components: QPainter, QTextBlock.
    # Interaction: Uses Qt's block iteration system to dynamically
    # map only visible lines to painted numbers on the gutter.
    # ============================================================
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(Theme.GUTTER_BG))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(Theme.GUTTER_TEXT))
                painter.drawText(
                    0, top, self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    # ============================================================
    # METHOD: keyPressEvent
    # What it does: Handles auto-indentation on Enter and block
    # indent/unindent on Tab/Shift+Tab.
    # ============================================================
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        
        # Handle Shift+Tab (Unindent)
        if event.key() == Qt.Key_Backtab:
            cursor.beginEditBlock()
            if cursor.hasSelection():
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                cursor.setPosition(start_pos)
                start_block = cursor.blockNumber()
                cursor.setPosition(end_pos)
                end_block = cursor.blockNumber()
                if cursor.positionInBlock() == 0 and end_block > start_block:
                    end_block -= 1
                
                for i in range(start_block, end_block + 1):
                    cursor.setPosition(self.document().findBlockByNumber(i).position())
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    line_text = cursor.block().text()
                    if line_text.startswith("    "):
                        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                        cursor.removeSelectedText()
                    elif line_text.startswith("\t"):
                        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                        cursor.removeSelectedText()
            else:
                cursor.movePosition(QTextCursor.StartOfBlock)
                line_text = cursor.block().text()
                if line_text.startswith("    "):
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                    cursor.removeSelectedText()
                elif line_text.startswith("\t"):
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                    cursor.removeSelectedText()
            cursor.endEditBlock()
            return

        # Handle Tab (Indent)
        elif event.key() == Qt.Key_Tab:
            if cursor.hasSelection():
                cursor.beginEditBlock()
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                
                cursor.setPosition(start_pos)
                start_block = cursor.blockNumber()
                
                cursor.setPosition(end_pos)
                end_block = cursor.blockNumber()
                
                # If selection ends exactly at the start of a line, don't indent that last line
                if cursor.positionInBlock() == 0 and end_block > start_block:
                    end_block -= 1

                for i in range(start_block, end_block + 1):
                    cursor.setPosition(self.document().findBlockByNumber(i).position())
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    cursor.insertText("    ")
                
                cursor.endEditBlock()
                return
            else:
                cursor.insertText("    ")
                return

        # Handle Return (Auto-indent)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            super().keyPressEvent(event)
            current_block = cursor.block()
            prev_block = current_block.previous()
            
            if prev_block.isValid():
                prev_text = prev_block.text()
                # Find indentation of previous line
                indent = ""
                for char in prev_text:
                    if char in (' ', '\t'):
                        indent += char
                    else:
                        break
                
                # If previous line ends with '{', increase indent
                if prev_text.strip().endswith('{'):
                    indent += "    "
                    
                if indent:
                    cursor.insertText(indent)
            return

        super().keyPressEvent(event)

    # ============================================================
    # METHOD: contextMenuEvent
    # What it does: Overrides the standard right-click context menu.
    # ============================================================
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()

        action_format = menu.addAction("Format Document\tShift+Alt+F")
        action_format.triggered.connect(self.format_document)

        action_find = menu.addAction("Find...\tCtrl+F")
        action_find.triggered.connect(self.show_find_dialog)

        action_replace = menu.addAction("Replace...\tCtrl+H")
        action_replace.triggered.connect(self.show_replace_dialog)

        menu.exec_(event.globalPos())

    # ============================================================
    # METHOD: format_document
    # What it does: Basic auto-indentation using braces nesting.
    # ============================================================
    def format_document(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        text = self.toPlainText()
        lines = text.split('\n')
        
        formatted_lines = []
        indent_level = 0
        tab_size = 4
        
        for line in lines:
            stripped = line.strip()
            
            # Decrease indent before processing if line starts with closing brace
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
                
            formatted_lines.append((' ' * (indent_level * tab_size)) + stripped)
            
            # Increase indent after processing if line ends with opening brace
            if stripped.endswith('{'):
                indent_level += 1
                
        self.setPlainText('\n'.join(formatted_lines))
        
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    # ============================================================
    # METHOD: show_find_dialog
    # What it does: Shows the inline search widget
    # ============================================================
    def show_find_dialog(self):
        # Notify the widget to show itself
        if hasattr(self, 'search_replace_widget'):
            self.search_replace_widget.show_find()

    # ============================================================
    # METHOD: show_replace_dialog
    # What it does: Shows the inline replace widget
    # ============================================================
    def show_replace_dialog(self):
        if hasattr(self, 'search_replace_widget'):
            self.search_replace_widget.show_replace()


# =====================================================================
# CLASS: CodePage (TAB CONTAINER)
# Encapsulates an editor, its highlighter, and a status bar into a
# single widget to be used within the main tab interface.
#
# Components: CodeEditor, Highlighter, QLabel, QVBoxLayout.
# Interaction: Serves as the data unit for the CodeEditorManager.
# =====================================================================
class CodePage(QWidget):
    # ============================================================
    # METHOD: __init__
    # What it does: Constructs the layout for a single open file tab.
    # Interaction: Links the cursor movement to the status bar update logic.
    # ============================================================
    def __init__(self, content="", file_path="", parent=None):
        super().__init__(parent)
        self.file_path = file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Editor setup
        self.editor = CodeEditor(self)
        self.editor.setPlainText(content)
        
        # Search/Replace widget (floating overlay, parent is editor)
        self.editor.search_replace_widget = SearchReplaceWidget(self.editor, self.editor)
        
        layout.addWidget(self.editor)

        # Attach syntax highligher to this specific document
        self.highlighter = Highlighter(self.editor.document())

        # Status Bar UI construction
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

    # ============================================================
    # METHOD: update_cursor_position
    # What it does: Updates Ln/Col labels based on cursor coordinates.
    # ============================================================
    def update_cursor_position(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")


# =====================================================================
# CLASS: CodeEditorManager (DOCUMENTS CONTROLLER)
# Orchestrates the lifecycle of multiple tabs, including opening,
# saving, closing, and tracking unsaved changes.
#
# Components: QTabWidget, QMessageBox, QFileDialog.
# Interaction: Connects to the main app to update global context
# based on which tab is currently selected.
# =====================================================================
class CodeEditorManager:
    # ============================================================
    # METHOD: __init__
    # What it does: Initializes the tab management logic.
    # Interaction: Connects tab closure signals to the local handler.
    # ============================================================
    def __init__(self, tab_widget, main_app):
        self.tabs = tab_widget
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_page)
        self.main_app = main_app
        self.tabs.currentChanged.connect(self.update_context_from_tab)

    # ============================================================
    # METHOD: update_context_from_tab
    # What it does: Updates global application paths when switching tabs.
    # ============================================================
    def update_context_from_tab(self, index):
            if index >= 0:
                page = self.tabs.widget(index)
                if hasattr(page, 'file_path') and page.file_path:
                    self.main_app.current_path = os.path.dirname(page.file_path)
                    self.main_app.current_file_selected = page.file_path

    # ============================================================
    # METHOD: add_new_page
    # What it does: Creates a new tab for a file.
    # Interaction: Checks if the file is already open before spawning
    # a new tab. Connects text change detection to the "*" unsaved marker.
    # ============================================================
    def add_new_page(self, title, content, file_path):
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if page.file_path == file_path and file_path != "":
                self.tabs.setCurrentIndex(i)
                return

        new_page = CodePage(content, file_path)
        index = self.tabs.addTab(new_page, title)
        self.tabs.setCurrentIndex(index)
        new_page.editor.textChanged.connect(lambda: self.mark_as_unsaved(new_page))

    # ============================================================
    # METHOD: mark_as_unsaved
    # What it does: Appends an asterisk to the tab title.
    # ============================================================
    def mark_as_unsaved(self, page):
        index = self.tabs.indexOf(page)
        if index >= 0:
            title = self.tabs.tabText(index)
            if not title.endswith("*"):
                self.tabs.setTabText(index, title + "*")

    # ============================================================
    # METHOD: close_page
    # What it does: Safely closes a tab.
    # Interaction: Displays a confirmation dialog if the file has
    # unsaved changes ("*").
    # ============================================================
    def close_page(self, index):
        title = self.tabs.tabText(index)

        if title.endswith("*"):
            response = QMessageBox.question(
                self.tabs,
                "Save Changes",
                f"The file '{title[:-1]}' has unsaved changes.\nDo you want to save it before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if response == QMessageBox.Save:
                self.tabs.setCurrentIndex(index)
                self.save_current_page()
                if self.tabs.tabText(index).endswith("*"):
                    return
            elif response == QMessageBox.Cancel:
                return

        if self.tabs.count() > 0:
            self.tabs.removeTab(index)

    # ============================================================
    # METHOD: save_current_page
    # What it does: Writes the buffer to disk.
    # Interaction: Delegates to "Save As" if no path is established.
    # ============================================================
    def save_current_page(self):
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            title = self.tabs.tabText(current_index)

            if current_page.file_path:
                try:
                    content = current_page.editor.toPlainText()
                    with open(current_page.file_path, 'w', encoding='latin-1') as f:
                        f.write(content)

                    if title.endswith("*"):
                        self.tabs.setTabText(current_index, title[:-1])

                    self.main_app.current_path = os.path.dirname(current_page.file_path)
                    self.main_app.current_file_selected = current_page.file_path

                    QMessageBox.information(self.tabs, "Success", "File saved successfully.")
                except Exception as e:
                    QMessageBox.critical(self.tabs, "Error", f"Error saving file:\n{e}")
            else:
                self.save_as_current_page()

    # ============================================================
    # METHOD: save_as_current_page
    # What it does: Opens a dialog to create or overwrite a file.
    # Interaction: Updates tab title and tree explorer root upon success.
    # ============================================================
    def save_as_current_page(self):
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            current_page = self.tabs.widget(current_index)
            start_path = current_page.file_path
            if not start_path:
                start_path = os.path.join(self.main_app.current_path, "untitled.jpp") if self.main_app.current_path else "untitled.jpp"

            file_path, _ = QFileDialog.getSaveFileName(
                self.tabs,
                "Save As...",
                start_path,
                "JPP Files (*.jpp);;All Files (*.*)"
            )

            if file_path:
                try:
                    content = current_page.editor.toPlainText()
                    with open(file_path, 'w', encoding='latin-1') as f:
                        f.write(content)

                    current_page.file_path = file_path
                    new_name = os.path.basename(file_path)
                    self.tabs.setTabText(current_index, new_name)
                    self.main_app.current_path = os.path.dirname(file_path)

                    if hasattr(self.main_app, 'explorer'):
                        self.main_app.explorer.tree.setRootIndex(
                            self.main_app.explorer.model.index(self.main_app.current_path)
                        )

                    QMessageBox.information(self.tabs, "Success", f"File saved as:\n{new_name}")
                except Exception as e:
                    QMessageBox.critical(self.tabs, "Error", f"Error during Save As:\n{e}")
