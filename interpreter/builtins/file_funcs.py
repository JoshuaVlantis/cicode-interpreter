"""CiCode file I/O built-in functions."""
import os
import glob as _glob_mod
import shutil


def register(registry, interp):
    _handles = {}
    _next_handle = [1]
    _dir_iter = [None]

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def FileOpen(sFile, nMode):
        sFile = interp.to_str(_unwrap(sFile))
        nMode = interp.to_int(_unwrap(nMode))
        mode_map = {0: 'r', 1: 'w', 2: 'a', 3: 'r+'}
        mode = mode_map.get(nMode, 'r')
        try:
            f = open(sFile, mode, encoding='utf-8', errors='replace')
            h = _next_handle[0]
            _next_handle[0] += 1
            _handles[h] = f
            return h
        except Exception as e:
            interp._last_error = 1
            interp._last_error_msg = str(e)
            return -1

    def FileClose(hFile):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.pop(h, None)
        if f:
            try:
                f.close()
            except Exception:
                pass

    def FileRead(hFile, sVar):
        from interpreter import Ref
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if not f:
            return -1
        try:
            line = f.readline()
            if not line:
                return -1  # EOF
            if isinstance(sVar, Ref):
                sVar.set(line.rstrip('\n\r'))
            return 0
        except Exception:
            interp._last_error = 1
            return -1

    def FileWrite(hFile, sData):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if f:
            try:
                f.write(interp.to_str(_unwrap(sData)))
            except Exception:
                pass

    def FileWriteLn(hFile, sData):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if f:
            try:
                f.write(interp.to_str(_unwrap(sData)) + '\n')
            except Exception:
                pass

    def FileEof(hFile):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if not f:
            return 1
        pos = f.tell()
        ch = f.read(1)
        if not ch:
            return 1
        f.seek(pos)
        return 0

    def FileSeek(hFile, nPos):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if f:
            try:
                f.seek(interp.to_int(_unwrap(nPos)))
            except Exception:
                pass

    def FileTell(hFile):
        h = interp.to_int(_unwrap(hFile))
        f = _handles.get(h)
        if f:
            try:
                return f.tell()
            except Exception:
                pass
        return 0

    def FileGetPos(hFile):
        return FileTell(hFile)

    def FileExists(sFile):
        return 1 if os.path.isfile(interp.to_str(_unwrap(sFile))) else 0

    def FileDelete(sFile):
        try:
            os.remove(interp.to_str(_unwrap(sFile)))
            return 0
        except Exception:
            return -1

    def FileRename(sOld, sNew):
        try:
            os.rename(interp.to_str(_unwrap(sOld)), interp.to_str(_unwrap(sNew)))
            return 0
        except Exception:
            return -1

    def FileCopy(sSrc, sDest):
        try:
            shutil.copy2(interp.to_str(_unwrap(sSrc)), interp.to_str(_unwrap(sDest)))
            return 0
        except Exception:
            return -1

    def FileSize(sFile):
        try:
            return os.path.getsize(interp.to_str(_unwrap(sFile)))
        except Exception:
            return -1

    def DirCreate(sPath):
        try:
            os.makedirs(interp.to_str(_unwrap(sPath)), exist_ok=True)
            return 0
        except Exception:
            return -1

    def DirDelete(sPath):
        try:
            shutil.rmtree(interp.to_str(_unwrap(sPath)))
            return 0
        except Exception:
            return -1

    def DirExists(sPath):
        return 1 if os.path.isdir(interp.to_str(_unwrap(sPath))) else 0

    def DirFindFirst(sPattern, nAttr=0):
        pattern = interp.to_str(_unwrap(sPattern))
        matches = _glob_mod.glob(pattern)
        _dir_iter[0] = iter(matches)
        return next(_dir_iter[0], "")

    def DirFindNext():
        if _dir_iter[0]:
            return next(_dir_iter[0], "")
        return ""

    fns = {
        'fileopen': FileOpen,
        'fileclose': FileClose,
        'fileread': FileRead,
        'filewrite': FileWrite,
        'filewriteln': FileWriteLn,
        'fileeof': FileEof,
        'fileseek': FileSeek,
        'filetell': FileTell,
        'filegetpos': FileGetPos,
        'fileexists': FileExists,
        'filedelete': FileDelete,
        'filerename': FileRename,
        'filecopy': FileCopy,
        'filesize': FileSize,
        'dircreate': DirCreate,
        'dirdelete': DirDelete,
        'direxists': DirExists,
        'dirfindfirst': DirFindFirst,
        'dirfindnext': DirFindNext,
    }
    registry.update(fns)
