"""CiCode task/threading built-in functions."""
import time
import threading
import sys


def register(registry, interp):
    _tasks = {}
    _next_handle = [1]

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def TaskNew(sFuncName, sArgs='', nMode=0):
        fname = interp.to_str(_unwrap(sFuncName))
        args_str = interp.to_str(_unwrap(sArgs))
        h = _next_handle[0]
        _next_handle[0] += 1

        def run():
            try:
                interp.call_function(fname, [args_str] if args_str else [])
            except Exception as e:
                print(f"Task error in {fname}: {e}", file=sys.stderr)

        t = threading.Thread(target=run, daemon=True)
        _tasks[h] = t
        t.start()
        return h

    def TaskKill(hTask):
        h = interp.to_int(_unwrap(hTask))
        _tasks.pop(h, None)

    def TaskSuspend(nMs):
        time.sleep(interp.to_int(_unwrap(nMs)) / 1000.0)

    def Sleep_(nSec):
        time.sleep(interp.to_real(_unwrap(nSec)))

    def SleepMS(nMs):
        time.sleep(interp.to_int(_unwrap(nMs)) / 1000.0)

    def Halt():
        from interpreter import HaltException
        raise HaltException()

    def TaskIsRunning(hTask):
        h = interp.to_int(_unwrap(hTask))
        t = _tasks.get(h)
        return 1 if (t and t.is_alive()) else 0

    fns = {
        'tasknew': TaskNew,
        'taskkill': TaskKill,
        'tasksuspend': TaskSuspend,
        'sleep': Sleep_,
        'sleepms': SleepMS,
        'halt': Halt,
        'taskisrunning': TaskIsRunning,
    }
    registry.update(fns)
