import codecs
import re
from typing import List, Tuple

from PySide6.QtGui import QColor, QFont, QTextCharFormat


# VS Code Dark+ ANSI color palette
ANSI_STANDARD_COLORS = {
    30: "#1e1e1e",  # Black
    31: "#f44747",  # Red
    32: "#6a9955",  # Green
    33: "#d7ba7d",  # Yellow
    34: "#569cd6",  # Blue
    35: "#c586c0",  # Magenta
    36: "#4ec9b0",  # Cyan
    37: "#d4d4d4",  # White
}

ANSI_BRIGHT_COLORS = {
    90: "#808080",  # Bright Black (Gray)
    91: "#ff6b6b",  # Bright Red
    92: "#b5cea8",  # Bright Green
    93: "#dcdcaa",  # Bright Yellow
    94: "#4fc1ff",  # Bright Blue
    95: "#d670d6",  # Bright Magenta
    96: "#4ec9b0",  # Bright Cyan
    97: "#ffffff",  # Bright White
}


class AnsiEscapeParser:
    """
    Incremental UTF-8 + ANSI escape sequence parser that turns raw terminal bytes
    into styled (text, QTextCharFormat, is_clear) chunks ready for QPlainTextEdit.
    """

    _CSI_OR_OSC_RE = re.compile(
        r"\x1b\[([0-9;?]*)([A-Za-z])"
        r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
        r"|\x0c"
    )

    def __init__(self, default_fg: str = "#cccccc"):
        self.default_fg = default_fg
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._pending_escape = ""
        self._current_format = self._make_default_format()

    def _make_default_format(self) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.default_fg))
        return fmt

    def reset(self) -> None:
        self._decoder.reset()
        self._pending_escape = ""
        self._current_format = self._make_default_format()

    def feed(self, raw_bytes: bytes) -> List[Tuple[str, QTextCharFormat, bool]]:
        """Decodes bytes incrementally and returns [(text, QTextCharFormat, clear_screen)]."""
        text = self._decoder.decode(raw_bytes, final=False)
        return self.feed_text(text)

    def feed_text(self, text: str) -> List[Tuple[str, QTextCharFormat, bool]]:
        """Parses text containing ANSI CSI/SGR codes into styled chunks."""
        if not text:
            return []

        # Normalize Windows CRLF and standalone CR updates cleanly
        text = text.replace("\r\n", "\n")

        if self._pending_escape:
            text = self._pending_escape + text
            self._pending_escape = ""

        # Check for an incomplete trailing ESC sequence across chunk boundaries
        last_esc = text.rfind("\x1b")
        if last_esc != -1:
            tail = text[last_esc:]
            if not self._CSI_OR_OSC_RE.match(tail):
                if len(tail) < 32 and (tail == "\x1b" or tail.startswith("\x1b[") or tail.startswith("\x1b]")):
                    self._pending_escape = tail
                    text = text[:last_esc]

        chunks: List[Tuple[str, QTextCharFormat, bool]] = []
        pos = 0

        for match in self._CSI_OR_OSC_RE.finditer(text):
            if match.start() > pos:
                plain = text[pos : match.start()]
                if plain:
                    chunks.append((plain, QTextCharFormat(self._current_format), False))

            full = match.group(0)
            if full == "\x0c":
                chunks.append(("", QTextCharFormat(self._current_format), True))
            elif match.group(2) is not None:
                params_str = match.group(1)
                cmd = match.group(2)
                if cmd == "m":
                    self._apply_sgr(params_str)
                elif cmd == "J" and params_str in ("2", "3"):
                    chunks.append(("", QTextCharFormat(self._current_format), True))
                # Other CSI cursor/title sequences (e.g., H, K, ?25h) are cleanly stripped
            pos = match.end()

        if pos < len(text):
            tail = text[pos:]
            if tail:
                chunks.append((tail, QTextCharFormat(self._current_format), False))

        return chunks

    def _apply_sgr(self, params_str: str) -> None:
        if not params_str:
            self._current_format = self._make_default_format()
            return

        parts = [p for p in params_str.split(";") if p != ""]
        if not parts:
            self._current_format = self._make_default_format()
            return

        codes: List[int] = []
        for p in parts:
            try:
                codes.append(int(p))
            except ValueError:
                continue

        idx = 0
        while idx < len(codes):
            code = codes[idx]
            if code == 0:
                self._current_format = self._make_default_format()
            elif code == 1:
                self._current_format.setFontWeight(QFont.Weight.Bold)
            elif code == 3:
                self._current_format.setFontItalic(True)
            elif code == 4:
                self._current_format.setFontUnderline(True)
            elif code == 22:
                self._current_format.setFontWeight(QFont.Weight.Normal)
            elif code == 23:
                self._current_format.setFontItalic(False)
            elif code == 24:
                self._current_format.setFontUnderline(False)
            elif code == 39:
                self._current_format.setForeground(QColor(self.default_fg))
            elif code == 49:
                self._current_format.clearBackground()
            elif code in ANSI_STANDARD_COLORS:
                self._current_format.setForeground(QColor(ANSI_STANDARD_COLORS[code]))
            elif code in ANSI_BRIGHT_COLORS:
                self._current_format.setForeground(QColor(ANSI_BRIGHT_COLORS[code]))
            elif 40 <= code <= 47:
                self._current_format.setBackground(QColor(ANSI_STANDARD_COLORS[code - 10]))
            elif 100 <= code <= 107:
                self._current_format.setBackground(QColor(ANSI_BRIGHT_COLORS[code - 10]))
            elif code in (38, 48) and idx + 1 < len(codes):
                is_fg = code == 38
                mode = codes[idx + 1]
                if mode == 2 and idx + 4 < len(codes):
                    r, g, b = codes[idx + 2], codes[idx + 3], codes[idx + 4]
                    color = QColor(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
                    if is_fg:
                        self._current_format.setForeground(color)
                    else:
                        self._current_format.setBackground(color)
                    idx += 4
                elif mode == 5 and idx + 2 < len(codes):
                    c_idx = codes[idx + 2]
                    color = self._xterm_256_color(c_idx)
                    if is_fg:
                        self._current_format.setForeground(color)
                    else:
                        self._current_format.setBackground(color)
                    idx += 2
            idx += 1

    @staticmethod
    def _xterm_256_color(index: int) -> QColor:
        if 0 <= index <= 7:
            return QColor(ANSI_STANDARD_COLORS[30 + index])
        if 8 <= index <= 15:
            return QColor(ANSI_BRIGHT_COLORS[90 + (index - 8)])
        if 16 <= index <= 231:
            index -= 16
            r = (index // 36) * 51
            g = ((index % 36) // 6) * 51
            b = (index % 6) * 51
            return QColor(r, g, b)
        if 232 <= index <= 255:
            gray = 8 + (index - 232) * 10
            return QColor(gray, gray, gray)
        return QColor("#cccccc")
