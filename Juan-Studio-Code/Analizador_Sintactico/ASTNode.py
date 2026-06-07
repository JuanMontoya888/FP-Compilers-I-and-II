from PySide6.QtCore import QObject, Signal

class ParserSignals(QObject):
    error_signal = Signal(str, int, int) # (Message, Line, Column)
    node_signal = Signal(str, str)       # (Node name, Lexeme)

class Token:
    def __init__(self, tipo, lexema, linea, columna):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna

class ASTNode:
    def __init__(self, name, value="", line="?", col="?"):
        self.name = name
        self.value = value
        self.line = line
        self.col = col
        self.children = []

    def add_child(self, node):
        if node:
            self.children.append(node)
