"""CiCode time/date built-in functions."""
import time as _time
from datetime import datetime, date, timedelta


def register(registry, interp):
    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def Time_():
        now = datetime.now()
        return now.hour * 3600 + now.minute * 60 + now.second

    def Date_():
        now = datetime.now()
        return now.year * 10000 + now.month * 100 + now.day

    def TimeCurrent():
        return int(_time.time())

    def SysTime():
        return int(_time.time())

    def TimeToStr(t, fmt=None):
        t = interp.to_int(_unwrap(t))
        h, m, s = t // 3600, (t % 3600) // 60, t % 60
        if fmt is None:
            return f"{h:02d}:{m:02d}:{s:02d}"
        fmt_str = interp.to_str(_unwrap(fmt))
        fmt_str = fmt_str.replace('hh', f'{h:02d}')
        fmt_str = fmt_str.replace('mm', f'{m:02d}')
        fmt_str = fmt_str.replace('ss', f'{s:02d}')
        return fmt_str

    def TimeHour(t):
        return interp.to_int(_unwrap(t)) // 3600

    def TimeMin(t):
        return (interp.to_int(_unwrap(t)) % 3600) // 60

    def TimeSec(t):
        return interp.to_int(_unwrap(t)) % 60

    def DateDay(d):
        return interp.to_int(_unwrap(d)) % 100

    def DateMonth(d):
        return (interp.to_int(_unwrap(d)) // 100) % 100

    def DateYear(d):
        return interp.to_int(_unwrap(d)) // 10000

    def DateWeekDay(d):
        d = interp.to_int(_unwrap(d))
        year, month, day = d // 10000, (d // 100) % 100, d % 100
        try:
            return date(year, month, day).weekday() + 1
        except Exception:
            return 0

    def TimeMidNight():
        now = datetime.now()
        return now.hour * 3600 + now.minute * 60 + now.second

    def DateSub(d1, d2):
        d1, d2 = interp.to_int(_unwrap(d1)), interp.to_int(_unwrap(d2))

        def to_date(d):
            return date(d // 10000, (d // 100) % 100, d % 100)

        try:
            return (to_date(d1) - to_date(d2)).days
        except Exception:
            return 0

    def DateAdd(d, n):
        d, n = interp.to_int(_unwrap(d)), interp.to_int(_unwrap(n))
        try:
            dt = date(d // 10000, (d // 100) % 100, d % 100) + timedelta(days=n)
            return dt.year * 10000 + dt.month * 100 + dt.day
        except Exception:
            return d

    def TimestampCurrent():
        return int(_time.time() * 1e9)

    def TimestampToStr(ts, fmt=None):
        ts_val = interp.to_int(_unwrap(ts)) / 1e9
        try:
            dt = datetime.fromtimestamp(ts_val)
        except Exception:
            return ""
        if fmt:
            return dt.strftime(interp.to_str(_unwrap(fmt)))
        return dt.isoformat()

    def StrToDate(s, fmt=None):
        s = interp.to_str(_unwrap(s))
        fmt_str = interp.to_str(_unwrap(fmt)) if fmt is not None else "%Y-%m-%d"
        try:
            dt = datetime.strptime(s.strip(), fmt_str)
            return dt.year * 10000 + dt.month * 100 + dt.day
        except Exception:
            return 0

    def StrToTime(s, fmt=None):
        s = interp.to_str(_unwrap(s))
        fmt_str = interp.to_str(_unwrap(fmt)) if fmt is not None else "%H:%M:%S"
        try:
            dt = datetime.strptime(s.strip(), fmt_str)
            return dt.hour * 3600 + dt.minute * 60 + dt.second
        except Exception:
            return 0

    def DateToStr(d, fmt=None):
        d = interp.to_int(_unwrap(d))
        year, month, day = d // 10000, (d // 100) % 100, d % 100
        try:
            dt = date(year, month, day)
            if fmt:
                return dt.strftime(interp.to_str(_unwrap(fmt)))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return ""

    fns = {
        'time': Time_,
        'date': Date_,
        'timecurrent': TimeCurrent,
        'systime': SysTime,
        'timetostr': TimeToStr,
        'timehour': TimeHour,
        'timemin': TimeMin,
        'timesec': TimeSec,
        'dateday': DateDay,
        'datemonth': DateMonth,
        'dateyear': DateYear,
        'dateweekday': DateWeekDay,
        'timemidnight': TimeMidNight,
        'datesub': DateSub,
        'dateadd': DateAdd,
        'timestampcurrent': TimestampCurrent,
        'timestamptostr': TimestampToStr,
        'strtodate': StrToDate,
        'strtotime': StrToTime,
        'datetostr': DateToStr,
    }
    registry.update(fns)
