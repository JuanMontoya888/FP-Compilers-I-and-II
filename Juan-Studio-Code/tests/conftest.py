import json
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
PROGRAMS_DIR = os.path.join(FIXTURES_DIR, "programs")


def load_compiler_cases():
    path = os.path.join(FIXTURES_DIR, "compiler_cases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_terminal_cases():
    path = os.path.join(FIXTURES_DIR, "terminal_cases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
