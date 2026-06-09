from Analizador_Lexico.GLOBALS import TokenType
from ASTNode import ASTNode, ParserSignals, Token

# =====================================================================
# CORE MODULE: SYNTAX ANALYZER (PARSER CLASS)
# Implements a recursive descent parser to validate the grammar of the 
# source code and construct an Abstract Syntax Tree (AST).
#
# Architecture:
# - Top-Down Parsing: Evaluates tokens sequentially matching grammar rules.
# - Flattened AST Generation: Avoids verbose concrete derivation trees by flattening nodes.
# - Fault Tolerance: Incorporates a panic-mode recovery system to continue parsing after errors.
# - Decoupled UI: Uses PySide6 Signals to stream nodes and errors to the frontend asynchronously.
# =====================================================================
class Parser:
    # =====================================================================
    # METHOD: __init__
    # What it does: Initializes the parser with a list of tokens and a signal emitter.
    # What components it uses: raw_tokens, TokenType (Enum), ParserSignals.
    # How it interacts: Normalizes cross-module Enums by string name mapping to prevent identity failures, filtering out comments and errors.
    # =====================================================================
    def __init__(self, raw_tokens, signals=None):
        self.signals = signals if signals else ParserSignals()
        
        self.tokens = []
        for t in raw_tokens:
            try:
                tipo_local = TokenType[t[0].name]
            except Exception:
                tipo_local = t[0]

            if tipo_local not in (TokenType.COMMENT_LINE, TokenType.COMMENT_BLOCK, TokenType.ERROR):
                linea = t[2] if len(t) > 2 else "?"
                columna = t[3] if len(t) > 3 else "?"
                self.tokens.append(Token(tipo_local, t[1], linea, columna))

        self.pos = 0
        self.panic_mode = False

    # =====================================================================
    # METHOD: current_token
    # What it does: Retrieves the token at the current parsing index.
    # What components it uses: self.tokens, self.pos, TokenType.ENDFILE.
    # How it interacts: Prevents out-of-bounds exceptions by returning an EOF token if the end is reached.
    # =====================================================================
    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.ENDFILE, "EOF", "?", "?")

    # =====================================================================
    # METHOD: peek_token
    # What it does: Retrieves the next token without advancing the parser pointer.
    # What components it uses: self.tokens, self.pos, TokenType.ENDFILE.
    # How it interacts: Allows lookahead (LL(1)) to distinguish between similar grammar rules like assignments and unary operations.
    # =====================================================================
    def peek_token(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return Token(TokenType.ENDFILE, "EOF", "?", "?")

    # =====================================================================
    # METHOD: advance
    # What it does: Moves the parsing pointer to the next token.
    # What components it uses: self.pos.
    # How it interacts: Steps forward through the token stream.
    # =====================================================================
    def advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    # =====================================================================
    # METHOD: match
    # What it does: Validates that the current token matches the expected grammatical type.
    # What components it uses: current_token(), expected_type, advance(), report_error().
    # How it interacts: Consumes the token if it matches, otherwise it triggers an error report and returns None.
    # =====================================================================
    def match(self, expected_type):
        token = self.current_token()
        if token.tipo == expected_type:
            self.advance()
            return token
        else:
            self.report_error(f"Expected {expected_type.name}")
            return None

    # =====================================================================
    # METHOD: report_error
    # What it does: Logs syntax errors and initiates the error recovery mechanism.
    # What components it uses: current_token(), error_signal, self.panic_mode.
    # How it interacts: Emits the error via PySide6 signals to the UI console and calls synchronize() to recover.
    # =====================================================================
    def report_error(self, message):
        if not self.panic_mode:
            token = self.current_token()
            error_msg = f"Token: {token.tipo.name} ('{token.lexema}') | {message}"
            
            try:
                line_val = int(token.linea)
            except ValueError:
                line_val = -1
                
            try:
                col_val = int(token.columna)
            except ValueError:
                col_val = -1
                
            self.signals.error_signal.emit(error_msg, line_val, col_val)
            self.panic_mode = True
            self.synchronize()

    # =====================================================================
    # METHOD: synchronize
    # What it does: Implements panic-mode recovery by discarding tokens until a synchronization point is found.
    # What components it uses: current_token(), advance().
    # How it interacts: Resets panic_mode once a safe statement boundary token is reached.
    # =====================================================================
    def synchronize(self):
        # Seguro anti-bucles: si el token problemático NO es una llave estructural, lo consumimos de inmediato.
        if self.current_token().tipo not in [TokenType.SEMI, TokenType.RBRACE, TokenType.LBRACE, TokenType.ENDFILE]:
            self.advance()
            
        sync_keywords = [
            TokenType.INT, TokenType.FLOAT, TokenType.IF, 
            TokenType.WHILE, TokenType.DO, TokenType.CIN, TokenType.COUT
        ]
        
        while True:
            token = self.current_token()
            if token.tipo == TokenType.ENDFILE:
                break
                
            # If the token is already a boundary, we don't consume it here. We break and let the parser handle it.
            if token.tipo in [TokenType.SEMI, TokenType.RBRACE, TokenType.LBRACE]:
                self.panic_mode = False
                break
                
            # Stop explicitly if we see a keyword that starts a new statement
            if token.tipo in sync_keywords or (token.tipo == TokenType.ID and token.lexema == "bool"):
                self.panic_mode = False
                break
                
            self.advance()

    # =====================================================================
    # METHOD: emit_node
    # What it does: Broadcasts the creation of a new AST node to the frontend.
    # What components it uses: node_signal.
    # How it interacts: Enables real-time UI updates during tree construction.
    # =====================================================================
    def emit_node(self, name, lexema=""):
        self.signals.node_signal.emit(name, lexema)

    # =====================================================================
    # METHOD: parse
    # What it does: Entry point of the syntactic analyzer.
    # What components it uses: current_token(), programa(), emit_node().
    # How it interacts: Begins the top-down evaluation of the token sequence and returns the root AST Node.
    # =====================================================================
    def parse(self):
        self.emit_node("Syntax Analysis Started", "")
        root = self.programa()
        if self.current_token().tipo != TokenType.ENDFILE:
            self.report_error("Unexpected tokens after program end")
        self.emit_node("Syntax Analysis Completed", "")
        self.serialize_ast(root)
        return root
        
    # =====================================================================
    # METHOD: serialize_ast
    # What it does: Recursively converts the AST into a formatted text string and saves it.
    # What components it uses: ASTNode.
    # How it interacts: Writes the final structured output to compiler_output/tree.txt.
    # =====================================================================
    def serialize_ast(self, node, level=0):
        import os
        
        # Only initialize file and create directory on the root call
        if level == 0:
            output_dir = "compiler_output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(os.path.join(output_dir, "tree.txt"), "w", encoding='utf-8') as f:
                f.write(self._build_ast_string(node, 0))
                
    def _build_ast_string(self, node, level):
        if not node:
            return ""
        indent = "  " * level
        result = f"{indent}|-- {node.name}: {node.value} (Ln {node.line}, Col {node.col})\n"
        for child in node.children:
            result += self._build_ast_string(child, level + 1)
        return result

    # =====================================================================
    # METHOD: programa
    # What it does: Evaluates the grammar rule: programa → main { lista_declaracion }
    # What components it uses: match(), lista_declaracion(), ASTNode.
    # How it interacts: Creates the root node of the AST and connects all child declarations to it.
    # =====================================================================
    def programa(self):
        token = self.current_token()
        node = ASTNode("Program", "main", line=token.linea, col=token.columna)
        self.emit_node("Program", "main")
        
        # Consuming 'main'
        main_token = self.match(TokenType.MAIN)
        if not main_token:
            return None
            
        if not self.match(TokenType.LBRACE): return None
        
        decls = self.lista_declaracion()
        for d in decls:
            if d is not None:
                node.add_child(d)
            
        if not self.match(TokenType.RBRACE): return None
        return node

    # =====================================================================
    # METHOD: lista_declaracion
    # What it does: Evaluates the grammar rule: lista_declaracion → (declaracion_variable | sentencia)*
    # What components it uses: current_token(), declaracion_variable(), sentencia().
    # How it interacts: Loops over tokens, routing to variables or statements until a closing brace is found.
    # =====================================================================
    def lista_declaracion(self):
        decls = []
        while True:
            t = self.current_token()
            if t.tipo == TokenType.RBRACE or t.tipo == TokenType.ENDFILE:
                break
            
            pos_initial = self.pos
            
            # Type detection for declarations
            if t.tipo in [TokenType.INT, TokenType.FLOAT] or (t.tipo == TokenType.ID and t.lexema == "bool"):
                decl_node = self.declaracion_variable()
                if decl_node is not None:
                    decls.append(decl_node)
            else:
                s_node = self.sentencia()
                if s_node is not None:
                    decls.append(s_node)
                   
            if self.pos == pos_initial:
                self.advance() 
        return decls

    # =====================================================================
    # METHOD: declaracion_variable
    # What it does: Evaluates the grammar rule: declaracion_variable → tipo id [ = expresion ] ( , id [ = expresion ] )* ;
    # What components it uses: current_token(), tipo(), expresion(), match(), ASTNode.
    # How it interacts: Creates an AST branch for a sequence of variable declarations with optional assignments.
    # =====================================================================
    def declaracion_variable(self):
        token = self.current_token()
        tipo_str = self.tipo()
        if tipo_str is None:
            return None
            
        node = ASTNode("Variable Declaration", tipo_str, line=token.linea, col=token.columna)
        self.emit_node("Variable Declaration", tipo_str)
        
        while True:
            id_token = self.match(TokenType.ID)
            if not id_token:
                return None
                
            child = ASTNode("Identifier", id_token.lexema, line=id_token.linea, col=id_token.columna)
            
            # Optional assignment
            if self.current_token().tipo == TokenType.ASSIGN:
                self.match(TokenType.ASSIGN)
                exp_node = self.expresion()
                
                init_node = ASTNode("Initialization", "=", line=id_token.linea, col=id_token.columna)
                init_node.add_child(child)
                if exp_node is not None:
                    init_node.add_child(exp_node)
                node.add_child(init_node)
            else:
                node.add_child(child)
            
            if self.current_token().tipo == TokenType.COMMA:
                self.match(TokenType.COMMA)
            else:
                break
                
        if not self.match(TokenType.SEMI):
            return None
            
        return node

    # =====================================================================
    # METHOD: tipo
    # What it does: Evaluates the grammar rule: tipo → int | float | bool
    # What components it uses: current_token(), advance(), report_error().
    # How it interacts: Extracts and validates the data type string for variable declarations.
    # =====================================================================
    def tipo(self):
        token = self.current_token()
        lexema = token.lexema
        if token.tipo in [TokenType.INT, TokenType.FLOAT]:
            self.advance()
            return lexema
        elif token.tipo == TokenType.ID and token.lexema == "bool":
            self.advance()
            return lexema
        else:
            self.report_error(f"Expected type (int, float, bool)")
            return None

    # =====================================================================
    # METHOD: lista_sentencias
    # What it does: Evaluates the grammar rule: lista_sentencias → sentencia*
    # What components it uses: current_token(), sentencia().
    # How it interacts: Gathers statement nodes recursively until a block closes.
    # =====================================================================
    def lista_sentencias(self):
        sents = []
        while True:
            t = self.current_token()
            if t.tipo == TokenType.RBRACE or t.tipo == TokenType.ENDFILE:
                break
            
            s_node = self.sentencia()
            if s_node is not None:
                sents.append(s_node)
        return sents

    # =====================================================================
    # METHOD: sentencia
    # What it does: Evaluates the grammar rule for routing statements.
    # What components it uses: current_token(), peek_token(), report_error().
    # How it interacts: Dispatches parsing routines based on the keyword or handles empty statements gracefully.
    # =====================================================================
    def sentencia(self):
        token = self.current_token()
        
        # Empty Statement Support
        if token.tipo == TokenType.SEMI:
            self.advance()
            return None
            
        if token.tipo == TokenType.IF:
            return self.seleccion()
        elif token.tipo == TokenType.WHILE:
            return self.iteracion()
        elif token.tipo == TokenType.DO:
            return self.repeticion()
        elif token.tipo == TokenType.CIN:
            return self.sent_in()
        elif token.tipo == TokenType.COUT:
            return self.sent_out()
        elif token.tipo == TokenType.ID:
            siguiente = self.peek_token()
            if siguiente.tipo in [TokenType.INC, TokenType.DEC]:
                return self.operacion_unaria()
            else:
                return self.asignacion()
        else:
            self.report_error("Invalid statement start")
            # If an invalid start is encountered, synchronize and abort this branch
            return None

    # =====================================================================
    # METHOD: seleccion
    # What it does: Evaluates: seleccion → if ( expresion ) { lista_sentencias } [ else { lista_sentencias } ]
    # What components it uses: match(), expresion(), lista_sentencias(), ASTNode.
    # How it interacts: Builds an IF structure with mandatory brackets.
    # =====================================================================
    def seleccion(self):
        token = self.current_token()
        node = ASTNode("Selection (if)", line=token.linea, col=token.columna)
        self.emit_node("Selection (if)", "")
        
        if not self.match(TokenType.IF): return None
        if not self.match(TokenType.LPAREN): return None
        
        exp_node = self.expresion()
        if exp_node is not None:
            node.add_child(exp_node)
            
        if not self.match(TokenType.RPAREN): return None
        
        if not self.match(TokenType.LBRACE): return None
        then_block = ASTNode("Then Block", line=token.linea, col=token.columna)
        for s in self.lista_declaracion():
            if s is not None:
                then_block.add_child(s)
        if not self.match(TokenType.RBRACE): return None
        node.add_child(then_block)
        
        if self.current_token().tipo == TokenType.ELSE:
            el_token = self.match(TokenType.ELSE)
            if not self.match(TokenType.LBRACE): return None
            
            else_block = ASTNode("Else Block", line=el_token.linea, col=el_token.columna)
            for s in self.lista_declaracion():
                if s is not None:
                    else_block.add_child(s)
                    
            if not self.match(TokenType.RBRACE): return None
            node.add_child(else_block)
            
        return node

    # =====================================================================
    # METHOD: iteracion
    # What it does: Evaluates: iteracion → while ( expresion ) { lista_sentencias }
    # What components it uses: match(), expresion(), lista_sentencias(), ASTNode.
    # How it interacts: Evaluates standard while loops with mandatory brackets.
    # =====================================================================
    def iteracion(self):
        token = self.current_token()
        node = ASTNode("Iteration (while)", line=token.linea, col=token.columna)
        self.emit_node("Iteration (while)", "")
        
        if not self.match(TokenType.WHILE): return None
        if not self.match(TokenType.LPAREN): return None
        
        exp_node = self.expresion()
        if exp_node is not None:
            node.add_child(exp_node)
            
        if not self.match(TokenType.RPAREN): return None
        
        if not self.match(TokenType.LBRACE): return None
        block = ASTNode("While Body", line=token.linea, col=token.columna)
        for s in self.lista_declaracion():
            if s is not None:
                block.add_child(s)
        if not self.match(TokenType.RBRACE): return None
        
        node.add_child(block)
        return node

    # =====================================================================
    # METHOD: repeticion
    # What it does: Evaluates: repeticion → do { lista_sentencias } while ( expresion ) ;
    # What components it uses: match(), lista_sentencias(), expresion(), ASTNode.
    # How it interacts: Validates robust do-while enclosures.
    # =====================================================================
    def repeticion(self):
        token = self.current_token()
        node = ASTNode("Repetition (do-while)", line=token.linea, col=token.columna)
        self.emit_node("Repetition (do-while)", "")
        
        if not self.match(TokenType.DO): return None
        if not self.match(TokenType.LBRACE): return None
        
        block = ASTNode("Do Body", line=token.linea, col=token.columna)
        for s in self.lista_declaracion():
            if s is not None:
                block.add_child(s)
                
        if not self.match(TokenType.RBRACE): return None
        node.add_child(block)
        
        if not self.match(TokenType.WHILE): return None
        if not self.match(TokenType.LPAREN): return None
        
        exp_node = self.expresion()
        if exp_node is not None:
            node.add_child(exp_node)
            
        if not self.match(TokenType.RPAREN): return None
        if not self.match(TokenType.SEMI): return None
        return node

    # =====================================================================
    # METHOD: sent_in
    # What it does: Evaluates: sent_in → cin >> id ;
    # What components it uses: match(), ASTNode.
    # How it interacts: Evaluates input streams explicitly.
    # =====================================================================
    def sent_in(self):
        token = self.current_token()
        if not self.match(TokenType.CIN): return None
        
        t = self.current_token()
        if t.tipo == TokenType.GT:
            self.advance()
            if self.current_token().tipo == TokenType.GT:
                self.advance()
            else:
                self.report_error("Expected >>")
                return None
        else:
            self.report_error("Expected >>")
            return None
            
        id_token = self.match(TokenType.ID)
        if not id_token: return None
        
        node = ASTNode("Input (cin)", id_token.lexema, line=token.linea, col=token.columna)
        self.emit_node("Input (cin)", id_token.lexema)
        
        if not self.match(TokenType.SEMI): return None
        return node

    # =====================================================================
    # METHOD: sent_out
    # What it does: Evaluates: sent_out → cout << salida ;
    # What components it uses: match(), salida(), ASTNode.
    # How it interacts: Evaluates standard outputs resolving to the chained output method.
    # =====================================================================
    def sent_out(self):
        token = self.current_token()
        if not self.match(TokenType.COUT): return None
        
        t = self.current_token()
        if t.tipo == TokenType.LT:
            self.advance()
            if self.current_token().tipo == TokenType.LT:
                self.advance()
            else:
                self.report_error("Expected <<")
                return None
        else:
            self.report_error("Expected <<")
            return None
            
        node = ASTNode("Output (cout)", line=token.linea, col=token.columna)
        self.emit_node("Output (cout)", "")
        
        out_node = self.salida()
        if out_node is not None:
            node.add_child(out_node)
            
        if not self.match(TokenType.SEMI): return None
        return node

    # =====================================================================
    # METHOD: salida
    # What it does: Evaluates: salida → (cadena | expresion) ( << (cadena | expresion) )*
    # What components it uses: cadena(), expresion(), ASTNode.
    # How it interacts: Evaluates cascaded outputs looping dynamically.
    # =====================================================================
    def salida(self):
        token = self.current_token()
        
        # Evaluar el primer elemento de la impresión
        if token.tipo == TokenType.STRING:
            node = self.cadena()
        else:
            node = self.expr_simple()
            
        if node is None:
            return None
            
        # Procesar los elementos encadenados mediante operadores '<<'
        while self.current_token().tipo == TokenType.LT:
            # Lookahead: Verificar que realmente sea un operador '<<' doble
            if self.peek_token().tipo == TokenType.LT:
                lt_t = self.current_token()
                self.advance() # Consume el primer '<'
                self.advance() # Consume el segundo '<'
                
                new_node = ASTNode("Multiple Output", line=lt_t.linea, col=lt_t.columna)
                new_node.add_child(node)
                
                # Evaluar el siguiente elemento en la cascada
                next_token = self.current_token()
                if next_token.tipo == TokenType.STRING:
                    c_node = self.cadena()
                    if c_node is not None:
                        new_node.add_child(c_node)
                else:
                    e_node = self.expr_simple()
                    if e_node is not None:
                        new_node.add_child(e_node)
                        
                node = new_node
            else:
                # Si solo hay un '<' suelto, no pertenece a la salida
                break
                
        return node

    # =====================================================================
    # METHOD: asignacion
    # What it does: Evaluates: asignacion → id = expresion ;
    # What components it uses: match(), expresion(), ASTNode.
    # How it interacts: Extracts target variables and binds their evaluated result expressions.
    # =====================================================================
    def asignacion(self):
        token = self.current_token()
        id_token = self.match(TokenType.ID)
        if not id_token: return None
        
        node = ASTNode("Assignment", id_token.lexema, line=token.linea, col=token.columna)
        self.emit_node("Assignment", id_token.lexema)
        
        if not self.match(TokenType.ASSIGN): return None
        
        exp_node = self.expresion()
        if exp_node is not None:
            node.add_child(exp_node)
            
        if not self.match(TokenType.SEMI): return None
        return node

    # =====================================================================
    # METHOD: operacion_unaria
    # What it does: Evaluates: operacion_unaria → id (++ | --) ;
    # What components it uses: match(), advance(), ASTNode.
    # How it interacts: Maps directly increment or decrement commands to the designated AST branches.
    # =====================================================================
    def operacion_unaria(self):
        token = self.current_token()
        id_token = self.match(TokenType.ID)
        if not id_token: return None
        
        op_token = self.current_token()
        if op_token.tipo == TokenType.INC:
            self.advance()
            op_str = "++"
        elif op_token.tipo == TokenType.DEC:
            self.advance()
            op_str = "--"
        else:
            self.report_error("Expected ++ or --")
            return None
            
        if not self.match(TokenType.SEMI): return None
        
        val = f"{id_token.lexema}{op_str}"
        node = ASTNode("Unary Operation", val, line=token.linea, col=token.columna)
        self.emit_node("Unary Operation", val)
        return node

    # =====================================================================
    # METHOD: expresion
    # What it does: Evaluates: expresion → expr_relacional ( (&& | ||) expr_relacional )*
    # What components it uses: expr_relacional(), advance(), ASTNode.
    # How it interacts: Top-level precedence wrapper resolving boolean chaining.
    # =====================================================================
    def expresion(self):
        node = self.expr_relacional()
        if node is None: return None
        
        while self.current_token().tipo in [TokenType.AND, TokenType.OR]:
            token = self.current_token()
            op_str = token.lexema
            self.advance()
            
            right_node = self.expr_relacional()
            
            new_node = ASTNode("Logical Operation", op_str, line=token.linea, col=token.columna)
            self.emit_node("Logical Operation", op_str)
            new_node.add_child(node)
            if right_node is not None:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: expr_relacional
    # What it does: Evaluates: expr_relacional → expr_simple [ (< | <= | > | >= | == | !=) expr_simple ]
    # What components it uses: expr_simple(), advance(), ASTNode.
    # How it interacts: Secondary precedence resolving comparisons across unified operations.
    # =====================================================================
    def expr_relacional(self):
        left_node = self.expr_simple()
        if left_node is None: return None
        
        rel_ops = [TokenType.LT, TokenType.LTEQ, TokenType.GT, TokenType.GTEQ, TokenType.EQ, TokenType.NEQ]
        token = self.current_token()
        
        if token.tipo in rel_ops:
            op_str = token.lexema
            self.advance()
            right_node = self.expr_simple()
            
            node = ASTNode("Relational Expression", op_str, line=token.linea, col=token.columna)
            self.emit_node("Relational Expression", op_str)
            node.add_child(left_node)
            if right_node is not None:
                node.add_child(right_node)
            return node
            
        return left_node

    # =====================================================================
    # METHOD: expr_simple
    # What it does: Evaluates: expr_simple → termino ( (+ | -) termino )*
    # What components it uses: termino(), advance(), ASTNode.
    # How it interacts: Precedence for addition and subtraction.
    # =====================================================================
    def expr_simple(self):
        node = self.termino()
        if node is None: return None
        
        while self.current_token().tipo in [TokenType.PLUS, TokenType.MINUS]:
            token = self.current_token()
            op_str = token.lexema
            self.advance()
            
            right_node = self.termino()
            
            new_node = ASTNode("Arithmetic Expression", op_str, line=token.linea, col=token.columna)
            self.emit_node("Arithmetic Expression", op_str)
            new_node.add_child(node)
            if right_node is not None:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: termino
    # What it does: Evaluates: termino → factor ( (* | / | %) factor )*
    # What components it uses: factor(), advance(), ASTNode.
    # How it interacts: Evaluates multiplicatives bindings prioritizing them over standard arithmetic bounds.
    # =====================================================================
    def termino(self):
        node = self.factor()
        if node is None: return None
        
        # CORRECTED: Changed TokenType.DIVIDE back to TokenType.OVER to match your Lexer configuration
        while self.current_token().tipo in [TokenType.TIMES, TokenType.OVER, TokenType.MOD]:
            token = self.current_token()
            op_str = token.lexema
            self.advance()
            
            right_node = self.factor()
            
            new_node = ASTNode("Arithmetic Expression", op_str, line=token.linea, col=token.columna)
            self.emit_node("Arithmetic Expression", op_str)
            new_node.add_child(node)
            if right_node is not None:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: factor
    # What it does: Evaluates: factor → componente ( ^ componente )*
    # What components it uses: componente(), advance(), ASTNode.
    # How it interacts: Evaluates exponential expressions, the highest mathematical priority rule.
    # =====================================================================
    def factor(self):
        node = self.componente()
        if node is None: return None
        
        while self.current_token().tipo == TokenType.POWER:
            token = self.current_token()
            op_str = token.lexema
            self.advance()
            
            right_node = self.componente()
            
            new_node = ASTNode("Arithmetic Expression", op_str, line=token.linea, col=token.columna)
            self.emit_node("Arithmetic Expression", op_str)
            new_node.add_child(node)
            if right_node is not None:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: componente
    # What it does: Evaluates: componente → ! componente | ( expresion ) | NUM_INT | NUM_FLOAT | ID | STRING | true | false
    # What components it uses: expresion(), advance(), match(), ASTNode.
    # How it interacts: Validates leaf tokens correctly resetting precedence paths if a grouped parenthesis invokes expression mapping again.
    # =====================================================================
    def componente(self):
        token = self.current_token()
        
        if token.tipo == TokenType.NOT:
            self.advance()
            inner = self.componente()
            node = ASTNode("Logical NOT", "!", line=token.linea, col=token.columna)
            self.emit_node("Logical NOT", "!")
            if inner is not None:
                node.add_child(inner)
            return node
            
        elif token.tipo == TokenType.LPAREN:
            self.advance()
            exp_node = self.expresion()
            if not self.match(TokenType.RPAREN): return None
            return exp_node
            
        elif token.tipo in [TokenType.NUM_INT, TokenType.NUM_FLOAT]:
            node = ASTNode("Numeric Literal", token.lexema, line=token.linea, col=token.columna)
            self.emit_node("Numeric Literal", token.lexema)
            self.advance()
            return node
            
        elif token.tipo == TokenType.ID:
            if token.lexema in ["true", "false"]:
                node = ASTNode("Boolean Literal", token.lexema, line=token.linea, col=token.columna)
                self.emit_node("Boolean Literal", token.lexema)
            else:
                node = ASTNode("Identifier", token.lexema, line=token.linea, col=token.columna)
                self.emit_node("Identifier", token.lexema)
            self.advance()
            return node
            
        elif token.tipo == TokenType.STRING:
            node = ASTNode("String Literal", token.lexema, line=token.linea, col=token.columna)
            self.emit_node("String Literal", token.lexema)
            self.advance()
            return node
            
        else:
            self.report_error("Invalid expression component")
            return None

    # =====================================================================
    # METHOD: cadena
    # What it does: Dedicated string handling function. Currently absorbed effectively into componente, but held for legacy structure mapping.
    # =====================================================================
    def cadena(self):
        token = self.current_token()
        node = ASTNode("String Literal", token.lexema, line=token.linea, col=token.columna)
        self.emit_node("String Literal", token.lexema)
        self.advance()
        return node