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
    # What components it uses: self.pos, len(self.tokens).
    # How it interacts: Controls the sequential consumption of tokens.
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
    # What components it uses: current_token(), advance(), TokenType.SEMI, TokenType.RBRACE.
    # How it interacts: Resets panic_mode once a safe token (like ';' or '}') is reached, allowing parsing to resume.
    # =====================================================================
    def synchronize(self):
        while True:
            token = self.current_token()
            if token.tipo == TokenType.SEMI:
                self.advance()
                self.panic_mode = False
                break
            elif token.tipo == TokenType.RBRACE:
                self.panic_mode = False
                break
            elif token.tipo == TokenType.ENDFILE:
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
    # What it does: Entry point for the syntax analysis.
    # What components it uses: programa().
    # How it interacts: Starts the recursive descent by calling the top-level grammar rule.
    # =====================================================================
    def parse(self):
        root_node = self.programa()
        self.serialize_ast(root_node)
        return root_node

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
    # What components it uses: current_token(), ASTNode, match(), lista_declaracion().
    # How it interacts: Creates the root node of the AST and orchestrates the block parsing.
    # =====================================================================
    def programa(self):
        token = self.current_token()
        node = ASTNode("Program", value="main", line=token.linea, col=token.columna)
        self.emit_node("Program", "main")
        
        main_token = self.match(TokenType.MAIN)
        self.match(TokenType.LBRACE)
        
        decls = self.lista_declaracion()
        for d in decls:
            node.add_child(d)
            
        self.match(TokenType.RBRACE)
        return node

    # =====================================================================
    # METHOD: lista_declaracion
    # What it does: Evaluates the grammar rule: lista_declaracion → declaracion lista_declaracion | declaracion
    # What components it uses: current_token(), declaracion().
    # How it interacts: Loops to gather multiple declarations and returns them as a flat list for the parent block.
    # =====================================================================
    def lista_declaracion(self):
        decls = []
        while True:
            t = self.current_token()
            first_decl = [TokenType.INT, TokenType.FLOAT, TokenType.IF, TokenType.WHILE, TokenType.DO, TokenType.CIN, TokenType.COUT, TokenType.ID]
            
            if t.tipo in first_decl or (t.tipo == TokenType.ID and t.lexema == "bool"):
                decl_node = self.declaracion()
                if decl_node:
                    if isinstance(decl_node, list):
                        decls.extend(decl_node)
                    else:
                        decls.append(decl_node)
            else:
                break
        return decls

    # =====================================================================
    # METHOD: declaracion
    # What it does: Routes to variable declarations or general statements based on the current token type.
    # What components it uses: current_token(), declaracion_variable(), lista_sentencias().
    # How it interacts: Acts as a dispatcher for statement execution and variable instantiation.
    # =====================================================================
    def declaracion(self):
        t = self.current_token()
        if t.tipo in [TokenType.INT, TokenType.FLOAT] or (t.tipo == TokenType.ID and t.lexema == "bool"):
            return self.declaracion_variable()
        else:
            return self.lista_sentencias()

    # =====================================================================
    # METHOD: declaracion_variable
    # What it does: Evaluates the grammar rule: declaracion_variable → tipo identificador { , identificador } ;
    # What components it uses: current_token(), tipo(), match(), ASTNode.
    # How it interacts: Aggregates multiple comma-separated identifiers under a single declaration parent node.
    # =====================================================================
    def declaracion_variable(self):
        token = self.current_token()
        tipo_str = self.tipo()
        
        node = ASTNode("Variable Declaration", tipo_str, line=token.linea, col=token.columna)
        self.emit_node("Variable Declaration", tipo_str)
        
        while True:
            id_token = self.match(TokenType.ID)
            if id_token:
                child = ASTNode("Identifier", id_token.lexema, line=id_token.linea, col=id_token.columna)
                node.add_child(child)
                
            if self.current_token().tipo == TokenType.COMMA:
                self.match(TokenType.COMMA)
            else:
                break
                
        self.match(TokenType.SEMI)
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
        elif token.tipo == TokenType.ID and token.lexema == "bool":
            self.advance()
        else:
            self.report_error(f"Expected type (int, float, bool)")
            lexema = ""
        return lexema

    # =====================================================================
    # METHOD: lista_sentencias
    # What it does: Evaluates the grammar rule: lista_sentencias → sentencia lista_sentencias | ε
    # What components it uses: current_token(), sentencia().
    # How it interacts: Loops over valid sentence-starting tokens and accumulates their respective sub-trees.
    # =====================================================================
    def lista_sentencias(self):
        sents = []
        first_sent = [TokenType.IF, TokenType.WHILE, TokenType.DO, TokenType.CIN, TokenType.COUT, TokenType.ID]
        
        while self.current_token().tipo in first_sent:
            if self.current_token().tipo == TokenType.RBRACE:
                break
            s_node = self.sentencia()
            if s_node:
                sents.append(s_node)
        return sents

    # =====================================================================
    # METHOD: sentencia
    # What it does: Evaluates the grammar rule: sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion | operacion_unaria
    # What components it uses: current_token(), peek_token(), report_error().
    # How it interacts: Dispatches to specific statement evaluation methods based on the current keyword token.
    # =====================================================================
    def sentencia(self):
        token = self.current_token()
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
            return None

    # =====================================================================
    # METHOD: asignacion
    # What it does: Evaluates the grammar rule: asignacion → id sent_expresion
    # What components it uses: match(), ASTNode, sent_expresion().
    # How it interacts: Creates an Assignment node and attaches the evaluated expression as its child.
    # =====================================================================
    def asignacion(self):
        token = self.current_token()
        id_token = self.match(TokenType.ID)
        id_lex = id_token.lexema if id_token else "?"
        
        node = ASTNode("Assignment", id_lex, line=token.linea, col=token.columna)
        self.emit_node("Assignment", id_lex)
        
        exp_node = self.sent_expresion()
        if exp_node:
            node.add_child(exp_node)
        return node

    # =====================================================================
    # METHOD: operacion_unaria
    # What it does: Evaluates the grammar rule: operacion_unaria → id (++ | --) ;
    # What components it uses: match(), ASTNode, TokenType.INC, TokenType.DEC.
    # How it interacts: Captures unary increment or decrement operations as standalone statements.
    # =====================================================================
    def operacion_unaria(self):
        token = self.current_token()
        id_token = self.match(TokenType.ID)
        id_lex = id_token.lexema if id_token else "?"
        
        op_token = self.current_token()
        if op_token.tipo == TokenType.INC:
            self.match(TokenType.INC)
            op_str = "++"
        elif op_token.tipo == TokenType.DEC:
            self.match(TokenType.DEC)
            op_str = "--"
        else:
            self.report_error("Expected ++ or --")
            op_str = "?"
            
        self.match(TokenType.SEMI)
        
        val = f"{id_lex}{op_str}"
        node = ASTNode("Unary Operation", val, line=token.linea, col=token.columna)
        self.emit_node("Unary Operation", val)
        return node

    # =====================================================================
    # METHOD: sent_expresion
    # What it does: Evaluates the grammar rule: sent_expresion → expresion ;
    # What components it uses: current_token(), match(), expresion().
    # How it interacts: Consumes the assignment operator (if present) and expects a semicolon after evaluating the expression.
    # =====================================================================
    def sent_expresion(self):
        if self.current_token().tipo == TokenType.ASSIGN:
            self.match(TokenType.ASSIGN)
            
        exp_node = self.expresion()
        self.match(TokenType.SEMI)
        return exp_node

    # =====================================================================
    # METHOD: seleccion
    # What it does: Evaluates the grammar rule: seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end [;]
    # What components it uses: match(), expresion(), lista_sentencias(), ASTNode.
    # How it interacts: Parses conditional blocks, creating distinct 'Then' and optional 'Else' sub-nodes.
    # =====================================================================
    def seleccion(self):
        token = self.current_token()
        node = ASTNode("Selection (if)", line=token.linea, col=token.columna)
        self.emit_node("Selection (if)", "")
        
        self.match(TokenType.IF)
        node.add_child(self.expresion())
        
        self.match(TokenType.LBRACE)
        then_block = ASTNode("Then Block", line=token.linea, col=token.columna)
        
        for s in self.lista_sentencias():
            then_block.add_child(s)
        self.match(TokenType.RBRACE)
        node.add_child(then_block)
        
        if self.current_token().tipo == TokenType.ELSE:
            el_token = self.match(TokenType.ELSE)
            self.match(TokenType.LBRACE)
            else_block = ASTNode("Else Block", line=el_token.linea, col=el_token.columna)
            for s in self.lista_sentencias():
                else_block.add_child(s)
            self.match(TokenType.RBRACE)
            node.add_child(else_block)
            
        return node

    # =====================================================================
    # METHOD: iteracion
    # What it does: Evaluates the grammar rule: iteracion → while ( expresion ) do lista_sentencias end [;]
    # What components it uses: match(), expresion(), lista_sentencias(), ASTNode.
    # How it interacts: Evaluates a loop construct, assigning the condition expression and the inner block sentences to a 'While' node.
    # =====================================================================
    def iteracion(self):
        token = self.current_token()
        node = ASTNode("Iteration (while)", line=token.linea, col=token.columna)
        self.emit_node("Iteration (while)", "")
        
        self.match(TokenType.WHILE)
        self.match(TokenType.LPAREN)
        node.add_child(self.expresion())
        self.match(TokenType.RPAREN)
        
        self.match(TokenType.LBRACE)
        block = ASTNode("While Body", line=token.linea, col=token.columna)
        for s in self.lista_sentencias():
            block.add_child(s)
        self.match(TokenType.RBRACE)
        
        node.add_child(block)
        return node

    # =====================================================================
    # METHOD: repeticion
    # What it does: Evaluates the grammar rule: repeticion → do { lista_sentencias } while ( expresion ) ;
    # What components it uses: match(), lista_sentencias(), expresion(), ASTNode.
    # How it interacts: Parses a do-while block structure delimited by curly braces, grouping its inner statements before evaluating the exit condition.
    # =====================================================================
    def repeticion(self):
        token = self.current_token()
        node = ASTNode("Repetition (do-while)", line=token.linea, col=token.columna)
        self.emit_node("Repetition (do-while)", "")
        
        self.match(TokenType.DO)
        self.match(TokenType.LBRACE)
        
        block = ASTNode("Do Body", line=token.linea, col=token.columna)
        for s in self.lista_sentencias():
            block.add_child(s)
            
        self.match(TokenType.RBRACE)
        node.add_child(block)
        
        self.match(TokenType.WHILE)
        self.match(TokenType.LPAREN)
        node.add_child(self.expresion())
        self.match(TokenType.RPAREN)
        self.match(TokenType.SEMI)
        return node

    # =====================================================================
    # METHOD: sent_in
    # What it does: Evaluates the grammar rule: sent_in → cin >> id ;
    # What components it uses: match(), ASTNode.
    # How it interacts: Parses console input commands, ensuring the extraction operator (>>) is used correctly before reading an identifier.
    # =====================================================================
    def sent_in(self):
        token = self.current_token()
        self.match(TokenType.CIN)
        
        t = self.current_token()
        if t.tipo == TokenType.GT:
            self.advance()
            if self.current_token().tipo == TokenType.GT:
                self.advance()
            else:
                self.report_error("Expected >>")
        
        id_token = self.match(TokenType.ID)
        id_val = id_token.lexema if id_token else "?"
        
        node = ASTNode("Input (cin)", id_val, line=token.linea, col=token.columna)
        self.emit_node("Input (cin)", id_val)
        
        self.match(TokenType.SEMI)
        return node

    # =====================================================================
    # METHOD: sent_out
    # What it does: Evaluates the grammar rule: sent_out → cout << salida
    # What components it uses: match(), salida(), ASTNode.
    # How it interacts: Validates the insertion operator (<<) and connects to the 'salida' method to process the data being printed.
    # =====================================================================
    def sent_out(self):
        token = self.current_token()
        self.match(TokenType.COUT)
        
        t = self.current_token()
        if t.tipo == TokenType.LT:
            self.advance()
            if self.current_token().tipo == TokenType.LT:
                self.advance()
            else:
                self.report_error("Expected <<")
                
        node = ASTNode("Output (cout)", line=token.linea, col=token.columna)
        self.emit_node("Output (cout)", "")
        
        node.add_child(self.salida())
        self.match(TokenType.SEMI)
        return node

    # =====================================================================
    # METHOD: salida
    # What it does: Evaluates the grammar rule: salida → cadena | expresion | cadena << expresion | expresion << cadena
    # What components it uses: current_token(), cadena(), expresion(), ASTNode.
    # How it interacts: Allows cascading outputs (e.g. cout << "string" << var) by creating a "Salida Múltiple" sub-node when necessary.
    # =====================================================================
    def salida(self):
        token = self.current_token()
        
        if token.tipo == TokenType.STRING:
            node = self.cadena()
        else:
            node = self.expresion()
            
        while self.current_token().tipo == TokenType.LT:
            lt_t = self.current_token()
            self.advance()
            if self.current_token().tipo == TokenType.LT:
                self.advance()
                new_node = ASTNode("Multiple Output", line=lt_t.linea, col=lt_t.columna)
                new_node.add_child(node)
                
                t2 = self.current_token()
                if t2.tipo == TokenType.STRING:
                    new_node.add_child(self.cadena())
                else:
                    new_node.add_child(self.expresion())
                node = new_node
            else:
                self.report_error("Expected <<")
                break
                
        return node

    # =====================================================================
    # METHOD: expresion
    # What it does: Evaluates the grammar rule: expresion → expresion_relacional { (&& | ||) expresion_relacional }
    # What components it uses: expresion_relacional(), current_token(), ASTNode.
    # How it interacts: Establishes top-level logical precedence (AND, OR), dynamically wrapping relational expressions into Logical Operation nodes.
    # =====================================================================
    def expresion(self):
        node = self.expresion_relacional()
        
        while self.current_token().tipo in [TokenType.AND, TokenType.OR]:
            token = self.current_token()
            op_str = token.lexema
            self.advance()
            right_node = self.expresion_relacional()
            
            new_node = ASTNode("Logical Operation", op_str, line=token.linea, col=token.columna)
            self.emit_node("Logical Operation", op_str)
            if node:
                new_node.add_child(node)
            if right_node:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: expresion_relacional
    # What it does: Evaluates the grammar rule: expresion_relacional → expresion_simple [ rel_op expresion_simple ]
    # What components it uses: expresion_simple(), rel_op(), ASTNode.
    # How it interacts: Evaluates comparison operations (<, <=, >, >=, ==, !=), grouping arithmetic sub-trees on both sides.
    # =====================================================================
    def expresion_relacional(self):
        left_node = self.expresion_simple()
        
        rel_ops = [TokenType.LT, TokenType.LTEQ, TokenType.GT, TokenType.GTEQ, TokenType.EQ, TokenType.NEQ]
        token = self.current_token()
        if token.tipo in rel_ops:
            op_str = self.rel_op()
            right_node = self.expresion_simple()
            
            node = ASTNode("Relational Expression", op_str, line=token.linea, col=token.columna)
            self.emit_node("Relational Expression", op_str)
            if left_node:
                node.add_child(left_node)
            if right_node:
                node.add_child(right_node)
            return node
            
        return left_node

    # =====================================================================
    # METHOD: rel_op
    # What it does: Evaluates the grammar rule: rel_op → < | <= | > | >= | == | !=
    # What components it uses: current_token(), advance().
    # How it interacts: Extracts the string representation of relational operators for AST assignments.
    # =====================================================================
    def rel_op(self):
        token = self.current_token()
        self.advance()
        return token.lexema

    # =====================================================================
    # METHOD: expresion_simple
    # What it does: Evaluates the grammar rule: expresion_simple → termino { suma_op termino }
    # What components it uses: termino(), suma_op(), ASTNode.
    # How it interacts: Handles standard arithmetic addition and subtraction logic.
    # =====================================================================
    def expresion_simple(self):
        node = self.termino()
        
        while self.current_token().tipo in [TokenType.PLUS, TokenType.MINUS]:
            token = self.current_token()
            op_str = self.suma_op()
            right_node = self.termino()
            
            new_node = ASTNode("Add/Subtract Operation", op_str, line=token.linea, col=token.columna)
            if node:
                new_node.add_child(node)
            if right_node:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: suma_op
    # What it does: Evaluates the grammar rule: suma_op → + | -
    # What components it uses: current_token(), advance().
    # How it interacts: Extracts the addition/subtraction string literal.
    # =====================================================================
    def suma_op(self):
        token = self.current_token()
        self.advance()
        return token.lexema

    # =====================================================================
    # METHOD: termino
    # What it does: Evaluates the grammar rule: termino → factor { mult_op factor }
    # What components it uses: factor(), mult_op(), ASTNode.
    # How it interacts: Evaluates multiplication, division, and modulo, applying higher precedence over addition logic.
    # =====================================================================
    def termino(self):
        node = self.factor()
        
        while self.current_token().tipo in [TokenType.TIMES, TokenType.OVER, TokenType.MOD]:
            token = self.current_token()
            op_str = self.mult_op()
            right_node = self.factor()
            
            new_node = ASTNode("Multiply/Divide Operation", op_str, line=token.linea, col=token.columna)
            if node:
                new_node.add_child(node)
            if right_node:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: mult_op
    # What it does: Evaluates the grammar rule: mult_op → * | / | %
    # What components it uses: current_token(), advance().
    # How it interacts: Extracts multiplicative operator strings.
    # =====================================================================
    def mult_op(self):
        token = self.current_token()
        self.advance()
        return token.lexema

    # =====================================================================
    # METHOD: factor
    # What it does: Evaluates the grammar rule: factor → componente { pot_op componente }
    # What components it uses: componente(), pot_op(), ASTNode.
    # How it interacts: Solves exponential expressions with the highest mathematical precedence.
    # =====================================================================
    def factor(self):
        node = self.componente()
        
        while self.current_token().tipo == TokenType.POWER:
            token = self.current_token()
            op_str = self.pot_op()
            right_node = self.componente()
            
            new_node = ASTNode("Power Operation", op_str, line=token.linea, col=token.columna)
            if node:
                new_node.add_child(node)
            if right_node:
                new_node.add_child(right_node)
            node = new_node
            
        return node

    # =====================================================================
    # METHOD: pot_op
    # What it does: Evaluates the grammar rule: pot_op → ^
    # What components it uses: current_token(), advance().
    # How it interacts: Extracts the power operator string literal.
    # =====================================================================
    def pot_op(self):
        token = self.current_token()
        self.advance()
        return token.lexema

    # =====================================================================
    # METHOD: componente
    # What it does: Evaluates the grammar rule: componente → ( expresion ) | número | id | bool | op_logico
    # What components it uses: current_token(), expresion(), op_logico(), ASTNode.
    # How it interacts: Extracts terminal leaf nodes (numbers, identifiers, strings) or resets precedence by parsing parenthesized sub-expressions.
    # =====================================================================
    def componente(self):
        token = self.current_token()
        
        if token.tipo == TokenType.NOT:
            self.advance()
            inner = self.componente()
            node = ASTNode("Logical NOT", "!", line=token.linea, col=token.columna)
            self.emit_node("Logical NOT", "!")
            if inner:
                node.add_child(inner)
            return node
            
        elif token.tipo == TokenType.LPAREN:
            self.advance()
            exp_node = self.expresion()
            self.match(TokenType.RPAREN)
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
            return self.cadena()
            
        else:
            self.report_error(f"Invalid expression component")
            return None

    # =====================================================================
    # METHOD: op_logico
    # What it does: Evaluates the grammar rule: op_logico → && | || | !
    # What components it uses: current_token(), advance(), ASTNode.
    # How it interacts: Validates explicit logical operators found outside standard binary precedence bounds.
    # =====================================================================
    def op_logico(self):
        token = self.current_token()
        node = ASTNode("Logical Operator", token.lexema, line=token.linea, col=token.columna)
        self.emit_node("Logical Operator", token.lexema)
        self.advance()
        return node

    # =====================================================================
    # METHOD: cadena
    # What it does: Evaluates the grammar rule: cadena → "cualquier texto"
    # What components it uses: current_token(), advance(), ASTNode.
    # How it interacts: Handles string literals natively as terminal nodes.
    # =====================================================================
    def cadena(self):
        token = self.current_token()
        node = ASTNode("String Literal", token.lexema, line=token.linea, col=token.columna)
        self.emit_node("String Literal", token.lexema)
        self.advance()
        return node