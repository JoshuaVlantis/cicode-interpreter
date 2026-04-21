# SQL — Database Connectivity

## Connection Details

Store your credentials in helper functions in your `.ci` files — **never hardcode them as plain strings** and never commit them to source control. A typical pattern:

```cicode
STRING FUNCTION GetServer()     RETURN "YOUR_SERVER_IP"; END
STRING FUNCTION GetDatabase()   RETURN "YOUR_DATABASE";  END
STRING FUNCTION GetPassword()   RETURN "YOUR_PASSWORD";  END
```

---

## Why `pymssql` (not `pyodbc`)

The ODBC Driver 18 for SQL Server enforces TLS 1.2, which older SQL Server versions (2008–2014) do not support. `pymssql` uses **FreeTDS** which handles older TLS handshakes. The `tds_version='7.0'` parameter is required.

`pyodbc` is kept as a fallback in `sql_funcs.py` but will fail with older servers.

---

## CiCode SQL API

### Connection

```cicode
INT hSQL;
hSQL = SQLConnect("DRIVER={SQL Server};SERVER=" + GetServer() + ";Database=" + GetDatabase() + ";Uid=sa;Pwd=" + GetPassword() + ";");
IF IsError() THEN
    // handle error
END
```

### Query

```cicode
INT hRec;
hRec = SQLSelect(hSQL, "SELECT Code, Name FROM MyTable");
```

### Iterate Results

```cicode
WHILE SQLNext(hRec) = 0 DO
    sCode = SQLGetField(hRec, "Code");
    sName = SQLGetField(hRec, "Name");
END
SQLClose(hRec);
```

### Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 259 | End of recordset (EOF) — `SQLNext` returns this when no more rows |
| non-zero | Error |

---

## Implementation (`builtins/sql_funcs.py`)

### Connection String Parsing

CiCode uses ODBC-style connection strings. `sql_funcs.py` parses these into kwargs:

```python
# Input:  "DRIVER={SQL Server};SERVER=host;Database=db;Uid=user;Pwd=pass;"
# Output: {'server': 'host', 'database': 'db', 'user': 'user', 'password': 'pass'}
```

The `DRIVER={SQL Server}` token is recognised and used to select `pymssql`.

### Handle System

Both connections and recordsets use integer handles:
```python
_connections = {}   # hSQL → pymssql connection
_recordsets  = {}   # hRec → {'cursor': ..., 'row': ..., 'done': bool}
```

### SQLGetField

Returns the current row's value for the given column name (case-insensitive lookup).

### SQLExecute

Executes non-SELECT statements (INSERT, UPDATE, DELETE) and commits.

---

## Troubleshooting

**`Can't open lib 'SQL Server'`** — pyodbc trying to use Windows ODBC driver. Install `pymssql` and ensure it's the primary backend.

**`TLS error`** — pyodbc with ODBC Driver 18. Use `pymssql` instead.

**`Connection refused`** — check VPN/network connectivity to your SQL Server host.

**`Login failed`** — check credentials. `sa` account must be enabled on the SQL Server.

