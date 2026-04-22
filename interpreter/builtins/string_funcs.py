"""CiCode string built-in functions."""


def register(registry, interp):
    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def _s(v):
        return interp.to_str(_unwrap(v))

    def _i(v):
        return interp.to_int(_unwrap(v))

    def StrLeft(s, n):
        s, n = _s(s), _i(n)
        return s[:n]

    def StrRight(s, n):
        s, n = _s(s), _i(n)
        return s[-n:] if n > 0 else ""

    def StrMid(s, start, length):
        s = _s(s)
        start = _i(start) - 1  # 1-based to 0-based
        length = _i(length)
        start = max(0, start)
        return s[start:start + length]

    def StrTrim(s):
        return _s(s).strip()

    def StrTrimLeft(s):
        return _s(s).lstrip()

    def StrTrimRight(s):
        return _s(s).rstrip()

    def StrLen(s):
        return len(_s(s))

    def StrUpr(s):
        return _s(s).upper()

    def StrLwr(s):
        return _s(s).lower()

    def StrChr(s, n):
        s = _s(s)
        n = _i(n) - 1  # 1-based
        return s[n] if 0 <= n < len(s) else ""

    def StrPos(sub, s):
        sub, s = _s(sub), _s(s)
        idx = s.find(sub)
        return idx + 1 if idx >= 0 else 0  # 1-based

    def StrSearch(sub, s):
        return StrPos(sub, s)

    def StrToInt(s):
        try:
            return int(float(_s(s).strip()))
        except Exception:
            return 0

    def StrToReal(s):
        try:
            return float(_s(s).strip())
        except Exception:
            return 0.0

    def StrFormat(fmt, *args):
        fmt = _s(fmt)
        uargs = [_unwrap(a) for a in args]
        try:
            return fmt % tuple(uargs)
        except Exception:
            return fmt

    def StrPad(s, n):
        s, n = _s(s), _i(n)
        abs_n = abs(n)
        if len(s) >= abs_n:
            return s[:abs_n]
        return s.ljust(abs_n) if n > 0 else s.rjust(abs_n)

    def StrReplace(s, old, new_s):
        return _s(s).replace(_s(old), _s(new_s))

    def StrRepeat(s, n):
        return _s(s) * _i(n)

    def StrWord(s, n, delim=None):
        s = _s(s)
        n = _i(n)
        if delim is not None:
            delim = _s(delim)
            words = s.split(delim)
        else:
            words = s.split()
        return words[n - 1] if 0 < n <= len(words) else ""

    def StrWordCount(s, delim=None):
        s = _s(s)
        if delim is not None:
            words = s.split(_s(delim))
        else:
            words = s.split()
        return len(words)

    def StrCompare(s1, s2):
        s1, s2 = _s(s1), _s(s2)
        return 0 if s1 == s2 else (1 if s1 > s2 else -1)

    def StrCompareLwr(s1, s2):
        s1, s2 = _s(s1).lower(), _s(s2).lower()
        return 0 if s1 == s2 else (1 if s1 > s2 else -1)

    def StrConcat(s1, s2):
        return _s(s1) + _s(s2)

    def IntToStr(n):
        return str(_i(n))

    def RealToStr(f, width=None, places=None, separator=None):
        """RealToStr(Number, Width, Places[, Separator]) — format real as string."""
        f = interp.to_real(_unwrap(f))
        if width is not None and places is not None:
            w = _i(width)
            p = _i(places)
            formatted = f"{f:.{p}f}"
            if w > 0:
                formatted = formatted.rjust(w)
            return formatted
        return interp.to_str(f)

    def Substr(s, start, length):
        return StrMid(s, start, length)

    def StrFull(s, n):
        """Pad string to exactly n chars."""
        s, n = _s(s), _i(n)
        if len(s) >= n:
            return s[:n]
        return s.ljust(n)

    def StrIsNum(s):
        s = _s(s).strip()
        try:
            float(s)
            return 1
        except Exception:
            return 0

    def ChrToStr(n):
        try:
            return chr(_i(n))
        except Exception:
            return ""

    def StrToChr(s):
        s = _s(s)
        return ord(s[0]) if s else 0

    fns = {
        'strleft': StrLeft,
        'strright': StrRight,
        'strmid': StrMid,
        'strtrim': StrTrim,
        'strtrimleft': StrTrimLeft,
        'strtrimright': StrTrimRight,
        'strlen': StrLen,
        'strupr': StrUpr,
        'strlwr': StrLwr,
        'strchr': StrChr,
        'strpos': StrPos,
        'strsearch': StrSearch,
        'strtoint': StrToInt,
        'strtoreal': StrToReal,
        'strformat': StrFormat,
        'strpad': StrPad,
        'strreplace': StrReplace,
        'strrepeat': StrRepeat,
        'strword': StrWord,
        'strwordcount': StrWordCount,
        'strcompare': StrCompare,
        'strcomparelwr': StrCompareLwr,
        'strconcat': StrConcat,
        'inttostr': IntToStr,
        'realtostr': RealToStr,
        'substr': Substr,
        'strfull': StrFull,
        'strisnum': StrIsNum,
        'chrtostr': ChrToStr,
        'strtochr': StrToChr,
    }
    registry.update(fns)
