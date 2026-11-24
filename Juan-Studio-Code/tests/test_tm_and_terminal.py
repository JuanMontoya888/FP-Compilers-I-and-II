import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest

from compiler.pipeline import CompilerPipeline
from compiler.tm_simulator.tm_simulator import TMSimulator
from ide.components.ansi_parser import AnsiEscapeParser
from ide.components.interactive_terminal import InteractiveTerminal
from tests.conftest import PROGRAMS_DIR, load_compiler_cases, load_terminal_cases


TM_CASES = [
    (case, run_spec)
    for case in load_compiler_cases()
    for run_spec in case.get("tm_runs", [])
]
TERMINAL_CASES = load_terminal_cases()


@pytest.mark.parametrize(
    "case,run_spec",
    TM_CASES,
    ids=lambda item: item["id"] if "program" in item else item["name"],
)
def test_e2e_tm_simulation(case, run_spec, tmp_path):
    program_path = os.path.join(PROGRAMS_DIR, case["program"])
    pipeline = CompilerPipeline(project_root=str(tmp_path))
    result = pipeline.run(program_path, target_stage="full")

    assert result.success is True
    assert result.tm_code

    sim = TMSimulator()
    sim.load_code(result.tm_code)

    if run_spec.get("expect_step_limit_error"):
        with pytest.raises(RuntimeError, match="maximum step limit"):
            sim.run(max_steps=run_spec["max_steps"], quiet=True)
        return

    inputs_iter = iter(run_spec.get("inputs", []))
    outputs = sim.run(
        input_callback=lambda: next(inputs_iter),
        quiet=True,
        max_steps=run_spec.get("max_steps", TMSimulator.DEFAULT_MAX_STEPS),
    )

    assert outputs == run_spec["expected_outputs"]
    assert sim.last_status == run_spec["expected_status"]


@pytest.mark.parametrize("tcase", TERMINAL_CASES, ids=lambda c: c["id"])
def test_ansi_escape_parser(qt_app, tcase):
    parser = AnsiEscapeParser()
    chunks = parser.feed_text(tcase["raw_text"])

    combined_text = "".join(chunk[0] for chunk in chunks if not chunk[2])
    assert tcase["expected_text_contains"] in combined_text

    if tcase.get("expect_clear"):
        assert any(chunk[2] for chunk in chunks)

    if "expected_first_color" in tcase:
        styled_chunks = [c for c in chunks if c[0]]
        assert styled_chunks[0][1].foreground().color().name().lower() == tcase["expected_first_color"].lower()

    if tcase.get("expect_bold"):
        styled_chunks = [c for c in chunks if c[0]]
        assert styled_chunks[0][1].fontWeight() >= 700


def test_interactive_terminal_key_routing_and_protection(qt_app):
    term = InteractiveTerminal()
    prompt = b"PS C:\\workspace> "
    term.append_output_bytes(prompt)
    watermark = term.interactive_position
    assert watermark == len(prompt.decode("utf-8"))

    # Typing text and ensuring async output preserves user draft
    QTest.keyClicks(term, "echo test")
    assert term.get_current_input() == "echo test"

    term.append_output_bytes(b"\n[ASYNC LOG]\n")
    assert term.interactive_position > watermark
    assert term.get_current_input() == "echo test"

    # Smart Home moves strictly to interactive_position, never over prompt
    QTest.keyClick(term, Qt.Key.Key_Home)
    assert term.textCursor().position() == term.interactive_position

    # Backspace / Left blocked at interactive_position
    QTest.keyClick(term, Qt.Key.Key_Left)
    assert term.textCursor().position() == term.interactive_position
    QTest.keyClick(term, Qt.Key.Key_Backspace)
    assert term.get_current_input() == "echo test"

    # Submit first and second commands to populate history
    submitted = []
    term.command_submitted.connect(submitted.append)
    QTest.keyClick(term, Qt.Key.Key_Return)
    assert submitted == ["echo test"]

    term.append_output_bytes(prompt)
    QTest.keyClicks(term, "dir")
    QTest.keyClick(term, Qt.Key.Key_Return)
    assert submitted == ["echo test", "dir"]

    # Up/Down arrow history navigation
    term.append_output_bytes(prompt)
    QTest.keyClick(term, Qt.Key.Key_Up)
    assert term.get_current_input() == "dir"
    QTest.keyClick(term, Qt.Key.Key_Up)
    assert term.get_current_input() == "echo test"
    QTest.keyClick(term, Qt.Key.Key_Down)
    assert term.get_current_input() == "dir"
    QTest.keyClick(term, Qt.Key.Key_Down)
    assert term.get_current_input() == ""

    # Ctrl+C without selection emits interrupt_requested
    interrupted = []
    term.interrupt_requested.connect(lambda: interrupted.append(True))
    ctrl_c = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    term.keyPressEvent(ctrl_c)
    assert interrupted == [True]


def test_consecutive_compilation_workers_do_not_crash(qt_app):
    """
    Regression test for RuntimeError: Internal C++ object (CompilationWorker) already deleted.
    Simulates opening a file, running silent/explicit compilation stages back-to-back,
    and letting deleteLater run in the Qt event loop between runs.
    """
    from PySide6.QtCore import QEventLoop
    from ide.core.widget import Widget

    w = Widget()
    tm = w.terminal_manager

    def run_and_wait(trigger_fn):
        loop = QEventLoop()
        tm.compilation_completed.connect(lambda *_: loop.quit())
        trigger_fn()
        loop.exec()
        qt_app.processEvents()

    example_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "example1.jpp",
    )

    try:
        run_and_wait(lambda: tm.execute_silent_compilation(example_path))
        run_and_wait(lambda: tm.execute_lexical(example_path))
        assert tm.lexico_output.topLevelItemCount() > 1

        run_and_wait(lambda: tm.execute_syntactic(example_path))
        assert tm.sintactico_output.topLevelItemCount() >= 1

        run_and_wait(lambda: tm.execute_semantic(example_path))
        assert tm.semantico_output.topLevelItemCount() >= 1
        assert tm.tabla.topLevelItemCount() >= 1

        run_and_wait(lambda: tm.execute_intermediate(example_path))
        assert "HALT" in tm.tm_code_edit.toPlainText()
    finally:
        if tm.process.state() != tm.process.ProcessState.NotRunning:
            tm.process.kill()
            tm.process.waitForFinished(500)
        w.close()
