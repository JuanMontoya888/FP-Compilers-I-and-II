from compiler.semantic_analyzer.symbol_table import SymbolTable
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
        self.export_results()
        
        return self.annotated_ast, self.errors

    def export_results(self):
        import os
        curr_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(curr_file_dir))
        output_dir = os.path.join(project_root, "compiler_output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Export Semantic Tree
        with open(os.path.join(output_dir, "semantic_tree.txt"), "w", encoding='utf-8') as f:
            f.write(self._build_ast_string(self.annotated_ast, 0))
            
        # Export Symbol Table
        with open(os.path.join(output_dir, "symbol_table.txt"), "w", encoding='utf-8') as f:
            f.write(f"{'VARIABLE':<15}\t{'TYPE':<10}\t{'VALUE':<12}\t{'OFFSET':<8}\tLINES\n")
            f.write("-" * 65 + "\n")
            for sym in self.sym_table.all_symbols:
                lines_str = ", ".join(map(str, sym.lines))
                val_str = str(sym.value) if getattr(sym, 'value', None) is not None else "-"
                f.write(f"{sym.name:<15}\t{sym.dtype:<10}\t{val_str:<12}\t{sym.offset:<8}\t{lines_str}\n")

    def _build_ast_string(self, node, level):
        if not node:
            return ""
        indent = "  " * level
        result = f"{indent}|-- {node.name.replace(chr(10), ' ')}: {node.value} (Ln {getattr(node, 'line', '')}, Col {getattr(node, 'col', '')})\n"
        for child in node.children:
            result += self._build_ast_string(child, level + 1)
        return result

    def _extract_node_meta(self, node):
        """Extracts and caches immutable node_kind and raw_value before visual mutations."""
        node_kind = node.node_kind if getattr(node, 'node_kind', None) else node.name
        raw_val = node.raw_value if getattr(node, 'raw_value', None) not in (None, "") else node.value
        node.node_kind = node_kind
        node.raw_value = raw_val
        return node_kind, raw_val

    def _traverse(self, node):
        if not node: return

        # Preserve immutable AST metadata before visual annotations mutate node.name / node.value
        node_kind, raw_val = self._extract_node_meta(node)

        # =====================================================================
        # PRE-ORDER TRAVERSAL (Downward)
        # TINY EQUIVALENT: insertNode() in buildSymtab()
        # ---------------------------------------------------------------------
        # We push a new scope when entering a block, and we process variable 
        # declarations to insert them into the symbol table BEFORE evaluating 
        # their children (inherited attributes).
        # =====================================================================
        if node_kind in ["Selection (if)", "Iteration (while)", "Repetition (do-while)", "Program", "Then Block", "Else Block", "Do Body"]:
            self.sym_table.enter_scope()

        # Handle different node types
        if node_kind == "Variable Declaration":
            dtype = raw_val # Inherited attribute
            for child in node.children:
                child_kind, child_raw = self._extract_node_meta(child)
                if child_kind == "Identifier":
                    var_name = child_raw
                    if not self.sym_table.insert(var_name, dtype, child.line):
                        self.report_error(f"Duplicate declaration of '{var_name}' in the same scope", child.line, child.col, child)
                    sym = self.sym_table.lookup(var_name)
                    child.var_name = var_name
                    child.dtype = dtype # annotate AST
                    child.mem_offset = sym.offset if sym else None
                    child.tm_offset = sym.tm_offset if sym else None
                    child.name = f"Identifier\n-> ({dtype})"
                elif child_kind == "Initialization":
                    var_node = child.children[0]
                    _, var_name = self._extract_node_meta(var_node)
                    if not self.sym_table.insert(var_name, dtype, var_node.line):
                        self.report_error(f"Duplicate declaration of '{var_name}' in the same scope", var_node.line, var_node.col, var_node)
                    sym = self.sym_table.lookup(var_name)
                    mem_off = sym.offset if sym else None
                    tm_off = sym.tm_offset if sym else None

                    var_node.var_name = var_name
                    var_node.dtype = dtype
                    var_node.mem_offset = mem_off
                    var_node.tm_offset = tm_off

                    child.op = "="
                    child.var_name = var_name
                    child.dtype = dtype
                    child.mem_offset = mem_off
                    child.tm_offset = tm_off
                    
                    # Need to evaluate expression and type check!
                    if len(child.children) > 1:
                        exp_node = child.children[1]
                        self._traverse(exp_node)
                        self._check_type_compatibility(dtype, getattr(exp_node, 'dtype', 'error'), exp_node, child)
                        
                        exp_type = getattr(exp_node, 'dtype', 'error')
                        status = "OK"
                        if dtype != exp_type:
                            if not (dtype == "float" and exp_type == "int"):
                                status = "Error"
                        if exp_type == "error":
                            status = "Error"

                        val = getattr(exp_node, 'const_value', None)
                        if sym and status == "OK" and val is not None:
                            if dtype == "float" and isinstance(val, int):
                                val = float(val)
                            elif dtype == "int" and isinstance(val, float):
                                val = int(val)
                            sym.value = val
                            var_node.const_value = val
                            var_node.name = f"Identifier\n-> ({dtype}) = {val}"
                            child.name = f"Initialization\n{dtype} = {exp_type} -> {status}\nval = {val}"
                        else:
                            var_node.name = f"Identifier\n-> ({dtype})"
                            child.name = f"Initialization\n{dtype} = {exp_type} -> {status}"
            
            # Since we traversed children manually for declarations, we can skip general traversal for this node
            
        elif node_kind == "Assignment":
            # Parent node is Assignment with value "="
            # Children:
            # children[0] = Identifier (target variable token)
            # children[1] = Expression (evaluated expression)
            if len(node.children) >= 2:
                id_node = node.children[0]
                exp_node = node.children[1]
                _, var_name = self._extract_node_meta(id_node)
            else:
                var_name = raw_val
                id_node = None
                exp_node = node.children[0] if len(node.children) > 0 else None

            node.op = "="
            node.var_name = var_name

            sym = self.sym_table.lookup(var_name)
            if not sym:
                self.report_error(f"Undeclared variable '{var_name}'", node.line, node.col, node)
                node.dtype = "error"
                if id_node:
                    id_node.dtype = "error"
                    id_node.var_name = var_name
            else:
                self.sym_table.add_reference(var_name, node.line)
                node.dtype = sym.dtype
                node.mem_offset = sym.offset
                node.tm_offset = sym.tm_offset
                if id_node:
                    id_node.dtype = sym.dtype
                    id_node.var_name = var_name
                    id_node.mem_offset = sym.offset
                    id_node.tm_offset = sym.tm_offset
                
            # Traverse expression
            if exp_node:
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
                    
                    val = getattr(exp_node, 'const_value', None)
                    if status == "OK" and val is not None:
                        if sym.dtype == "float" and isinstance(val, int):
                            val = float(val)
                        elif sym.dtype == "int" and isinstance(val, float):
                            val = int(val)
                        sym.value = val
                        node.const_value = val
                        if id_node:
                            id_node.const_value = val
                            id_node.name = f"Identifier\n-> ({sym.dtype}) = {val}"
                        node.name = f"Assignment\n{sym.dtype} = {exp_type} -> {status}\nval = {val}"
                    else:
                        if status == "OK":
                            sym.value = None # reset if runtime or non-constant
                        if id_node:
                            id_node.name = f"Identifier\n-> ({sym.dtype})"
                        node.name = f"Assignment\n{sym.dtype} = {exp_type} -> {status}"
        
        elif node_kind == "Identifier":
            # This is a variable usage (in expressions, etc)
            var_name = raw_val
            node.var_name = var_name
            sym = self.sym_table.lookup(var_name)
            if not sym:
                self.report_error(f"Undeclared variable '{var_name}'", node.line, node.col, node)
                node.dtype = "error"
            else:
                self.sym_table.add_reference(var_name, node.line)
                node.dtype = sym.dtype
                node.mem_offset = sym.offset
                node.tm_offset = sym.tm_offset
                if getattr(sym, 'value', None) is not None:
                    node.const_value = sym.value
                    node.name = f"Id ({sym.dtype})\nval = {sym.value}"
                else:
                    node.name = f"Id ({sym.dtype})"
                
        elif node_kind in ["Numeric Literal", "Boolean Literal", "String Literal"]:
            if node_kind == "Numeric Literal":
                node.dtype = "float" if "." in str(raw_val) else "int"
                try:
                    if node.dtype == "int": node.const_value = int(raw_val)
                    else: node.const_value = float(raw_val)
                except: pass
            elif node_kind == "Boolean Literal":
                node.dtype = "bool"
                node.const_value = True if raw_val == "true" else False
            elif node_kind == "String Literal":
                node.dtype = "string"
                
        elif node_kind in ["Arithmetic Expression", "Relational Expression", "Logical Expression", "Logical Operation"]:
            for child in node.children:
                self._traverse(child)
            
            # Preserve clean operator before constant folding mutates node.value
            op_char = str(raw_val)
            node.op = op_char

            if len(node.children) == 2:
                left_type = getattr(node.children[0], 'dtype', 'error')
                right_type = getattr(node.children[1], 'dtype', 'error')
                
                node.dtype = self._get_result_type(op_char, left_type, right_type, node)
                
                # Annotate AST node name with detailed type propagation
                if node.dtype != "error":
                    node.name = f"{node_kind}\n{left_type} {op_char} {right_type} -> {node.dtype}"
                
                # Constant folding (visual only; codegen still evaluates children)
                left_const = getattr(node.children[0], 'const_value', None)
                right_const = getattr(node.children[1], 'const_value', None)
                if left_const is not None and right_const is not None:
                    node.const_value = self._fold_constants(op_char, left_const, right_const)
                    if node.const_value is not None:
                        # Append semantic info to the value field for visualization
                        node.value = str(node.const_value)

        elif node_kind == "Logical NOT":
            node.op = "!"
            for child in node.children:
                self._traverse(child)

            if len(node.children) >= 1:
                inner = node.children[0]
                inner_type = getattr(inner, 'dtype', 'error')
                if inner_type == "error":
                    node.dtype = "error"
                elif inner_type != "bool":
                    self.report_error(f"Logical operator '!' requires boolean operand, got {inner_type}", node.line, node.col, node)
                    node.dtype = "error"
                else:
                    node.dtype = "bool"
                    node.name = f"Logical NOT\n!{inner_type} -> bool"
                    inner_val = getattr(inner, 'const_value', None)
                    if isinstance(inner_val, bool):
                        node.const_value = not inner_val
                        
        elif node_kind == "Unary Operation":
            # The value string is like "x++"
            raw_str = str(raw_val)
            var_name = raw_str.replace("++", "").replace("--", "")
            op_str = "++" if "++" in raw_str else ("--" if "--" in raw_str else "")
            node.var_name = var_name
            node.op = op_str

            sym = self.sym_table.lookup(var_name)
            if not sym:
                self.report_error(f"Undeclared variable '{var_name}' in unary operation", node.line, node.col, node)
                node.dtype = "error"
            else:
                self.sym_table.add_reference(var_name, node.line)
                node.dtype = sym.dtype
                node.mem_offset = sym.offset
                node.tm_offset = sym.tm_offset
                if sym.dtype not in ["int", "float"]:
                    self.report_error(f"Invalid operand: Unary operations require numeric types, got {sym.dtype}", node.line, node.col, node)
                    node.dtype = "error"
                else:
                    if getattr(sym, 'value', None) is not None:
                        if "++" in raw_str:
                            sym.value += 1
                        elif "--" in raw_str:
                            sym.value -= 1
                        node.name = f"{node_kind}\nval = {sym.value}"
                    
        elif node_kind == "Input (cin)":
            var_name = raw_val
            node.var_name = var_name
            if var_name: # might be empty on syntax error
                sym = self.sym_table.lookup(var_name)
                if not sym:
                    self.report_error(f"Undeclared variable '{var_name}' in cin", node.line, node.col, node)
                    node.dtype = "error"
                else:
                    self.sym_table.add_reference(var_name, node.line)
                    node.dtype = sym.dtype
                    node.mem_offset = sym.offset
                    node.tm_offset = sym.tm_offset
                    sym.value = None # Runtime user input resets constant value
                    
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
            if node_kind in ["Selection (if)", "Iteration (while)", "Repetition (do-while)"]:
                cond_idx = 1 if node_kind == "Repetition (do-while)" else 0
                if len(node.children) > cond_idx:
                    self._validate_condition_node(node.children[cond_idx], node)
                        
        # Append semantic info to the node name for visualization
        if hasattr(node, 'dtype') and node.dtype and node.dtype != "error":
            if "Literal" in node.name or node.name.startswith("Variable Declaration"):
                if "->" not in node.name:
                    node.name = f"{node.name}\n-> {node.dtype}"
                
        # Post-order: Exit Scopes
        if node_kind in ["Selection (if)", "Iteration (while)", "Repetition (do-while)", "Program", "Then Block", "Else Block", "Do Body"]:
            self.sym_table.exit_scope()

    def _validate_condition_node(self, cond_node, parent_node):
        """Ensures control-flow condition expressions evaluate to boolean."""
        cond_kind = getattr(cond_node, 'node_kind', cond_node.name)
        expr_kinds = {
            "Arithmetic Expression",
            "Relational Expression",
            "Logical Expression",
            "Logical Operation",
            "Logical NOT",
            "Identifier",
            "Numeric Literal",
            "Boolean Literal",
            "String Literal",
        }
        if cond_kind in expr_kinds or cond_node.name.startswith(("Arithmetic", "Relational", "Logical", "Identifier")) or "Literal" in cond_node.name:
            c_type = getattr(cond_node, 'dtype', 'error')
            if c_type not in ["bool", "error"]:
                self.report_error(f"Condition expression must be of boolean type, got {c_type}", parent_node.line, parent_node.col, cond_node)

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
        if parent_node.name.startswith("Assignment"):
            if len(parent_node.children) >= 1 and parent_node.children[0].name.startswith("Identifier"):
                var_name = parent_node.children[0].value
            else:
                var_name = parent_node.value
        elif parent_node.name.startswith("Initialization") and len(parent_node.children) > 0:
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
