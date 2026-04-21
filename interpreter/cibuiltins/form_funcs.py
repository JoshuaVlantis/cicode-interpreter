"""CiCode form/UI built-in functions — terminal fallback implementation."""


def register(registry, interp):
    _forms = {}
    _next_handle = [1]
    _current_form = [None]
    _current_listbox = [None]

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    class FormContext:
        def __init__(self, title, width, height, mode):
            self.title = title
            self.width = max(width, 20)
            self.height = height
            self.mode = mode
            self.widgets = []
            self.current_listbox = None

    def FormNew(sTitle, nWidth, nHeight, nMode):
        title = interp.to_str(_unwrap(sTitle))
        width = interp.to_int(_unwrap(nWidth))
        height = interp.to_int(_unwrap(nHeight))
        mode = interp.to_int(_unwrap(nMode))
        ctx = FormContext(title, width, height, mode)
        h = _next_handle[0]
        _next_handle[0] += 1
        _forms[h] = ctx
        _current_form[0] = ctx
        return h

    def FormPrompt(nX, nY, sText):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append({'type': 'label', 'text': interp.to_str(_unwrap(sText))})

    def FormInput(nX, nY, nLen, sVar, nMode=0):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append({
                'type': 'input',
                'var_ref': sVar,
                'len': interp.to_int(_unwrap(nLen)),
            })

    def FormListBox(nX, nY, nWidth, nHeight, sVar, nMode=0):
        ctx = _current_form[0]
        if ctx:
            lb = {'type': 'listbox', 'var_ref': sVar, 'items': []}
            ctx.widgets.append(lb)
            ctx.current_listbox = lb
            _current_listbox[0] = lb

    def FormAddList(sItem):
        lb = _current_listbox[0]
        if lb is not None:
            lb['items'].append(interp.to_str(_unwrap(sItem)))

    def FormButton(nX, nY, sLabel, nMode, nResult):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append({
                'type': 'button',
                'label': interp.to_str(_unwrap(sLabel)).strip(),
                'result': interp.to_int(_unwrap(nResult)),
            })

    def FormRead(nMode=0):
        from interpreter import Ref
        ctx = _current_form[0]
        if not ctx:
            return -1

        width = ctx.width
        print()
        border = '═' * (width - 2)
        print(f"╔{border}╗")
        title_str = ctx.title.center(width - 2)
        print(f"║{title_str}║")
        print(f"╠{border}╣")

        listbox = None
        buttons = []
        labels = []
        inputs = []

        for w in ctx.widgets:
            if w['type'] == 'label':
                labels.append(w)
            elif w['type'] == 'listbox':
                listbox = w
            elif w['type'] == 'button':
                buttons.append(w)
            elif w['type'] in ('input', 'numeric'):
                inputs.append(w)

        for lbl in labels:
            print(f"║  {lbl['text']}")

        if listbox:
            items = listbox['items']
            print(f"║  Items ({len(items)} total):")
            visible = items[:20]
            for i, item in enumerate(visible, 1):
                print(f"║  {i:3d}. {item}")
            if len(items) > 20:
                print(f"║  ... and {len(items) - 20} more")

        if buttons:
            btn_txt = "  ".join(f"[{i + 1}] {b['label']}" for i, b in enumerate(buttons))
            print(f"║")
            print(f"║  {btn_txt}")

        print(f"╚{border}╝")
        print()

        selected_value = ""
        button_result = -1

        if listbox and listbox['items']:
            items = listbox['items']
            while True:
                try:
                    choice = input(f"Enter item number (1-{len(items)}) or 0 to cancel: ").strip()
                    if choice == '0' or choice == '':
                        button_result = 1
                        break
                    n = int(choice) - 1
                    if 0 <= n < len(items):
                        selected_value = items[n]
                        button_result = 0
                        break
                    else:
                        print(f"Please enter 1-{len(items)} or 0")
                except (ValueError, KeyboardInterrupt, EOFError):
                    button_result = 1
                    break

            var_ref = listbox.get('var_ref')
            if isinstance(var_ref, Ref):
                var_ref.set(selected_value)

        elif buttons:
            while True:
                btn_prompt = "/".join(f"{i + 1}={b['label']}" for i, b in enumerate(buttons))
                try:
                    choice = input(f"Choose ({btn_prompt}): ").strip()
                    try:
                        n = int(choice) - 1
                        if 0 <= n < len(buttons):
                            button_result = buttons[n]['result']
                            break
                        else:
                            print("Invalid choice")
                    except ValueError:
                        if not choice and buttons:
                            button_result = buttons[0]['result']
                            break
                except (KeyboardInterrupt, EOFError):
                    button_result = buttons[-1]['result'] if buttons else -1
                    break

        for inp in inputs:
            var_ref = inp.get('var_ref')
            if isinstance(var_ref, Ref):
                try:
                    val = input("> ").strip()
                    var_ref.set(val)
                except (KeyboardInterrupt, EOFError):
                    pass

        _current_form[0] = None
        _current_listbox[0] = None
        return button_result

    def FormDestroy(hForm):
        h = interp.to_int(_unwrap(hForm))
        _forms.pop(h, None)

    def FormNumeric(nX, nY, nLen, nVar, sFmt=None):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append({'type': 'numeric', 'var_ref': nVar})

    def FormCheckBox(nX, nY, sLabel, nVar):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append({
                'type': 'checkbox',
                'label': interp.to_str(_unwrap(sLabel)),
                'var_ref': nVar,
            })

    def FormComboBox(nX, nY, nWidth, sVar, nMode=0):
        FormListBox(nX, nY, nWidth, 1, sVar, nMode)

    def FormOpenFile(sTitle, sFilter, sVar):
        from interpreter import Ref
        if isinstance(sVar, Ref):
            try:
                val = input(f"{interp.to_str(_unwrap(sTitle))} - enter filename: ").strip()
                sVar.set(val)
            except (KeyboardInterrupt, EOFError):
                sVar.set("")
        return 0

    def FormCursor(nRow):
        pass

    def FormPosition(nX, nY):
        pass

    fns = {
        'formnew': FormNew,
        'formprompt': FormPrompt,
        'forminput': FormInput,
        'formlistbox': FormListBox,
        'formaddlist': FormAddList,
        'formbutton': FormButton,
        'formread': FormRead,
        'formdestroy': FormDestroy,
        'formnumeric': FormNumeric,
        'formcheckbox': FormCheckBox,
        'formcombobox': FormComboBox,
        'formopenfile': FormOpenFile,
        'formcursor': FormCursor,
        'formposition': FormPosition,
    }
    registry.update(fns)
