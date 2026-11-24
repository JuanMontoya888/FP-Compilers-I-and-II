from typing import Any, Callable, Dict, List, Optional


class PureSignal:
    """
    Lightweight, pure-Python replacement for PySide6.QtCore.Signal.
    Decouples the compiler backend from Qt while preserving .connect() and .emit().
    """

    def __init__(self, *arg_types: Any):
        self._arg_types = arg_types
        self._subscribers: List[Callable[..., None]] = []

    def connect(self, callback: Callable[..., None]) -> None:
        if callable(callback) and callback not in self._subscribers:
            self._subscribers.append(callback)

    def disconnect(self, callback: Optional[Callable[..., None]] = None) -> None:
        if callback is None:
            self._subscribers.clear()
        elif callback in self._subscribers:
            self._subscribers.remove(callback)

    def emit(self, *args: Any) -> None:
        for callback in list(self._subscribers):
            callback(*args)


class ParserSignals:
    """
    Signal container for syntax analysis events.
    Each instance gets its own isolated PureSignal channels.
    """

    def __init__(self):
        self.error_signal = PureSignal(str, int, int)  # (Message, Line, Column)
        self.node_signal = PureSignal(str, str)        # (Node name, Lexeme)


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
        self.children: List["ASTNode"] = []

        # Clean immutable metadata preserved for intermediate/TM code generation
        self.node_kind = name
        self.raw_value = value if value != "" else None
        self.op = None
        self.var_name = None
        self.dtype = None
        self.const_value = None
        self.mem_offset = None
        self.tm_offset = None
        self.has_error = False
        self.error_message = ""

    def add_child(self, node: Optional["ASTNode"]) -> None:
        if node:
            self.children.append(node)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the AST node into a canonical dictionary for testing and inspection."""
        return {
            "node_kind": self.node_kind,
            "raw_value": self.raw_value,
            "dtype": self.dtype,
            "const_value": self.const_value,
            "line": self.line,
            "col": self.col,
            "has_error": getattr(self, "has_error", False),
            "children": [child.to_dict() for child in self.children],
        }
