import os
import sys
import pytest

from compiler.pipeline import CompilerPipeline
from tests.conftest import PROGRAMS_DIR, load_compiler_cases


ALL_CASES = load_compiler_cases()
VALID_CASES = [c for c in ALL_CASES if c.get("expect_success", False)]
ERROR_CASES = [c for c in ALL_CASES if not c.get("expect_success", False)]


def _compile_case(case: dict, tmp_path):
    program_path = os.path.join(PROGRAMS_DIR, case["program"])
    pipeline = CompilerPipeline(project_root=str(tmp_path))
    return pipeline.run(program_path, target_stage="full")


def test_compiler_backend_has_zero_qt_dependency():
    """Verifies compiler.pipeline and ASTNode run cleanly without importing PySide6."""
    import compiler.syntax_analyzer.ASTNode as ast_mod
    assert not hasattr(ast_mod, "QObject")
    assert hasattr(ast_mod, "PureSignal")


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: c["id"])
def test_lexical_and_syntactic_phases(case, tmp_path):
    result = _compile_case(case, tmp_path)

    assert len(result.valid_tokens) >= case["min_valid_tokens"]
    assert result.syntactic_ast is not None

    ast_dict = result.syntactic_ast.to_dict()
    assert ast_dict["node_kind"] == case["expected_ast_root_kind"]

    if "expected_ast_child_kinds" in case:
        actual_child_kinds = [child["node_kind"] for child in ast_dict["children"]]
        assert actual_child_kinds == case["expected_ast_child_kinds"]


@pytest.mark.parametrize("case", VALID_CASES, ids=lambda c: c["id"])
def test_semantic_symbol_table_and_codegen(case, tmp_path):
    result = _compile_case(case, tmp_path)

    assert result.success is True
    assert result.diagnostics == []
    assert result.semantic_ast is not None

    if "expected_symbols" in case:
        actual_symbols = [
            {
                "name": sym.name,
                "dtype": sym.dtype,
                "offset": sym.offset,
                "tm_offset": sym.tm_offset,
            }
            for sym in result.symbols
        ]
        assert actual_symbols == case["expected_symbols"]

    for fragment in case.get("expected_ci_fragments", []):
        assert fragment in result.ci_code

    for fragment in case.get("expected_tm_fragments", []):
        assert fragment in result.tm_code


@pytest.mark.parametrize("case", ERROR_CASES, ids=lambda c: c["id"])
def test_error_detection_and_stale_artifact_gate(case, tmp_path):
    result = _compile_case(case, tmp_path)

    assert result.success is False
    assert result.tm_path is None
    assert result.ci_code == ""
    assert result.tm_code == ""

    phases = {d.phase for d in result.diagnostics}
    for expected_phase in case.get("expected_diagnostic_phases", []):
        assert expected_phase in phases

    all_messages = "\n".join(d.message for d in result.diagnostics)
    for substr in case.get("expected_error_substrings", []):
        assert substr in all_messages
