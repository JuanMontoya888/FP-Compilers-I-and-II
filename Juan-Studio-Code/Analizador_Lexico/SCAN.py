import os
from GLOBALS import TokenType, State

# ============================================================
# MOTOR DE ANÁLISIS LÉXICO (CLASE SCANNER)
# Clase principal que actúa como un transductor: toma una 
# secuencia de caracteres crudos y emite tokens estructurados.
#
# Arquitectura:
# Mantiene un estado interno de lectura (cursor, línea, columna)
# y emplea una tabla Hash (diccionario) para búsquedas de
# palabras reservadas de tiempo O(1).
# ============================================================
class SCANNER():

    # ============================================================
    # INICIALIZACIÓN DEL ENTORNO DE ESCANEO (__init__)
    # 
    # Qué hace: Prepara el entorno cargando el archivo fuente en
    # memoria y configurando los cursores y buffers.
    # Componentes que usa: Módulo de I/O de Python (open).
    # Interacción: Configura la matriz de palabras reservadas
    # (self.reserved_words) que luego será consultada por el DFA
    # para distinguir identificadores de palabras clave.
    # ============================================================
    def __init__(self, file_path):
        self.source_path = file_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.source = file.read()
        except FileNotFoundError:
            print(f"Error: File '{file_path}' was not found")
            self.source = ""
        except Exception as e:
            print(f"Error opening file: {e}")
            self.source = ""
            
        # Control variables
        self.pos = 0
        self.line_no = 1  # Starting line number
        self.col_no = 1   # Starting column number
        self.EOF_FLAG = False

        #tokens will be stored here, like (token_type, lexem)
        self.list_tokens = []

        # Reserved words dictionary
        self.reserved_words = {
            "if": TokenType.IF, "else": TokenType.ELSE, "end": TokenType.END,
            "do": TokenType.DO, "while": TokenType.WHILE, "switch": TokenType.SWITCH,
            "case": TokenType.CASE, "int": TokenType.INT, "float": TokenType.FLOAT,
            "main": TokenType.MAIN, "cin": TokenType.CIN, "cout": TokenType.COUT
        }

        
    # ============================================================
    # CONSUMIDOR DE CARACTERES (_get_next_char)
    # 
    # Qué hace: Extrae el siguiente caracter del buffer de código
    # y actualiza los punteros espaciales (línea/columna).
    # Componentes que usa: self.source, self.pos, self.line_no.
    # Interacción: Alimenta directamente al ciclo del autómata,
    # informando también cuando se alcanza el fin de archivo (EOF).
    # ============================================================
    def _get_next_char(self):
        """
        Returns the next character and updates the line and column.
        """
        if self.pos >= len(self.source):
            self.EOF_FLAG = True
            return '\0'
        
        char = self.source[self.pos]
        self.pos += 1

        # Update line and column if there is a newline character
        if char == '\n':
            self.line_no += 1
            self.col_no = 1
        else:
            self.col_no += 1

        return char

    # ============================================================
    # LECTURA ANTICIPADA (_peek_next_char)
    # 
    # Qué hace: Permite observar el siguiente caracter en el flujo
    # sin extraerlo ni avanzar el cursor principal.
    # Componentes que usa: self.source, self.pos.
    # Interacción: Crítico para resolver ambigüedades en operadores
    # compuestos (ej. distinguir entre '=' y '==', o '+' y '++').
    # ============================================================
    def _peek_next_char(self):
        """
        Peeks the next character without advancing the pointer.
        """
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]
    

    # ============================================================
    # NÚCLEO DEL AUTÓMATA FINITO DETERMINISTA (get_token)
    # 
    # Qué hace: Es el motor de transiciones de estado. Evalúa 
    # caracter por caracter y construye los lexemas agrupándolos.
    # Componentes que usa: Los métodos _get y _peek, TokenType, State.
    # Interacción: Constituye el ciclo de vida central de la clase.
    # Tras procesar todo el texto en memoria, consolida el resultado
    # volcando la lista de tokens en un archivo físico ("tokens.txt").
    # ============================================================
    def get_token(self):
        """
        Reads the entire source code, classifies tokens, and stores them in self.list_tokens.
        """
        # Principal loop it won't stop until the end of the file
        while not self.EOF_FLAG:
            state = State.START # state of current lexeme
            current_lexem = '' # It will store the current lexeme

            # Internal loop: builds ONE token (Automaton)
            while state != State.DONE and not self.EOF_FLAG:
                # get the next character
                char = self._get_next_char()

                # classify the character by state
                match state:
                    
                    # --------------------------------------------------------
                    # ESTADO INICIAL (START)
                    # Aquí el autómata decide hacia qué rama bifurcarse 
                    # analizando el primer caracter del lexema actual.
                    # --------------------------------------------------------
                    case State.START:
                        # 1. Ignore whitespace, read it but not consume it
                        if char in [' ', '\t', '\n', '\r']:
                            continue

                        # 2. Add to lexeme, read and consume it
                        current_lexem += char

                        # 3. Initial classification
                        # if it is a letter, go to INID state
                        if char.isalpha():
                            state = State.INID

                        elif char.isdigit():
                            state = State.INNUM_INT
                        
                        # --------------------------------------------------------
                        # TRANSICIÓN A LITERALES (STRINGS Y CHARS)
                        # Deriva el estado hacia la recolección de cadenas si
                        # detecta comillas dobles, o de caracteres simples si
                        # detecta comillas simples.
                        # --------------------------------------------------------
                        elif char == '"':
                            state = State.INSTRING
                        
                        elif char == "'":
                            state = State.INCHAR
                        
                        # 4. Symbols and operators
                        else:
                            # --------------------------------------------------------
                            # RESOLUCIÓN DE SÍMBOLOS Y OPERADORES
                            # Evalúa combinaciones de 1 o 2 caracteres empleando 
                            # lookahead para evitar la extracción errónea.
                            # --------------------------------------------------------
                            match char:
                                case '\0': # EOF
                                    state = State.DONE
                                    if current_lexem == '\0':
                                        self.list_tokens.append((TokenType.ENDFILE, "EOF"))
                                    
                                # --- OPERATORS OF 1 OR 2 CHARACTERS ---
                                case '+':
                                    if self._peek_next_char() == '+':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.INC, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.PLUS, current_lexem))
                                    state = State.DONE
                                    
                                case '-':
                                    if self._peek_next_char() == '-':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.DEC, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.MINUS, current_lexem))
                                    state = State.DONE
                                    
                                case '=':
                                    if self._peek_next_char() == '=':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.EQ, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.ASSIGN, current_lexem))
                                    state = State.DONE

                                case '<':
                                    if self._peek_next_char() == '=':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.LTEQ, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.LT, current_lexem))
                                    state = State.DONE
                                    
                                case '>':
                                    if self._peek_next_char() == '=':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.GTEQ, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.GT, current_lexem))
                                    state = State.DONE
                                    
                                case '!':
                                    if self._peek_next_char() == '=':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.NEQ, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.NOT, current_lexem))
                                    state = State.DONE

                                case '&':
                                    if self._peek_next_char() == '&':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.AND, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.ERROR, current_lexem))
                                    state = State.DONE
                                    
                                case '|':
                                    if self._peek_next_char() == '|':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.OR, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.ERROR, current_lexem))
                                    state = State.DONE
                                    
                                # --------------------------------------------------------
                                # ANÁLISIS DE COMENTARIOS Y DIVISIÓN
                                # --------------------------------------------------------
                                case '/':
                                    if self._peek_next_char() == '/':
                                        current_lexem += self._get_next_char()
                                        state = State.INCOMMENT_LINE
                                    elif self._peek_next_char() == '*':
                                        current_lexem += self._get_next_char()
                                        state = State.INCOMMENT_BLOCK
                                    else:
                                        self.list_tokens.append((TokenType.OVER, current_lexem))
                                        state = State.DONE
                                        
                                # --- OPERATORS OF 1 CHARACTER ---
                                case '*':
                                    self.list_tokens.append((TokenType.TIMES, current_lexem))
                                    state = State.DONE
                                case '%':
                                    self.list_tokens.append((TokenType.MOD, current_lexem))
                                    state = State.DONE
                                case '^':
                                    self.list_tokens.append((TokenType.POWER, current_lexem))
                                    state = State.DONE
                                case '(':
                                    self.list_tokens.append((TokenType.LPAREN, current_lexem))
                                    state = State.DONE
                                case ')':
                                    self.list_tokens.append((TokenType.RPAREN, current_lexem))
                                    state = State.DONE
                                case '{':
                                    self.list_tokens.append((TokenType.LBRACE, current_lexem))
                                    state = State.DONE
                                case '}':
                                    self.list_tokens.append((TokenType.RBRACE, current_lexem))
                                    state = State.DONE
                                case ',':
                                    self.list_tokens.append((TokenType.COMMA, current_lexem))
                                    state = State.DONE
                                case ';':
                                    self.list_tokens.append((TokenType.SEMI, current_lexem))
                                    state = State.DONE
                                case ':':
                                    self.list_tokens.append((TokenType.COLON, current_lexem))
                                    state = State.DONE
                                case _:
                                    # Only mark error if the character is not empty (by EOF)
                                    if current_lexem != '\0':
                                        self.list_tokens.append((TokenType.ERROR, current_lexem))
                                    state = State.DONE

                    # --------------------------------------------------------
                    # ESTADOS DE CONSTRUCCIÓN DE LEXEMAS MULTI-CARACTER
                    # Estas ramas acumulan caracteres mientras pertenezcan
                    # a la clase lógica esperada.
                    # --------------------------------------------------------
                    
                    # --- CASE INID ---
                    case State.INID:
                        if char.isalnum() or char == '_':
                            current_lexem += char
                        else:
                            # --------------------------------------------------------
                            # RESOLUCIÓN DE IDENTIFICADORES VS PALABRAS RESERVADAS
                            # Consulta el diccionario 'reserved_words'. Si existe en 
                            # él, es palabra clave; si no, es un identificador general.
                            # --------------------------------------------------------
                            self.pos -= 1
                            self.col_no -= 1

                            token_type = self.reserved_words.get(current_lexem, TokenType.ID)
                            self.list_tokens.append((token_type, current_lexem))
                            state = State.DONE
                        
                    # --- CASE INNUM_INT ---
                    case State.INNUM_INT:
                        if char.isdigit():
                            current_lexem += char
                        elif char == '.':
                            # Transición de estado: De entero a flotante
                            current_lexem += char
                            state = State.INNUM_FLOAT
                        else:
                            self.pos -= 1
                            self.col_no -= 1

                            self.list_tokens.append((TokenType.NUM_INT, current_lexem))
                            state = State.DONE
                        
                    # --- CASE INNUM_FLOAT ---
                    case State.INNUM_FLOAT:
                        if char.isdigit():
                            current_lexem += char
                        else:
                            self.pos -= 1
                            self.col_no -= 1

                            self.list_tokens.append((TokenType.NUM_FLOAT, current_lexem))
                            state = State.DONE
                        
                    # --- CASE INCOMMENT_LINE ---
                    case State.INCOMMENT_LINE:
                        # Ignora el contenido hasta encontrar un salto de línea o EOF
                        if char != '\n' and char != '\0':
                            current_lexem += char
                        else:
                            self.pos -= 1
                            self.list_tokens.append((TokenType.COMMENT_LINE, current_lexem))
                            state = State.DONE
                        
                    # --- CASE INCOMMENT_BLOCK ---
                    case State.INCOMMENT_BLOCK:
                        current_lexem += char
                        # Busca activamente la secuencia de cierre '*/'
                        if char == '*' and self._peek_next_char() == '/':
                            current_lexem += self._get_next_char() # Consume el '/'
                            self.list_tokens.append((TokenType.COMMENT_BLOCK, current_lexem))
                            state = State.DONE
                        elif char == '\0':
                            # Manejo de error léxico: fin de archivo sin cerrar comentario
                            self.list_tokens.append((TokenType.ERROR, current_lexem))
                            state = State.DONE

                    # --------------------------------------------------------
                    # GESTIÓN DE CONSTANTES LITERALES (STRINGS Y CHARS)
                    # Estados dedicados a capturar todo el contenido hasta
                    # encontrar su respectivo delimitador de cierre, controlando
                    # que no se rompan por saltos de línea sin escapar.
                    # --------------------------------------------------------
                    
                    # --- ESTADO INSTRING ---
                    case State.INSTRING:
                        current_lexem += char
                        if char == '"':
                            # Cerramos la cadena
                            self.list_tokens.append((TokenType.STRING, current_lexem))
                            state = State.DONE
                        elif char == '\0' or char == '\n':
                            # Error: la cadena no se cerró antes del fin de línea o archivo
                            self.list_tokens.append((TokenType.ERROR, current_lexem))
                            state = State.DONE

                    # --- ESTADO INCHAR ---
                    case State.INCHAR:
                        current_lexem += char
                        if char == "'":
                            # Cerramos el caracter
                            self.list_tokens.append((TokenType.CHAR_CONST, current_lexem))
                            state = State.DONE
                        elif char == '\0' or char == '\n':
                            # Error: el caracter no se cerró
                            self.list_tokens.append((TokenType.ERROR, current_lexem))
                            state = State.DONE

        # ============================================================
        # EXPORTACIÓN DE RESULTADOS
        # 
        # Qué hace: Persiste los resultados del análisis en un archivo.
        # Componentes que usa: self.list_tokens y módulo I/O nativo.
        # Interacción: Crea "tokens.txt" con una estructura tabular 
        # mejorada para mayor legibilidad humana.
        # ============================================================
        with open("tokens.txt", "w", encoding='utf-8') as file:
            file.write(f"{'TOKEN':<20}\tLEXEMA\n")
            file.write("-" * 45 + "\n")
            for token in self.list_tokens:
                file.write(f"{token[0].name:<20}\t{token[1]}\n")