"""CiCode miscellaneous built-in functions."""
import sys
import socket


def register(registry, interp):
    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def Message(sTitle, sText, nMode=0):
        title = interp.to_str(_unwrap(sTitle))
        text = interp.to_str(_unwrap(sText))
        nMode = interp.to_int(_unwrap(nMode))
        print(f"\n[{title}] {text}")
        buttons_map = {
            0: [("OK", 1)],
            1: [("OK", 1), ("Cancel", 2)],
            2: [("Abort", 3), ("Retry", 4), ("Ignore", 5)],
            3: [("Yes", 6), ("No", 7), ("Cancel", 2)],
        }
        btn_type = nMode & 3
        buttons = buttons_map.get(btn_type, [("OK", 1)])
        if len(buttons) == 1:
            try:
                input("Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                pass
            return buttons[0][1]
        else:
            prompt = "/".join(f"{i + 1}={b[0]}" for i, b in enumerate(buttons))
            try:
                choice = input(f"Choice ({prompt}): ").strip()
                try:
                    n = int(choice) - 1
                    if 0 <= n < len(buttons):
                        return buttons[n][1]
                except ValueError:
                    pass
            except (KeyboardInterrupt, EOFError):
                pass
            return buttons[-1][1]

    def Print_(sText):
        print(interp.to_str(_unwrap(sText)))

    def ErrLog(sText):
        print(interp.to_str(_unwrap(sText)), file=sys.stderr)

    def Trace(sText):
        print(f"[TRACE] {interp.to_str(_unwrap(sText))}", file=sys.stderr)

    def DebugMsg(sText):
        print(f"[DEBUG] {interp.to_str(_unwrap(sText))}", file=sys.stderr)

    def Assert(bCond, sMsg='Assertion failed'):
        if not interp.to_int(_unwrap(bCond)):
            msg = interp.to_str(_unwrap(sMsg))
            print(f"[ASSERT] {msg}", file=sys.stderr)

    def IsError():
        return 1 if interp._last_error else 0

    def ErrMsg(nCode=None):
        if nCode is None:
            return interp._last_error_msg
        return f"Error {interp.to_int(_unwrap(nCode))}"

    def ErrSet(nCode):
        interp._last_error = interp.to_int(_unwrap(nCode))

    def IsGateway():
        return 0

    def ServerName():
        try:
            return socket.gethostname()
        except Exception:
            return "localhost"

    def ClusterName():
        return "LocalCluster"

    def ComputerName():
        try:
            return socket.gethostname()
        except Exception:
            return "localhost"

    def ProjectInfo(sField):
        return ""

    def TypeInfo(sType):
        return ""

    def ObjectCallMethod(hObj, sMethod, *args):
        return 0

    def ObjectGetProperty(hObj, sProp):
        return ""

    def ObjectSetProperty(hObj, sProp, sValue):
        pass

    fns = {
        'message': Message,
        'print': Print_,
        'errlog': ErrLog,
        'trace': Trace,
        'debugmsg': DebugMsg,
        'assert': Assert,
        'iserror': IsError,
        'errmsg': ErrMsg,
        'errset': ErrSet,
        'isgateway': IsGateway,
        'servername': ServerName,
        'clustername': ClusterName,
        'computername': ComputerName,
        'projectinfo': ProjectInfo,
        'typeinfo': TypeInfo,
        'objectcallmethod': ObjectCallMethod,
        'objectgetproperty': ObjectGetProperty,
        'objectsetproperty': ObjectSetProperty,
    }
    registry.update(fns)
