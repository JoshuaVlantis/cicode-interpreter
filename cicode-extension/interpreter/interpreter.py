"""CiCode tree-walking interpreter."""
import sys
from ast_nodes import (
    Program, ScopeDecl, FunctionDecl, Param, VarDecl,
    AssignStmt, LValue, FuncCallStmt,
    IfStmt, WhileStmt, ForStmt, SelectStmt, CaseClause,
    ReturnStmt, NopStmt,
    BinaryOp, UnaryOp, FuncCallExpr, VarRef,
    IntLit, RealLit, StringLit,
)


class CiCodeArray:
    """Sparse array supporting 1D and 2D indexing."""

    def __init__(self, dims, type_='string', default=None):
        self.dims = dims
        self.type_ = type_
        self.data = {}
        if default is not None:
            self._default = default
        else:
            self._default = self._type_default(type_)

    def _type_default(self, t):
        t = (t or 'string').lower()
        if t in ('int', 'object', 'quality', 'timestamp'):
            return 0
        if t == 'real':
            return 0.0
        return ''

    def get(self, indices):
        return self.data.get(tuple(indices), self._default)

    def set(self, indices, value):
        self.data[tuple(indices)] = value

    def __repr__(self):
        return f"CiCodeArray(dims={self.dims}, entries={len(self.data)})"


class ReturnException(Exception):
    def __init__(self, value=None):
        self.value = value


class HaltException(Exception):
    pass


class CiCodeError(Exception):
    pass


class Ref:
    """Reference wrapper for pass-by-reference parameters."""

    def __init__(self, getter, setter):
        self._getter = getter
        self._setter = setter

    @property
    def value(self):
        return self._getter()

    def set(self, v):
        self._setter(v)


class Interpreter:
    def __init__(self):
        self.global_scope = {}
        self.module_scopes = {}
        self.functions = {}
        self.builtins = {}
        self.current_module = None
        self._last_error = 0
        self._last_error_msg = ""
        self._call_stack = []
        self.debug_hook = None
        self._load_builtins()

    # ------------------------------------------------------------------ builtins

    def _load_builtins(self):
        import importlib.util
        import os as _os
        _builtins_init = _os.path.join(_os.path.dirname(__file__), 'builtins', '__init__.py')
        spec = importlib.util.spec_from_file_location("_ci_builtins", _builtins_init)
        mod = importlib.util.module_from_spec(spec)
        # Inject sub-module stubs so relative imports work
        import sys as _sys
        # Register submodules
        _pkg_dir = _os.path.dirname(_builtins_init)
        for _sub in ('string_funcs', 'math_funcs', 'time_funcs', 'file_funcs',
                     'form_funcs', 'task_funcs', 'map_funcs', 'misc_funcs',
                     'stub_funcs', 'sql_funcs'):
            _sub_path = _os.path.join(_pkg_dir, f'{_sub}.py')
            if _os.path.exists(_sub_path):
                _sub_spec = importlib.util.spec_from_file_location(
                    f'builtins.{_sub}', _sub_path)
                _sub_mod = importlib.util.module_from_spec(_sub_spec)
                _sys.modules[f'builtins.{_sub}'] = _sub_mod
                _sub_spec.loader.exec_module(_sub_mod)
        _sys.modules['_ci_builtins'] = mod
        spec.loader.exec_module(mod)
        self.builtins = mod.get_all_builtins(self)

    # ------------------------------------------------------------------ type helpers

    def to_int(self, v):
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return 0
            try:
                return int(float(s))
            except (ValueError, OverflowError):
                return 0
        return 0

    def to_real(self, v):
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, float):
            return v
        if isinstance(v, int):
            return float(v)
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return 0.0
            try:
                return float(s)
            except (ValueError, OverflowError):
                return 0.0
        return 0.0

    def to_str(self, v):
        if isinstance(v, str):
            return v
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            if v == int(v) and abs(v) < 1e15:
                return str(int(v))
            return str(v)
        if v is None:
            return ""
        return str(v)

    def coerce(self, v, type_):
        t = (type_ or 'string').lower()
        if t == 'int':
            return self.to_int(v)
        if t == 'real':
            return self.to_real(v)
        if t == 'string':
            return self.to_str(v)
        if t == 'object':
            return self.to_int(v)
        return v

    def _default_for_type(self, type_):
        if not type_:
            return 0
        t = type_.lower()
        if t in ('int', 'object', 'quality', 'timestamp'):
            return 0
        if t == 'real':
            return 0.0
        if t == 'string':
            return ''
        return 0

    # ------------------------------------------------------------------ scope helpers

    def lookup_var(self, name, local_scope, module_scope):
        name = name.lower()
        if name in local_scope:
            return local_scope[name]
        if name in module_scope:
            return module_scope[name]
        if name in self.global_scope:
            return self.global_scope[name]
        return None

    def set_var(self, name, value, local_scope, module_scope):
        name = name.lower()
        if name in local_scope:
            local_scope[name] = value
        elif name in module_scope:
            module_scope[name] = value
        elif name in self.global_scope:
            self.global_scope[name] = value
        else:
            # Auto-create in global scope
            self.global_scope[name] = value

    def get_array(self, name, local_scope, module_scope):
        name_lower = name.lower()
        val = self.lookup_var(name_lower, local_scope, module_scope)
        if val is None or not isinstance(val, CiCodeArray):
            arr = CiCodeArray([], 'string')
            # Check where to store it
            if name_lower in local_scope:
                local_scope[name_lower] = arr
            elif name_lower in module_scope:
                module_scope[name_lower] = arr
            else:
                self.global_scope[name_lower] = arr
            return arr
        return val

    # ------------------------------------------------------------------ file loading

    def load_file(self, filename):
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        from lexer import tokenize
        from parser import Parser
        tokens = tokenize(source, filename)
        p = Parser(tokens, filename)
        program = p.parse()

        mod_name = filename
        if mod_name not in self.module_scopes:
            self.module_scopes[mod_name] = {}

        for decl in program.decls:
            if isinstance(decl, ScopeDecl):
                self._register_scope_decl(decl, mod_name)
            elif isinstance(decl, FunctionDecl):
                self.functions[decl.name.lower()] = decl
                decl._module = mod_name

    def _register_scope_decl(self, decl, mod_name):
        name = decl.name.lower()
        if decl.dims:
            dims = []
            for d in decl.dims:
                if isinstance(d, IntLit):
                    dims.append(d.value)
                elif isinstance(d, RealLit):
                    dims.append(int(d.value))
                else:
                    dims.append(100)  # default if non-literal
            arr_val = CiCodeArray(dims, decl.type_)
            if decl.scope == 'global':
                self.global_scope[name] = arr_val
            else:
                scope = self.module_scopes.setdefault(mod_name, {})
                scope[name] = arr_val
        else:
            default = decl.default
            if default is not None:
                if isinstance(default, IntLit):
                    default = default.value
                elif isinstance(default, RealLit):
                    default = default.value
                elif isinstance(default, StringLit):
                    default = default.value
                else:
                    # Try to evaluate simple expressions
                    default = self._default_for_type(decl.type_)
            else:
                default = self._default_for_type(decl.type_)

            if decl.scope == 'global':
                self.global_scope.setdefault(name, default)
            else:
                scope = self.module_scopes.setdefault(mod_name, {})
                scope.setdefault(name, default)

    # ------------------------------------------------------------------ function calls

    def call_function(self, name, args, module_name=None):
        name_lower = name.lower()

        if name_lower in self.builtins:
            return self.builtins[name_lower](*args)

        if name_lower not in self.functions:
            print(f"Warning: unknown function '{name}'", file=sys.stderr)
            return 0

        func = self.functions[name_lower]
        func_module = getattr(func, '_module', module_name) or ''
        module_scope = self.module_scopes.get(func_module, {})
        local_scope = {}

        # Bind parameters
        for i, param in enumerate(func.params):
            pname = param.name.lower()
            if i < len(args):
                val = args[i]
                if isinstance(val, CiCodeArray):
                    local_scope[pname] = val
                elif isinstance(val, Ref):
                    # Pass by ref: store the Ref and unwrap on var access
                    local_scope[pname] = val.value
                else:
                    local_scope[pname] = self.coerce(val, param.type_)
            else:
                local_scope[pname] = self._default_for_type(param.type_)

        self._call_stack.append([name_lower, func_module, 0])
        try:
            self._exec_body(func.body, local_scope, module_scope)
        except ReturnException as e:
            ret = e.value
            if ret is None:
                ret = self._default_for_type(func.return_type)
            return ret
        finally:
            self._call_stack.pop()

        return self._default_for_type(func.return_type)

    # ------------------------------------------------------------------ expression evaluation

    def eval_expr(self, node, local_scope, module_scope):
        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, RealLit):
            return node.value
        if isinstance(node, StringLit):
            return node.value

        if isinstance(node, VarRef):
            name = node.name.lower()
            if node.indices:
                arr = self.get_array(name, local_scope, module_scope)
                indices = [self.to_int(self.eval_expr(i, local_scope, module_scope))
                           for i in node.indices]
                return arr.get(indices)
            else:
                val = self.lookup_var(name, local_scope, module_scope)
                return val if val is not None else 0

        if isinstance(node, FuncCallExpr):
            call_args = self._build_call_args(node.args, local_scope, module_scope)
            return self.call_function(node.name, call_args)

        if isinstance(node, BinaryOp):
            return self._eval_binop(node, local_scope, module_scope)

        if isinstance(node, UnaryOp):
            v = self.eval_expr(node.operand, local_scope, module_scope)
            if node.op == '-':
                if isinstance(v, float):
                    return -v
                return -self.to_int(v)
            if node.op == 'not':
                return 0 if v else 1
        return 0

    def _build_call_args(self, arg_nodes, local_scope, module_scope):
        args = []
        for arg in arg_nodes:
            if isinstance(arg, VarRef) and not arg.indices:
                aname = arg.name.lower()

                def make_ref(n=aname):
                    def getter():
                        v = self.lookup_var(n, local_scope, module_scope)
                        return v if v is not None else ""

                    def setter(v):
                        self.set_var(n, v, local_scope, module_scope)

                    return Ref(getter, setter)

                args.append(make_ref())
            elif isinstance(arg, VarRef) and arg.indices:
                args.append(self.eval_expr(arg, local_scope, module_scope))
            else:
                args.append(self.eval_expr(arg, local_scope, module_scope))
        return args

    def _eval_binop(self, node, local_scope, module_scope):
        op = node.op

        # Short-circuit
        if op == 'and':
            l = self.eval_expr(node.left, local_scope, module_scope)
            if not l:
                return 0
            r = self.eval_expr(node.right, local_scope, module_scope)
            return 1 if r else 0

        if op == 'or':
            l = self.eval_expr(node.left, local_scope, module_scope)
            if l:
                return 1
            r = self.eval_expr(node.right, local_scope, module_scope)
            return 1 if r else 0

        l = self.eval_expr(node.left, local_scope, module_scope)
        r = self.eval_expr(node.right, local_scope, module_scope)

        if op == '+':
            if isinstance(l, str) or isinstance(r, str):
                return self.to_str(l) + self.to_str(r)
            if isinstance(l, float) or isinstance(r, float):
                return self.to_real(l) + self.to_real(r)
            return self.to_int(l) + self.to_int(r)

        if op == '-':
            if isinstance(l, float) or isinstance(r, float):
                return self.to_real(l) - self.to_real(r)
            return self.to_int(l) - self.to_int(r)

        if op == '*':
            if isinstance(l, float) or isinstance(r, float):
                return self.to_real(l) * self.to_real(r)
            return self.to_int(l) * self.to_int(r)

        if op == '/':
            r_val = self.to_real(r)
            if r_val == 0:
                return 0
            return self.to_real(l) / r_val

        if op == '^':
            return self.to_real(l) ** self.to_real(r)

        if op == 'mod':
            ri = self.to_int(r)
            return self.to_int(l) % ri if ri != 0 else 0

        if op == '=':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l == r else 0
            return 1 if self.to_real(l) == self.to_real(r) else 0

        if op == '<>':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l != r else 0
            return 1 if self.to_real(l) != self.to_real(r) else 0

        if op == '<':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l < r else 0
            return 1 if self.to_real(l) < self.to_real(r) else 0

        if op == '>':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l > r else 0
            return 1 if self.to_real(l) > self.to_real(r) else 0

        if op == '<=':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l <= r else 0
            return 1 if self.to_real(l) <= self.to_real(r) else 0

        if op == '>=':
            if isinstance(l, str) and isinstance(r, str):
                return 1 if l >= r else 0
            return 1 if self.to_real(l) >= self.to_real(r) else 0

        if op == 'bitand':
            return self.to_int(l) & self.to_int(r)
        if op == 'bitor':
            return self.to_int(l) | self.to_int(r)
        if op == 'bitxor':
            return self.to_int(l) ^ self.to_int(r)

        return 0

    # ------------------------------------------------------------------ statement execution

    def _exec_body(self, body, local_scope, module_scope):
        for stmt in body:
            self._exec_stmt(stmt, local_scope, module_scope)

    def _exec_stmt(self, stmt, local_scope, module_scope):
        if self.debug_hook and hasattr(stmt, 'line') and stmt.line > 0:
            if self._call_stack:
                self._call_stack[-1][2] = stmt.line
            file_path = self._call_stack[-1][1] if self._call_stack else ''
            self.debug_hook(file_path, stmt.line, local_scope, module_scope)
        if isinstance(stmt, VarDecl):
            name = stmt.name.lower()
            if stmt.dims:
                dims = [self.to_int(self.eval_expr(d, local_scope, module_scope))
                        for d in stmt.dims]
                arr = CiCodeArray(dims, stmt.type_)
                local_scope[name] = arr
            else:
                if stmt.default is not None:
                    val = self.eval_expr(stmt.default, local_scope, module_scope)
                    local_scope[name] = self.coerce(val, stmt.type_)
                else:
                    local_scope.setdefault(name, self._default_for_type(stmt.type_))

        elif isinstance(stmt, AssignStmt):
            val = self.eval_expr(stmt.value, local_scope, module_scope)
            target = stmt.target
            name = target.name.lower()
            if target.indices:
                arr = self.get_array(name, local_scope, module_scope)
                indices = [self.to_int(self.eval_expr(i, local_scope, module_scope))
                           for i in target.indices]
                arr.set(indices, val)
            else:
                self.set_var(name, val, local_scope, module_scope)

        elif isinstance(stmt, FuncCallStmt):
            call_args = self._eval_call_args(stmt.args, local_scope, module_scope)
            try:
                self.call_function(stmt.name, call_args)
            except HaltException:
                raise
            except ReturnException:
                raise
            except Exception as e:
                self._last_error = 1
                self._last_error_msg = str(e)

        elif isinstance(stmt, IfStmt):
            cond = self.eval_expr(stmt.condition, local_scope, module_scope)
            if cond:
                self._exec_body(stmt.then_body, local_scope, module_scope)
            else:
                executed = False
                for (elseif_cond, elseif_body) in stmt.elseif_clauses:
                    if self.eval_expr(elseif_cond, local_scope, module_scope):
                        self._exec_body(elseif_body, local_scope, module_scope)
                        executed = True
                        break
                if not executed and stmt.else_body:
                    self._exec_body(stmt.else_body, local_scope, module_scope)

        elif isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.condition, local_scope, module_scope):
                self._exec_body(stmt.body, local_scope, module_scope)

        elif isinstance(stmt, ForStmt):
            start = self.to_real(self.eval_expr(stmt.start, local_scope, module_scope))
            end_ = self.to_real(self.eval_expr(stmt.end, local_scope, module_scope))
            step = (self.to_real(self.eval_expr(stmt.step, local_scope, module_scope))
                    if stmt.step else 1.0)
            var = stmt.var.lower()
            if var not in local_scope:
                local_scope[var] = 0
            i = start
            while (step > 0 and i <= end_ + 1e-12) or (step < 0 and i >= end_ - 1e-12):
                self.set_var(var, int(i) if i == int(i) else i, local_scope, module_scope)
                self._exec_body(stmt.body, local_scope, module_scope)
                i += step

        elif isinstance(stmt, SelectStmt):
            val = self.eval_expr(stmt.expr, local_scope, module_scope)
            matched = False
            for case in stmt.cases:
                for cv in case.values:
                    cv_val = self.eval_expr(cv, local_scope, module_scope)
                    if isinstance(val, str) and isinstance(cv_val, str):
                        match = val == cv_val
                    else:
                        try:
                            match = self.to_real(val) == self.to_real(cv_val)
                        except Exception:
                            match = self.to_str(val) == self.to_str(cv_val)
                    if match:
                        self._exec_body(case.body, local_scope, module_scope)
                        matched = True
                        break
                if matched:
                    break
            if not matched and stmt.else_body:
                self._exec_body(stmt.else_body, local_scope, module_scope)

        elif isinstance(stmt, ReturnStmt):
            val = (self.eval_expr(stmt.value, local_scope, module_scope)
                   if stmt.value is not None else None)
            raise ReturnException(val)

        elif isinstance(stmt, NopStmt):
            pass

        elif isinstance(stmt, FunctionDecl):
            # Nested function declaration — register it
            self.functions[stmt.name.lower()] = stmt

    def _eval_call_args(self, arg_nodes, local_scope, module_scope):
        args = []
        for arg in arg_nodes:
            if isinstance(arg, VarRef) and not arg.indices:
                aname = arg.name.lower()

                def make_ref(n=aname):
                    def getter():
                        v = self.lookup_var(n, local_scope, module_scope)
                        return v if v is not None else ""

                    def setter(v):
                        self.set_var(n, v, local_scope, module_scope)

                    return Ref(getter, setter)

                args.append(make_ref())
            elif isinstance(arg, VarRef) and arg.indices:
                args.append(self.eval_expr(arg, local_scope, module_scope))
            else:
                args.append(self.eval_expr(arg, local_scope, module_scope))
        return args
