import os
import re
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from ide.components.ansi_parser import AnsiEscapeParser


class InteractiveTerminal(QPlainTextEdit):
    """
    VS Code-inspired interactive terminal widget built on QPlainTextEdit.

    Features:
    - Incremental UTF-8 + ANSI SGR color rendering via AnsiEscapeParser.
    - Strict protection of output history (interactive_position watermark).
    - Preserves in-progress user input if async stdout/stderr arrives mid-typing.
    - Command history navigation via Up/Down arrows.
    - Smart Home key jumping to the start of user input (never overwriting prompt).
    - Dual Ctrl+C: copies when text is selected, interrupts running process otherwise.
    - Ctrl+L clear screen.
    """

    command_submitted = Signal(str)
    interrupt_requested = Signal()
    clear_requested = Signal()
    tab_completion_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(False)
        self.setUndoRedoEnabled(False)

        self.ansi_parser = AnsiEscapeParser()
        self.interactive_position: int = 0
        self.command_history: List[str] = []
        self.history_index: int = 0
        self._history_draft: str = ""
        self._tab_completion_state = None
        self.custom_key_handler: Optional[Callable] = None

    def clear_terminal(self) -> None:
        self.clear()
        self.ansi_parser.reset()
        self.interactive_position = 0
        self._tab_completion_state = None

    def get_current_input(self) -> str:
        doc_len = max(0, self.document().characterCount() - 1)
        safe_pos = min(self.interactive_position, doc_len)
        cursor = self.textCursor()
        cursor.setPosition(safe_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        return cursor.selectedText()

    def _replace_current_input(self, new_text: str) -> None:
        doc_len = max(0, self.document().characterCount() - 1)
        safe_pos = min(self.interactive_position, doc_len)
        cursor = self.textCursor()
        cursor.setPosition(safe_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#cccccc"))
        cursor.insertText(new_text, fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_output_bytes(self, raw_bytes: bytes, is_stderr: bool = False) -> None:
        """
        Safely appends stdout/stderr bytes from a QProcess while protecting any
        unsent text currently typed by the user past interactive_position.
        """
        if not raw_bytes:
            return

        # Extract any unsent user draft typed past the watermark
        draft = self.get_current_input()
        if draft:
            self._replace_current_input("")

        chunks = self.ansi_parser.feed(raw_bytes)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        for text_chunk, fmt, is_clear in chunks:
            if is_clear:
                self.clear()
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.interactive_position = 0
                continue

            if is_stderr and fmt.foreground().color().name().lower() == self.ansi_parser.default_fg.lower():
                err_fmt = QTextCharFormat(fmt)
                err_fmt.setForeground(QColor("#f48771"))
                cursor.insertText(text_chunk, err_fmt)
            else:
                cursor.insertText(text_chunk, fmt)

        self.setTextCursor(cursor)
        self.interactive_position = cursor.position()

        if draft:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#cccccc"))
            cursor.insertText(draft, fmt)
            self.setTextCursor(cursor)

        self.ensureCursorVisible()

    def append_system_message(self, text: str, color_hex: str = "#4ec9b0") -> None:
        """Writes a clean IDE status line without disturbing output formatting."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))
        cursor.insertText(text, fmt)
        self.setTextCursor(cursor)
        self.interactive_position = cursor.position()
        self.ensureCursorVisible()

    def consume_current_input(self) -> str:
        """Reads and removes the user's unsent input line so the process echo or handler takes over."""
        doc_len = max(0, self.document().characterCount() - 1)
        safe_pos = min(self.interactive_position, doc_len)
        cursor = self.textCursor()
        cursor.setPosition(safe_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        command = cursor.selectedText().rstrip("\r\n")
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        self.interactive_position = cursor.position()
        return command

    def record_history(self, command: str) -> None:
        stripped = command.strip()
        if stripped and (not self.command_history or self.command_history[-1] != stripped):
            self.command_history.append(stripped)
        self.history_index = len(self.command_history)
        self._history_draft = ""

    def insertFromMimeData(self, source) -> None:
        """Ensures pasted text always lands in the editable input region."""
        if not source.hasText():
            return
        cursor = self.textCursor()
        if cursor.position() < self.interactive_position:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        elif cursor.hasSelection() and cursor.selectionStart() < self.interactive_position:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

        text = source.text().replace("\r\n", "\n")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#cccccc"))
        cursor.insertText(text, fmt)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event) -> None:
        if self.custom_key_handler is not None:
            self.custom_key_handler(event)
            return

        key = event.key()
        mods = event.modifiers()
        cursor = self.textCursor()

        # Dual Ctrl+C: Copy if selected, Interrupt subprocess otherwise
        if (mods & Qt.KeyboardModifier.ControlModifier) and key == Qt.Key.Key_C:
            if cursor.hasSelection():
                self.copy()
            else:
                self._tab_completion_state = None
                self.interrupt_requested.emit()
            return

        # Ctrl+L: Clear terminal
        if (mods & Qt.KeyboardModifier.ControlModifier) and key == Qt.Key.Key_L:
            self._tab_completion_state = None
            self.clear_requested.emit()
            return

        # Ctrl+V: Paste strictly at editable region
        if (mods & Qt.KeyboardModifier.ControlModifier) and key == Qt.Key.Key_V:
            self.paste()
            return

        # Smart Home: jump right after the prompt watermark
        if key == Qt.Key.Key_Home:
            move_mode = (
                QTextCursor.MoveMode.KeepAnchor
                if (mods & Qt.KeyboardModifier.ShiftModifier)
                else QTextCursor.MoveMode.MoveAnchor
            )
            cursor.setPosition(self.interactive_position, move_mode)
            self.setTextCursor(cursor)
            return

        # Protect history from Left / Backspace
        if key == Qt.Key.Key_Left:
            if cursor.position() <= self.interactive_position:
                return
            super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_Backspace:
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                if end <= self.interactive_position:
                    return
                if start < self.interactive_position:
                    cursor.setPosition(self.interactive_position)
                    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                    self.setTextCursor(cursor)
            elif cursor.position() <= self.interactive_position:
                return
            self._tab_completion_state = None
            super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_Delete:
            if cursor.hasSelection() and cursor.selectionStart() < self.interactive_position:
                return
            if cursor.position() < self.interactive_position:
                return
            self._tab_completion_state = None
            super().keyPressEvent(event)
            return

        # History navigation via Up / Down arrows
        if key == Qt.Key.Key_Up:
            if not self.command_history:
                return
            if self.history_index == len(self.command_history):
                self._history_draft = self.get_current_input()
            if self.history_index > 0:
                self.history_index -= 1
                self._replace_current_input(self.command_history[self.history_index])
            return

        if key == Qt.Key.Key_Down:
            if not self.command_history:
                return
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._replace_current_input(self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self._replace_current_input(self._history_draft)
            return

        # Tab completion hook
        if key == Qt.Key.Key_Tab:
            self.tab_completion_requested.emit()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._tab_completion_state = None
            command = self.consume_current_input()
            self.record_history(command)
            self.command_submitted.emit(command)
            return

        # Reset tab state on typing keys
        if key not in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            self._tab_completion_state = None

        # Redirect printable input to end if user clicked into history zone
        if event.text() and not (mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            if cursor.position() < self.interactive_position or (
                cursor.hasSelection() and cursor.selectionStart() < self.interactive_position
            ):
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)

        super().keyPressEvent(event)
