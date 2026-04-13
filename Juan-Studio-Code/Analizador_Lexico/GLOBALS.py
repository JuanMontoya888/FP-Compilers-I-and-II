# ============================================================
# DEFINICIÓN DEL VOCABULARIO Y ESTADOS DEL AUTÓMATA (DFA)
# Esta sección define las estructuras de datos fundamentales
# para la arquitectura del analizador léxico.
#
# Responsabilidades:
# - TokenType: Catálogo completo de todos los símbolos, palabras
#   reservadas y operadores válidos en el lenguaje. Actúa como
#   el "diccionario" de salida del analizador.
# - State: Representa los nodos del Autómata Finito Determinista
#   (DFA) utilizado para construir e identificar lexemas de 
#   forma progresiva.
# ============================================================
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
    COLON = auto()      # :

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
    STRING = auto()     # String
    CHAR_CONST = auto() # Caracter 'A'

    ENDFILE = auto()
    ERROR = auto()


class State(Enum):
    START = auto()
    INID = auto()             # Leyendo identificador o palabra reservada
    INNUM_INT = auto()        # Leyendo número entero
    INNUM_FLOAT = auto()      # Leyendo número real
    INASSIGN = auto()         # Leyendo asignación o relacional (ej. vio un '<' y espera un '=')
    INCOMMENT_LINE = auto()   # Dentro de comentario //
    INCOMMENT_BLOCK = auto()  # Dentro de comentario /* */
    INSTRING = auto()         # Dentro de string ""
    INCHAR = auto()           # Dentro de char ''
    INERROR = auto()
    DONE = auto()             # Terminó de leer el token
    