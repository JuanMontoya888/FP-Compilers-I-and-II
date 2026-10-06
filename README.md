# Compiler IDE - Lexical, Syntax, and Semantic Analysis Project

This project implements a high-performance modular compiler integrated into a custom Integrated Development Environment (IDE) built with **PySide6**. The system processes C/C++-like source code, transforming it from its lexical representation into a complex hierarchical structure, featuring lexical, syntax, and semantic analysis phases.

## Core Features

### Analysis Engine (Compiler)

* **Lexical Analyzer (DFA):** State-transition based engine for an efficient single-pass (O(N)) reading.
* **Syntax Analyzer (Parser):** Recursive descent (LL(1)) implementation for grammatical validation.
* **Semantic Analyzer:** Type checking and symbol table management.
* **AST Generation:** Construction of an Abstract Syntax Tree (AST) that organizes control structures, expressions, and declarations into a logical hierarchy.
* **Error Handling (Panic-Mode):** Defensive system that identifies errors, reports their exact location, and synchronizes the flow to continue parsing.

### Development Environment (IDE)

* **Clean and Decoupled Organization:** Professional architecture separating the compiler logic (`compiler/`) from the Graphical User Interface (`ide/`).
* **Output Console and Terminal:** Rich text formatting to identify real-time errors with asynchronous support.
* **Jump-to-Error:** Automatic navigation: clicking on an error in the terminal positions the editor cursor and highlights the exact location of the failure.
* **File Management (File Tree):** Visual file explorer in the sidebar to quickly navigate and open files.
* **Advanced Search:** Floating widget (VS Code style) integrated into the editor for Code Search and Replace without losing context.
* **Document Management:** Editor with dynamic syntax highlighting and file persistence.

## Project Structure

```text
Juan-Studio-Code/
├── compiler/                       # Internal compiler logic
│   ├── lexical_analyzer/           # Scanner (DFA) and Token definitions
│   ├── syntax_analyzer/            # Parser LL(1) and Abstract Syntax Tree (ASTNode)
│   └── semantic_analyzer/          # Symbol table and semantic validation
│
├── ide/                            # Integrated Development Environment logic (GUI)
│   ├── core/                       # UI Orchestrator (widget.py) and shortcuts
│   ├── managers/                   # Controllers (Editor, Terminal, File Tree)
│   ├── components/                 # Floating search, context menus, and syntax highlighter
│   ├── resources/                  # Stylesheets (.qss) and logos
│   └── icons/                      # SVG Icons (folders, files)
│
├── compiler_output/                # Outputs generated during compilation (tokens, tree.txt)
├── main.py                         # Unified entry point of the application
└── requirements.txt                # Project dependencies
```

## Processing Flow

1. **Lexical Analysis:** The scanner identifies lexemes and classifies them, discarding comments and detecting lexical errors.
2. **Syntax Analysis:** The parser consumes the token stream and validates grammatical rules (EBNF), recursively building the syntax tree.
3. **Semantic Analysis:** Verifies data type consistency and proper variable declarations.
4. **AST Construction:** Each grammatical rule generates linked nodes that represent the hierarchy of the program.
5. **Visualization:** The resulting tree is serialized into `compiler_output/tree.txt` for debugging and can be quickly viewed in the editor.

## Requirements and Installation

1. **Python 3.10 or higher** (required for `match-case` syntax).
2. **PySide6**:
```bash
pip install PySide6
```

## Usage

1. Run the IDE by starting the main entry point from the root:
```bash
python main.py
```
2. Write or open a source file with C/C++ syntax.
3. Use the analysis buttons on the sidebar or keyboard shortcuts (e.g., Ctrl+F to search).
4. **Results:** 
* The bottom tab displays tokens and analysis results.
* The errors tab allows direct navigation to the source code by clicking on them.
* The tree and other generated data are automatically saved in `compiler_output/`.

---

*Compilers I & II Project | Juan-Studio-Code*

