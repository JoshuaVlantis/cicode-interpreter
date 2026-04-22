# CiCode Interpreter & VSCode Extension

> A full-featured VSCode development environment for **AVEVA Plant SCADA CiCode** — run, debug, and test CiCode scripts without needing the Plant SCADA runtime, plus rich IntelliSense, offline documentation for all 1,159 built-in functions, and a Python-powered interpreter with SQL, forms, and file I/O.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Extension Commands](#extension-commands)
- [Extension Settings](#extension-settings)
- [IntelliSense & Language Features](#intellisense--language-features)
- [Running & Debugging](#running--debugging)
- [Offline Help & Function Reference](#offline-help--function-reference)
- [Interpreter — Implemented Built-ins](#interpreter--implemented-built-ins)
- [CiCode Language Reference](#cicode-language-reference)
- [SQL Server Connection](#sql-server-connection)
- [GUI Forms](#gui-forms)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Further Documentation](#further-documentation)

---

## Features

### Editor & IntelliSense
| Feature | Description |
|---------|-------------|
| **Syntax Highlighting** | Full TextMate grammar for `.ci` files — keywords, types, strings, comments, operators |
| **Auto-complete** | IntelliSense for all 1,159 AVEVA built-in functions + your own user functions |
| **Hover Docs** | Hover over any function to see its signature, parameters, return type, and description |
| **Signature Help** | Parameter hints as you type function calls |
| **Go to Definition** | `F12` / right-click → Go to Definition for user-defined functions |
| **Find All References** | See every call site of a function across all `.ci` files |
| **Code Lens** | Reference counts shown above each function definition |
| **Diagnostics** | Errors for undefined functions, duplicate definitions, undeclared variables |
| **Lint Warnings** | Mixed indent, missing semicolons, keyword casing, magic numbers, deep nesting |
| **Code Formatter** | Format document with consistent indentation and blank-line collapsing |
| **Doc Skeleton** | Auto-generate a documentation comment block for any function (`Ctrl+Alt+D`) |
| **CiCode Explorer** | Side bar tree view showing all functions across workspace files |

### Running & Debugging
| Feature | Description |
|---------|-------------|
| **Run Function** | Pick and run any function from the current file via quick-pick dropdown |
| **Run (All Files)** | Same as above but loads all `.ci` files in the workspace |
| **Auto-save on Run** | File is saved automatically before running — no manual save needed |
| **F5 Debug** | Full DAP debug session — breakpoints, step over/in/out, call stack, watch |
| **Function Picker on F5** | Prompts for which function to debug every time — no config needed |
| **Variable Inspection** | Inspect local variables in the Debug sidebar during a debug session |

### Help & Reference
| Feature | Description |
|---------|-------------|
| **Offline Hover Help** | All 1,159 built-in functions documented offline (no AVEVA install needed) |
| **Function Reference Panel** | Searchable panel (`Ctrl+Alt+R`) listing all 1,159 built-ins with full docs |
| **Accurate Return Types** | Return types inferred from the AVEVA CiCode 2026 PDF for all functions |
| **AVEVA Help Integration** | If AVEVA Plant SCADA is installed, links open the official HTML help |

---

## Requirements

- **VSCode** 1.80 or later
- **Python 3.8+** (for the interpreter / debug adapter)
- **pip packages** (for SQL support):
  ```bash
  pip3 install pymssql
  ```
- AVEVA Plant SCADA is **not required** — all 1,159 built-in function docs are bundled offline

---

## Installation

### Option A — Install the VSIX (recommended)

1. Download the latest `.vsix` from the [Releases](../../releases) page (or from this repo root)
2. In VSCode: `Ctrl+Shift+P` → **Extensions: Install from VSIX...**
3. Select the downloaded `.vsix` file
4. Reload VSCode when prompted

### Option B — Build from source

```bash
git clone https://github.com/JoshuaVlantis/cicode-interpreter.git
cd cicode-interpreter/cicode-extension
npm install
npm run build
npx @vscode/vsce package --no-dependencies
code --install-extension cicode-*.vsix --force
```

### Python dependencies (for running/debugging)

```bash
pip3 install pymssql
```

> `pymssql` handles SQL Server 2008–2019 including older TLS configurations. `pyodbc` is supported as a fallback.

---

## Quick Start

### Run a function
1. Open a `.ci` file in VSCode
2. Press **`Ctrl+Shift+B`** or click the **▶** button in the editor title bar
3. Pick a function from the dropdown
4. Output appears in the integrated terminal

### Debug a function
1. Click the gutter (left of line numbers) to set a breakpoint
2. Press **`F5`**
3. Pick a function from the dropdown
4. Execution pauses at breakpoints — use the Debug sidebar for watch/call stack/stepping

### Look up a built-in function
- **Hover** over any built-in name to see its docs inline
- Press **`Ctrl+Alt+R`** to open the full searchable reference panel
- Right-click → **Cicode: Open Help for Symbol** for a detailed help panel

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+B` | Run a function from the current file |
| `F5` | Debug a function (prompts for function name) |
| `Ctrl+Alt+R` | Open the searchable Function Reference panel |
| `Ctrl+Alt+D` | Insert a doc comment skeleton above the current function |
| `F12` | Go to definition of the symbol under cursor |
| `Shift+F12` | Find all references to the symbol under cursor |
| `Ctrl+Space` | Trigger IntelliSense / autocomplete manually |
| `Ctrl+Shift+Space` | Trigger signature help (parameter hints) |

---

## Extension Commands

Access all commands via `Ctrl+Shift+P` and type **CiCode** or **Cicode**:

| Command | Description |
|---------|-------------|
| `CiCode: Run Function` | Pick and run a function from the active `.ci` file |
| `CiCode: Run Function (All Files)` | Run a function with all workspace `.ci` files loaded |
| `CiCode: Pick Function` | Open the function picker without running |
| `CiCode: Open Function Reference` | Open the searchable built-in function reference panel |
| `Cicode: Open Help for Symbol` | Show offline help for the symbol under the cursor |
| `Cicode: Insert Doc Skeleton for Function` | Generate a `(* ... *)` doc comment block |
| `Cicode: Rebuild Builtin Functions` | Regenerate built-in cache from AVEVA HTML (if installed) |
| `Cicode: Reindex All Files` | Force a full re-scan of all workspace `.ci` files |

---

## Extension Settings

Configure in VSCode Settings (`Ctrl+,`) — search for **cicode**:

### General
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.avevaPath` | `""` | Path to AVEVA Plant SCADA install folder (enables official HTML help) |
| `cicode.hover.showHelpLink` | `true` | Show "Open full help" link in hover tooltips |

### Diagnostics
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.diagnostics.enable` | `true` | Enable undefined functions & duplicate definition errors |
| `cicode.diagnostics.warnUndeclaredVariables` | `true` | Warn on variables used but never declared |
| `cicode.diagnostics.warnInvalidTypes` | `true` | Warn on invalid type declarations |
| `cicode.diagnostics.warnDeclarationsInBlocks` | `true` | Warn on variable declarations inside IF/FOR/WHILE |
| `cicode.diagnostics.ignoredFunctions` | `[]` | Regex list of function names to exclude from "undefined" errors |
| `cicode.diagnostics.ignoredUndeclaredVariables` | `[]` | Regex list of variable names to exclude from undeclared warnings |

### Linting
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.lint.enable` | `true` | Enable lint diagnostics |
| `cicode.lint.maxLineLength` | `120` | Warn when lines exceed this length (0 = off) |
| `cicode.lint.warnMixedIndent` | `true` | Warn on mixing tabs and spaces |
| `cicode.lint.warnMissingSemicolons` | `true` | Warn on type declarations without trailing semicolon |
| `cicode.lint.warnKeywordCase` | `true` | Suggest UPPERCASE for keywords (IF, END, FUNCTION, etc.) |
| `cicode.lint.warnUnusedVariables` | `true` | Warn on declared but never-used variables |
| `cicode.lint.warnMagicNumbers` | `false` | Warn on hardcoded numeric literals (excludes 0, 1, -1) |
| `cicode.lint.maxCallNestingDepth` | `5` | Warn when function calls are nested deeper than this |
| `cicode.lint.maxBlockNestingDepth` | `5` | Warn when IF/FOR/WHILE blocks are nested deeper than this |

### Formatting
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.format.enable` | `true` | Enable the CiCode document formatter |
| `cicode.format.maxConsecutiveBlankLines` | `2` | Collapse more than N consecutive blank lines |

### Code Lens & Explorer
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.codeLens.enable` | `true` | Show reference counts above function definitions |
| `cicode.explorer.expandFolders` | `true` | Expand folders by default in the CiCode Explorer sidebar |

### Indexing
| Setting | Default | Description |
|---------|---------|-------------|
| `cicode.indexing.excludePatterns` | `[]` | Regex patterns for files to exclude from indexing |
| `cicode.signatureOverrides` | `{}` | Override or add function signatures for IntelliSense |

---

## IntelliSense & Language Features

### Auto-complete
The extension indexes all `.ci` files in your workspace and provides completions for:
- All **1,159 AVEVA built-in functions** with correct signatures
- All **user-defined functions** across all workspace files
- Keywords: `IF`, `THEN`, `ELSE`, `END`, `FOR`, `WHILE`, `DO`, `RETURN`, etc.

### Hover Documentation
Hover over any built-in function to see:
- Full function signature with parameter types
- Return type (e.g. `INT`, `REAL`, `STRING`)
- Description from the AVEVA CiCode 2026 reference
- Parameter descriptions
- Link to open the full help panel

### Diagnostics
Squiggly underlines appear for:
- 🔴 **Error** — calling an undefined function
- 🔴 **Error** — duplicate function definition
- 🟡 **Warning** — undeclared variable
- 🟡 **Warning** — variable declared in a block (not at function top)
- 🔵 **Info** — missing semicolons, keyword casing, long lines

### Code Lens
Above every `FUNCTION` definition, a clickable label shows **N references** — click it to see all call sites across the workspace.

---

## Running & Debugging

### Run (no breakpoints)
| Method | Action |
|--------|--------|
| `Ctrl+Shift+B` | Run from current file only |
| ▶ button (title bar) | Run from current file only |
| Command: **Run Function (All Files)** | Run with all workspace `.ci` files loaded |

The interpreter:
1. Auto-saves the file
2. Shows a quick-pick of all `FUNCTION` definitions in the file
3. Runs the selected function in the integrated terminal
4. Press **Enter** to close when done

### Debug (F5)
1. Set breakpoints by clicking the gutter
2. Press **F5** — a quick-pick prompts for the function to run
3. Execution pauses at breakpoints
4. Use the standard VSCode Debug sidebar:
   - **Variables** — inspect locals
   - **Call Stack** — see the full call chain
   - **Watch** — add expressions to monitor
   - **Step Over** `F10` / **Step Into** `F11` / **Step Out** `Shift+F11`
   - **Continue** `F5` / **Stop** `Shift+F5`

> The interpreter loads all `.ci` files in the workspace folder, so functions defined in other files are available during debugging.

---

## Offline Help & Function Reference

### Hover help
Every built-in function has offline docs bundled in the extension — no internet or AVEVA install needed. Hover over a function name to see it.

### Function Reference Panel (`Ctrl+Alt+R`)
Opens a full WebView panel with:
- **Search box** — filter by function name or description text
- **Left pane** — scrollable list of all 1,159 built-in functions
- **Right pane** — full documentation for the selected function including parameters and return type

### Help for symbol
Right-click any built-in function name → **Cicode: Open Help for Symbol**, or place your cursor on a name and run the command. A detailed panel opens showing the function docs.

### AVEVA HTML help (optional)
If you have AVEVA Plant SCADA installed, set `cicode.avevaPath` to your install folder (e.g. `C:\Program Files (x86)\AVEVA Plant SCADA 2023`). Help links will open the official HTML documentation instead of the offline panel.

---

## Interpreter — Implemented Built-ins

The Python interpreter implements the following CiCode built-in categories:

### String Functions (30)
`StrLeft` `StrRight` `StrMid` `StrTrim` `StrTrimLeft` `StrTrimRight` `StrLen` `StrUpr` `StrLwr` `StrChr` `StrPos` `StrSearch` `StrToInt` `StrToReal` `StrFormat` `StrPad` `StrReplace` `StrRepeat` `StrWord` `StrWordCount` `StrCompare` `StrCompareLwr` `StrConcat` `IntToStr` `RealToStr` `Substr` `StrFull` `StrIsNum` `ChrToStr` `StrToChr`

### SQL Functions (24)
`SQLConnect` `SQLDisconnect` `SQLExec` `SQLNext` `SQLGetField` `SQLEnd` `SQLErrMsg` `SQLBeginTran` `SQLCommit` `SQLRollback` `SQLNumChange` `SQLCreate` `SQLFirst` `SQLLast` `SQLPrev` `SQLCurr` `SQLCall` `SQLAppend` `SQLDelete` `SQLUpdate` `SQLSetParam` `SQLGetParam` `SQLTraceOn` `SQLTraceOff`

### Time & Date Functions (21)
`TimeCurrent` `SysTime` `TimeToStr` `TimeHour` `TimeMin` `TimeSec` `DateDay` `DateMonth` `DateYear` `DateWeekDay` `TimeMidNight` `DateSub` `DateAdd` `TimestampCurrent` `TimestampToStr` `StrToDate` `StrToTime` `DateToStr` `Time_` `Date_`

### Form / GUI Functions (24)
`FormNew` `FormPrompt` `FormInput` `FormEdit` `FormListBox` `FormAddList` `FormButton` `FormRead` `FormDestroy` `FormNumeric` `FormCheckBox` `FormComboBox` `FormOpenFile` `FormActive` `FormCursor` `FormPosition` `FormSetData` `FormGetData`

> Forms are rendered using **tkinter** and mirror the AVEVA Plant SCADA dialog system.

### File Functions (19)
`FileOpen` `FileClose` `FileRead` `FileWrite` `FileWriteLn` `FileEof` `FileSeek` `FileTell` `FileGetPos` `FileExists` `FileDelete` `FileRename` `FileCopy` `FileSize` `DirCreate` `DirDelete` `DirExists` `DirFindFirst` `DirFindNext`

### Map / Associative Array Functions (11)
`MapOpen` `MapClose` `MapValueSet` `MapValueGet` `MapKeyExists` `MapKeyDelete` `MapKeyCount` `MapKeyFirst` `MapKeyNext` `MapExists` `MapClear`

### Task Functions (8)
`TaskNew` `TaskKill` `TaskSuspend` `Sleep` `SleepMS` `Halt` `TaskIsRunning`

> `TaskNew` runs tasks sequentially (no true parallelism) — sufficient for logic testing.

### Misc Functions (18)
`Message` `Print` `ErrLog` `Trace` `DebugMsg` `Assert` `IsError` `ErrMsg` `ErrSet` `IsGateway` `ServerName` `ClusterName` `ComputerName` `ProjectInfo` `TypeInfo` `ObjectCallMethod` `ObjectGetProperty` `ObjectSetProperty`

> All other AVEVA built-ins (display, I/O device, alarm, trend, etc.) are available as **no-op stubs** that return 0 — so code that calls them won't crash.

---

## CiCode Language Reference

### Types
| Type | Description |
|------|-------------|
| `INT` | 32-bit integer (also used for booleans: 0=false, 1=true) |
| `REAL` | Double-precision float |
| `STRING` | Variable-length string |
| `OBJECT` | COM/ActiveX object reference |
| `QUALITY` | Tag quality value |
| `TIMESTAMP` | Date/time value |

### Syntax Basics

```cicode
(* Block comment *)
// Line comment

INT FUNCTION Add(INT a, INT b)
    INT result;
    result = a + b;
    RETURN result;
END

STRING FUNCTION Greet(STRING name)
    RETURN "Hello, " + name + "!";
END
```

### Control Flow
```cicode
IF condition THEN
    // ...
ELSE
    // ...
END

FOR i = 0 TO 9 DO
    // ...
END

WHILE condition DO
    // ...
END

SELECT CASE value
    CASE 1: // ...
    CASE 2: // ...
    CASE ELSE: // ...
END SELECT
```

### Key Rules
- **Case-insensitive** — `MyFunc` and `myfunc` are the same
- **No exceptions** — use `IsError()` to check for errors after calls
- **Semicolons** on variable declarations: `INT x;`
- **Arrays** — `INT arr[100];` (0-indexed, fixed size)
- **Globals** — variables declared outside functions are module-global and shared across files
- **String concat** — `+` operator: `"Hello " + name`
- **Comments** — `(* block *)` or `// line`

### Common Error Codes
| Code | Meaning |
|------|---------|
| `0` | Success |
| `259` | End of data (e.g. SQL EOF, file EOF) |
| `299` | Cancelled (user pressed Cancel / Escape) |

---

## SQL Server Connection

CiCode uses `SQLConnect` to connect to SQL Server:

```cicode
INT FUNCTION ConnectDB()
    INT hSQL;
    hSQL = SQLConnect("DRIVER={SQL Server};SERVER=myserver;Database=mydb;Uid=sa;Pwd=mypassword;");
    IF IsError() THEN
        Message("DB Error", SQLErrMsg(hSQL), 48);
        RETURN -1;
    END
    RETURN hSQL;
END
```

The interpreter converts this connection string to a `pymssql` connection. Supports SQL Server 2008–2019, including older TLS configurations (`tds_version='7.0'`).

See [SQL.md](SQL.md) for full documentation including transactions, parameterised queries, and error handling.

---

## GUI Forms

CiCode forms are rendered as native dialogs using **tkinter**:

```cicode
INT FUNCTION ShowNameDialog()
    INT hForm;
    STRING name;
    hForm = FormNew("Enter Details", 400, 200, 1);
    FormPrompt(hForm, 10, 10, "Your name:");
    FormInput(hForm, 10, 30, 200, 20, name, 50);
    FormButton(hForm, 10, 60, 80, 25, "OK", 1);
    FormButton(hForm, 100, 60, 80, 25, "Cancel", 0);
    FormRead(hForm);
    FormDestroy(hForm);
    IF IsError() THEN RETURN -1; END
    Message("Hello", "Hello " + name, 64);
    RETURN 0;
END
```

See [FORMS.md](FORMS.md) for all supported form controls and layout system.

---

## Project Structure

```
cicode-interpreter/
├── README.md                          ← You are here
├── ARCHITECTURE.md                    ← Interpreter internals deep-dive
├── BUILTINS.md                        ← Full list of implemented built-ins
├── DEBUGGING.md                       ← How the DAP debug adapter works
├── EXTENSION.md                       ← Extension source code walkthrough
├── FORMS.md                           ← GUI form system documentation
├── SQL.md                             ← SQL connection and usage guide
│
├── interpreter/                       ← Python CiCode interpreter
│   ├── cicode.py                      ← CLI entry point
│   ├── lexer.py                       ← Tokeniser
│   ├── parser.py                      ← Recursive-descent parser → AST
│   ├── ast_nodes.py                   ← AST dataclass definitions
│   ├── interpreter.py                 ← Tree-walking evaluator
│   ├── debug_adapter.py               ← DAP (Debug Adapter Protocol) server
│   ├── requirements.txt               ← Python dependencies
│   └── builtins/                      ← Built-in function implementations
│       ├── sql_funcs.py               ← SQLConnect, SQLExec, SQLNext, etc.
│       ├── form_funcs.py              ← FormNew, FormRead, FormButton, etc.
│       ├── string_funcs.py            ← StrLeft, StrToInt, StrFormat, etc.
│       ├── math_funcs.py              ← Abs, Sin, Sqrt, etc.
│       ├── time_funcs.py              ← TimeCurrent, TimeToStr, DateAdd, etc.
│       ├── file_funcs.py              ← FileOpen, FileRead, FileWrite, etc.
│       ├── task_funcs.py              ← TaskNew, Sleep, Halt, etc.
│       ├── map_funcs.py               ← MapOpen, MapValueSet, MapValueGet, etc.
│       ├── misc_funcs.py              ← Print, IsError, ErrMsg, Message, etc.
│       └── stub_funcs.py              ← No-op stubs for unimplemented built-ins
│
└── cicode-extension/                  ← VSCode extension source (TypeScript)
    ├── package.json                   ← Extension manifest
    ├── src/
    │   ├── extension.ts               ← Activation entry point
    │   ├── core/
    │   │   ├── indexer.ts             ← Workspace file indexer
    │   │   └── builtins/
    │   │       ├── builtins.ts        ← Built-in loader & type extractor
    │   │       └── builtinFunctions.json  ← 1,159 built-in function definitions
    │   └── features/
    │       ├── runner.ts              ← Run & debug commands, function picker
    │       ├── commands.ts            ← Help panel, doc skeleton, rebuild
    │       ├── referencePanel.ts      ← Searchable function reference WebView
    │       ├── statusBar.ts           ← Status bar item
    │       ├── sideBar.ts             ← CiCode Explorer tree view
    │       ├── docSkeleton.ts         ← Doc comment generator
    │       ├── diagnostics/           ← Error & warning providers
    │       └── providers/             ← IntelliSense providers
    │           ├── completion.ts      ← Auto-complete
    │           ├── hover.ts           ← Hover docs
    │           ├── signature.ts       ← Signature help
    │           ├── navigation.ts      ← Go to definition, find references
    │           └── inlayHints.ts      ← Inline type hints
    └── syntaxes/
        └── cicode.tmLanguage.json     ← TextMate syntax grammar
```

---

## Known Limitations

- **No real-time I/O** — `TagRead`, `TagWrite`, and all `IODevice` functions are stubs
- **No display functions** — `DspXxx`, `PageDisplay`, `WinNew` etc. are stubs
- **No alarm/trend functions** — `AlarmXxx`, `TrnXxx` etc. are stubs
- **Sequential tasks** — `TaskNew` runs tasks sequentially, not in parallel threads
- **Partial error codes** — the most common ones (0, 259, 299) are correct; others may differ
- **No `#INCLUDE`** — all files in the workspace folder are automatically loaded instead

---

## Further Documentation

| File | Contents |
|------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the lexer, parser, and interpreter work internally |
| [BUILTINS.md](BUILTINS.md) | Detailed list of every implemented built-in with notes |
| [DEBUGGING.md](DEBUGGING.md) | How the DAP debug adapter integrates with VSCode |
| [EXTENSION.md](EXTENSION.md) | Extension source code architecture and feature walkthrough |
| [FORMS.md](FORMS.md) | All supported form controls and the tkinter rendering system |
| [SQL.md](SQL.md) | SQL connection string format, transactions, parameterised queries |

---

*Built by [JoshuaVlantis](https://github.com/JoshuaVlantis) — contributions welcome.*
