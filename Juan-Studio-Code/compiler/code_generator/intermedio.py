import os


class IntermediateCodeGenerator:
    """
    Generates classical three-address intermediate code (.ci) from an
    annotated AST produced by SemanticAnalyzer.

    This output is a parallel didactic representation from the same AST
    and does not replace or feed the TM target code generator.
    """

    CONTAINER_KINDS = frozenset({
        "Program",
        "Then Block",
        "Else Block",
        "While Body",
        "Do Body",
    })

    BINARY_EXP_KINDS = frozenset({
        "Arithmetic Expression",
        "Relational Expression",
        "Logical Operation",
        "Logical Expression",
    })

    LITERAL_KINDS = frozenset({
        "Numeric Literal",
        "Boolean Literal",
        "String Literal",
    })

    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions = []

    def reset(self):
        """Resets temporary/label counters and clears emitted instructions."""
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions = []

    def new_temp(self) -> str:
        """Allocates and returns a new sequential symbolic temporary (t1, t2, ...)."""
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self) -> str:
        """Allocates and returns a new sequential symbolic label (L1, L2, ...)."""
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, instruction: str):
        """Appends a three-address instruction line to the output buffer."""
        self.instructions.append(instruction)

    def _get_kind(self, node) -> str:
        """Reads immutable node_kind, ignoring visual annotations on node.name."""
        if node is None:
            return ""
        kind = getattr(node, "node_kind", None)
        return kind if kind else getattr(node, "name", "")

    def generar_codigo_intermedio(self, ast_root, output_path=None) -> str:
        """
        Traverses ast_root to generate three-address code and writes the .ci file.
        Returns the generated code string.
        """
        self.reset()
        if not ast_root:
            return ""

        self._gen_node(ast_root)
        code = "\n".join(self.instructions)

        if output_path is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(curr_dir))
            output_path = os.path.join(project_root, "compiler_output", "intermedio.ci")

        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)

        return code

    def _gen_node(self, node):
        """Dispatches statement and container AST nodes for three-address emission."""
        if not node:
            return

        kind = self._get_kind(node)

        if kind in self.CONTAINER_KINDS:
            for child in node.children:
                self._gen_node(child)
            return

        if kind == "Variable Declaration":
            for child in node.children:
                if self._get_kind(child) == "Initialization":
                    self._gen_node(child)
            return

        if kind in ("Initialization", "Assignment"):
            self._gen_assign(node)
            return

        if kind == "Unary Operation":
            self._gen_unary(node)
            return

        if kind == "Input (cin)":
            var_name = getattr(node, "var_name", None) or getattr(node, "raw_value", None)
            if var_name:
                self.emit(f"read {var_name}")
            return

        if kind in ("Output (cout)", "Multiple Output"):
            self._emit_output_items(node)
            return

        if kind == "Selection (if)":
            self._gen_if(node)
            return

        if kind == "Iteration (while)":
            self._gen_while(node)
            return

        if kind == "Repetition (do-while)":
            self._gen_do_while(node)
            return

        if kind in self.BINARY_EXP_KINDS or kind in self.LITERAL_KINDS or kind in ("Identifier", "Logical NOT"):
            self._gen_exp(node)
            return

        for child in node.children:
            self._gen_node(child)

    def _gen_assign(self, node):
        """Emits three-address code for variable initialization or assignment."""
        var_name = getattr(node, "var_name", None)
        if not var_name and node.children:
            var_name = getattr(node.children[0], "var_name", None) or getattr(node.children[0], "raw_value", None)

        exp_node = node.children[1] if len(node.children) > 1 else (node.children[0] if node.children else None)
        if var_name and exp_node is not None:
            rhs = self._gen_exp(exp_node)
            self.emit(f"{var_name} = {rhs}")

    def _gen_unary(self, node):
        """Translates x++ / x-- into two three-address instructions using a temporary."""
        raw_str = str(getattr(node, "raw_value", "") or "")
        var_name = getattr(node, "var_name", None) or raw_str.replace("++", "").replace("--", "")
        op_raw = getattr(node, "op", None) or ("++" if "++" in raw_str else "--")
        arith_op = "+" if op_raw == "++" else "-"

        temp = self.new_temp()
        self.emit(f"{temp} = {var_name} {arith_op} 1")
        self.emit(f"{var_name} = {temp}")

    def _emit_output_items(self, node):
        """Recursively emits write directives left-to-right for cout and Multiple Output."""
        if not node:
            return

        kind = self._get_kind(node)
        if kind in ("Output (cout)", "Multiple Output"):
            for child in node.children:
                self._emit_output_items(child)
            return

        val = self._gen_exp(node)
        self.emit(f"write {val}")

    def _gen_if(self, node):
        """Emits conditional jump and labels for if / if-else selection."""
        cond_node = node.children[0] if len(node.children) > 0 else None
        then_node = node.children[1] if len(node.children) > 1 else None
        else_node = node.children[2] if len(node.children) > 2 else None

        cond_val = self._gen_exp(cond_node)

        if else_node is not None:
            l_else = self.new_label()
            l_end = self.new_label()
            self.emit(f"if_false {cond_val} goto {l_else}")
            self._gen_node(then_node)
            self.emit(f"goto {l_end}")
            self.emit(f"{l_else}:")
            self._gen_node(else_node)
            self.emit(f"{l_end}:")
        else:
            l_end = self.new_label()
            self.emit(f"if_false {cond_val} goto {l_end}")
            self._gen_node(then_node)
            self.emit(f"{l_end}:")

    def _gen_while(self, node):
        """Emits loop start/end labels and conditional exit for while iteration."""
        cond_node = node.children[0] if len(node.children) > 0 else None
        body_node = node.children[1] if len(node.children) > 1 else None

        l_start = self.new_label()
        l_end = self.new_label()

        self.emit(f"{l_start}:")
        cond_val = self._gen_exp(cond_node)
        self.emit(f"if_false {cond_val} goto {l_end}")
        self._gen_node(body_node)
        self.emit(f"goto {l_start}")
        self.emit(f"{l_end}:")

    def _gen_do_while(self, node):
        """Emits body-first loop and repeat-while-true branch for do-while."""
        body_node = node.children[0] if len(node.children) > 0 else None
        cond_node = node.children[1] if len(node.children) > 1 else None

        l_start = self.new_label()
        self.emit(f"{l_start}:")
        self._gen_node(body_node)
        cond_val = self._gen_exp(cond_node)
        self.emit(f"if_true {cond_val} goto {l_start}")

    def _gen_exp(self, node) -> str:
        """Evaluates expressions in post-order, returning a literal, variable, or temp."""
        if not node:
            return ""

        kind = self._get_kind(node)

        if kind in self.LITERAL_KINDS:
            raw = getattr(node, "raw_value", None)
            return str(raw if raw is not None else node.value)

        if kind == "Identifier":
            var_name = getattr(node, "var_name", None) or getattr(node, "raw_value", None)
            return str(var_name if var_name is not None else node.value)

        if kind in self.BINARY_EXP_KINDS:
            if len(node.children) >= 2:
                left_operand = self._gen_exp(node.children[0])
                right_operand = self._gen_exp(node.children[1])
                op = getattr(node, "op", None) or getattr(node, "raw_value", None) or node.value
                temp = self.new_temp()
                self.emit(f"{temp} = {left_operand} {op} {right_operand}")
                return temp

        if kind == "Logical NOT":
            if node.children:
                inner_operand = self._gen_exp(node.children[0])
                op = getattr(node, "op", None) or "!"
                temp = self.new_temp()
                self.emit(f"{temp} = {op}{inner_operand}")
                return temp

        raw = getattr(node, "raw_value", None)
        return str(raw if raw is not None else node.value)


def generar_codigo_intermedio(ast_root, output_path=None) -> str:
    """Module-level entry point equivalent to generarCodigoIntermedio(raiz, destino)."""
    generator = IntermediateCodeGenerator()
    return generator.generar_codigo_intermedio(ast_root, output_path)
