from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PySide6.QtCore import QRegularExpression
from ide.components.theme import Theme

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
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(Theme.SYNTAX_STRING))

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
