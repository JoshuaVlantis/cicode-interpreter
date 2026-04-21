"""CiCode math built-in functions."""
import math
import random


def register(registry, interp):
    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def _r(v):
        return interp.to_real(_unwrap(v))

    def _i(v):
        return interp.to_int(_unwrap(v))

    fns = {
        'abs':      lambda n: abs(_r(n)),
        'sqrt':     lambda n: math.sqrt(max(0.0, _r(n))),
        'pow':      lambda b, e: math.pow(_r(b), _r(e)),
        'sin':      lambda n: math.sin(_r(n)),
        'cos':      lambda n: math.cos(_r(n)),
        'tan':      lambda n: math.tan(_r(n)),
        'arcsin':   lambda n: math.asin(max(-1.0, min(1.0, _r(n)))),
        'arccos':   lambda n: math.acos(max(-1.0, min(1.0, _r(n)))),
        'arctan':   lambda n: math.atan(_r(n)),
        'arctan2':  lambda y, x: math.atan2(_r(y), _r(x)),
        'exp':      lambda n: math.exp(_r(n)),
        'ln':       lambda n: math.log(_r(n)) if _r(n) > 0 else 0.0,
        'log':      lambda n: math.log10(_r(n)) if _r(n) > 0 else 0.0,
        'round':    lambda n, d=0: round(_r(n), _i(d)),
        'int':      lambda n: int(_r(n)),
        'sign':     lambda n: (1 if _r(n) > 0 else (-1 if _r(n) < 0 else 0)),
        'max':      lambda a, b: max(_r(a), _r(b)),
        'min':      lambda a, b: min(_r(a), _r(b)),
        'rand':     lambda n=1: random.random() * _r(n),
        'pi':       lambda: math.pi,
        'fact':     lambda n: float(math.factorial(max(0, _i(n)))),
        'mod':      lambda a, b: _i(a) % _i(b) if _i(b) != 0 else 0,
        'degtorad': lambda n: math.radians(_r(n)),
        'radtodeg': lambda n: math.degrees(_r(n)),
        'highbyte': lambda n: (_i(n) >> 8) & 0xFF,
        'lowbyte':  lambda n: _i(n) & 0xFF,
        'highword': lambda n: (_i(n) >> 16) & 0xFFFF,
        'lowword':  lambda n: _i(n) & 0xFFFF,
        'floor':    lambda n: int(math.floor(_r(n))),
        'ceil':     lambda n: int(math.ceil(_r(n))),
        'trunc':    lambda n: int(math.trunc(_r(n))),
    }
    registry.update(fns)
