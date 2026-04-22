"""CiCode recursive-descent parser — produces an AST from token list."""
from typing import List, Optional, Any, Tuple
from lexer import Token, TT
from ast_nodes import (
    Program, ScopeDecl, FunctionDecl, Param, VarDecl,
    AssignStmt, LValue, FuncCallStmt,
    IfStmt, WhileStmt, ForStmt, SelectStmt, CaseClause,
    ReturnStmt, NopStmt,
    BinaryOp, UnaryOp, FuncCallExpr, VarRef,
    IntLit, RealLit, StringLit,
)

TYPE_KEYWORDS = {'int', 'real', 'string', 'object', 'timestamp', 'quality'}


class ParseError(Exception):
    def __init__(self, msg: str, filename: str = '', line: int = 0):
        self.msg = msg
        self.filename = filename
        self.line = line
        super().__init__(f"{filename}:{line}: {msg}")


class Parser:
    def __init__(self, tokens: List[Token], filename: str = '<unknown>'):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    # ------------------------------------------------------------------ helpers

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def skip_newlines(self):
        while self.current().type == TT.NEWLINE:
            self.advance()

    def expect(self, ttype: TT, value=None) -> Token:
        self.skip_newlines()
        tok = self.current()
        if tok.type != ttype:
            raise ParseError(
                f"Expected {ttype.name} but got {tok.type.name} ({tok.value!r})",
                self.filename, tok.line)
        if value is not None and tok.value != value:
            raise ParseError(
                f"Expected {value!r} but got {tok.value!r}",
                self.filename, tok.line)
        return self.advance()

    def match(self, ttype: TT, value=None) -> bool:
        self.skip_newlines()
        tok = self.current()
        if tok.type != ttype:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def consume_if(self, ttype: TT, value=None) -> Optional[Token]:
        if self.match(ttype, value):
            return self.advance()
        return None

    def error(self, msg: str) -> ParseError:
        tok = self.current()
        return ParseError(msg, self.filename, tok.line)

    def _keyword_prefix_hint(self, name: str) -> str:
        """Return a hint string if `name` starts with a CiCode keyword, e.g. 'whilezn' → WHILE."""
        for kw in ('while', 'select', 'return', 'for', 'if'):
            if name.startswith(kw) and len(name) > len(kw):
                rest = name[len(kw):]
                return f" — did you mean '{kw.upper()} {rest}'?"
        return ''

    # ------------------------------------------------------------------ top-level

    def parse(self) -> Program:
        decls = []
        self.skip_newlines()
        while self.current().type != TT.EOF:
            self.skip_newlines()
            if self.current().type == TT.EOF:
                break
            decl = self._parse_top_level()
            if decl is not None:
                decls.append(decl)
            self.skip_newlines()
        return Program(decls=decls, line=0)

    def _parse_top_level(self):
        tok = self.current()

        # Stray semicolons / newlines
        if tok.type in (TT.SEMICOLON, TT.NEWLINE):
            self.advance()
            return None

        # NOP
        if tok.type == TT.KEYWORD and tok.value == 'nop':
            self.advance()
            return None

        # GLOBAL scope declaration
        if tok.type == TT.KEYWORD and tok.value == 'global':
            return self._parse_scope_decl('global')

        # MODULE scope declaration
        if tok.type == TT.KEYWORD and tok.value == 'module':
            return self._parse_scope_decl('module')

        # Type keyword — could be function or file-level var
        if tok.type == TT.KEYWORD and tok.value in TYPE_KEYWORDS:
            # Peek ahead: type FUNCTION ... → function decl
            nxt = self.peek(1)
            if nxt.type == TT.KEYWORD and nxt.value == 'function':
                return self._parse_function_decl()
            # Otherwise: file-level variable declaration
            return self._parse_file_var_decl()

        # FUNCTION (no return type)
        if tok.type == TT.KEYWORD and tok.value == 'function':
            return self._parse_function_decl()

        # Unknown — skip token to avoid infinite loop
        self.advance()
        return None

    def _parse_scope_decl(self, scope: str) -> ScopeDecl:
        line = self.current().line
        self.advance()  # consume 'global' or 'module'
        type_tok = self.expect(TT.KEYWORD)
        if type_tok.value not in TYPE_KEYWORDS:
            raise self.error(f"Expected type keyword, got {type_tok.value!r}")
        type_ = type_tok.value

        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value

        dims = self._parse_optional_dims()
        default = None
        if self.consume_if(TT.EQ):
            default = self._parse_expr()

        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return ScopeDecl(scope=scope, type_=type_, name=name, dims=dims, default=default, line=line)

    def _parse_file_var_decl(self) -> ScopeDecl:
        line = self.current().line
        type_tok = self.advance()
        type_ = type_tok.value
        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value
        dims = self._parse_optional_dims()
        default = None
        if self.consume_if(TT.EQ):
            default = self._parse_expr()
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return ScopeDecl(scope='module', type_=type_, name=name, dims=dims, default=default, line=line)

    def _parse_optional_dims(self) -> list:
        dims = []
        while self.current().type == TT.LBRACKET:
            self.advance()  # consume '['
            dim_expr = self._parse_expr()
            dims.append(dim_expr)
            self.expect(TT.RBRACKET)
        return dims

    def _parse_function_decl(self) -> FunctionDecl:
        line = self.current().line
        return_type = None

        # Optional return type
        if self.current().type == TT.KEYWORD and self.current().value in TYPE_KEYWORDS:
            return_type = self.advance().value

        # 'function' keyword
        self.expect(TT.KEYWORD, 'function')

        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value

        # Parameter list
        self.expect(TT.LPAREN)
        params = []
        self.skip_newlines()
        while not self.match(TT.RPAREN):
            if self.current().type == TT.EOF:
                break
            params.append(self._parse_param())
            if not self.consume_if(TT.COMMA):
                break
            self.skip_newlines()
        self.expect(TT.RPAREN)

        # Body — everything until bare 'end'
        body = self._parse_body(end_tokens={('keyword', 'end')})

        # Consume 'end' (and optionally an 'function' keyword after it — non-standard)
        self.skip_newlines()
        self.expect(TT.KEYWORD, 'end')
        # optional trailing identifier (some dialects use END FunctionName)
        self.skip_newlines()
        if self.current().type == TT.IDENTIFIER:
            self.advance()
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)

        return FunctionDecl(
            return_type=return_type, name=name, params=params,
            var_decls=[], body=body, line=line
        )

    def _parse_param(self) -> Param:
        self.skip_newlines()
        line = self.current().line
        type_tok = self.expect(TT.KEYWORD)
        if type_tok.value not in TYPE_KEYWORDS:
            raise self.error(f"Expected parameter type, got {type_tok.value!r}")
        type_ = type_tok.value
        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value
        dims = self._parse_optional_dims()
        return Param(type_=type_, name=name, dims=dims, line=line)

    # ------------------------------------------------------------------ body / statements

    def _parse_body(self, end_tokens) -> list:
        """Parse statements until one of the end_tokens is found (without consuming)."""
        body = []
        while True:
            self.skip_newlines()
            tok = self.current()
            if tok.type == TT.EOF:
                break
            # Check if we're at an end token
            if self._is_end_token(end_tokens):
                break
            stmt = self._parse_statement()
            if stmt is not None:
                body.append(stmt)
        return body

    def _is_end_token(self, end_tokens) -> bool:
        tok = self.current()
        for et in end_tokens:
            etype, evalue = et
            if etype == 'keyword' and tok.type == TT.KEYWORD and tok.value == evalue:
                return True
        return False

    def _parse_statement(self):
        self.skip_newlines()
        tok = self.current()

        if tok.type == TT.EOF:
            return None

        # Stray semicolons
        if tok.type == TT.SEMICOLON:
            self.advance()
            return NopStmt(line=tok.line)

        # Type keyword → variable declaration
        if tok.type == TT.KEYWORD and tok.value in TYPE_KEYWORDS:
            # Make sure it's not a function decl (shouldn't appear inside a body)
            nxt = self.peek(1)
            if nxt.type == TT.KEYWORD and nxt.value == 'function':
                # nested function? skip
                return self._parse_function_decl()
            return self._parse_var_decl()

        if tok.type == TT.KEYWORD:
            if tok.value == 'if':
                return self._parse_if()
            if tok.value == 'while':
                return self._parse_while()
            if tok.value == 'for':
                return self._parse_for()
            if tok.value == 'select':
                return self._parse_select()
            if tok.value == 'return':
                return self._parse_return()
            if tok.value == 'nop':
                self.advance()
                return NopStmt(line=tok.line)
            if tok.value in ('global', 'module'):
                return self._parse_var_decl_with_scope()
            # Unknown keyword — skip
            self.advance()
            return NopStmt(line=tok.line)

        if tok.type == TT.IDENTIFIER:
            return self._parse_assign_or_call()

        # Stray operator in statement position is always a syntax error
        _stray_ops = {TT.LT, TT.GT, TT.LEQ, TT.GEQ, TT.NEQ,
                      TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH, TT.CARET}
        if tok.type in _stray_ops:
            raise self.error(f"Unexpected operator '{tok.value}' in statement position")

        # Skip unknown tokens
        self.advance()
        return NopStmt(line=tok.line)

    def _parse_var_decl(self) -> VarDecl:
        line = self.current().line
        type_tok = self.advance()
        type_ = type_tok.value
        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value
        dims = self._parse_optional_dims()
        default = None
        if self.consume_if(TT.EQ):
            default = self._parse_expr()
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return VarDecl(type_=type_, name=name, dims=dims, default=default, line=line)

    def _parse_var_decl_with_scope(self) -> VarDecl:
        """LOCAL/GLOBAL/MODULE modifier inside a function body — treat as plain VarDecl."""
        line = self.current().line
        self.advance()  # consume 'local'/'global'/'module'
        type_tok = self.expect(TT.KEYWORD)
        if type_tok.value not in TYPE_KEYWORDS:
            raise self.error(f"Expected type keyword after scope modifier, got {type_tok.value!r}")
        type_ = type_tok.value
        name_tok = self.expect(TT.IDENTIFIER)
        name = name_tok.value
        dims = self._parse_optional_dims()
        default = None
        if self.consume_if(TT.EQ):
            default = self._parse_expr()
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return VarDecl(type_=type_, name=name, dims=dims, default=default, line=line)

    def _parse_assign_or_call(self):
        """
        Decide between assignment (name [idx]* = expr) and function call (name(args)).
        """
        line = self.current().line
        name = self.advance().value  # consume identifier (already lowercase)

        # Skip newlines for lookahead
        # Check for array indices before = sign
        indices = []
        while self.current().type == TT.LBRACKET:
            self.advance()
            idx = self._parse_expr()
            indices.append(idx)
            self.expect(TT.RBRACKET)

        if self.current().type == TT.EQ:
            self.advance()  # consume '='
            value = self._parse_expr()
            # Check for run-on keyword that became an assignment: e.g. "fori = 1 TO 10 DO"
            next_tok = self.current()
            _assignment_trailing = {'to', 'then', 'do'}
            if next_tok.type == TT.KEYWORD and next_tok.value in _assignment_trailing:
                hint = self._keyword_prefix_hint(name)
                raise self.error(
                    f"Unexpected '{next_tok.value.upper()}' after assignment to '{name}'{hint}"
                )
            self.consume_if(TT.SEMICOLON)
            self.consume_if(TT.NEWLINE)
            return AssignStmt(target=LValue(name=name, indices=indices, line=line), value=value, line=line)

        if self.current().type == TT.LPAREN and not indices:
            # Function call statement
            self.advance()  # consume '('
            args = self._parse_arg_list()
            self.expect(TT.RPAREN)
            self.consume_if(TT.SEMICOLON)
            self.consume_if(TT.NEWLINE)
            return FuncCallStmt(name=name, args=args, line=line)

        # Standalone identifier with no '=' and no '(' — check for operator that
        # indicates a mistyped keyword (e.g. "WHILEznRow < 500 DO")
        next_tok = self.current()
        _op_types = {TT.LT, TT.GT, TT.LEQ, TT.GEQ, TT.NEQ,
                     TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH, TT.CARET}
        _kw_ops = {'and', 'or', 'not', 'mod', 'bitand', 'bitor', 'bitxor', 'is'}
        if next_tok.type in _op_types or (next_tok.type == TT.KEYWORD and next_tok.value in _kw_ops):
            hint = self._keyword_prefix_hint(name)
            raise self.error(
                f"Unexpected '{next_tok.value}' after identifier '{name}'{hint}"
            )
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return NopStmt(line=line)

    def _parse_arg_list(self) -> list:
        args = []
        self.skip_newlines()
        while not self.match(TT.RPAREN):
            if self.current().type == TT.EOF:
                break
            args.append(self._parse_expr())
            if not self.consume_if(TT.COMMA):
                break
            self.skip_newlines()
        return args

    # ------------------------------------------------------------------ control flow

    def _parse_if(self) -> IfStmt:
        line = self.current().line
        self.expect(TT.KEYWORD, 'if')
        condition = self._parse_expr()
        self.expect(TT.KEYWORD, 'then')
        self.consume_if(TT.NEWLINE)

        then_body = self._parse_body(end_tokens={
            ('keyword', 'end'), ('keyword', 'else'),
        })

        elseif_clauses = []
        else_body = []

        while self.current().type == TT.KEYWORD and self.current().value == 'else':
            self.advance()  # consume 'else'
            self.skip_newlines()
            if self.current().type == TT.KEYWORD and self.current().value == 'if':
                # ELSE IF
                self.advance()  # consume 'if'
                elseif_cond = self._parse_expr()
                self.expect(TT.KEYWORD, 'then')
                self.consume_if(TT.NEWLINE)
                elseif_body = self._parse_body(end_tokens={
                    ('keyword', 'end'), ('keyword', 'else'),
                })
                elseif_clauses.append((elseif_cond, elseif_body))
            else:
                # Plain ELSE
                self.consume_if(TT.NEWLINE)
                else_body = self._parse_body(end_tokens={('keyword', 'end')})
                break

        self.skip_newlines()
        self.expect(TT.KEYWORD, 'end')
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)

        return IfStmt(
            condition=condition, then_body=then_body,
            elseif_clauses=elseif_clauses, else_body=else_body, line=line
        )

    def _parse_while(self) -> WhileStmt:
        line = self.current().line
        self.expect(TT.KEYWORD, 'while')
        condition = self._parse_expr()
        self.expect(TT.KEYWORD, 'do')
        self.consume_if(TT.NEWLINE)
        body = self._parse_body(end_tokens={('keyword', 'end')})
        self.skip_newlines()
        self.expect(TT.KEYWORD, 'end')
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return WhileStmt(condition=condition, body=body, line=line)

    def _parse_for(self) -> ForStmt:
        line = self.current().line
        self.expect(TT.KEYWORD, 'for')
        var_tok = self.expect(TT.IDENTIFIER)
        var = var_tok.value
        self.expect(TT.EQ)
        start = self._parse_expr()
        self.expect(TT.KEYWORD, 'to')
        end_ = self._parse_expr()
        step = None
        self.skip_newlines()
        if self.current().type == TT.KEYWORD and self.current().value == 'step':
            self.advance()
            step = self._parse_expr()
        self.skip_newlines()
        self.expect(TT.KEYWORD, 'do')
        self.consume_if(TT.NEWLINE)
        body = self._parse_body(end_tokens={('keyword', 'end')})
        self.skip_newlines()
        self.expect(TT.KEYWORD, 'end')
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return ForStmt(var=var, start=start, end=end_, step=step, body=body, line=line)

    def _parse_select(self) -> SelectStmt:
        line = self.current().line
        self.expect(TT.KEYWORD, 'select')
        self.expect(TT.KEYWORD, 'case')
        expr = self._parse_expr()
        self.consume_if(TT.NEWLINE)

        cases = []
        else_body = []

        self.skip_newlines()
        while not (self.current().type == TT.KEYWORD and self.current().value == 'end'):
            if self.current().type == TT.EOF:
                break
            self.skip_newlines()
            if self.current().type == TT.KEYWORD and self.current().value == 'end':
                break
            if self.current().type == TT.KEYWORD and self.current().value == 'case':
                self.advance()  # consume 'case'
                self.skip_newlines()
                if self.current().type == TT.KEYWORD and self.current().value == 'else':
                    self.advance()  # consume 'else'
                    self.consume_if(TT.COLON)
                    self.consume_if(TT.NEWLINE)
                    else_body = self._parse_body(end_tokens={('keyword', 'end'), ('keyword', 'case')})
                else:
                    values = [self._parse_expr()]
                    while self.current().type == TT.COMMA:
                        self.advance()
                        values.append(self._parse_expr())
                    self.consume_if(TT.COLON)
                    self.consume_if(TT.NEWLINE)
                    case_body = self._parse_body(end_tokens={('keyword', 'end'), ('keyword', 'case')})
                    cases.append(CaseClause(values=values, body=case_body, line=line))
            else:
                self.advance()  # skip unexpected token

        self.skip_newlines()
        self.expect(TT.KEYWORD, 'end')
        self.skip_newlines()
        # consume 'select' in 'end select'
        self.consume_if(TT.KEYWORD, 'select')
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return SelectStmt(expr=expr, cases=cases, else_body=else_body, line=line)

    def _parse_return(self) -> ReturnStmt:
        line = self.current().line
        self.expect(TT.KEYWORD, 'return')
        # If next meaningful token starts an expression, parse it
        self.skip_newlines()
        tok = self.current()
        if tok.type in (TT.NEWLINE, TT.SEMICOLON, TT.EOF) or (
                tok.type == TT.KEYWORD and tok.value == 'end'):
            value = None
        else:
            value = self._parse_expr()
        self.consume_if(TT.SEMICOLON)
        self.consume_if(TT.NEWLINE)
        return ReturnStmt(value=value, line=line)

    # ------------------------------------------------------------------ expressions

    def _parse_expr(self) -> Any:
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self.current().type == TT.KEYWORD and self.current().value == 'or':
            op_line = self.current().line
            self.advance()
            right = self._parse_and()
            left = BinaryOp(op='or', left=left, right=right, line=op_line)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self.current().type == TT.KEYWORD and self.current().value == 'and':
            op_line = self.current().line
            self.advance()
            right = self._parse_not()
            left = BinaryOp(op='and', left=left, right=right, line=op_line)
        return left

    def _parse_not(self):
        if self.current().type == TT.KEYWORD and self.current().value == 'not':
            op_line = self.current().line
            self.advance()
            operand = self._parse_not()
            return UnaryOp(op='not', operand=operand, line=op_line)
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_additive()
        cmp_types = {TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LEQ, TT.GEQ}
        while self.current().type in cmp_types:
            tok = self.current()
            op_line = tok.line
            op_map = {
                TT.EQ: '=', TT.NEQ: '<>', TT.LT: '<',
                TT.GT: '>', TT.LEQ: '<=', TT.GEQ: '>=',
            }
            op = op_map[tok.type]
            self.advance()
            right = self._parse_additive()
            left = BinaryOp(op=op, left=left, right=right, line=op_line)
        return left

    def _parse_additive(self):
        left = self._parse_multiplicative()
        additive_kw = {'bitand', 'bitor', 'bitxor'}
        while True:
            tok = self.current()
            if tok.type == TT.PLUS:
                op_line = tok.line; self.advance()
                right = self._parse_multiplicative()
                left = BinaryOp(op='+', left=left, right=right, line=op_line)
            elif tok.type == TT.MINUS:
                op_line = tok.line; self.advance()
                right = self._parse_multiplicative()
                left = BinaryOp(op='-', left=left, right=right, line=op_line)
            elif tok.type == TT.KEYWORD and tok.value in additive_kw:
                op = tok.value; op_line = tok.line; self.advance()
                right = self._parse_multiplicative()
                left = BinaryOp(op=op, left=left, right=right, line=op_line)
            else:
                break
        return left

    def _parse_multiplicative(self):
        left = self._parse_power()
        while True:
            tok = self.current()
            if tok.type == TT.STAR:
                op_line = tok.line; self.advance()
                right = self._parse_power()
                left = BinaryOp(op='*', left=left, right=right, line=op_line)
            elif tok.type == TT.SLASH:
                op_line = tok.line; self.advance()
                right = self._parse_power()
                left = BinaryOp(op='/', left=left, right=right, line=op_line)
            elif tok.type == TT.KEYWORD and tok.value == 'mod':
                op_line = tok.line; self.advance()
                right = self._parse_power()
                left = BinaryOp(op='mod', left=left, right=right, line=op_line)
            else:
                break
        return left

    def _parse_power(self):
        base = self._parse_unary()
        if self.current().type == TT.CARET:
            op_line = self.current().line
            self.advance()
            exp = self._parse_power()  # right-associative
            return BinaryOp(op='^', left=base, right=exp, line=op_line)
        return base

    def _parse_unary(self):
        tok = self.current()
        if tok.type == TT.MINUS:
            op_line = tok.line
            self.advance()
            operand = self._parse_unary()
            return UnaryOp(op='-', operand=operand, line=op_line)
        if tok.type == TT.PLUS:
            self.advance()
            return self._parse_unary()
        return self._parse_primary()

    def _parse_primary(self):
        self.skip_newlines()
        tok = self.current()

        if tok.type == TT.INTEGER:
            self.advance()
            return IntLit(value=tok.value, line=tok.line)

        if tok.type == TT.REAL:
            self.advance()
            return RealLit(value=tok.value, line=tok.line)

        if tok.type == TT.STRING:
            self.advance()
            return StringLit(value=tok.value, line=tok.line)

        if tok.type == TT.LPAREN:
            self.advance()
            expr = self._parse_expr()
            self.skip_newlines()
            self.expect(TT.RPAREN)
            return expr

        if tok.type == TT.IDENTIFIER:
            name = tok.value
            name_line = tok.line
            self.advance()
            # Function call
            if self.current().type == TT.LPAREN:
                self.advance()  # consume '('
                args = self._parse_arg_list()
                self.expect(TT.RPAREN)
                return FuncCallExpr(name=name, args=args, line=name_line)
            # Array / var reference
            indices = []
            while self.current().type == TT.LBRACKET:
                self.advance()
                idx = self._parse_expr()
                indices.append(idx)
                self.expect(TT.RBRACKET)
            return VarRef(name=name, indices=indices, line=name_line)

        # Keyword used as value (rare but possible for some builtins)
        if tok.type == TT.KEYWORD and tok.value in TYPE_KEYWORDS:
            # Could be int() as a function-like cast
            name = tok.value
            name_line = tok.line
            self.advance()
            if self.current().type == TT.LPAREN:
                self.advance()
                args = self._parse_arg_list()
                self.expect(TT.RPAREN)
                return FuncCallExpr(name=name, args=args, line=name_line)
            return VarRef(name=name, indices=[], line=name_line)

        # Unexpected token — return 0 literal and skip
        self.advance()
        return IntLit(value=0, line=tok.line)
