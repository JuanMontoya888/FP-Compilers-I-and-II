import os
from .code import TMCodeEmitter


class TMCodeGenerator:
    """
    Translates a semantically validated AST into Tiny Machine (.tm) instructions.
    Direct Python adaptation of Louden's cgen.h and cgen.c.
    """

    CONTAINER_KINDS = frozenset({
        "Program",
        "Then Block",
        "Else Block",
        "While Body",
        "Do Body",
    })

    STMT_KINDS = frozenset({
        "Variable Declaration",
        "Initialization",
        "Assignment",
        "Unary Operation",
        "Input (cin)",
        "Output (cout)",
        "Multiple Output",
        "Selection (if)",
        "Iteration (while)",
        "Repetition (do-while)",
    })

    BINARY_EXP_KINDS = frozenset({
        "Arithmetic Expression",
        "Relational Expression",
        "Logical Operation",
        "Logical Expression",
    })

    RELATIONAL_JUMPS = {
        "<": "JLT",
        "<=": "JLE",
        ">": "JGT",
        ">=": "JGE",
        "==": "JEQ",
        "!=": "JNE",
    }

    def __init__(self, trace_code: bool = True):
        self.emitter = TMCodeEmitter(trace_code=trace_code)
        self.tmpOffset = 0
        self._var_offsets = {}

    def _get_kind(self, node) -> str:
        """Reads immutable node_kind, ignoring visual annotations on node.name."""
        if node is None:
            return ""
        kind = getattr(node, "node_kind", None)
        return kind if kind else getattr(node, "name", "")

    def _get_tm_offset(self, node) -> int:
        """Retrieves the sequential TM word offset (relative to gp) from the AST node."""
        if not node:
            return 0

        var_name = getattr(node, "var_name", None)
        tm_off = getattr(node, "tm_offset", None)

        if tm_off is None and getattr(node, "children", None):
            first_child = node.children[0]
            if self._get_kind(first_child) == "Identifier":
                tm_off = getattr(first_child, "tm_offset", None)
                if not var_name:
                    var_name = getattr(first_child, "var_name", None) or getattr(first_child, "raw_value", None)

        if tm_off is not None:
            if var_name:
                self._var_offsets[var_name] = tm_off
            return tm_off

        if not var_name:
            var_name = getattr(node, "raw_value", None)
        return self._var_offsets.get(var_name, 0)

    def codeGen(self, ast_root, output_path=None) -> str:
        """
        Generates Tiny Machine (.tm) instructions for ast_root and writes them to output_path.
        Returns the generated TM program text.
        """
        self.emitter.reset()
        self.tmpOffset = 0
        self._var_offsets = {}

        if not ast_root:
            return ""

        ac = self.emitter.ac
        mp = self.emitter.mp

        # Standard TM prelude
        self.emitter.emitComment("TINY / JPP Compilation to TM Code")
        self.emitter.emitComment("Standard prelude:")
        self.emitter.emitRM("LD", mp, 0, ac, "load maxaddress from location 0")
        self.emitter.emitRM("ST", ac, 0, ac, "clear location 0")
        self.emitter.emitComment("End of standard prelude.")

        # Generate code for the validated AST
        self.cGen(ast_root)

        # Standard TM epilogue
        self.emitter.emitComment("End of execution.")
        self.emitter.emitRO("HALT", 0, 0, 0, "")

        tm_code = self.emitter.get_code()

        if output_path is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(curr_dir))
            output_path = os.path.join(project_root, "compiler_output", "programa.tm")

        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(tm_code)

        return tm_code

    def cGen(self, node):
        """Recursively walks the AST generating TM instructions."""
        if not node:
            return

        kind = self._get_kind(node)
        if kind in self.CONTAINER_KINDS:
            for child in node.children:
                self.cGen(child)
        elif kind in self.STMT_KINDS:
            self.gen_stmt(node)
        else:
            self.gen_exp(node)

    def gen_stmt(self, node):
        """Generates TM instructions for statement nodes."""
        if not node:
            return

        kind = self._get_kind(node)
        ac = self.emitter.ac
        ac1 = self.emitter.ac1
        gp = self.emitter.gp
        pc = self.emitter.pc

        if kind == "Variable Declaration":
            for child in node.children:
                child_kind = self._get_kind(child)
                if child_kind == "Identifier":
                    self._get_tm_offset(child)
                elif child_kind == "Initialization":
                    self.gen_stmt(child)

        elif kind in ("Initialization", "Assignment"):
            self.emitter.emitComment("-> assign")
            exp_node = node.children[1] if len(node.children) > 1 else (node.children[0] if node.children else None)
            if exp_node is not None:
                self.gen_exp(exp_node)
            offset = self._get_tm_offset(node)
            var_name = getattr(node, "var_name", None) or getattr(node, "raw_value", "")
            self.emitter.emitRM("ST", ac, offset, gp, f"assign: store value into {var_name}")
            self.emitter.emitComment("<- assign")

        elif kind == "Unary Operation":
            self.emitter.emitComment("-> unary op")
            offset = self._get_tm_offset(node)
            raw_str = str(getattr(node, "raw_value", "") or "")
            var_name = getattr(node, "var_name", None) or raw_str.replace("++", "").replace("--", "")
            op_str = getattr(node, "op", None) or ("++" if "++" in raw_str else "--")
            ro_op = "ADD" if op_str == "++" else "SUB"

            self.emitter.emitRM("LD", ac, offset, gp, f"unary: load {var_name}")
            self.emitter.emitRM("LDC", ac1, 1, 0, "unary: load constant 1")
            self.emitter.emitRO(ro_op, ac, ac, ac1, f"unary: {var_name}{op_str}")
            self.emitter.emitRM("ST", ac, offset, gp, f"unary: store {var_name}")
            self.emitter.emitComment("<- unary op")

        elif kind == "Input (cin)":
            offset = self._get_tm_offset(node)
            var_name = getattr(node, "var_name", None) or getattr(node, "raw_value", "")
            self.emitter.emitRO("IN", ac, 0, 0, f"read integer value for {var_name}")
            self.emitter.emitRM("ST", ac, offset, gp, f"read: store value in {var_name}")

        elif kind in ("Output (cout)", "Multiple Output"):
            self._emit_output_items(node)

        elif kind == "Selection (if)":
            self.emitter.emitComment("-> if")
            cond_node = node.children[0] if len(node.children) > 0 else None
            then_node = node.children[1] if len(node.children) > 1 else None
            else_node = node.children[2] if len(node.children) > 2 else None

            self.gen_exp(cond_node)
            saved_loc1 = self.emitter.emitSkip(1)
            self.emitter.emitComment("if: jump to else belongs here")

            self.cGen(then_node)

            if else_node is not None:
                saved_loc2 = self.emitter.emitSkip(1)
                self.emitter.emitComment("if: jump to end belongs here")
                current_loc = self.emitter.emitSkip(0)
                self.emitter.emitBackup(saved_loc1)
                self.emitter.emitRM_Abs("JEQ", ac, current_loc, "if: jmp to else")
                self.emitter.emitRestore()

                self.cGen(else_node)
                current_loc = self.emitter.emitSkip(0)
                self.emitter.emitBackup(saved_loc2)
                self.emitter.emitRM_Abs("LDA", pc, current_loc, "jmp to end")
                self.emitter.emitRestore()
            else:
                current_loc = self.emitter.emitSkip(0)
                self.emitter.emitBackup(saved_loc1)
                self.emitter.emitRM_Abs("JEQ", ac, current_loc, "if: jmp to end")
                self.emitter.emitRestore()

            self.emitter.emitComment("<- if")

        elif kind == "Iteration (while)":
            self.emitter.emitComment("-> while")
            cond_node = node.children[0] if len(node.children) > 0 else None
            body_node = node.children[1] if len(node.children) > 1 else None

            start_loc = self.emitter.emitSkip(0)
            self.gen_exp(cond_node)
            saved_loc = self.emitter.emitSkip(1)
            self.emitter.emitComment("while: jump to end belongs here")

            self.cGen(body_node)
            self.emitter.emitRM_Abs("LDA", pc, start_loc, "while: jmp back to test")

            current_loc = self.emitter.emitSkip(0)
            self.emitter.emitBackup(saved_loc)
            self.emitter.emitRM_Abs("JEQ", ac, current_loc, "while: jmp to end")
            self.emitter.emitRestore()
            self.emitter.emitComment("<- while")

        elif kind == "Repetition (do-while)":
            self.emitter.emitComment("-> do-while")
            body_node = node.children[0] if len(node.children) > 0 else None
            cond_node = node.children[1] if len(node.children) > 1 else None

            start_loc = self.emitter.emitSkip(0)
            self.cGen(body_node)
            self.gen_exp(cond_node)
            self.emitter.emitRM_Abs("JNE", ac, start_loc, "do-while: jmp back to body if true")
            self.emitter.emitComment("<- do-while")

    def _emit_output_items(self, node):
        """Recursively emits cout output items; strings become comments only."""
        if not node:
            return

        kind = self._get_kind(node)
        if kind in ("Output (cout)", "Multiple Output"):
            for child in node.children:
                self._emit_output_items(child)
            return

        if kind == "String Literal":
            raw_val = getattr(node, "raw_value", None)
            if raw_val is None:
                raw_val = node.value
            self.emitter.emitComment(f"cout string: {raw_val}")
            return

        self.gen_exp(node)
        self.emitter.emitRO("OUT", self.emitter.ac, 0, 0, "write ac")

    def gen_exp(self, node):
        """Generates TM instructions for expressions in post-order, leaving result in ac."""
        if not node:
            return

        kind = self._get_kind(node)
        ac = self.emitter.ac
        ac1 = self.emitter.ac1
        gp = self.emitter.gp
        mp = self.emitter.mp
        pc = self.emitter.pc

        if kind == "Numeric Literal":
            raw_val = getattr(node, "raw_value", None)
            if raw_val is None:
                raw_val = node.value
            raw_str = str(raw_val)
            try:
                int_val = int(raw_str)
            except ValueError:
                int_val = int(float(raw_str))
            self.emitter.emitRM("LDC", ac, int_val, 0, f"load const {raw_str}")

        elif kind == "Boolean Literal":
            raw_val = getattr(node, "raw_value", None)
            if raw_val is None:
                raw_val = node.value
            int_val = 1 if str(raw_val).strip().lower() == "true" else 0
            self.emitter.emitRM("LDC", ac, int_val, 0, f"load bool {raw_val}")

        elif kind == "Identifier":
            offset = self._get_tm_offset(node)
            var_name = getattr(node, "var_name", None) or getattr(node, "raw_value", "")
            self.emitter.emitRM("LD", ac, offset, gp, f"load id {var_name}")

        elif kind == "Logical NOT":
            self.emitter.emitComment("-> not")
            if node.children:
                self.gen_exp(node.children[0])
            self.emitter.emitRM("JEQ", ac, 2, pc, "not: br if zero (becomes 1)")
            self.emitter.emitRM("LDC", ac, 0, 0, "not: false case")
            self.emitter.emitRM("LDA", pc, 1, pc, "not: unconditional jmp")
            self.emitter.emitRM("LDC", ac, 1, 0, "not: true case")
            self.emitter.emitComment("<- not")

        elif kind in self.BINARY_EXP_KINDS:
            if len(node.children) < 2:
                return

            self.emitter.emitComment("-> Op")
            # Evaluate left operand into ac and push onto temp stack (mp)
            self.gen_exp(node.children[0])
            self.emitter.emitRM("ST", ac, self.tmpOffset, mp, "op: push left")
            self.tmpOffset -= 1

            # Evaluate right operand into ac
            self.gen_exp(node.children[1])

            # Pop left operand into ac1
            self.tmpOffset += 1
            self.emitter.emitRM("LD", ac1, self.tmpOffset, mp, "op: load left")

            op = getattr(node, "op", None) or getattr(node, "raw_value", None) or node.value
            self._emit_binary_op(op)
            self.emitter.emitComment("<- Op")

    def _emit_binary_op(self, op: str):
        """Emits TM instructions for a binary operator with left in ac1 and right in ac."""
        ac = self.emitter.ac
        ac1 = self.emitter.ac1
        mp = self.emitter.mp
        pc = self.emitter.pc

        arith_map = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV",
        }
        if op in arith_map:
            self.emitter.emitRO(arith_map[op], ac, ac1, ac, f"op {op}")
            return

        if op == "%":
            self.emitter.emitRM("ST", ac1, self.tmpOffset, mp, "mod: save left operand")
            self.emitter.emitRO("DIV", ac1, ac1, ac, "mod: q = left / right")
            self.emitter.emitRO("MUL", ac1, ac1, ac, "mod: q * right")
            self.emitter.emitRM("LD", ac, self.tmpOffset, mp, "mod: reload left operand")
            self.emitter.emitRO("SUB", ac, ac, ac1, "mod: left - (q * right)")
            return

        if op == "^":
            self._emit_power_loop()
            return

        if op in self.RELATIONAL_JUMPS:
            self.emitter.emitRO("SUB", ac, ac1, ac, f"op {op}")
            self.emitter.emitRM(self.RELATIONAL_JUMPS[op], ac, 2, pc, "br if true")
            self.emitter.emitRM("LDC", ac, 0, 0, "false case")
            self.emitter.emitRM("LDA", pc, 1, pc, "unconditional jmp")
            self.emitter.emitRM("LDC", ac, 1, 0, "true case")
            return

        if op == "&&":
            self.emitter.emitRM("JEQ", ac1, 3, pc, "&&: false if left == 0")
            self.emitter.emitRM("JEQ", ac, 2, pc, "&&: false if right == 0")
            self.emitter.emitRM("LDC", ac, 1, 0, "&&: true case")
            self.emitter.emitRM("LDA", pc, 1, pc, "&&: unconditional jmp")
            self.emitter.emitRM("LDC", ac, 0, 0, "&&: false case")
            return

        if op == "||":
            self.emitter.emitRM("JNE", ac1, 3, pc, "||: true if left != 0")
            self.emitter.emitRM("JNE", ac, 2, pc, "||: true if right != 0")
            self.emitter.emitRM("LDC", ac, 0, 0, "||: false case")
            self.emitter.emitRM("LDA", pc, 1, pc, "||: unconditional jmp")
            self.emitter.emitRM("LDC", ac, 1, 0, "||: true case")

    def _emit_power_loop(self):
        """Emits an iterative multiplication loop for base (ac1) ^ exp (ac) into ac."""
        ac = self.emitter.ac
        ac1 = self.emitter.ac1
        mp = self.emitter.mp
        pc = self.emitter.pc

        slot_res = self.tmpOffset
        slot_base = self.tmpOffset - 1
        slot_exp = self.tmpOffset - 2

        self.emitter.emitRM("ST", ac1, slot_base, mp, "pow: save base")
        self.emitter.emitRM("ST", ac, slot_exp, mp, "pow: save exponent")
        self.emitter.emitRM("LDC", ac, 1, 0, "pow: init result = 1")
        self.emitter.emitRM("ST", ac, slot_res, mp, "pow: store result")

        loop_start = self.emitter.emitSkip(0)
        self.emitter.emitRM("LD", ac, slot_exp, mp, "pow: load exponent")
        jump_end = self.emitter.emitSkip(1)
        self.emitter.emitComment("pow: exit loop if exponent <= 0")

        self.emitter.emitRM("LD", ac, slot_res, mp, "pow: load result")
        self.emitter.emitRM("LD", ac1, slot_base, mp, "pow: load base")
        self.emitter.emitRO("MUL", ac, ac, ac1, "pow: result *= base")
        self.emitter.emitRM("ST", ac, slot_res, mp, "pow: update result")

        self.emitter.emitRM("LD", ac, slot_exp, mp, "pow: load exponent")
        self.emitter.emitRM("LDC", ac1, 1, 0, "pow: load 1")
        self.emitter.emitRO("SUB", ac, ac, ac1, "pow: exponent -= 1")
        self.emitter.emitRM("ST", ac, slot_exp, mp, "pow: store exponent")
        self.emitter.emitRM_Abs("LDA", pc, loop_start, "pow: loop back")

        loop_end = self.emitter.emitSkip(0)
        self.emitter.emitBackup(jump_end)
        self.emitter.emitRM_Abs("JLE", ac, loop_end, "pow: jmp to end if exp <= 0")
        self.emitter.emitRestore()

        self.emitter.emitRM("LD", ac, slot_res, mp, "pow: load final result")


def codeGen(ast_root, output_path=None) -> str:
    """Module-level entry point equivalent to codeGen(syntaxTree, codefile)."""
    generator = TMCodeGenerator()
    return generator.codeGen(ast_root, output_path)
