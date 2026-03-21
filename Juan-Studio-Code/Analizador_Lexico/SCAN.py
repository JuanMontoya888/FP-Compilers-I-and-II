import os
from GLOBALS import TokenType, State


class SCANNER():
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


        
    '''
    Function: _get_next_char
    Description: This function will get the next character from the source code
    Parameters: self
    Return: self.source[self.pos] as char
    '''
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

    def _peek_next_char(self):
        """
        Peeks the next character without advancing the pointer.
        """
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]
    

    '''
    Function: get_token
    Description: This function will get the next token from the source code
    Parameters: self
    Return: self.source[self.pos] as char
    '''
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

                        # if it is a number, go to INNUM_INT state
                        elif char.isdigit():
                            state = State.INNUM_INT
                        
                        # if it is a double quote, save the token and end this lexeme
                        elif char == '"':
                            self.list_tokens.append((TokenType.DQUOTE, current_lexem))
                            state = State.DONE
                        
                        # if it is a single quote, save the token and end this lexeme
                        elif char == "'":
                            self.list_tokens.append((TokenType.SQUOTE, current_lexem))
                            state = State.DONE
                        
                        # 4. Symbols and operators
                        else:
                            match char:
                                case '\0': # EOF
                                    state = State.DONE
                                    # Only save EOF if there is nothing else in the lexeme
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

                                # --- COMMENTS OR DIVISION ---
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
                                case _:
                                    # Only mark error if the character is not empty (by EOF)
                                    if current_lexem != '\0':
                                        self.list_tokens.append((TokenType.ERROR, current_lexem))
                                    state = State.DONE

                    # --- CASE INID ---
                    case State.INID:
                        if char.isalnum() or char == '_':
                            current_lexem += char
                        else:
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
                        if char != '\n' and char != '\0':
                            current_lexem += char
                        else:
                            self.pos -= 1

                            self.list_tokens.append((TokenType.COMMENT_LINE, current_lexem))
                            state = State.DONE
                        
                    
                    # --- CASE INCOMMENT_BLOCK ---
                    case State.INCOMMENT_BLOCK:
                        current_lexem += char
                        if char == '*' and self._peek_next_char() == '/':
                            current_lexem += self._get_next_char() # Consume el '/'
                            self.list_tokens.append((TokenType.COMMENT_BLOCK, current_lexem))
                            state = State.DONE
                        elif char == '\0':
                            # Error léxico: se acabó el archivo sin cerrar el comentario
                            self.list_tokens.append((TokenType.ERROR, current_lexem))
                            state = State.DONE

                    # --- END OF THE SWITCH STATEMENT ---
                    
            # --- END OF THE WHILE LOOP ---
        
        # --- END OF THE SCAN METHOD ---
        
        with open("tokens.txt", "w") as file:
            file.write("TOKEN\tLEXEMA\n")
            for token in self.list_tokens:
                file.write(f"{token[0]}\t{token[1]}\n")

    # --- END OF THE SCANNER CLASS ---
    