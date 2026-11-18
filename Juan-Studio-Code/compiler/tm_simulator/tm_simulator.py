import os
import re
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional


class StepResult:
    """Execution status codes matching Louden's tm.c STEPRESULT enum."""

    OKAY = "srOKAY"
    HALT = "srHALT"
    IMEM_ERR = "srIMEM_ERR"
    DMEM_ERR = "srDMEM_ERR"
    ZERODIVIDE = "srZERODIVIDE"


@dataclass
class Instruction:
    """Single instruction stored in TM instruction memory (iMem)."""

    iop: str = "HALT"
    iarg1: int = 0
    iarg2: int = 0
    iarg3: int = 0


class TMSimulator:
    """
    Python port of Kenneth C. Louden's Tiny Machine (TM) simulator (tm.c),
    configured for direct automatic execution (Go mode) for IDE integration.
    """

    IADDR_SIZE = 1024
    DADDR_SIZE = 1024
    NO_REGS = 8
    PC_REG = 7
    DEFAULT_MAX_STEPS = 500_000

    RO_OPS = frozenset({"HALT", "IN", "OUT", "ADD", "SUB", "MUL", "DIV"})
    RM_OPS = frozenset({"LD", "ST"})
    RA_OPS = frozenset({"LDA", "LDC", "JLT", "JLE", "JGT", "JGE", "JEQ", "JNE"})
    ALL_OPS = RO_OPS | RM_OPS | RA_OPS

    _LINE_PATTERN = re.compile(
        r"^\s*(\d+)\s*:\s*([A-Za-z]+)\s+(-?\d+)\s*,\s*(-?\d+)\s*(?:\(\s*(-?\d+)\s*\)|,\s*(-?\d+))?"
    )

    def __init__(self):
        self.iMem: List[Instruction] = []
        self.dMem: List[int] = []
        self.reg: List[int] = []
        self.outputs: List[int] = []
        self.last_status: str = StepResult.OKAY
        self.step_count: int = 0
        self.reset()

    def reset(self):
        """Resets instruction memory, data memory, registers, and execution counters."""
        self.iMem = [Instruction() for _ in range(self.IADDR_SIZE)]
        self.dMem = [0] * self.DADDR_SIZE
        self.dMem[0] = self.DADDR_SIZE - 1
        self.reg = [0] * self.NO_REGS
        self.outputs = []
        self.last_status = StepResult.OKAY
        self.step_count = 0

    def load_code(self, tm_text: str):
        """Parses TM assembly text and loads instructions into iMem."""
        self.reset()

        for line_no, raw_line in enumerate(tm_text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("*"):
                continue

            match = self._LINE_PATTERN.match(stripped)
            if not match:
                raise ValueError(f"Syntax error in TM file at line {line_no}: {raw_line}")

            loc = int(match.group(1))
            op = match.group(2).upper()
            r = int(match.group(3))
            arg2 = int(match.group(4))

            if match.group(5) is not None:
                arg3 = int(match.group(5))
            elif match.group(6) is not None:
                arg3 = int(match.group(6))
            else:
                raise ValueError(f"Missing third operand in TM file at line {line_no}: {raw_line}")

            if op not in self.ALL_OPS:
                raise ValueError(f"Illegal opcode '{op}' at line {line_no}")
            if not (0 <= loc < self.IADDR_SIZE):
                raise ValueError(f"Instruction location {loc} out of bounds [0, {self.IADDR_SIZE - 1}] at line {line_no}")
            if not (0 <= r < self.NO_REGS):
                raise ValueError(f"Illegal register '{r}' at line {line_no}")

            if op in self.RO_OPS:
                if not (0 <= arg2 < self.NO_REGS and 0 <= arg3 < self.NO_REGS):
                    raise ValueError(f"Illegal RO register operand at line {line_no}: {raw_line}")
            else:
                if not (0 <= arg3 < self.NO_REGS):
                    raise ValueError(f"Illegal base register '{arg3}' at line {line_no}")

            self.iMem[loc] = Instruction(iop=op, iarg1=r, iarg2=arg2, iarg3=arg3)

    def load_file(self, file_path: str):
        """Loads TM instructions from a .tm file on disk."""
        with open(file_path, "r", encoding="utf-8") as f:
            self.load_code(f.read())

    def _read_input_value(self, input_callback: Optional[Callable[[], int]] = None) -> int:
        """Reads an integer input for the IN instruction via callback or stdin."""
        if input_callback is not None:
            val = input_callback()
            try:
                return int(val)
            except (TypeError, ValueError):
                return int(float(val))

        while True:
            print("Enter value for IN instruction: ", end="", flush=True)
            raw_line = sys.stdin.readline()
            if raw_line == "":
                raise EOFError("End of input reached while waiting for IN instruction.")

            cleaned = raw_line.strip()
            # Echo input when attached to a non-TTY pipe (e.g. Qt QProcess terminal)
            if not sys.stdin.isatty():
                print(cleaned, flush=True)

            try:
                return int(cleaned)
            except ValueError:
                try:
                    return int(float(cleaned))
                except ValueError:
                    print(f"Illegal integer value '{cleaned}', please try again.", flush=True)

    def step_tm(
        self,
        input_callback: Optional[Callable[[], int]] = None,
        output_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        """Executes one fetch-decode-execute cycle of the Tiny Machine."""
        pc = self.reg[self.PC_REG]
        if not (0 <= pc < self.IADDR_SIZE):
            return StepResult.IMEM_ERR

        instr = self.iMem[pc]
        self.reg[self.PC_REG] = pc + 1

        op = instr.iop
        r = instr.iarg1
        s = instr.iarg2
        t = instr.iarg3

        m = 0
        if op in self.RM_OPS or op in self.RA_OPS:
            m = s + self.reg[t]
            if op in self.RM_OPS and not (0 <= m < self.DADDR_SIZE):
                return StepResult.DMEM_ERR

        if op == "HALT":
            return StepResult.HALT

        if op == "IN":
            self.reg[r] = self._read_input_value(input_callback)
        elif op == "OUT":
            val = self.reg[r]
            self.outputs.append(val)
            if output_callback is not None:
                output_callback(val)
            else:
                print(f"OUT instruction prints: {val}", flush=True)
        elif op == "ADD":
            self.reg[r] = self.reg[s] + self.reg[t]
        elif op == "SUB":
            self.reg[r] = self.reg[s] - self.reg[t]
        elif op == "MUL":
            self.reg[r] = self.reg[s] * self.reg[t]
        elif op == "DIV":
            divisor = self.reg[t]
            if divisor == 0:
                return StepResult.ZERODIVIDE
            dividend = self.reg[s]
            quotient = abs(dividend) // abs(divisor)
            self.reg[r] = -quotient if (dividend < 0) ^ (divisor < 0) else quotient
        elif op == "LD":
            self.reg[r] = self.dMem[m]
        elif op == "ST":
            self.dMem[m] = self.reg[r]
        elif op == "LDA":
            self.reg[r] = m
        elif op == "LDC":
            self.reg[r] = s
        elif op == "JLT":
            if self.reg[r] < 0:
                self.reg[self.PC_REG] = m
        elif op == "JLE":
            if self.reg[r] <= 0:
                self.reg[self.PC_REG] = m
        elif op == "JGT":
            if self.reg[r] > 0:
                self.reg[self.PC_REG] = m
        elif op == "JGE":
            if self.reg[r] >= 0:
                self.reg[self.PC_REG] = m
        elif op == "JEQ":
            if self.reg[r] == 0:
                self.reg[self.PC_REG] = m
        elif op == "JNE":
            if self.reg[r] != 0:
                self.reg[self.PC_REG] = m

        return StepResult.OKAY

    def run(
        self,
        input_callback: Optional[Callable[[], int]] = None,
        output_callback: Optional[Callable[[int], None]] = None,
        quiet: bool = False,
        max_steps: Optional[int] = None,
    ) -> List[int]:
        """
        Runs the loaded TM program continuously until HALT or runtime error.
        Returns the list of integer values emitted by OUT instructions.
        """
        self.outputs = []
        self.step_count = 0
        status = StepResult.OKAY

        while status == StepResult.OKAY:
            if max_steps is not None and self.step_count >= max_steps:
                raise RuntimeError(f"TM execution exceeded maximum step limit ({max_steps}).")
            status = self.step_tm(input_callback=input_callback, output_callback=output_callback)
            self.step_count += 1

        self.last_status = status

        if not quiet:
            if status == StepResult.HALT:
                print(f"HALT: Execution finished cleanly ({self.step_count} steps).", flush=True)
            elif status == StepResult.ZERODIVIDE:
                print(f"TM Runtime Error: Division by zero (PC={self.reg[self.PC_REG] - 1}).", flush=True)
            elif status == StepResult.DMEM_ERR:
                print(f"TM Runtime Error: Data memory address out of bounds (PC={self.reg[self.PC_REG] - 1}).", flush=True)
            elif status == StepResult.IMEM_ERR:
                print(f"TM Runtime Error: Instruction memory address out of bounds (PC={self.reg[self.PC_REG]}).", flush=True)

        return self.outputs


def run_tm_file(
    file_path: str,
    input_callback: Optional[Callable[[], int]] = None,
    output_callback: Optional[Callable[[int], None]] = None,
    quiet: bool = False,
    max_steps: Optional[int] = TMSimulator.DEFAULT_MAX_STEPS,
) -> List[int]:
    """Convenience helper to load and execute a .tm file directly."""
    simulator = TMSimulator()
    simulator.load_file(file_path)
    return simulator.run(
        input_callback=input_callback,
        output_callback=output_callback,
        quiet=quiet,
        max_steps=max_steps,
    )


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for executing a .tm program in interactive Go mode."""
    args = sys.argv[1:] if argv is None else argv
    quiet = False
    max_steps: Optional[int] = TMSimulator.DEFAULT_MAX_STEPS
    file_args = []

    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg in ("-q", "--quiet"):
            quiet = True
        elif arg.startswith("--max-steps="):
            raw_val = arg.split("=", 1)[1].strip()
            try:
                parsed = int(raw_val)
            except ValueError:
                print(f"Error: Invalid --max-steps value '{raw_val}'.", file=sys.stderr, flush=True)
                return 1
            max_steps = None if parsed <= 0 else parsed
        elif arg == "--max-steps":
            if idx + 1 >= len(args):
                print("Error: --max-steps requires an integer argument.", file=sys.stderr, flush=True)
                return 1
            idx += 1
            try:
                parsed = int(args[idx])
            except ValueError:
                print(f"Error: Invalid --max-steps value '{args[idx]}'.", file=sys.stderr, flush=True)
                return 1
            max_steps = None if parsed <= 0 else parsed
        else:
            file_args.append(arg)
        idx += 1

    if not file_args:
        print(
            "Usage: python -u -m compiler.tm_simulator.tm_simulator <program.tm> [--quiet] [--max-steps N]",
            file=sys.stderr,
            flush=True,
        )
        return 1

    file_path = file_args[0]
    if not os.path.exists(file_path):
        print(f"Error: TM file not found: {file_path}", file=sys.stderr, flush=True)
        return 1

    if not quiet:
        print(f"=== Tiny Machine Simulator ({os.path.basename(file_path)}) ===", flush=True)

    try:
        simulator = TMSimulator()
        simulator.load_file(file_path)
        simulator.run(quiet=quiet, max_steps=max_steps)
        return 0 if simulator.last_status == StepResult.HALT else 1
    except EOFError as exc:
        print(f"\nExecution stopped: {exc}", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.", file=sys.stderr, flush=True)
        return 130
    except Exception as exc:
        print(f"TM Simulator Error: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
