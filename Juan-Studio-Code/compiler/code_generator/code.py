class TMCodeEmitter:
    """
    Code emitting utilities for the Tiny Machine (TM) architecture.
    Direct Python adaptation of Louden's code.h and code.c.
    """

    # Register conventions
    ac = 0   # Primary accumulator
    ac1 = 1  # Secondary accumulator
    gp = 5   # Global pointer (symbol table base in dMem)
    mp = 6   # Memory pointer (temporary stack top in dMem)
    pc = 7   # Program counter

    def __init__(self, trace_code: bool = True):
        self.trace_code = trace_code
        self.emitLoc = 0
        self.highEmitLoc = 0
        self.lines = []
        self._slot_indices = {}

    def reset(self):
        """Resets instruction location counters and output buffer."""
        self.emitLoc = 0
        self.highEmitLoc = 0
        self.lines = []
        self._slot_indices = {}

    def emitComment(self, c: str):
        """Emits a TM comment line when trace_code is enabled."""
        if self.trace_code:
            self.lines.append(f"* {c}")

    def _write_instruction(self, line: str):
        """Writes an instruction at emitLoc, patching reserved slots in place."""
        if self.emitLoc in self._slot_indices:
            self.lines[self._slot_indices[self.emitLoc]] = line
        else:
            self._slot_indices[self.emitLoc] = len(self.lines)
            self.lines.append(line)

        self.emitLoc += 1
        if self.highEmitLoc < self.emitLoc:
            self.highEmitLoc = self.emitLoc

    def emitRO(self, op: str, r: int, s: int, t: int, c: str = ""):
        """Emits a register-only TM instruction: loc: OP r,s,t * c"""
        comment = f"\t* {c}" if (self.trace_code and c) else ""
        line = f"{self.emitLoc:3d}:  {op:5s}  {r},{s},{t}{comment}"
        self._write_instruction(line)

    def emitRM(self, op: str, r: int, d: int, s: int, c: str = ""):
        """Emits a register-to-memory TM instruction: loc: OP r,d(s) * c"""
        comment = f"\t* {c}" if (self.trace_code and c) else ""
        line = f"{self.emitLoc:3d}:  {op:5s}  {r},{d}({s}){comment}"
        self._write_instruction(line)

    def emitSkip(self, howMany: int) -> int:
        """Skips howMany instruction locations for later backpatching."""
        i = self.emitLoc
        for offset in range(howMany):
            loc = self.emitLoc + offset
            if loc not in self._slot_indices:
                self._slot_indices[loc] = len(self.lines)
                self.lines.append(None)

        self.emitLoc += howMany
        if self.highEmitLoc < self.emitLoc:
            self.highEmitLoc = self.emitLoc
        return i

    def emitBackup(self, loc: int):
        """Backs up emitLoc to a previously skipped instruction location."""
        if loc > self.highEmitLoc:
            self.emitComment("BUG in emitBackup")
        self.emitLoc = loc

    def emitRestore(self):
        """Restores emitLoc to the highest emitted instruction location."""
        self.emitLoc = self.highEmitLoc

    def emitRM_Abs(self, op: str, r: int, a: int, c: str = ""):
        """Converts an absolute code address 'a' to a PC-relative offset."""
        self.emitRM(op, r, a - (self.emitLoc + 1), self.pc, c)

    def get_code(self) -> str:
        """Returns the assembled TM program text."""
        valid_lines = [line for line in self.lines if line is not None]
        if not valid_lines:
            return ""
        return "\n".join(valid_lines) + "\n"
