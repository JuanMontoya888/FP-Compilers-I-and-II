import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from compiler.lexical_analyzer.SCAN import SCANNER
from compiler.syntax_analyzer.analizador_sintactico import Parser
from compiler.syntax_analyzer.ASTNode import ASTNode, ParserSignals
from compiler.semantic_analyzer.semantic_analyzer import SemanticAnalyzer
from compiler.code_generator import codeGen, generar_codigo_intermedio


@dataclass
class CompilerDiagnostic:
    """Structured representation of a Lexical, Syntax, Semantic, or General error."""

    phase: str          # "Lexical" | "Syntax" | "Semantic" | "General"
    message: str        # Full human-readable message
    line: Any = "?"
    col: Any = "?"

    def to_dict(self) -> dict:
        return {
            "type": self.phase,
            "msg": self.message,
            "line": self.line,
            "col": self.col,
        }


@dataclass
class CompilationResult:
    """
    Data Transfer Object containing all outputs of a compilation run.
    Safe to pass across threads (QThread -> Main UI Thread).
    """

    success: bool = False
    source_path: Optional[str] = None
    source_code: str = ""
    all_tokens: List[Tuple] = field(default_factory=list)
    valid_tokens: List[Tuple] = field(default_factory=list)
    syntactic_ast: Optional[ASTNode] = None
    semantic_ast: Optional[ASTNode] = None
    symbols: List[Any] = field(default_factory=list)
    diagnostics: List[CompilerDiagnostic] = field(default_factory=list)
    syntax_error_strings: List[str] = field(default_factory=list)
    semantic_error_strings: List[str] = field(default_factory=list)
    ci_code: str = ""
    tm_code: str = ""
    ci_path: Optional[str] = None
    tm_path: Optional[str] = None

    @property
    def errors_as_dicts(self) -> List[dict]:
        return [d.to_dict() for d in self.diagnostics]


class CompilerPipeline:
    """
    Pure-Python Facade that orchestrates the compiler stages without any UI coupling.
    Can execute up to a specific stage ('lexical', 'syntactic', 'semantic', 'full').
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(curr_dir)
        self.project_root = project_root
        self.output_dir = os.path.join(self.project_root, "compiler_output")
        os.makedirs(self.output_dir, exist_ok=True)

    def resolve_source(
        self,
        source_code_or_path: Optional[str],
        fallback_text: str = "",
    ) -> Tuple[Optional[str], str]:
        """Resolves a valid .jpp file path on disk and its UTF-8/Latin-1 source text."""
        file_path: Optional[str] = None
        source_code: str = ""

        if source_code_or_path and os.path.isfile(source_code_or_path):
            file_path = source_code_or_path
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    source_code = f.read()
            except Exception:
                source_code = fallback_text
        elif source_code_or_path:
            source_code = str(source_code_or_path)
        else:
            source_code = fallback_text

        if not file_path and source_code:
            buffer_path = os.path.join(self.output_dir, "_active_buffer.jpp")
            with open(buffer_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            file_path = buffer_path

        return file_path, source_code

    def clear_stale_artifacts(self) -> None:
        """Removes stale .tm and .ci files so invalid builds cannot be executed."""
        for fname in ("programa.tm", "intermedio.ci"):
            fpath = os.path.join(self.output_dir, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def run(
        self,
        source_code_or_path: Optional[str],
        fallback_text: str = "",
        target_stage: str = "full",
    ) -> CompilationResult:
        """
        Executes the compilation pipeline up to `target_stage`:
        - 'lexical': Stage 1 only
        - 'syntactic': Stages 1 -> 2
        - 'semantic': Stages 1 -> 2 -> 3
        - 'full': Stages 1 -> 2 -> 3 -> 4 (.ci & .tm generation)
        """
        result = CompilationResult()
        file_path, source_code = self.resolve_source(source_code_or_path, fallback_text)
        result.source_path = file_path
        result.source_code = source_code

        if not file_path or not source_code.strip():
            result.diagnostics.append(
                CompilerDiagnostic(
                    phase="General",
                    message="Compilation Error: No source code found. Open or write a .jpp file first.",
                    line="?",
                    col="?",
                )
            )
            self.clear_stale_artifacts()
            return result

        # -----------------------------------------------------------------
        # STAGE 1: LEXICAL ANALYSIS
        # -----------------------------------------------------------------
        scanner = SCANNER(file_path)
        scanner.get_token()
        result.all_tokens = list(scanner.list_tokens)

        for t in result.all_tokens:
            token_type = t[0]
            type_name = token_type.name if hasattr(token_type, "name") else str(token_type)
            line = t[2] if len(t) > 2 else "?"
            col = t[3] if len(t) > 3 else "?"

            if type_name == "ERROR":
                result.diagnostics.append(
                    CompilerDiagnostic(
                        phase="Lexical",
                        message=f"Lexical Error: Unexpected Token ('{t[1]}')",
                        line=line,
                        col=col,
                    )
                )
            elif type_name not in ("COMMENT_LINE", "COMMENT_BLOCK"):
                result.valid_tokens.append(t)

        if target_stage == "lexical":
            result.success = len(result.diagnostics) == 0
            return result

        # -----------------------------------------------------------------
        # STAGE 2: SYNTACTIC ANALYSIS
        # -----------------------------------------------------------------
        signals = ParserSignals()

        def on_syntax_error(msg: str, line: int, col: int) -> None:
            formatted = f"Syntax Error: {msg}"
            result.syntax_error_strings.append(f"{formatted} (Ln {line}, Col {col})")
            result.diagnostics.append(
                CompilerDiagnostic(phase="Syntax", message=formatted, line=line, col=col)
            )

        signals.error_signal.connect(on_syntax_error)
        parser = Parser(result.all_tokens, signals=signals)
        ast_root = parser.parse()
        result.syntactic_ast = ast_root

        if ast_root and getattr(ast_root, "has_error", False) and not result.syntax_error_strings:
            msg = getattr(ast_root, "error_message", "Syntax Error")
            result.syntax_error_strings.append(msg)
            result.diagnostics.append(
                CompilerDiagnostic(
                    phase="Syntax",
                    message=msg,
                    line=getattr(ast_root, "line", "?"),
                    col=getattr(ast_root, "col", "?"),
                )
            )

        if target_stage == "syntactic":
            result.success = len(result.diagnostics) == 0 and ast_root is not None
            return result

        # -----------------------------------------------------------------
        # STAGE 3: SEMANTIC ANALYSIS & SYMBOL TABLE
        # -----------------------------------------------------------------
        if ast_root is not None:
            analyzer = SemanticAnalyzer()
            annotated_ast, sem_errors = analyzer.analyze(ast_root)
            result.semantic_ast = annotated_ast
            result.symbols = list(analyzer.sym_table.all_symbols)

            for err in sem_errors:
                msg = f"Semantic Error: {err['msg']}"
                line = err.get("line", "?")
                col = err.get("col", "?")
                result.semantic_error_strings.append(f"{msg} (Ln {line}, Col {col})")
                result.diagnostics.append(
                    CompilerDiagnostic(phase="Semantic", message=msg, line=line, col=col)
                )

        if target_stage == "semantic":
            result.success = len(result.diagnostics) == 0 and result.semantic_ast is not None
            return result

        # -----------------------------------------------------------------
        # STAGE 4: INTERMEDIATE (.ci) & TARGET (.tm) CODE GENERATION
        # -----------------------------------------------------------------
        if result.diagnostics or result.semantic_ast is None:
            self.clear_stale_artifacts()
            result.success = False
            return result

        ci_path = os.path.join(self.output_dir, "intermedio.ci")
        tm_path = os.path.join(self.output_dir, "programa.tm")

        result.ci_code = generar_codigo_intermedio(result.semantic_ast, ci_path)
        result.tm_code = codeGen(result.semantic_ast, tm_path)
        result.ci_path = ci_path
        result.tm_path = tm_path
        result.success = True
        return result
