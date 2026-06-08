# This Python file uses the following encoding: utf-8
import os
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLabel, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QTextFormat
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import QRegularExpression

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
# CLASS: Highlighter (SYNTAX HIGHLIGHTING ENGINE)
# Scans the editor's document using Regular Expressions to apply
# visual styles (colors, bold, italics) to specific code tokens.
#
# Components: QSyntaxHighlighter, QRegularExpression, QTextCharFormat.
# Interaction: Attaches to the QTextDocument of the editor and
# re-highlights text blocks whenever they are modified.
# =====================================================================
class Highlighter(QSyntaxHighlighter):
    # ============================================================
    # METHOD: __init__
    # What it does: Defines the language grammar and visual palette.
    # Components: QTextCharFormat for styling, QRegularExpression for matching.
    # Interaction: Populates a list of rules that map patterns to styles.
    # ============================================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []

        # ----------------------------------------------------
        # STYLING DEFINITIONS (DARK MODE THEME)
        # ----------------------------------------------------

        # Structural Keywords (Pink/Red Monokai style)
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#ff6480"))
        keywordFormat.setFontItalic(True)

        # Data Types (Cyan/Teal)
        typeFormat = QTextCharFormat()
        typeFormat.setForeground(QColor("#56b6c2"))
        typeFormat.setFontItalic(True)

        # Numbers (Light Green)
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor("#B5CEA8"))

        # Strings, Chars, and angle-bracket headers (Orange/Yellow)
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor("#e5c07b"))

        # Operators and Symbols (Light Gray)
        operatorFormat = QTextCharFormat()
        operatorFormat.setForeground(QColor("#AAAAAA"))

        # Comments (Green)
        self.commentFormat = QTextCharFormat()
        self.commentFormat.setForeground(QColor("#6A9955"))
        self.commentFormat.setFontItalic(True)

        # Preprocessor Directives (Purple Bold)
        self.librariesFormat = QTextCharFormat()
        self.librariesFormat.setForeground(QColor("#C586C0"))
        self.librariesFormat.setFontItalic(True)
        self.librariesFormat.setFontWeight(QFont.Bold)

        # ----------------------------------------------------
        # REGEX MAPPING
        # ----------------------------------------------------

        # Structural Keywords mapping
        keywords = [
            r"\bif\b", r"\belse\b", r"\bend\b", r"\bdo\b", r"\bwhile\b", r"\bthen\b",
            r"\bswitch\b", r"\bcase\b", r"\bmain\b", r"\bcin\b", r"\bcout\b",
            r"\bbreak\b", r"\bcontinue\b", r"\bfor\b", r"\bgoto\b", r"\breturn\b",
            r"\btry\b", r"\bcatch\b", r"\bthrow\b", r"\bclass\b", r"\bstruct\b",
            r"\bpublic\b", r"\bprivate\b", r"\bprotected\b", r"\bvirtual\b",
            r"\bfriend\b", r"\binline\b", r"\btemplate\b", r"\btypename\b",
            r"\bthis\b", r"\bnew\b", r"\bdelete\b", r"\benum\b", r"\bunion\b",
            r"\bnamespace\b", r"\busing\b", r"\btypedef\b", r"\bsizeof\b",
            r"\bstatic\b", r"\bconst\b", r"\bextern\b", r"\bexplicit\b",
            r"\boperator\b", r"\bconstexpr\b", r"\bdecltype\b", r"\bnoexcept\b",
            r"\bvolatile\b", r"\bdefault\b", r"\btrue\b", r"\bfalse\b", r"\bnullptr\b"
        ]
        for word in keywords:
            self.highlightingRules.append((QRegularExpression(word), keywordFormat))

        # Data types mapping
        data_types = [
            r"\bint\b", r"\bfloat\b", r"\bstring\b", r"\bbool\b", r"\bchar\b",
            r"\bdouble\b", r"\blong\b", r"\bshort\b", r"\bvoid\b", r"\bauto\b",
            r"\bsigned\b", r"\bunsigned\b", r"\bwchar_t\b"
        ]
        for word in data_types:
            self.highlightingRules.append((QRegularExpression(word), typeFormat))

        # Directives, Numbers, Strings, and Operators rules
        self.highlightingRules.append((QRegularExpression(r"#include"), self.librariesFormat))
        self.highlightingRules.append((QRegularExpression(r"#define"), self.librariesFormat))
        self.highlightingRules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), numberFormat))
        self.highlightingRules.append((QRegularExpression(r'".*"'), stringFormat))
        self.highlightingRules.append((QRegularExpression(r"'.?'"), stringFormat))
        self.highlightingRules.append((QRegularExpression(r"<[a-zA-Z0-9_.]+>"), stringFormat))

        operators = [
            r"\+", r"-", r"\*", r"/", r"%", r"\^", r"\+\+", r"--",
            r"<", r"<=", r">", r">=", r"==", r"!=", r"=", r"&&", r"\|\|", r"!",
            r"\(", r"\)", r"\{", r"\}", r",", r";", r":"
        ]
        for op in operators:
            self.highlightingRules.append((QRegularExpression(op), operatorFormat))

        self.highlightingRules.append((QRegularExpression(r"//[^\n]*"), self.commentFormat))

        # Block comment logic (state-dependent)
        self.commentStartExpression = QRegularExpression(r"/\*")
        self.commentEndExpression = QRegularExpression(r"\*/")

    # ============================================================
    # METHOD: highlightBlock
    # What it does: Applies highlighting rules to a specific line.
    # Interaction: Uses Qt's state management to handle multi-line
    # comments spanning several blocks.
    # ============================================================
    def highlightBlock(self, text):
        # Apply all independent single-line rules
        for pattern, format in self.highlightingRules:
            matchIterator = pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Multi-line comment processing (State: 0 = Code, 1 = Comment)
        self.setCurrentBlockState(0)
        startIndex = 0

        if self.previousBlockState() != 1:
            match = self.commentStartExpression.match(text)
            startIndex = match.capturedStart()

        while startIndex >= 0:
            endMatch = self.commentEndExpression.match(text, startIndex)
            endIndex = endMatch.capturedStart()
            commentLength = 0

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + endMatch.capturedLength()

            self.setFormat(startIndex, commentLength, self.commentFormat)
            startMatch = self.commentStartExpression.match(text, startIndex + commentLength)
            startIndex = startMatch.capturedStart()


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
            line_color = QColor("#2d2d30")
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
    def add_error_highlight(self, line, col):
        selection = QTextEdit.ExtraSelection()
        format = QTextCharFormat()
        format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        format.setUnderlineColor(QColor("red"))
        selection.format = format
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, col)
        cursor.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        
        if cursor.selectedText() == "":
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
            
        selection.cursor = cursor
        self.error_selections.append(selection)
        self.highlight_current_line()

    # ============================================================
    # METHOD: clear_error_highlights
    # What it does: Clears all red squiggly underlines.
    # ============================================================
    def clear_error_highlights(self):
        self.error_selections.clear()
        self.highlight_current_line()

    # ============================================================
    # METHOD: lineNumberAreaPaintEvent
    # What it does: The core drawing loop for the line numbers.
    # Components: QPainter, QTextBlock.
    # Interaction: Iterates only through visible blocks for performance
    # optimization in large files.
    # ============================================================
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

        self.editor = CodeEditor()
        self.editor.setPlainText(content)
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
            start_path = current_page.file_path or self.main_app.current_path

            file_path, _ = QFileDialog.getSaveFileName(
                self.tabs,
                "Save As...",
                start_path,
                "All Files (*);;Text Files (*.txt);;Python Files (*.py)"
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
