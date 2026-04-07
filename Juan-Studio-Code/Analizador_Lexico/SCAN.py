import os
from GLOBALS import TokenType, State

# =====================================================================
# CORE MODULE: LEXICAL ANALYZER (SCANNER CLASS)
# This class implements a Deterministic Finite Automaton (DFA) to
# transform a source code character stream into a list of tokens.
#
# Architecture:
# - Input Buffer: Manages file reading with encoding fallback.
# - Pointer System: Tracks position, lines, and columns for error reporting.
# - State Machine: Uses a 'match-case' structure to transition between
#   lexical states (START, ID, NUM, STRING, etc.).
# - Output: Persists result to a structured 'tokens.txt' file.
# =====================================================================
class SCANNER():

    # =====================================================================
    # METHOD: __init__
    # What it does: Initializes the scanner, loads the source code, 
    # and sets up control variables.
    # What components it uses: os, File I/O, TokenType (from GLOBALS).
    # How it interacts: Receives a file path and populates 'self.source'.
    # =====================================================================
    def __init__(self, file_path):
        self.source_path = file_path
        
        try:
            # Attempt to read the file using UTF-8 as primary encoding
            with open(file_path, 'r', encoding='utf-8') as file:
                self.source = file.read()
        except UnicodeDecodeError:
            # Fallback to Latin-1 if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                self.source = file.read()
        except FileNotFoundError:
            print(f"Error: File '{file_path}' was not found")
            self.source = ""
        except Exception as e:
            print(f"Critical error opening file: {e}")
            self.source = ""
            
        # Internal control pointers and tracking
        self.pos = 0
        self.line_no = 1  
        self.col_no = 1   
        self.EOF_FLAG = False
        self.list_tokens = []

        # Mapping of reserved keywords to their corresponding TokenTypes
        self.reserved_words = {
            "if": TokenType.IF, "else": TokenType.ELSE, "end": TokenType.END,
            "do": TokenType.DO, "while": TokenType.WHILE, "switch": TokenType.SWITCH,
            "case": TokenType.CASE, "int": TokenType.INT, "float": TokenType.FLOAT,
            "main": TokenType.MAIN, "cin": TokenType.CIN, "cout": TokenType.COUT
        }


    # =====================================================================
    # SECTION: STREAM MANAGEMENT (POINTER CONTROL)
    # These methods manage the character-by-character consumption 
    # of the source code and handle coordinate synchronization.
    # =====================================================================

    # =====================================================================
    # METHOD: _get_next_char
    # What it does: Consumes the next character and updates coordinates.
    # Components used: self.source buffer.
    # How it interacts: Updates self.pos, self.line_no, and self.col_no.
    # =====================================================================
    def _get_next_char(self):
        if self.pos >= len(self.source):
            self.EOF_FLAG = True
            return '\0'
        
        char = self.source[self.pos]
        self.pos += 1

        # Track line breaks to reset column count
        if char == '\n':
            self.line_no += 1
            self.col_no = 1
        else:
            self.col_no += 1

        return char

    # =====================================================================
    # METHOD: _peek_next_char
    # What it does: Lookahead of one character without consuming it.
    # How it interacts: Allows the DFA to decide transitions without moving pos.
    # =====================================================================
    def _peek_next_char(self):
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]


    # =====================================================================
    # METHOD: _unget_char
    # What it does: Safely moves the pointer back one position.
    # How it interacts: Recalculates exact line/col coordinates to prevent 
    # location offsets during error reporting or token completion.
    # =====================================================================
    def _unget_char(self):
        """
        Safely backtracks the pointer, restoring the exact line and column
        to avoid discrepancies in error highlighting.
        """
        if self.pos > 0:
            self.pos -= 1
            char = self.source[self.pos]
            if char == '\n':
                self.line_no -= 1
                # Recalculate column based on the previous line's length
                last_newline = self.source.rfind('\n', 0, self.pos)
                if last_newline == -1:
                    self.col_no = self.pos + 1
                else:
                    self.col_no = self.pos - last_newline
            else:
                self.col_no -= 1


    # =====================================================================
    # METHOD: get_token (DFA IMPLEMENTATION)
    # What it does: Main tokenizer loop. It categorizes lexemes into tokens.
    # What components it uses: State machine (State), TokenType, coordinates.
    # How it interacts: Processes 'self.source' until EOF is reached, 
    # populating 'self.list_tokens' and exporting to 'tokens.txt'.
    # =====================================================================
    def get_token(self):
        while not self.EOF_FLAG:
            state = State.START 
            current_lexem = '' 
            
            # Anchor coordinates at the beginning of the lexeme
            token_line = self.line_no
            token_col = self.col_no

            while state != State.DONE and not self.EOF_FLAG:
                
                char = self._get_next_char()

                match state:
                    
                    # -----------------------------------------------------
                    # STATE: START (Entry point for every new lexeme)
                    # -----------------------------------------------------
                    case State.START:
                        # Ignore whitespace and control characters
                        if char in [' ', '\t', '\n', '\r']:
                            continue

                        if current_lexem == '':
                            token_line = self.line_no
                            token_col = self.col_no - 1 if char != '\n' else 1
                            if token_col == 0: 
                                token_col = 1
                                
                        current_lexem += char

                        # Dispatch to specialized sub-states
                        if char.isalpha():
                            state = State.INID
                        elif char.isdigit():
                            state = State.INNUM_INT
                        elif char == '"':
                            state = State.INSTRING
                        elif char == "'":
                            state = State.INCHAR
                        else:
                            # Handle Operators and Symbols
                            match char:
                                case '\0': 
                                    state = State.DONE
                                    if current_lexem == '\0':
                                        self.list_tokens.append((TokenType.ENDFILE, "EOF"))
                                    
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
                                        self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                                    state = State.DONE
                                    
                                case '|':
                                    if self._peek_next_char() == '|':
                                        current_lexem += self._get_next_char()
                                        self.list_tokens.append((TokenType.OR, current_lexem))
                                    else:
                                        self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                                    state = State.DONE

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
                                    if current_lexem != '\0':
                                        self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                                    state = State.DONE

                    # -----------------------------------------------------
                    # SUB-STATE: Identifiers and Reserved Words
                    # -----------------------------------------------------
                    case State.INID:
                        if char.isalnum() or char == '_':
                            current_lexem += char
                        else:
                            self._unget_char() # Backtrack to keep non-ID char for next token
                            token_type = self.reserved_words.get(current_lexem, TokenType.ID)
                            self.list_tokens.append((token_type, current_lexem))
                            state = State.DONE
                        
                    # -----------------------------------------------------
                    # SUB-STATE: Numeric literals (Integer and Float)
                    # -----------------------------------------------------
                    case State.INNUM_INT:
                        if char.isdigit():
                            current_lexem += char
                        elif char == '.':
                            if self._peek_next_char().isdigit():
                                current_lexem += char
                                state = State.INNUM_FLOAT
                            else:
                                # Example: "32.something" results in an Error token
                                current_lexem += char
                                self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                                state = State.DONE
                        else:
                            # Standard integer identified
                            self._unget_char()
                            self.list_tokens.append((TokenType.NUM_INT, current_lexem))
                            state = State.DONE
                        
                    case State.INNUM_FLOAT:
                        if char.isdigit():
                            current_lexem += char
                        else:
                            # End of float found
                            self._unget_char()
                            self.list_tokens.append((TokenType.NUM_FLOAT, current_lexem))
                            state = State.DONE

                    # -----------------------------------------------------
                    # SUB-STATES: Comments (Line and Block)
                    # -----------------------------------------------------
                    case State.INCOMMENT_LINE:
                        if char != '\n' and char != '\0':
                            current_lexem += char
                        else:
                            self._unget_char()
                            self.list_tokens.append((TokenType.COMMENT_LINE, current_lexem))
                            state = State.DONE
                        
                    case State.INCOMMENT_BLOCK:
                        current_lexem += char
                        if char == '*' and self._peek_next_char() == '/':
                            current_lexem += self._get_next_char() 
                            self.list_tokens.append((TokenType.COMMENT_BLOCK, current_lexem))
                            state = State.DONE
                        elif char == '\0':
                            # Unfinished block comment error
                            self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                            state = State.DONE

                    # -----------------------------------------------------
                    # SUB-STATES: String and Character Constants
                    # -----------------------------------------------------
                    case State.INSTRING:
                        current_lexem += char
                        if char == '"':
                            self.list_tokens.append((TokenType.STRING, current_lexem))
                            state = State.DONE
                        elif char == '\0' or char == '\n':
                            # Missing closing quote error
                            self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                            state = State.DONE

                    case State.INCHAR:
                        current_lexem += char
                        if char == "'":
                            self.list_tokens.append((TokenType.CHAR_CONST, current_lexem))
                            state = State.DONE
                        elif char == '\0' or char == '\n':
                            # Invalid char constant error
                            self.list_tokens.append((TokenType.ERROR, current_lexem, token_line, token_col))
                            state = State.DONE

        # =====================================================================
        # EXPORT SECTION: Final Token Serialization
        # Writes the results to a structured text file for debugging.
        # =====================================================================
        with open("tokens.txt", "w", encoding='utf-8') as file:
            file.write(f"{'TOKEN':<20}\t{'LEXEME':<15}\tPOSITION\n")
            file.write("-" * 55 + "\n")
            for token in self.list_tokens:
                if token[0] == TokenType.ERROR and len(token) == 4:
                    # Log errors with line and column detail
                    file.write(f"{token[0].name:<20}\t{token[1]:<15}\tLn {token[2]}, Col {token[3]}\n")
                else:
                    # Log standard tokens
                    file.write(f"{token[0].name:<20}\t{token[1]}\n")