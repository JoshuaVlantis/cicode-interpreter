"""Stub implementations for SCADA-only CiCode functions."""
import sys


def register(registry, interp):
    warned = set()

    def make_stub(name):
        def stub(*args, **kwargs):
            if name not in warned:
                print(f"[STUB] {name}() - SCADA runtime required", file=sys.stderr)
                warned.add(name)
            return 0

        stub.__name__ = name
        return stub

    stub_names = [
        # Tag functions
        'tagread', 'tagwrite', 'tagsubscribe', 'tagunsubscribe', 'taginfo',
        'taggetproperty', 'tagsetproperty', 'tagbrowse',
        # Alarm functions
        'alarmbrowse', 'alarmack', 'alarmdisable', 'alarmenable',
        'alarminfo', 'alarmcountlist', 'alarmactive', 'alarmunack',
        'alarmsum', 'alarmsetstate',
        # Trend functions
        'trendbrowse', 'trendread', 'trendwrite', 'trendinfo',
        # Report functions
        'reportcreate', 'reportprint', 'reportexport',
        # Device functions
        'devread', 'devwrite', 'devinfo',
        # Accumulator functions
        'acccontrol', 'accinfo',
        # Misc SCADA
        'serverinfo', 'iodevicestateget', 'iodevicecontrol',
        'kernelversion', 'kernelconfig',
        'winexec', 'wingetprofile', 'winsetprofile',
        'menucreate', 'menuitemcreate', 'menushow',
        'pagedisplay', 'pageinfo', 'pageopen', 'pagehardware',
        'giselectobj', 'giselall', 'gicopy',
        'dspangle', 'dspattr', 'dspbmp', 'dspcopy', 'dspgetangle',
        'controlopen', 'controlcreate',
        'plantscadainfo',
    ]

    for name in stub_names:
        if name not in registry:
            registry[name] = make_stub(name)
