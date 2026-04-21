# CiCode Interpreter & VSCode Extension

A native Linux interpreter and VSCode debug extension for **AVEVA Plant SCADA CiCode** — allowing you to run, debug, and test CiCode scripts without needing the full Plant SCADA runtime.

---

## Why This Exists

AVEVA Plant SCADA uses a proprietary scripting language called **CiCode**. The official IDE is Windows-only and tightly coupled to the SCADA runtime. This project lets you:

- Write CiCode in VSCode with syntax highlighting
- Run CiCode functions directly from VSCode (▶ button or `Ctrl+Shift+B`)
- Debug with full breakpoints, watch panel, call stack, and step over/in/out (F5)
- Connect to a live SQL Server database (same connection as the SCADA runtime)
- Render GUI forms using tkinter that mirror Plant SCADA's `FormNew`/`FormRead` dialog system

---

## Project Structure

```
CiCode/
├── README.md                        # This file
├── ARCHITECTURE.md                  # Interpreter internals deep-dive
├── BUILTINS.md                      # Implemented CiCode builtin functions
├── DEBUGGING.md                     # How the DAP debug adapter works
├── FORMS.md                         # GUI form system documentation
├── SQL.md                           # SQL connection and CiCode SQLConnect usage
├── your_script.ci                   # Your CiCode source files go here (gitignored)
├── interpreter/                     # Python CiCode interpreter
│   ├── cicode.py                    # CLI entry point
│   ├── lexer.py                     # Tokeniser
│   ├── parser.py                    # Recursive-descent parser → AST
│   ├── ast_nodes.py                 # AST dataclass definitions
│   ├── interpreter.py               # Tree-walking evaluator
│   ├── debug_adapter.py             # DAP (Debug Adapter Protocol) server
│   ├── requirements.txt             # Python dependencies
│   └── builtins/                    # CiCode builtin implementations
│       ├── __init__.py
│       ├── sql_funcs.py             # SQLConnect, SQLSelect, SQLNext, etc.
│       ├── form_funcs.py            # FormNew, FormRead, FormButton, etc. (tkinter)
│       ├── string_funcs.py          # StrLeft, StrTrim, StrToInt, etc.
│       ├── math_funcs.py            # Abs, Int, Mod, etc.
│       ├── time_funcs.py            # TimeCurrent, TimeToStr, etc.
│       ├── file_funcs.py            # FileOpen, FileRead, FileWrite, etc.
│       ├── task_funcs.py            # TaskNew, TaskQuit, Sleep, etc.
│       ├── map_funcs.py             # AssocCreate, AssocGet, AssocSet, etc.
│       ├── misc_funcs.py            # Print, Trace, MsgBox, etc.
│       └── stub_funcs.py            # No-op stubs for unimplemented builtins
└── cicode-extension/                # VSCode extension source
    ├── package.json                 # Extension manifest (contributes, activates)
    ├── extension.js                 # Run/debug commands, function picker
    ├── language-configuration.json  # Bracket/comment config for cicode language
    └── syntaxes/
        └── cicode.tmLanguage.json   # TextMate grammar for syntax highlighting
```

---

## Quick Start

### 1. Install Python dependencies

```bash
pip3 install pymssql --break-system-packages
```

> `pyodbc` is used as a fallback but `pymssql` is the primary SQL backend because it handles older SQL Server versions (2008–2014) without TLS 1.2 enforcement.

### 2. Install the VSCode extension

The extension is already installed to `~/.vscode/extensions/cicode-1.0.0/`.

To reinstall from source after changes:
```bash
cp -r ~/Desktop/CiCode/cicode-extension/* ~/.vscode/extensions/cicode-1.0.0/
```
Then in VSCode: `Ctrl+Shift+P` → **Developer: Reload Window**

### 3. Run a CiCode function

- Open any `.ci` file in VSCode
- Click the **▶** button in the editor title bar, or press `Ctrl+Shift+B`
- A dropdown will show all `FUNCTION` names in the file — pick one
- The terminal runs the function and shows output; press **Enter** to close

### 4. Debug a CiCode function (F5)

- Click the gutter (left of line numbers) to set breakpoints
- Press **F5**
- Pick a function from the dropdown
- Execution halts at breakpoints; use the Debug panel for watch, call stack, step controls

---

## SQL Server Connection

The SQL Server connection details are stored in your `.ci` files via helper functions that return the server host, database name, and password. Update those functions with your own server details.

CiCode connection string format (parsed by `sql_funcs.py`):
```
DRIVER={SQL Server};SERVER=<host>;Database=<database>;Uid=<user>;Pwd=<password>;
```

`sql_funcs.py` converts this to `pymssql.connect(server=..., database=..., user=..., password=..., tds_version='7.0')`.

---

## CiCode Language Notes

- **Case-insensitive**: All identifiers are normalised to lowercase internally
- **Types**: INT, REAL, STRING, OBJECT, QUALITY, TIMESTAMP (all duck-typed in Python)
- **Arrays**: 0-indexed, declared as `INT arr[100];` or used dynamically
- **Error handling**: `IsError()` checks last error; no exceptions
- **Functions**: `FUNCTION`, `INT FUNCTION`, `STRING FUNCTION`, etc.
- **Return**: `RETURN value;`
- **Globals**: Variables declared outside functions are module-global
- **String concat**: `+` operator
- **Comments**: `(* ... *)` block, `//` line comment

---

## Known Limitations

- No `TaskNew` parallelism (tasks run sequentially as function calls)
- No `DspXxx` display/graphics functions (stubs only)
- No `IODevice` real-time tag reading (stubs only)
- `FormGetCurr` and some advanced form functions are stubbed
- Error codes partially implemented — main ones (0=OK, 259=EOF, 299=Cancel) are correct

---

## File Naming

- `.ci` — CiCode source files
- The interpreter loads **all** `.ci` files in the workspace root when running from VSCode, so functions defined in any file are visible to all others

---

## Reference Documentation

The full AVEVA Plant SCADA CiCode Reference (2026 edition) PDF and a plain-text extracted copy (`cicode_reference.txt`, 83,568 lines) are both in the project root alongside this README. The `.txt` is gitignored — keep it local for fast searching.

Key error codes from the reference:
| Code | Meaning |
|------|---------|
| 0    | Success / OK button pressed |
| 259  | End of data (SQL EOF) |
| 299  | Cancelled (Cancel button / Escape) |
