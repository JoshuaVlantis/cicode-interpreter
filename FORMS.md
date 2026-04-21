# GUI Forms — tkinter Implementation

## Overview

AVEVA Plant SCADA has a built-in form system for CiCode. Functions like `FormNew`, `FormButton`, `FormRead` create and display modal dialogs. This interpreter replicates that system using **tkinter** (Python's standard GUI library).

---

## CiCode Form API → tkinter Mapping

### Typical CiCode form pattern:

```cicode
INT FUNCTION FnFormulaSelect()
    STRING sBuf[10][8];
    INT    hForm;
    INT    nResult;

    hForm = FormNew("Select Formula", 40, 15, 0);
    FormListBox(hForm, sBuf, "Formula Code", 0, 0, 40, 10, 0);
    FormButton(hForm, "OK",     0, 11, 10, 1);  // mode 1 = OK button
    FormButton(hForm, "Cancel", 15, 11, 10, 2); // mode 2 = Cancel button
    
    // Populate the list
    FormAddList(hForm, "BBM 18");
    FormAddList(hForm, "BBM 21");
    
    nResult = FormRead(0);  // 0 = blocking modal, returns 0 on OK, 299 on Cancel
    
    IF nResult = 0 THEN
        // sBuf now contains the selected item
    END
END
```

---

## Return Values

| Event | `FormRead` return value |
|-------|------------------------|
| OK button clicked | `0` |
| Cancel button clicked | `299` |
| Escape key / window X button | `299` |

These match the AVEVA Plant SCADA spec (error 299 = "Cancelled").

---

## Implementation Details (`builtins/form_funcs.py`)

### Form Handle

`FormNew()` returns an integer handle (incrementing counter). The handle is a key into `_forms` dict:
```python
_forms = {}  # handle → FormState object
```

### FormState

Tracks all widgets and state for a single form instance:
```python
@dataclass
class FormState:
    title: str
    width: int
    height: int
    listbox_var: None | Ref   # reference to CiCode variable for selected item
    items: list[str]           # items added via FormAddList
    result: int                # 0 or 299
    ready: threading.Event     # blocks FormRead until user acts
```

### Threading Model

- tkinter **must run on the main thread** on most platforms, but on Linux it can run on any thread
- `FormRead()` spawns a daemon thread to run the tkinter event loop
- `FormRead()` then blocks on `threading.Event.wait()` until the user clicks OK or Cancel
- When a button is clicked, the event is set and the thread joins

**⚠ Each form call creates a new `Tk()` root — this works on Linux. On macOS/Windows only one `Tk()` can exist at a time.**

### Ref (Variable Writeback)

When `FormListBox` is called with a CiCode variable reference (e.g. `sBuf`), the interpreter passes a `Ref` object — a wrapper that allows writing back to the original variable in the interpreter's scope:

```python
class Ref:
    def __init__(self, scope, name):
        self.scope = scope
        self.name = name
    def set(self, value):
        self.scope[self.name] = value
```

When OK is clicked and a listbox selection exists, `ref.set(selected_item)` writes back to `sBuf`.

---

## Implemented Functions

| CiCode Function | Status | Notes |
|----------------|--------|-------|
| `FormNew(title, w, h, mode)` | ✅ | Returns form handle |
| `FormButton(h, label, x, y, w, mode)` | ✅ | mode 1=OK, 2=Cancel, 3=disabled |
| `FormListBox(h, var, label, x, y, w, h, mode)` | ✅ | Single selection listbox |
| `FormAddList(h, item)` | ✅ | Adds item to last listbox |
| `FormRead(mode)` | ✅ | Blocking modal; returns 0 or 299 |
| `FormInput(h, var, label, x, y, w, mode)` | ✅ | Text entry field |
| `FormEdit(h, var, label, x, y, w, mode)` | ✅ | Multi-line text edit |
| `FormPrompt(h, text, x, y, w, mode)` | ✅ | Static label |
| `FormNumeric(h, var, label, x, y, w, mode)` | ✅ | Numeric entry |
| `FormCheckBox(h, var, label, x, y, mode)` | ✅ | Checkbox (0/1) |
| `FormComboBox(h, var, label, x, y, w, mode)` | ✅ | Dropdown combo box |
| `FormOpenFile(h, var, label, x, y, w, mode)` | ✅ | File picker dialog |
| `FormDestroy(h)` | ✅ | Destroys form state |
| `FormGetCurr(h)` | 🔶 Stub | Returns 0 |

---

## Layout System

Plant SCADA uses a character-grid layout. The x/y/width/height parameters are in character units. The tkinter implementation converts these approximately:
- 1 character unit ≈ 8px wide, 16px tall (adjustable constants at top of `form_funcs.py`)

This is approximate — the exact pixel layout won't match Plant SCADA exactly but the forms are functional.

---

## Extending Forms

To add a new form widget type:

1. Add a `FormXxx` function in `form_funcs.py`
2. Store widget state on the `FormState` object
3. In `_build_and_show()`, create the corresponding tkinter widget
4. If it has a writeback variable, store a `Ref` and call `ref.set(value)` when OK is clicked
5. Register `formxxx` in `register(interp)` at the bottom of the file
