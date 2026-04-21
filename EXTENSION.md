# VSCode Extension

## Overview

The VSCode extension (`cicode-extension/`) provides:
- **Syntax highlighting** for `.ci` files (TextMate grammar)
- **▶ Run button** in the editor title bar — runs a selected function
- **F5 Debugging** — full breakpoints, watch, call stack, step controls
- **Function picker** — QuickPick dropdown populated from FUNCTION declarations in the active file

---

## Extension Source vs Installed Location

| Location | Purpose |
|----------|---------|
| `~/Desktop/CiCode/cicode-extension/` | Source of truth — edit here |
| `~/.vscode/extensions/cicode-1.0.0/` | VSCode reads from here |

**After any change to `cicode-extension/`**, sync and reload:
```bash
cp -r ~/Desktop/CiCode/cicode-extension/* ~/.vscode/extensions/cicode-1.0.0/
# Then in VSCode: Ctrl+Shift+P → "Developer: Reload Window"
```

---

## Key Files

### `package.json`

Declares:
- `"contributes.languages"` — registers `cicode` language for `.ci` files
- `"contributes.grammars"` — links `cicode.tmLanguage.json` for syntax highlighting
- `"contributes.breakpoints"` — **required** for gutter breakpoints to work: `[{"language": "cicode"}]`
- `"contributes.debuggers"` — registers `cicode` debug type, links `launch.json` schema
- `"contributes.commands"` — registers `cicode.runFunction`, `cicode.runAllFiles`, `cicode.pickFunction`
- `"activationEvents"` — activates on `onLanguage:cicode`

### `extension.js`

Main extension logic. Key functions:

**`parseFunctions(text)`** — extracts FUNCTION names from CiCode source using regex:
```js
/^\s*(?:INT|REAL|STRING|OBJECT|QUALITY|TIMESTAMP)?\s*FUNCTION\s+(\w+)\s*\(/gim
```

**`pickFunction(text)`** — shows VSCode QuickPick dropdown with parsed function names. Returns selected name or undefined.

**`cicode.runFunction`** command:
1. Gets active editor file
2. Finds all `.ci` files in workspace root
3. Shows function picker
4. Creates a terminal, runs: `python3 <interpreter/cicode.py> run <files> -c <funcName>`
5. Terminal shows `"Press Enter to close..."` when done

**`cicode.runAllFiles`** command — same as above but always loads all `.ci` files.

**`cicode.pickFunction`** command — exposed for use in `launch.json` `${input:functionName}` binding. Returns selected function name to VSCode.

**`DebugAdapterDescriptorFactory`** — tells VSCode to spawn `python3 debug_adapter.py` as the DAP process.

### `syntaxes/cicode.tmLanguage.json`

TextMate grammar for CiCode syntax highlighting. Originally sourced from the `mskjel.cicode-vscode-extension` extension at:
```
~/.vscode/extensions/mskjel.cicode-vscode-extension-0.7.0/
```

---

## `launch.json` Configuration

Located at `~/Desktop/CiCode/.vscode/launch.json`. Two configurations:

1. **"CiCode: Debug active file"** — loads only the currently active `.ci` file
2. **"CiCode: Debug all files"** — loads all `.ci` files in the workspace together

The `${input:functionName}` binding calls `cicode.pickFunction` to show the QuickPick.

> **Note:** If you add new `.ci` files to the workspace, update `additionalFiles` in `launch.json` to include them so cross-file functions resolve correctly.

---

## Interpreter CLI (`interpreter/cicode.py`)

```bash
python3 cicode.py run <file1.ci> [file2.ci ...] -c FunctionName
```

- Loads all specified files (functions from all files are available to each other)
- Calls the named function
- Exits with code 0 on success, 1 on error

---

## Common Issues

**Breakpoints can't be placed in gutter:**
- Check `package.json` has `"breakpoints": [{"language": "cicode"}]`
- Reload window after any `package.json` change

**Function picker shows empty list:**
- Make sure the active file has FUNCTION declarations
- The regex requires the `FUNCTION` keyword (case-insensitive)

**Extension commands not found:**
- Extension may not be activated — open a `.ci` file first
- Or reload window

**Run terminal stays open / doesn't close:**
- The `; read -p "Press Enter to close..." && exit` appended to the command handles this
- Press Enter in the terminal after the script finishes
