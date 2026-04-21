"""CiCode SQL built-in functions — uses pymssql (preferred) with pyodbc fallback."""
import re


def _parse_connect_string(s):
    """Parse an ODBC connection string into a dict."""
    params = {}
    for part in re.split(r';', s):
        part = part.strip()
        if '=' in part:
            k, v = part.split('=', 1)
            params[k.strip().lower()] = v.strip()
    return params


def register(registry, interp):
    _handles = {}
    _next_handle = [1]
    _last_error = ['']

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def _get_ctx(h):
        return _handles.get(interp.to_int(_unwrap(h)))

    # Try pymssql first (no system ODBC driver needed, works with older SQL Server)
    try:
        import pymssql
        has_pymssql = True
    except ImportError:
        has_pymssql = False

    try:
        import pyodbc
        has_pyodbc = True
    except ImportError:
        has_pyodbc = False

    def SQLConnect(sConnect):
        sConnect = interp.to_str(_unwrap(sConnect))
        p = _parse_connect_string(sConnect)
        server   = p.get('server', p.get('data source', 'localhost'))
        database = p.get('database', p.get('initial catalog', ''))
        user     = p.get('uid', p.get('user id', 'sa'))
        password = p.get('pwd', p.get('password', ''))

        if has_pymssql:
            try:
                conn = pymssql.connect(
                    server=server, user=user, password=password,
                    database=database, login_timeout=10, tds_version='7.0'
                )
                h = _next_handle[0]
                _next_handle[0] += 1
                _handles[h] = {
                    'conn': conn, 'cursor': None,
                    'rows': [], 'current_row': -1, 'fields': []
                }
                _last_error[0] = ''
                interp._last_error = 0
                return h
            except Exception as e:
                _last_error[0] = str(e)
                interp._last_error = 1
                interp._last_error_msg = str(e)
                return -1
        elif has_pyodbc:
            import pyodbc as odbc
            sConnect = sConnect.replace(
                'driver={SQL Server}', 'driver={ODBC Driver 18 for SQL Server}'
            ).replace(
                'Driver={SQL Server}', 'Driver={ODBC Driver 18 for SQL Server}'
            )
            sConnect = re.sub(r'Encrypt=[^;]+;?', '', sConnect, flags=re.IGNORECASE)
            sConnect = re.sub(r'TrustServerCertificate=[^;]+;?', '', sConnect, flags=re.IGNORECASE)
            sConnect = sConnect.rstrip(';') + ';Encrypt=no;TrustServerCertificate=yes;'
            try:
                conn = odbc.connect(sConnect, timeout=10)
                h = _next_handle[0]
                _next_handle[0] += 1
                _handles[h] = {
                    'conn': conn, 'cursor': None,
                    'rows': [], 'current_row': -1, 'fields': []
                }
                _last_error[0] = ''
                interp._last_error = 0
                return h
            except Exception as e:
                _last_error[0] = str(e)
                interp._last_error = 1
                interp._last_error_msg = str(e)
                return -1
        else:
            _last_error[0] = "No SQL driver available (install pymssql or pyodbc)"
            interp._last_error = 1
            interp._last_error_msg = _last_error[0]
            return -1

    def SQLDisconnect(hSQL):
        h = interp.to_int(_unwrap(hSQL))
        ctx = _handles.pop(h, None)
        if ctx:
            try:
                ctx['conn'].close()
            except Exception:
                pass

    def SQLExec(hSQL, sQuery):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return -1
        sQuery = interp.to_str(_unwrap(sQuery))
        try:
            cursor = ctx['conn'].cursor()
            cursor.execute(sQuery)
            ctx['cursor'] = cursor
            try:
                ctx['rows'] = cursor.fetchall()
                ctx['fields'] = (
                    [col[0] for col in cursor.description]
                    if cursor.description else []
                )
            except Exception:
                ctx['rows'] = []
                ctx['fields'] = []
            ctx['current_row'] = -1
            _last_error[0] = ''
            interp._last_error = 0
            return 0
        except Exception as e:
            _last_error[0] = str(e)
            interp._last_error = 1
            interp._last_error_msg = str(e)
            return -1

    def SQLNext(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return 1
        ctx['current_row'] += 1
        return 0 if ctx['current_row'] < len(ctx['rows']) else 1

    def SQLGetField(hSQL, sField):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return ''
        sField = interp.to_str(_unwrap(sField))
        row_idx = ctx['current_row']
        if row_idx < 0 or row_idx >= len(ctx['rows']):
            return ''
        row = ctx['rows'][row_idx]
        field_lower = sField.lower()
        for i, fname in enumerate(ctx['fields']):
            if fname.lower() == field_lower:
                val = row[i]
                return interp.to_str(val) if val is not None else ''
        return ''

    def SQLEnd(hSQL):
        ctx = _get_ctx(hSQL)
        if ctx:
            ctx['rows'] = []
            ctx['current_row'] = -1
            if ctx.get('cursor'):
                try:
                    ctx['cursor'].close()
                except Exception:
                    pass
                ctx['cursor'] = None

    def SQLErrMsg(*args):
        return _last_error[0]

    def SQLBeginTran(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return -1
        try:
            ctx['conn'].autocommit = False
            return 0
        except Exception as e:
            _last_error[0] = str(e)
            return -1

    def SQLCommit(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return -1
        try:
            ctx['conn'].commit()
            return 0
        except Exception as e:
            _last_error[0] = str(e)
            return -1

    def SQLRollback(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return -1
        try:
            ctx['conn'].rollback()
            return 0
        except Exception as e:
            _last_error[0] = str(e)
            return -1

    def SQLNumChange(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return 0
        try:
            return ctx['cursor'].rowcount if ctx.get('cursor') else 0
        except Exception:
            return 0

    def SQLCreate(sConnect):
        return SQLConnect(sConnect)

    def SQLFirst(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return 1
        if ctx['rows']:
            ctx['current_row'] = 0
            return 0
        return 1

    def SQLLast(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return 1
        if ctx['rows']:
            ctx['current_row'] = len(ctx['rows']) - 1
            return 0
        return 1

    def SQLPrev(hSQL):
        ctx = _get_ctx(hSQL)
        if not ctx:
            return 1
        if ctx['current_row'] > 0:
            ctx['current_row'] -= 1
            return 0
        return 1

    def SQLCurr(hSQL):
        ctx = _get_ctx(hSQL)
        return ctx['current_row'] if ctx else -1

    def SQLCall(hSQL, sProc, sParams=''):
        return SQLExec(hSQL, f"EXEC {interp.to_str(_unwrap(sProc))} {interp.to_str(_unwrap(sParams))}")

    def SQLAppend(hSQL):
        return 0

    def SQLDelete(hSQL):
        return 0

    def SQLUpdate(hSQL, sField, sValue):
        return 0

    def SQLSetParam(hSQL, nParam, sValue):
        pass

    def SQLGetParam(hSQL, nParam):
        return ''

    def SQLTraceOn():
        pass

    def SQLTraceOff():
        pass

    fns = {
        'sqlconnect': SQLConnect,
        'sqldisconnect': SQLDisconnect,
        'sqlexec': SQLExec,
        'sqlnext': SQLNext,
        'sqlgetfield': SQLGetField,
        'sqlend': SQLEnd,
        'sqlerrmsg': SQLErrMsg,
        'sqlbegintran': SQLBeginTran,
        'sqlcommit': SQLCommit,
        'sqlrollback': SQLRollback,
        'sqlnumchange': SQLNumChange,
        'sqlcreate': SQLCreate,
        'sqlfirst': SQLFirst,
        'sqllast': SQLLast,
        'sqlprev': SQLPrev,
        'sqlcurr': SQLCurr,
        'sqlcall': SQLCall,
        'sqlappend': SQLAppend,
        'sqldelete': SQLDelete,
        'sqlupdate': SQLUpdate,
        'sqlsetparam': SQLSetParam,
        'sqlgetparam': SQLGetParam,
        'sqltraceon': SQLTraceOn,
        'sqltraceoff': SQLTraceOff,
    }
    registry.update(fns)
