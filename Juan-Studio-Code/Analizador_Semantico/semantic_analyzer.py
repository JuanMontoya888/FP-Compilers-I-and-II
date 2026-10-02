from Analizador_Semantico.symbol_table import SymbolTable
import copy

class SemanticAnalyzer:
    def __init__(self):
        self.sym_table = SymbolTable()
        self.errors = []
        self.annotated_ast = None

    # =========================================================================
    # TINY EQUIVALENT: typeError()
    # -------------------------------------------------------------------------
    # In TINY, this logs errors without necessarily breaking the traversal.
    # =========================================================================
    def report_error(self, message, line, col, node=None):
        self.errors.append({"msg": message, "line": line, "col": col})
        if node:
            node.has_error = True

    # =========================================================================
    # TINY EQUIVALENT: buildSymtab() & typeCheck() Initialization
    # -------------------------------------------------------------------------
    # In the classic TINY compiler, semantic analysis requires two separate passes:
    #   1. traverse(ast_root, insertNode, nullProc) -> builds the Symbol Table
    #   2. traverse(ast_root, nullProc, checkNode)  -> performs Type Checking
    #
    # Here, we do a SINGLE PASS utilizing Python's recursion stack to handle
    # both pre-order (insertNode) and post-order (checkNode) simultaneously.
    # =========================================================================
    def analyze(self, ast_root):
        if not ast_root:
            return None, self.errors
            
        self.annotated_ast = copy.deepcopy(ast_root)
        self.sym_table = SymbolTable()
        self.errors = []
        
        self._traverse(self.annotated_ast)
        
        return self.annotated_ast, self.errors

    def _traverse(self, node):
        if not node: return

        # =====================================================================
        # PRE-ORDER TRAVERSAL (Downward)
        # TINY EQUIVALENT: insertNode() in buildSymtab()
        # ---------------------------------------------------------------------
        # We push a new scope when entering a block, and we process variable 
        # declarations to insert them into the symbol table BEFORE evaluating 
        # their children (inherited attributes).
        # =====================================================================
        if node.name in ["Selection (if)", "Iteration (while)", "Repetition (do-while)", "Program", "Then Block", "Else Block", "Do Body"]:
            self.sym_table.enter_scope()

        # Handle different node types
        if node.name == "Variable Declaration":
            dtype = node.value # Inherited attribute
            for child in node.children:
                if child.name == "Identifier":
                    var_name = child.value
                    if not self.sym_table.insert(var_name, dtype, child.line):
                        self.report_error(f"Duplicate declaration of '{var_name}' in the same scope", child.line, child.col, child)
                    child.dtype = dtype # annotate AST
                elif child.name == "Initialization":
                    var_node = child.children[0]
                    var_name = var_node.value
                    if not self.sym_table.insert(var_name, dtype, var_node.line):
                        self.report_error(f"Duplicate declaration of '{var_name}' in the same scope", var_node.line, var_node.col, var_node)
                    var_node.dtype = dtype
                    
                    # Need to evaluate expression and type check!
                    if len(child.children) > 1:
                        exp_node = child.children[1]
                        self._traverse(exp_node)
                        self._check_type_compatibility(dtype, getattr(exp_node, 'dtype', 'error'), exp_node, child)
            
            # Since we traversed children manually for declarations, we can skip general traversal for this node
            
        elif node.name == "Assignment":
            var_name = node.value
            sym = self.sym_table.lookup(var_name)
            if not sym:
                self.report_error(f"Undeclared variable '{var_name}'", node.line, node.col, node)
                node.dtype = "error"
            else:
                self.sym_table.add_reference(var_name, node.line)
                node.dtype = sym.dtype
                
            # Traverse expression
            if len(node.children) > 0:
                exp_node = node.children[0]
                self._traverse(exp_node)
                if sym:
                    exp_type = getattr(exp_node, 'dtype', 'error')
                    self._check_type_compatibility(sym.dtype, exp_type, exp_node, node)
                    
                    status = "OK"
                    if sym.dtype != exp_type:
                        if not (sym.dtype == "float" and exp_type == "int"):
                            status = "Error"
                    if exp_type == "error":
                        status = "Error"
                    
                    node.name = f"{node.name}\n{sym.dtype} = {exp_type} -> {status}"
        
        elif node.name == "Identifier":
            # This is a variable usage (in expressions, etc)
            sym = self.sym_table.lookup(node.value)
            if not sym:
                self.report_error(f"Undeclared variable '{node.value}'", node.line, node.col, node)
                node.dtype = "error"
            else:
                self.sym_table.add_reference(node.value, node.line)
                node.dtype = sym.dtype
                node.name = f"Id ({sym.dtype})" # visual annotation
                
        elif node.name in ["Numeric Literal", "Boolean Literal", "String Literal"]:
            if node.name == "Numeric Literal":
                node.dtype = "float" if "." in node.value else "int"
                try:
                    if node.dtype == "int": node.const_value = int(node.value)
                    else: node.const_value = float(node.value)
                except: pass
            elif node.name == "Boolean Literal":
                node.dtype = "bool"
                node.const_value = True if node.value == "true" else False
            elif node.name == "String Literal":
                node.dtype = "string"
                
        elif node.name in ["Arithmetic Expression", "Relational Expression", "Logical Expression"]:
            for child in node.children:
                self._traverse(child)
            
            if len(node.children) == 2:
                left_type = getattr(node.children[0], 'dtype', 'error')
                right_type = getattr(node.children[1], 'dtype', 'error')
                
                # The operator character (+, -, *, <, ==, etc.) is stored in node.value
                op_char = str(node.value)
                
                node.dtype = self._get_result_type(op_char, left_type, right_type, node)
                
                # Annotate AST node name with detailed type propagation
                if node.dtype != "error":
                    node.name = f"{node.name}\n{left_type} {op_char} {right_type} -> {node.dtype}"
                
                # Constant folding
                if hasattr(node.children[0], 'const_value') and hasattr(node.children[1], 'const_value'):
                    node.const_value = self._fold_constants(op_char, node.children[0].const_value, node.children[1].const_value)
                    if node.const_value is not None:
                        # Append semantic info to the value field for visualization
                        node.value = str(node.const_value)
                        
        elif node.name == "Unary Operation":
            # The value string is like "x++"
            var_name = node.value.replace("++", "").replace("--", "")
            sym = self.sym_table.lookup(var_name)
            if not sym:
                self.report_error(f"Undeclared variable '{var_name}' in unary operation", node.line, node.col, node)
                node.dtype = "error"
            else:
                self.sym_table.add_reference(var_name, node.line)
                node.dtype = sym.dtype
                if sym.dtype not in ["int", "float"]:
                    self.report_error(f"Invalid operand: Unary operations require numeric types, got {sym.dtype}", node.line, node.col, node)
                    node.dtype = "error"
                    
        elif node.name == "Input (cin)":
            var_name = node.value
            if var_name: # might be empty on syntax error
                sym = self.sym_table.lookup(var_name)
                if not sym:
                    self.report_error(f"Undeclared variable '{var_name}' in cin", node.line, node.col, node)
                    node.dtype = "error"
                else:
                    self.sym_table.add_reference(var_name, node.line)
                    node.dtype = sym.dtype
                    
        else:
            # =================================================================
            # RECURSION (Depth-First)
            # -----------------------------------------------------------------
            for child in node.children:
                self._traverse(child)
                
            # =================================================================
            # POST-ORDER TRAVERSAL (Upward)
            # TINY EQUIVALENT: checkNode() in typeCheck()
            # -----------------------------------------------------------------
            # After children are evaluated (synthesized attributes are ready), 
            # we perform the semantic type checks and validation rules.
            # =================================================================
            
            # Post-order: check conditions for control flow
            if node.name in ["Selection (if)", "Iteration (while)"]:
                if len(node.children) > 0:
                    cond_node = node.children[0]
                    if cond_node.name.startswith("Arithmetic") or cond_node.name.startswith("Relational") or cond_node.name.startswith("Logical") or cond_node.name.startswith("Identifier") or "Literal" in cond_node.name:
                        c_type = getattr(cond_node, 'dtype', 'error')
                        if c_type not in ["bool", "error"]:
                            self.report_error(f"Condition expression must be of boolean type, got {c_type}", node.line, node.col, cond_node)
            elif node.name == "Repetition (do-while)":
                if len(node.children) > 1:
                    cond_node = node.children[1] # Condition is the 2nd child
                    if cond_node.name.startswith("Arithmetic") or cond_node.name.startswith("Relational") or cond_node.name.startswith("Logical") or cond_node.name.startswith("Identifier") or "Literal" in cond_node.name:
                        c_type = getattr(cond_node, 'dtype', 'error')
                        if c_type not in ["bool", "error"]:
                            self.report_error(f"Condition expression must be of boolean type, got {c_type}", node.line, node.col, cond_node)
                        
        # Append semantic info to the node name for visualization
        if hasattr(node, 'dtype') and node.dtype and node.dtype != "error":
            if "Literal" in node.name or node.name.startswith("Variable Declaration") or node.name.startswith("Identifier"):
                if "->" not in node.name:
                    node.name = f"{node.name}\n-> {node.dtype}"
                
        # Post-order: Exit Scopes
        if node.name in ["Selection (if)", "Iteration (while)", "Repetition (do-while)", "Program", "Then Block", "Else Block", "Do Body"]:
            self.sym_table.exit_scope()

    # =========================================================================
    # TINY EQUIVALENT: typeError() checks inside typeCheck()
    # -------------------------------------------------------------------------
    # In the TINY compiler, typeCheck validates nodes and calls typeError 
    # when types clash. This specialized function handles those mismatch validations.
    # =========================================================================
    def _check_type_compatibility(self, target_type, src_type, src_node, parent_node):
        if target_type == "error" or src_type == "error": return
        if target_type == src_type: return
        
        if target_type == "float" and src_type == "int":
            # Implicit conversion allowed
            src_node.name += " (cast float)"
            return
            
        var_name = ""
        if parent_node.name == "Assignment":
            var_name = parent_node.value
        elif parent_node.name == "Initialization" and len(parent_node.children) > 0:
            var_name = parent_node.children[0].value
            
        if var_name:
            msg = f"Type mismatch in assignment. Cannot assign '{src_type}' to '{target_type}' variable '{var_name}'"
        else:
            msg = f"Type mismatch: Cannot assign '{src_type}' to '{target_type}'"
            
        self.report_error(msg, getattr(src_node, 'line', parent_node.line), getattr(src_node, 'col', parent_node.col), parent_node)
        
    def _get_result_type(self, op_char, left_type, right_type, node):
        if left_type == "error" or right_type == "error": return "error"
        
        math_ops = ["+", "-", "*", "/", "%", "^"]
        rel_ops = ["<", ">", "==", "!=", "<=", ">="]
        log_ops = ["&&", "||"]
        
        if op_char in math_ops:
            if left_type in ["int", "float"] and right_type in ["int", "float"]:
                if left_type == "float" or right_type == "float": return "float"
                return "int"
            else:
                self.report_error(f"Invalid operand types for math operation: {left_type} and {right_type}", node.line, node.col, node)
                return "error"
                
        elif op_char in rel_ops:
            if left_type in ["int", "float"] and right_type in ["int", "float"]:
                return "bool"
            elif left_type == right_type: # bool == bool
                return "bool"
            else:
                self.report_error(f"Invalid operand types for relational operation: {left_type} and {right_type}", node.line, node.col, node)
                return "error"
                
        elif op_char in log_ops:
            if left_type == "bool" and right_type == "bool":
                return "bool"
            else:
                self.report_error(f"Logical operators require boolean operands, got {left_type} and {right_type}", node.line, node.col, node)
                return "error"
                
        return "error"

    def _fold_constants(self, op_char, left_val, right_val):
        try:
            if op_char == "+": return left_val + right_val
            if op_char == "-": return left_val - right_val
            if op_char == "*": return left_val * right_val
            if op_char == "/": 
                if right_val == 0: return None
                return left_val / right_val if isinstance(left_val, float) or isinstance(right_val, float) else left_val // right_val
            if op_char == "%": return left_val % right_val
            if op_char == "^": return left_val ** right_val
            if op_char == "<": return left_val < right_val
            if op_char == ">": return left_val > right_val
            if op_char == "==": return left_val == right_val
            if op_char == "!=": return left_val != right_val
            if op_char == "<=": return left_val <= right_val
            if op_char == ">=": return left_val >= right_val
            if op_char == "&&": return left_val and right_val
            if op_char == "||": return left_val or right_val
        except:
            pass
        return None
