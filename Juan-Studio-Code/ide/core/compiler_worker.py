from typing import Optional
from PySide6.QtCore import QThread, Signal

from compiler.pipeline import CompilationResult, CompilerDiagnostic, CompilerPipeline


class CompilationWorker(QThread):
    """
    Worker QThread that runs CompilerPipeline off the main Qt UI event loop.
    Emits (CompilationResult, target_stage, silent) when finished.
    """

    compilation_finished = Signal(object, str, bool)

    def __init__(
        self,
        source_code_or_path: Optional[str],
        fallback_text: str = "",
        target_stage: str = "full",
        silent: bool = False,
        run_after: bool = False,
        project_root: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.source_code_or_path = source_code_or_path
        self.fallback_text = fallback_text
        self.target_stage = target_stage
        self.silent = silent
        self.run_after = run_after
        self.project_root = project_root
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        try:
            pipeline = CompilerPipeline(project_root=self.project_root)
            result = pipeline.run(
                self.source_code_or_path,
                fallback_text=self.fallback_text,
                target_stage=self.target_stage,
            )
        except Exception as exc:
            result = CompilationResult(
                success=False,
                diagnostics=[
                    CompilerDiagnostic(
                        phase="General",
                        message=f"Internal Compiler Error: {exc}",
                        line="?",
                        col="?",
                    )
                ],
            )

        if not self._cancelled:
            self.compilation_finished.emit(result, self.target_stage, self.silent)
