# Architecture — CiCode Interpreter

## Overview

The interpreter is a classic **tree-walking evaluator**:

```
Source text
    │
    ▼
Lexer (lexer.py)          → Token stream
    │
    ▼
Parser (parser.py)        → Abstract Syntax Tree (AST)
    │
    ▼
Interpreter (interpreter.py) → executes AST nodes directly
    │
    ├── builtins/         → Python implementations of CiCode built-in functions
    └── debug_adapter.py  → DAP server hooks into interpreter for F5 debugging
```

---

## Lexer (`lexer.py`)

- Hand-written tokeniser
- Produces `Token(type, value, line)` objects
- Token types: `NUMBER`, `STRING`, `IDENT`, `OP`, `KEYWORD`, `EOF`
- All identifiers are **lowercased** at lex time → case-insensitivity
- String literals use `""` delimiters (CiCode style), escape `""` as literal quote
- Comments stripped: `(* ... *)` and `// ...`

---

## Parser (`parser.py`)

- Recursive-descent, single-pass
- Produces AST nodes defined in `ast_nodes.py`
- Entry point: `Parser.parse()` → list of top-level declarations
- Key productions:
  - `parse_function()` → `FunctionDecl`
  - `parse_statement()` → `IfStmt`, `ForStmt`, `WhileStmt`, `AssignStmt`, `ReturnStmt`, `CallStmt`
  - `parse_expr()` → operator precedence via `parse_or` → `parse_and` → `parse_cmp` → `parse_add` → `parse_mul` → `parse_unary` → `parse_primary`
  - Array subscript and function calls parsed in `parse_primary`

---

## AST Nodes (`ast_nodes.py`)

All nodes are `@dataclass` with a `line: int` field for debug info.

Key nodes:
```python
FunctionDecl(name, params, return_type, body, line)
AssignStmt(target, index_expr, value, line)   # index_expr = None for scalar
IfStmt(condition, then_body, elif_clauses, else_body, line)
ForStmt(var, start, stop, step, body, line)
WhileStmt(condition, body, line)
ReturnStmt(value, line)
CallExpr(name, args, line)
BinOp(op, left, right, line)
UnaryOp(op, operand, line)
Subscript(target, index, line)
NumberLit(value, line)
StringLit(value, line)
Identifier(name, line)
```

---

## Interpreter (`interpreter.py`)

### Class: `Interpreter`

**State:**
- `self.globals: dict` — module-level variables across all loaded files
- `self.functions: dict` — all declared functions (name → `FunctionDecl`)
- `self._call_stack: list` — each entry is `[func_name, file_path, current_line]`
- `self.debug_hook` — callable or `None`; set by DAP adapter for debugging
- `self._last_error: int` — tracks last error code for `IsError()`

**Key methods:**
- `load_file(path)` — lex + parse + register functions + exec top-level statements
- `call_function(name, args)` — push frame, exec body, pop frame
- `_exec_stmt(stmt, scope)` — dispatches on stmt type; calls `debug_hook` before each statement
- `_eval_expr(expr, scope)` — evaluates expression, returns Python value
- `to_str(val)` / `to_int(val)` / `to_real(val)` — CiCode type coercions

**Variable resolution order:** local `scope` dict → `self.globals`

**Debug hook signature:**
```python
def debug_hook(file: str, line: int, local_scope: dict, module_scope: dict) -> None
```
Called before every statement execution. The DAP adapter sets this to check breakpoints and handle stepping.

**Call stack format:**
```python
[["FunctionName", "/path/to/file.ci", current_line_number], ...]
```
Used by the DAP adapter to populate the "Call Stack" panel in VSCode.

---

## Builtins Registration

Each `builtins/*.py` module exposes a `register(interp)` function that adds entries to `interp.globals`:

```python
def register(interp):
    interp.globals['strleft'] = lambda s, n: ...
    interp.globals['strtrim'] = lambda s: ...
```

`interpreter.py` calls all `register()` functions at init time.

---

## Error Handling Model

CiCode uses **return-code error handling**, not exceptions. The interpreter mirrors this:
- Functions return values normally
- On error, `interp._last_error` is set and the function returns `0` / `""`
- `IsError()` builtin returns `interp._last_error`
- `ErrMsg(code)` returns a string for an error code

---

## Debug Adapter (`debug_adapter.py`)

See `DEBUGGING.md` for full details.

---

## Adding New Builtins

1. Add a new file `interpreter/builtins/my_funcs.py`
2. Implement functions and a `register(interp)` function
3. Import and call `register` in `interpreter.py`'s `__init__`

Example:
```python
# builtins/my_funcs.py
def register(interp):
    def MyFunc(arg):
        return str(arg).upper()
    interp.globals['myfunc'] = MyFunc
```
