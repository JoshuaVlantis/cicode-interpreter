"""CiCode form/UI built-in functions — tkinter GUI implementation."""


def register(registry, interp):
    import threading

    _forms = {}
    _next_handle = [1]
    _current_form = [None]
    _current_listbox = [None]

    # Pixels per character unit (monospace grid)
    CW = 8   # column width in pixels
    RH = 20  # row height in pixels
    PAD = 10  # window padding

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    class Widget:
        def __init__(self, kind, col, row, **kw):
            self.kind = kind
            self.col = col
            self.row = row
            self.__dict__.update(kw)

    class FormContext:
        def __init__(self, title, width, height, mode):
            self.title = title
            self.width = max(width, 20)
            self.height = max(height, 4)
            self.mode = mode
            self.widgets = []
            self.current_listbox = None

    def FormNew(sTitle, nWidth, nHeight, nMode=0):
        title  = interp.to_str(_unwrap(sTitle))
        width  = interp.to_int(_unwrap(nWidth))
        height = interp.to_int(_unwrap(nHeight))
        mode   = interp.to_int(_unwrap(nMode))
        ctx = FormContext(title, width, height, mode)
        h = _next_handle[0]
        _next_handle[0] += 1
        _forms[h] = ctx
        _current_form[0] = ctx
        return h

    def FormPrompt(nX, nY, sText):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('label', interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      text=interp.to_str(_unwrap(sText))))

    def FormInput(nX, nY, nLen, sVar, nMode=0):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('input',
                                      interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      length=interp.to_int(_unwrap(nLen)),
                                      var_ref=sVar))

    def FormEdit(nX, nY, sVar, nWidth, nMaxLen=0, nHeight=1, bReadOnly=0):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('input',
                                      interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      length=interp.to_int(_unwrap(nWidth)),
                                      var_ref=sVar,
                                      readonly=interp.to_int(_unwrap(bReadOnly))))

    def FormListBox(nX, nY, nWidth, nHeight, sVar, nMode=0):
        ctx = _current_form[0]
        if ctx:
            w = Widget('listbox',
                       interp.to_int(_unwrap(nX)),
                       interp.to_int(_unwrap(nY)),
                       width=interp.to_int(_unwrap(nWidth)),
                       height=interp.to_int(_unwrap(nHeight)),
                       var_ref=sVar,
                       items=[])
            ctx.widgets.append(w)
            ctx.current_listbox = w
            _current_listbox[0] = w
        return 0

    def FormAddList(sItem):
        lb = _current_listbox[0]
        if lb is not None:
            lb.items.append(interp.to_str(_unwrap(sItem)))

    def FormButton(nX, nY, sLabel, fn_ref, nMode):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('button',
                                      interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      label=interp.to_str(_unwrap(sLabel)).strip(),
                                      mode=interp.to_int(_unwrap(nMode))))
        return 0

    def FormRead(nMode=0):
        from interpreter import Ref
        ctx = _current_form[0]
        if not ctx:
            return -1

        result_holder = [None]   # [button_result]
        done_event = threading.Event()

        def build_and_run():
            try:
                import tkinter as tk
                from tkinter import font as tkfont

                root = tk.Tk()
                root.title(ctx.title)
                root.resizable(False, False)
                root.configure(bg='#f0f0f0')

                # Use system monospace font for proper column alignment
                mono = tkfont.Font(family='Courier New', size=9)
                label_font = tkfont.Font(family='Segoe UI', size=9)
                btn_font = tkfont.Font(family='Segoe UI', size=9)

                # Title bar strip
                title_bar = tk.Frame(root, bg='#1e6ba8', height=28)
                title_bar.pack(fill='x')
                tk.Label(title_bar, text=ctx.title, bg='#1e6ba8', fg='white',
                         font=tkfont.Font(family='Segoe UI', size=10, weight='bold'),
                         padx=10).pack(side='left', pady=4)

                # Content frame
                content = tk.Frame(root, bg='#f0f0f0', padx=PAD, pady=PAD)
                content.pack(fill='both', expand=True)

                tk_vars = {}   # widget index → tk variable

                # Collect widget types
                labels   = [w for w in ctx.widgets if w.kind == 'label']
                listboxes= [w for w in ctx.widgets if w.kind == 'listbox']
                inputs   = [w for w in ctx.widgets if w.kind == 'input']
                buttons  = [w for w in ctx.widgets if w.kind == 'button']
                checkboxes=[w for w in ctx.widgets if w.kind == 'checkbox']
                combos   = [w for w in ctx.widgets if w.kind == 'combobox']

                # ── Labels ──────────────────────────────────────────────
                for lbl in labels:
                    tk.Label(content, text=lbl.text, bg='#f0f0f0',
                             font=mono, anchor='w').pack(fill='x', pady=(2, 0))

                # ── List boxes ──────────────────────────────────────────
                lb_widgets = {}
                for i, w in enumerate(listboxes):
                    frame = tk.Frame(content, bg='#f0f0f0')
                    frame.pack(fill='both', expand=True, pady=(4, 4))
                    vis = min(w.height, 20)
                    lb = tk.Listbox(frame, font=mono,
                                    width=w.width, height=vis,
                                    selectmode=tk.SINGLE,
                                    activestyle='dotbox',
                                    bg='white', fg='#1a1a1a',
                                    selectbackground='#1e6ba8',
                                    selectforeground='white',
                                    relief='sunken', bd=1)
                    sb = tk.Scrollbar(frame, orient='vertical', command=lb.yview)
                    lb.configure(yscrollcommand=sb.set)
                    lb.pack(side='left', fill='both', expand=True)
                    sb.pack(side='right', fill='y')
                    for item in w.items:
                        lb.insert(tk.END, item)
                    if w.items:
                        lb.selection_set(0)
                        lb.activate(0)
                    lb_widgets[i] = (lb, w)

                # ── Text inputs ─────────────────────────────────────────
                inp_vars = {}
                for i, w in enumerate(inputs):
                    frame = tk.Frame(content, bg='#f0f0f0')
                    frame.pack(fill='x', pady=2)
                    var = tk.StringVar()
                    from interpreter import Ref
                    init = w.var_ref.value if isinstance(w.var_ref, Ref) else interp.to_str(_unwrap(w.var_ref))
                    var.set(init)
                    state = 'readonly' if getattr(w, 'readonly', 0) else 'normal'
                    entry = tk.Entry(frame, textvariable=var,
                                     width=getattr(w, 'length', 20),
                                     font=mono, state=state,
                                     bg='white', relief='sunken', bd=1)
                    entry.pack(side='left')
                    inp_vars[i] = (var, w)

                # ── Check boxes ─────────────────────────────────────────
                chk_vars = {}
                for i, w in enumerate(checkboxes):
                    frame = tk.Frame(content, bg='#f0f0f0')
                    frame.pack(fill='x', pady=2)
                    from interpreter import Ref
                    init = w.var_ref.value if isinstance(w.var_ref, Ref) else '0'
                    var = tk.IntVar(value=1 if init == '1' else 0)
                    tk.Checkbutton(frame, text=w.label, variable=var,
                                   bg='#f0f0f0', font=label_font).pack(side='left')
                    chk_vars[i] = (var, w)

                # ── Separator before buttons ─────────────────────────────
                tk.Frame(content, bg='#cccccc', height=1).pack(fill='x', pady=(8, 4))

                # ── Buttons ──────────────────────────────────────────────
                btn_frame = tk.Frame(content, bg='#f0f0f0')
                btn_frame.pack(pady=(0, 4))

                def make_ok_handler(mode_val):
                    def handler():
                        # Collect listbox selection
                        for idx, (lb, w) in lb_widgets.items():
                            sel = lb.curselection()
                            val = lb.get(sel[0]) if sel else ''
                            from interpreter import Ref
                            if isinstance(w.var_ref, Ref):
                                w.var_ref.set(val)
                        # Collect input values
                        for idx, (var, w) in inp_vars.items():
                            from interpreter import Ref
                            if isinstance(w.var_ref, Ref):
                                w.var_ref.set(var.get())
                        # Collect checkbox values
                        for idx, (var, w) in chk_vars.items():
                            from interpreter import Ref
                            if isinstance(w.var_ref, Ref):
                                w.var_ref.set('1' if var.get() else '0')
                        result_holder[0] = 0  # success
                        root.destroy()
                    return handler

                def cancel_handler():
                    result_holder[0] = 299  # CiCode cancel error code
                    root.destroy()

                # If no buttons defined, add default OK/Cancel
                if not buttons:
                    buttons = [Widget('button', 0, 0, label='OK', mode=1),
                               Widget('button', 0, 0, label='Cancel', mode=2)]

                for w in buttons:
                    mode = w.mode
                    if mode == 1:
                        tk.Button(btn_frame, text=w.label, width=10,
                                  command=make_ok_handler(mode),
                                  font=btn_font, bg='#1e6ba8', fg='white',
                                  activebackground='#155a8a', relief='flat',
                                  padx=8, pady=4).pack(side='left', padx=6)
                    elif mode == 2:
                        tk.Button(btn_frame, text=w.label, width=10,
                                  command=cancel_handler,
                                  font=btn_font, bg='#e0e0e0', fg='#1a1a1a',
                                  activebackground='#cccccc', relief='flat',
                                  padx=8, pady=4).pack(side='left', padx=6)
                    else:
                        # Normal button — treat like OK for now
                        tk.Button(btn_frame, text=w.label, width=10,
                                  command=make_ok_handler(0),
                                  font=btn_font, relief='flat',
                                  padx=8, pady=4).pack(side='left', padx=6)

                # Double-click on listbox = OK
                def on_double_click(event):
                    for idx, (lb, w) in lb_widgets.items():
                        make_ok_handler(1)()
                        return
                for idx, (lb, w) in lb_widgets.items():
                    lb.bind('<Double-Button-1>', on_double_click)
                    lb.bind('<Return>', on_double_click)

                # Bind Escape and window close to cancel
                root.protocol("WM_DELETE_WINDOW", cancel_handler)
                root.bind('<Escape>', lambda e: cancel_handler())

                # Center on screen
                root.update_idletasks()
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                rw = root.winfo_reqwidth()
                rh = root.winfo_reqheight()
                root.geometry(f'+{(sw - rw) // 2}+{(sh - rh) // 2}')

                root.focus_force()
                if lb_widgets:
                    list(lb_widgets.values())[0][0].focus_set()

                root.mainloop()

            except Exception as e:
                import traceback
                traceback.print_exc()
                result_holder[0] = -1
            finally:
                done_event.set()

        t = threading.Thread(target=build_and_run, daemon=True)
        t.start()
        done_event.wait()

        _current_form[0] = None
        _current_listbox[0] = None
        return result_holder[0] if result_holder[0] is not None else -1

    def FormDestroy(hForm):
        h = interp.to_int(_unwrap(hForm))
        _forms.pop(h, None)

    def FormNumeric(nX, nY, nLen, nVar, sFmt=None):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('input',
                                      interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      length=interp.to_int(_unwrap(nLen)),
                                      var_ref=nVar))

    def FormCheckBox(nX, nY, sLabel, sVar):
        ctx = _current_form[0]
        if ctx:
            ctx.widgets.append(Widget('checkbox',
                                      interp.to_int(_unwrap(nX)),
                                      interp.to_int(_unwrap(nY)),
                                      label=interp.to_str(_unwrap(sLabel)),
                                      var_ref=sVar))
        return 0

    def FormComboBox(nX, nY, nWidth, nHeight, sVar, nMode=0):
        FormListBox(nX, nY, nWidth, nHeight, sVar, nMode)
        return 0

    def FormOpenFile(sTitle, sFilter, sVar):
        from interpreter import Ref
        import threading
        result = ['']
        done = threading.Event()
        def run():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                path = filedialog.askopenfilename(
                    title=interp.to_str(_unwrap(sTitle)))
                result[0] = path or ''
                root.destroy()
            except Exception:
                pass
            finally:
                done.set()
        threading.Thread(target=run, daemon=True).start()
        done.wait()
        if isinstance(sVar, Ref):
            sVar.set(result[0])
        return 0

    def FormActive(hForm):
        h = interp.to_int(_unwrap(hForm))
        return 1 if h in _forms else 0

    def FormCursor(nRow):
        pass

    def FormPosition(nX, nY):
        pass

    def FormSetData(hForm, hField, sData):
        pass

    def FormGetData(hForm, hField):
        return ''

    registry.update({
        'formnew':       FormNew,
        'formprompt':    FormPrompt,
        'forminput':     FormInput,
        'formedit':      FormEdit,
        'formlistbox':   FormListBox,
        'formaddlist':   FormAddList,
        'formbutton':    FormButton,
        'formread':      FormRead,
        'formdestroy':   FormDestroy,
        'formnumeric':   FormNumeric,
        'formcheckbox':  FormCheckBox,
        'formcombobox':  FormComboBox,
        'formopenfile':  FormOpenFile,
        'formactive':    FormActive,
        'formcursor':    FormCursor,
        'formposition':  FormPosition,
        'formsetdata':   FormSetData,
        'formgetdata':   FormGetData,
    })
