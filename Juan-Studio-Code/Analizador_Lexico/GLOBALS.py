from enum import Enum, auto

class TokenType(Enum):
    # Palabras Reservadas (Color 4)
    IF = auto()
    ELSE = auto()
    END = auto()
    DO = auto()
    WHILE = auto()
    SWITCH = auto()
    CASE = auto()
    INT = auto()
    FLOAT = auto()
    MAIN = auto()
    CIN = auto()
    COUT = auto()

    # Operadores Aritméticos (Color 5)
    PLUS = auto()       # +
    MINUS = auto()      # -
    TIMES = auto()      # *
    OVER = auto()       # /
    MOD = auto()        # %
    POWER = auto()      # ^
    INC = auto()        # ++
    DEC = auto()        # --

    # Operadores Relacionales (Color 6)
    LT = auto()         # <
    LTEQ = auto()       # <=
    GT = auto()         # >
    GTEQ = auto()       # >=
    NEQ = auto()        # !=
    EQ = auto()         # ==

    # Operadores Lógicos (Color 6)
    AND = auto()        # &&
    OR = auto()         # ||
    NOT = auto()        # !

    # Símbolos
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    COMMA = auto()      # ,
    SEMI = auto()       # ;
    DQUOTE = auto()     # "
    SQUOTE = auto()     # '

    # Asignación
    ASSIGN = auto()     # =

    # Otros Tokens (Colores 1 y 2)
    ID = auto()         # Identificadores
    NUM_INT = auto()    # Números enteros
    NUM_FLOAT = auto()  # Números reales
    COMMENT_LINE = auto()  # Comentarios de una línea
    COMMENT_BLOCK = auto() # Comentarios de bloque

    ENDFILE = auto()
    ERROR = auto()


class State(Enum):
    START = auto()
    INID = auto()             # Leyendo identificador o palabra reservada
    INNUM_INT = auto()        # Leyendo número entero [cite: 11]
    INNUM_FLOAT = auto()      # Leyendo número real [cite: 11]
    INASSIGN = auto()         # Leyendo asignación o relacional (ej. vio un '<' y espera un '=')
    INCOMMENT_LINE = auto()   # Dentro de comentario // [cite: 12]
    INCOMMENT_BLOCK = auto()  # Dentro de comentario /* */ [cite: 12]
    DONE = auto()             # Terminó de leer el token