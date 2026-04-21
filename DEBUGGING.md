# Debugging — DAP (Debug Adapter Protocol)

## How F5 Debugging Works

VSCode's debugger communicates with external tools via the **Debug Adapter Protocol (DAP)** — a JSON-RPC protocol over stdin/stdout. `debug_adapter.py` implements a DAP server that bridges VSCode ↔ the CiCode interpreter.

```
VSCode Debug UI
      │  DAP JSON-RPC over stdin/stdout
      ▼
debug_adapter.py  (DAP server)
      │  debug_hook callback
      ▼
interpreter.py    (CiCode evaluator)
```

---

## Starting the Debug Session

`launch.json` configures VSCode to launch `debug_adapter.py` as a subprocess:

```json
{
  "type": "cicode",
  "request": "launch",
  "program": "${file}",
  "function": "${input:functionName}",
  "additionalFiles": ["...other .ci files..."]
}
```

`extension.js` registers a `DebugAdapterDescriptorFactory` that spawns `python3 debug_adapter.py` as the adapter process.

---

## DAP Protocol Basics

Messages are framed:
```
Content-Length: <N>\r\n\r\n<N bytes of JSON>
```

Three message types:
- **Request** (VSCode → adapter): `initialize`, `launch`, `setBreakpoints`, `continue`, `next`, `stepIn`, `stepOut`, `stackTrace`, `scopes`, `variables`, `evaluate`
- **Response** (adapter → VSCode): reply to each request
- **Event** (adapter → VSCode): `initialized`, `stopped`, `output`, `terminated`

---

## Stdout Isolation (Critical Detail)

The DAP protocol uses **stdin/stdout** for framed JSON. Any stray `print()` output would corrupt the protocol pipe. To prevent this:

1. At **module load** (before any imports), the raw stdout buffer is captured:
   ```python
   _dap_out = sys.stdout.buffer  # line 11 of debug_adapter.py
   ```

2. All DAP messages use `_dap_out` directly.

3. When the interpreter runs, `sys.stdout` is replaced with a `DAPStream` object that routes `print()` to DAP `output` events (shown in VSCode's Debug Console):
   ```python
   sys.stdout = DAPStream('stdout')
   ```

4. After the interpreter finishes, stdout is restored.

**⚠ If you add any `print()` statements to `debug_adapter.py` itself, use `_dap_out.write(...)` not `print()`.**

---

## Breakpoints

When VSCode calls `setBreakpoints`, the adapter stores:
```python
self.breakpoints = {
    "/path/to/file.ci": {10, 25, 42},  # set of line numbers
}
```

The `debug_hook` is called before every CiCode statement:
```python
def debug_hook(file, line, local_scope, module_scope):
    if line in self.breakpoints.get(file, set()):
        # pause execution
        self._pause('breakpoint', file, line, local_scope)
        # blocks until VSCode sends 'continue', 'next', etc.
```

---

## Stepping

Stepping is implemented via an `_action` state variable:
- `'continue'` — run freely
- `'next'` — step over (pause at next statement at same or lower call depth)
- `'stepIn'` — pause at very next statement
- `'stepOut'` — run until call stack is shallower

The `debug_hook` checks `_action` and `_step_depth` on every statement.

---

## Pause / Resume Flow

When pausing:
1. `debug_hook` calls `_pause()` which sets `_paused = True` and sends a `stopped` event to VSCode
2. `_pause()` blocks on `threading.Event.wait()` until resumed
3. VSCode sends `continue` / `next` / `stepIn` / `stepOut` request
4. Adapter updates `_action`, calls `event.set()` → `debug_hook` unblocks

---

## Watch Variables & Scopes

When VSCode requests `scopes` and `variables`, the adapter returns:
- **Locals** — `local_scope` dict captured at pause point
- **Globals** — `interp.globals` (module-level variables)

Variables are serialised to strings for display. Arrays show a preview.

---

## Call Stack Display

`interpreter.py` maintains `_call_stack` as:
```python
[["FunctionName", "/path/to/file.ci", line_number], ...]
```

The DAP adapter converts this to DAP `StackFrame` objects for the Call Stack panel.

---

## Output Events

- `Print("text")` in CiCode → appears in **Debug Console** as stdout
- `Trace("text")` → appears as stderr (orange)
- Interpreter errors → appear as stderr

---

## launch.json Reference

```json
{
  "version": "0.2.0",
  "inputs": [
    {
      "id": "functionName",
      "type": "command",
      "command": "cicode.pickFunction"
    }
  ],
  "configurations": [
    {
      "name": "CiCode: Debug active file",
      "type": "cicode",
      "request": "launch",
      "program": "${file}",
      "function": "${input:functionName}",
      "additionalFiles": []
    },
    {
      "name": "CiCode: Debug all files",
      "type": "cicode",
      "request": "launch",
      "program": "${file}",
      "function": "${input:functionName}",
      "additionalFiles": ["${workspaceFolder}/MySQL.ci", "${workspaceFolder}/MyFunctions.ci"]
    }
  ]
}
```

---

## Troubleshooting Debug Sessions

**Breakpoints not appearing in gutter:**
- `package.json` must have `"breakpoints": [{"language": "cicode"}]`

**F5 crashes immediately:**
- Check `~/.vscode/extensions/cicode-1.0.0/` is up to date
- Run `python3 debug_adapter.py` manually to see if it starts without import errors

**Print() not showing in Debug Console:**
- Ensure stdout redirect happens before `interp.call_function(...)` in `_run_interpreter`
- Check that `DAPStream.write()` calls `send_event('output', ...)`

**Cross-file functions not found:**
- `additionalFiles` in `launch.json` must list the other `.ci` files
- Or use the "Debug all files" config which loads everything
