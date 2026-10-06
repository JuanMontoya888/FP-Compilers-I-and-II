from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                               QLineEdit, QPushButton, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextDocument, QTextCursor

class SearchReplaceWidget(QFrame):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setup_ui()
        self.hide() # Hidden by default
        
        # Style the frame
        self.setObjectName("searchReplaceFrame")
        self.setStyleSheet("""
            QFrame#searchReplaceFrame {
                background-color: #252526;
                border: 1px solid #454545;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                padding: 2px 4px;
                border-radius: 2px;
                selection-background-color: #264F78;
            }
            QLineEdit:focus {
                border: 1px solid #007ACC;
            }
            QPushButton {
                background-color: transparent;
                color: #CCCCCC;
                border: none;
                padding: 2px;
                border-radius: 2px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QPushButton:pressed {
                background-color: #007ACC;
            }
        """)

    def setup_ui(self):
        self.setFixedWidth(280)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # --- Top row: Find ---
        find_layout = QHBoxLayout()
        find_layout.setSpacing(2)
        
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find")
        self.find_input.returnPressed.connect(self.on_find_next)
        
        self.btn_prev = QPushButton("↑")
        self.btn_prev.setFixedSize(22, 22)
        self.btn_prev.setToolTip("Previous match")
        self.btn_prev.clicked.connect(self.on_find_prev)
        
        self.btn_next = QPushButton("↓")
        self.btn_next.setFixedSize(22, 22)
        self.btn_next.setToolTip("Next match")
        self.btn_next.clicked.connect(self.on_find_next)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.clicked.connect(self.hide)

        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.btn_prev)
        find_layout.addWidget(self.btn_next)
        find_layout.addWidget(self.btn_close)

        # --- Bottom row: Replace ---
        replace_layout = QHBoxLayout()
        replace_layout.setSpacing(2)
        
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace")
        self.replace_input.returnPressed.connect(self.on_replace)
        
        self.btn_replace = QPushButton("↻")
        self.btn_replace.setFixedSize(22, 22)
        self.btn_replace.setToolTip("Replace")
        self.btn_replace.clicked.connect(self.on_replace)
        
        self.btn_replace_all = QPushButton("↻↻")
        self.btn_replace_all.setFixedSize(22, 22)
        self.btn_replace_all.setToolTip("Replace All")
        self.btn_replace_all.clicked.connect(self.on_replace_all)

        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.btn_replace)
        replace_layout.addWidget(self.btn_replace_all)
        # Spacer to align inputs properly (match the width of the close button)
        replace_layout.addSpacing(24)

        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)

    def update_position(self):
        if self.parent():
            x = self.parent().width() - self.width() - 25
            y = 15
            self.move(max(0, x), y)

    def show_find(self):
        self.show()
        self.update_position()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def show_replace(self):
        self.show()
        self.update_position()
        self.replace_input.setFocus()
        self.replace_input.selectAll()

    def on_find_next(self):
        text = self.find_input.text()
        if text:
            cursor = self.editor.document().find(text, self.editor.textCursor())
            if cursor.isNull():
                cursor = self.editor.document().find(text, 0)
            if not cursor.isNull():
                self.editor.setTextCursor(cursor)

    def on_find_prev(self):
        text = self.find_input.text()
        if text:
            cursor = self.editor.document().find(text, self.editor.textCursor(), QTextDocument.FindBackward)
            if cursor.isNull():
                cursor = self.editor.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor = self.editor.document().find(text, cursor, QTextDocument.FindBackward)
            if not cursor.isNull():
                self.editor.setTextCursor(cursor)

    def on_replace(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text:
            cursor = self.editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
            self.on_find_next()

    def on_replace_all(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text:
            return
            
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        
        while True:
            cursor = self.editor.document().find(find_text, cursor)
            if cursor.isNull():
                break
            cursor.insertText(replace_text)
            
        cursor.endEditBlock()

