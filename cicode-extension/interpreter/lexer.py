"""CiCode Lexer — tokenizes .ci source files."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TT(Enum):
    INTEGER    = auto()
    REAL       = auto()
    STRING     = auto()
    IDENTIFIER = auto()
    KEYWORD    = auto()
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    CARET      = auto()
    EQ         = auto()
    NEQ        = auto()
    LT         = auto()
    GT         = auto()
    LEQ        = auto()
    GEQ        = auto()
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    SEMICOLON  = auto()
    COMMA      = auto()
    COLON      = auto()
    NEWLINE    = auto()
    EOF        = auto()


KEYWORDS = {
    'and', 'global', 'quality', 'bitand', 'if', 'real', 'bitor', 'int',
    'return', 'bitxor', 'is', 'select', 'case', 'mod', 'string', 'cicode',
    'module', 'then', 'civba', 'nop', 'timestamp', 'do', 'not', 'to',
    'object', 'var', 'end', 'or', 'while', 'for', 'function', 'else',
    'local', 'step',
}


@dataclass
class Token:
    type: TT
    value: object
    line: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


class LexError(Exception):
    pass


def tokenize(source: str, filename: str = '<unknown>') -> List[Token]:
    tokens: List[Token] = []
    pos = 0
    line = 1
    n = len(source)
    paren_depth = 0

    def peek(offset=0):
        idx = pos + offset
        return source[idx] if idx < n else ''

    while pos < n:
        ch = source[pos]

        # Skip CR
        if ch == '\r':
            pos += 1
            continue

        # Line comment
        if ch == '/' and peek(1) == '/':
            while pos < n and source[pos] != '\n':
                pos += 1
            continue

        # Newline
        if ch == '\n':
            line += 1
            pos += 1
            if paren_depth == 0:
                # Collapse consecutive newlines
                if not tokens or tokens[-1].type != TT.NEWLINE:
                    tokens.append(Token(TT.NEWLINE, '\n', line - 1))
            continue

        # Whitespace
        if ch in ' \t':
            pos += 1
            continue

        # String literal
        if ch == '"':
            pos += 1
            buf = []
            while pos < n:
                c = source[pos]
                if c == '^':
                    pos += 1
                    if pos < n:
                        esc = source[pos]
                        pos += 1
                        if esc == 'n':
                            buf.append('\n')
                        elif esc == 't':
                            buf.append('\t')
                        elif esc == 'r':
                            buf.append('\r')
                        elif esc == '"':
                            buf.append('"')
                        elif esc == '^':
                            buf.append('^')
                        else:
                            buf.append('^')
                            buf.append(esc)
                    else:
                        buf.append('^')
                elif c == '"':
                    pos += 1
                    break
                elif c == '\n':
                    line += 1
                    buf.append(c)
                    pos += 1
                else:
                    buf.append(c)
                    pos += 1
            tokens.append(Token(TT.STRING, ''.join(buf), line))
            continue

        # Numbers
        if ch.isdigit() or (ch == '.' and peek(1).isdigit()):
            start = pos
            is_real = False
            while pos < n and source[pos].isdigit():
                pos += 1
            if pos < n and source[pos] == '.':
                is_real = True
                pos += 1
                while pos < n and source[pos].isdigit():
                    pos += 1
            # Scientific notation
            if pos < n and source[pos] in 'eE':
                is_real = True
                pos += 1
                if pos < n and source[pos] in '+-':
                    pos += 1
                while pos < n and source[pos].isdigit():
                    pos += 1
            raw = source[start:pos]
            if is_real:
                tokens.append(Token(TT.REAL, float(raw), line))
            else:
                tokens.append(Token(TT.INTEGER, int(raw), line))
            continue

        # Identifiers and keywords
        if ch.isalpha() or ch == '_':
            start = pos
            while pos < n and (source[pos].isalnum() or source[pos] == '_'):
                pos += 1
            word = source[start:pos].lower()
            if word in KEYWORDS:
                tokens.append(Token(TT.KEYWORD, word, line))
            else:
                tokens.append(Token(TT.IDENTIFIER, word, line))
            continue

        # Multi-char operators
        if ch == '<':
            if peek(1) == '>':
                tokens.append(Token(TT.NEQ, '<>', line))
                pos += 2
            elif peek(1) == '=':
                tokens.append(Token(TT.LEQ, '<=', line))
                pos += 2
            else:
                tokens.append(Token(TT.LT, '<', line))
                pos += 1
            continue

        if ch == '>':
            if peek(1) == '=':
                tokens.append(Token(TT.GEQ, '>=', line))
                pos += 2
            else:
                tokens.append(Token(TT.GT, '>', line))
                pos += 1
            continue

        # Single-char tokens
        single = {
            '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR, '/': TT.SLASH,
            '^': TT.CARET, '=': TT.EQ, ';': TT.SEMICOLON, ',': TT.COMMA,
            ':': TT.COLON, '[': TT.LBRACKET, ']': TT.RBRACKET,
        }
        if ch in single:
            tt = single[ch]
            tokens.append(Token(tt, ch, line))
            pos += 1
            if tt == TT.SEMICOLON and paren_depth == 0:
                # Semicolons act as statement terminators; emit a NEWLINE too
                if not tokens or tokens[-1].type != TT.NEWLINE:
                    tokens.append(Token(TT.NEWLINE, '\n', line))
            continue

        if ch == '(':
            paren_depth += 1
            tokens.append(Token(TT.LPAREN, '(', line))
            pos += 1
            continue

        if ch == ')':
            paren_depth -= 1
            if paren_depth < 0:
                paren_depth = 0
            tokens.append(Token(TT.RPAREN, ')', line))
            pos += 1
            continue

        # Unknown character — skip silently (handles stray chars)
        pos += 1

    # Remove trailing newlines
    while tokens and tokens[-1].type == TT.NEWLINE:
        tokens.pop()

    tokens.append(Token(TT.EOF, None, line))
    return tokens
