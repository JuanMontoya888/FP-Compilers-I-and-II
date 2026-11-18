from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PySide6.QtCore import QRegularExpression
from ide.components.theme import Theme


# =====================================================================
# CLASS: Highlighter (OPTIMIZED SYNTAX HIGHLIGHTING ENGINE)
# Scans modified QTextDocument blocks using consolidated, precompiled
# QRegularExpression patterns with OptimizeOnFirstUsageOption.
# =====================================================================
class Highlighter(QSyntaxHighlighter):
    @staticmethod
    def _compile_regex(pattern: str) -> QRegularExpression:
        regex = QRegularExpression(pattern)
        regex.optimize()
        return regex

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []

        # Structural Keywords (Pink/Red Monokai style)
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(Theme.SYNTAX_KEYWORD))
        keywordFormat.setFontItalic(True)

        # Data Types (Cyan/Teal)
        typeFormat = QTextCharFormat()
        typeFormat.setForeground(QColor(Theme.SYNTAX_TYPE))
        typeFormat.setFontItalic(True)

        # Numbers (Light Green)
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(Theme.SYNTAX_NUMBER))

        # Strings, Chars, and angle-bracket headers (Orange/Yellow)
        self.stringFormat = QTextCharFormat()
        self.stringFormat.setForeground(QColor(Theme.SYNTAX_STRING))

        # Operators and Symbols (Light Gray)
        operatorFormat = QTextCharFormat()
        operatorFormat.setForeground(QColor(Theme.SYNTAX_OPERATOR))

        # Comments (Green)
        self.commentFormat = QTextCharFormat()
        self.commentFormat.setForeground(QColor(Theme.SYNTAX_COMMENT))
        self.commentFormat.setFontItalic(True)

        # Preprocessor Directives (Purple Bold)
        self.librariesFormat = QTextCharFormat()
        self.librariesFormat.setForeground(QColor(Theme.SYNTAX_LIBRARY))
        self.librariesFormat.setFontItalic(True)
        self.librariesFormat.setFontWeight(QFont.Bold)

        # -----------------------------------------------------------------
        # CONSOLIDATED PRECOMPILED REGEX RULES (7 patterns instead of 93)
        # -----------------------------------------------------------------
        keywords_pattern = (
            r"\b(?:if|else|end|do|while|then|switch|case|main|cin|cout|"
            r"break|continue|for|goto|return|try|catch|throw|class|struct|"
            r"public|private|protected|virtual|friend|inline|template|typename|"
            r"this|new|delete|enum|union|namespace|using|typedef|sizeof|"
            r"static|const|extern|explicit|operator|constexpr|decltype|noexcept|"
            r"volatile|default|true|false|nullptr)\b"
        )
        data_types_pattern = (
            r"\b(?:int|float|string|bool|char|double|long|short|void|auto|"
            r"signed|unsigned|wchar_t)\b"
        )
        directives_pattern = r"#(?:include|define)\b"
        numbers_pattern = r"\b[0-9]+(?:\.[0-9]+)?\b"
        operators_pattern = r"\+\+|--|<=|>=|==|!=|&&|\|\||[+\-*/%^<>!=(),;:{}\[\]]"
        # Non-greedy string & char literals supporting escaped quotes
        string_char_pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''

        self.highlightingRules = [
            (self._compile_regex(keywords_pattern), keywordFormat),
            (self._compile_regex(data_types_pattern), typeFormat),
            (self._compile_regex(directives_pattern), self.librariesFormat),
            (self._compile_regex(numbers_pattern), numberFormat),
            (self._compile_regex(operators_pattern), operatorFormat),
            (self._compile_regex(string_char_pattern), self.stringFormat),
        ]

        self.includeHeaderExpression = self._compile_regex(r"<[a-zA-Z0-9_.]+>")
        self.singleLineCommentExpression = self._compile_regex(r"//[^\n]*")
        self.stringLiteralExpression = self._compile_regex(string_char_pattern)
        self.commentStartExpression = self._compile_regex(r"/\*")
        self.commentEndExpression = self._compile_regex(r"\*/")

    def _collect_string_spans(self, text: str):
        spans = []
        it = self.stringLiteralExpression.globalMatch(text)
        while it.hasNext():
            m = it.next()
            spans.append((m.capturedStart(), m.capturedStart() + m.capturedLength()))
        return spans

    @staticmethod
    def _inside_spans(pos: int, spans) -> bool:
        for start, end in spans:
            if start <= pos < end:
                return True
        return False

    def highlightBlock(self, text):
        # 1. Apply consolidated token rules
        for pattern, fmt in self.highlightingRules:
            matchIterator = pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Highlight <header.h> only on preprocessor #include lines
        if "#include" in text:
            headerIterator = self.includeHeaderExpression.globalMatch(text)
            while headerIterator.hasNext():
                match = headerIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.stringFormat)

        # 2. Apply single-line comments (only when '//' is outside string literals)
        string_spans = self._collect_string_spans(text)
        comment_match = self.singleLineCommentExpression.match(text)
        while comment_match.hasMatch():
            c_start = comment_match.capturedStart()
            if not self._inside_spans(c_start, string_spans):
                self.setFormat(c_start, comment_match.capturedLength(), self.commentFormat)
                break
            comment_match = self.singleLineCommentExpression.match(text, c_start + 2)

        # 3. Multi-line block comment state machine (0 = Code, 1 = Inside /* ... */)
        self.setCurrentBlockState(0)
        startIndex = 0

        if self.previousBlockState() != 1:
            match = self.commentStartExpression.match(text)
            while match.hasMatch():
                idx = match.capturedStart()
                if not self._inside_spans(idx, string_spans):
                    startIndex = idx
                    break
                match = self.commentStartExpression.match(text, idx + 2)
            else:
                startIndex = -1

        while startIndex >= 0:
            endMatch = self.commentEndExpression.match(text, startIndex)
            endIndex = endMatch.capturedStart()

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + endMatch.capturedLength()

            self.setFormat(startIndex, commentLength, self.commentFormat)
            nextMatch = self.commentStartExpression.match(text, startIndex + commentLength)
            startIndex = -1
            while nextMatch.hasMatch():
                idx = nextMatch.capturedStart()
                if not self._inside_spans(idx, string_spans):
                    startIndex = idx
                    break
                nextMatch = self.commentStartExpression.match(text, idx + 2)
