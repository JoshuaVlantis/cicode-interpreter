# Builtin Functions Reference

This documents which CiCode builtins are implemented, stubbed, or missing.

## String Functions (`builtins/string_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `StrLeft(s, n)` | ✅ | |
| `StrRight(s, n)` | ✅ | |
| `StrMid(s, pos, n)` | ✅ | |
| `StrTrim(s)` | ✅ | Strips whitespace |
| `StrTrimLeft(s)` | ✅ | |
| `StrTrimRight(s)` | ✅ | |
| `StrLen(s)` | ✅ | |
| `StrUpper(s)` | ✅ | |
| `StrLower(s)` | ✅ | |
| `StrToInt(s)` | ✅ | |
| `StrToReal(s)` | ✅ | |
| `IntToStr(n)` | ✅ | |
| `RealToStr(r, format)` | ✅ | |
| `StrFormat(fmt, ...)` | ✅ | printf-style |
| `StrSearch(s, pattern)` | ✅ | Returns position or -1 |
| `StrReplace(s, old, new)` | ✅ | |
| `StrPadLeft(s, n, ch)` | ✅ | |
| `StrPadRight(s, n, ch)` | ✅ | |
| `StrWord(s, n, delim)` | ✅ | nth word |

## Math Functions (`builtins/math_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `Abs(x)` | ✅ | |
| `Int(x)` | ✅ | Truncate to integer |
| `Round(x)` | ✅ | |
| `Mod(x, y)` | ✅ | x mod y |
| `Sqrt(x)` | ✅ | |
| `Power(x, y)` | ✅ | |
| `Sin/Cos/Tan(x)` | ✅ | Radians |
| `Log(x)` | ✅ | Natural log |
| `Log10(x)` | ✅ | |
| `Max(a, b)` | ✅ | |
| `Min(a, b)` | ✅ | |
| `Random(n)` | ✅ | 0..n-1 |

## Time Functions (`builtins/time_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `TimeCurrent()` | ✅ | Unix timestamp |
| `TimeToStr(t, fmt)` | ✅ | |
| `TimeToDate(t)` | ✅ | |
| `TimeAdd(t, secs)` | ✅ | |
| `TimeDiff(t1, t2)` | ✅ | |
| `TimeHour(t)` | ✅ | |
| `TimeMinute(t)` | ✅ | |
| `TimeSecond(t)` | ✅ | |
| `TimeDay(t)` | ✅ | |
| `TimeMonth(t)` | ✅ | |
| `TimeYear(t)` | ✅ | |

## SQL Functions (`builtins/sql_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `SQLConnect(connStr)` | ✅ | Returns handle |
| `SQLDisconnect(h)` | ✅ | |
| `SQLSelect(h, sql)` | ✅ | Returns recordset handle |
| `SQLNext(hRec)` | ✅ | 0=row, 259=EOF |
| `SQLGetField(hRec, col)` | ✅ | |
| `SQLExecute(h, sql)` | ✅ | INSERT/UPDATE/DELETE |
| `SQLClose(hRec)` | ✅ | |
| `SQLNumColumns(hRec)` | ✅ | |
| `SQLColName(hRec, n)` | ✅ | |

## Form Functions (`builtins/form_funcs.py`)

See `FORMS.md` for full details.

## File Functions (`builtins/file_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `FileOpen(path, mode)` | ✅ | |
| `FileClose(h)` | ✅ | |
| `FileRead(h)` | ✅ | Returns line |
| `FileWrite(h, s)` | ✅ | |
| `FileEOF(h)` | ✅ | |
| `FileExists(path)` | ✅ | |
| `FileDelete(path)` | ✅ | |
| `FileCopy(src, dst)` | ✅ | |

## Misc Functions (`builtins/misc_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `Print(s)` | ✅ | Outputs to debug console |
| `Trace(s)` | ✅ | Outputs to stderr |
| `MsgBox(s, title)` | ✅ | tkinter messagebox |
| `IsError()` | ✅ | Returns last error code |
| `ErrMsg(code)` | ✅ | Error code → string |
| `ErrSet(code)` | ✅ | Set last error |
| `Sleep(ms)` | ✅ | |
| `Beep()` | 🔶 Stub | No-op on Linux |

## Task Functions (`builtins/task_funcs.py`)

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `TaskNew(fn, ...)` | 🔶 Partial | Runs synchronously, no parallelism |
| `TaskQuit()` | ✅ | |
| `TaskHnd()` | 🔶 Stub | Returns 0 |

## Stub Functions (`builtins/stub_funcs.py`)

All display (`DspXxx`), I/O device (`IODevice`), alarm (`AlmXxx`), trend (`TrnXxx`), and report functions are **no-op stubs** — they return 0 or "" without doing anything. This prevents unimplemented functions from crashing the interpreter when real CiCode uses them.

---

## Adding a Missing Builtin

1. Find the function spec in the CiCode Reference PDF or `cicode_reference.txt` in the project root (gitignored, 83,568 lines — fast to grep)
2. Implement it in the appropriate `builtins/*.py` file (or `stub_funcs.py` if it's complex and not needed)
3. Register it in the module's `register(interp)` function
4. Use `interp._last_error` to report errors instead of raising exceptions
