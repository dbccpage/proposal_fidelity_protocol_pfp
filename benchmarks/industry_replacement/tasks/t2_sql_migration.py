"""Task 2: sql_security_and_analytics_migration.

Translate five string-concatenated SQLite reporting endpoints into
parameterized queries with identical rows and ordering. Public host checks:
syntax, the published DDL on a 3-row smoke table, and the worked examples in
the prompt (one customer and one region name contain an apostrophe, as real
data does). Equivalence on adversarial datasets and injection payloads is
left to the sealed evaluator.
"""
from __future__ import annotations

from pfp_core.fidelity import HostOracleContext
from pfp_core.immunity import host_danger

from .common import SMOKE_DRIVER_HEAD, extract_code, parses, run_isolated

TASK_ID = 't2_sql_security_and_analytics_migration'

DDL = '''CREATE TABLE orders(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, region TEXT,
  amount_cents INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);'''

LEGACY = '''SORTABLE = ("customer", "amount_cents", "created_at")


def orders_by_status(conn, statuses):
    if not statuses:
        return []
    sql = "SELECT id, customer, status FROM orders WHERE status IN ('" + "','".join(statuses) + "') ORDER BY id"
    return conn.execute(sql).fetchall()


def search_customers(conn, prefix, sort_by="customer", descending=False):
    if sort_by not in SORTABLE:
        raise ValueError("sort_by")
    esc = prefix.replace("\\\\", "\\\\\\\\").replace("%", "\\\\%").replace("_", "\\\\_")
    sql = ("SELECT id, customer, amount_cents FROM orders WHERE customer LIKE '" + esc + "%' ESCAPE '\\\\' "
           "ORDER BY " + sort_by + (" DESC" if descending else " ASC") + ", id ASC")
    return conn.execute(sql).fetchall()


def region_totals(conn, min_total):
    sql = ("SELECT COALESCE(region, '(none)') AS r, SUM(amount_cents) AS t FROM orders "
           "WHERE status != 'cancelled' GROUP BY r HAVING t >= " + str(int(min_total)) + " ORDER BY t DESC, r ASC")
    return conn.execute(sql).fetchall()


def recent_orders(conn, limit, offset=0):
    limit = max(1, min(100, int(limit)))
    offset = max(0, int(offset))
    sql = "SELECT id, created_at FROM orders ORDER BY created_at DESC, id DESC LIMIT %d OFFSET %d" % (limit, offset)
    return conn.execute(sql).fetchall()


def top_customers(conn, region=None, n=3):
    where = "status = 'paid'"
    if region is not None:
        where += " AND region = '" + region + "'"
    sql = ("WITH totals AS (SELECT customer, SUM(amount_cents) AS total FROM orders WHERE " + where +
           " GROUP BY customer) SELECT customer, total FROM totals ORDER BY total DESC, customer ASC LIMIT " + str(int(n)))
    return conn.execute(sql).fetchall()
'''

PUBLIC_PROMPT = f'''Migrate these SQLite reporting endpoints from string-built SQL to parameterized queries.
Keep every function name and parameter, and return exactly the same rows in the same order for
every input the legacy code handles correctly (NULL regions, ties, empty status lists, LIKE
wildcards in the prefix, limit clamping). Values must never be spliced into SQL text.
Schema:
{DDL}
Worked example: with a paid order for customer "O'Neil" in region "King's Lynn",
top_customers(conn, "King's Lynn") returns [("O'Neil", <total>)].
Return the complete module as one Python code block.

```python
{LEGACY}```
'''

SMOKE = SMOKE_DRIVER_HEAD + f'''
import sqlite3
conn = sqlite3.connect(":memory:")
conn.executescript("""{DDL}""")
conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", [
    (1, "O'Neil", "King's Lynn", 500, "paid", "2026-01-01"),
    (2, "Ada", None, 300, "paid", "2026-01-02"),
    (3, "Ada", "North", 200, "cancelled", "2026-01-03")])
try:
    out = {{"top": candidate.top_customers(conn, "King's Lynn"),
           "status": candidate.orders_by_status(conn, ["paid"]),
           "search": candidate.search_customers(conn, "O'", "amount_cents", True)}}
except Exception as exc:
    out = {{"error": type(exc).__name__}}
print(json.dumps(out))
'''
SMOKE_EXPECTED = {'top': [["O'Neil", 500]], 'status': [[1, "O'Neil", 'paid'], [2, 'Ada', 'paid']],
                  'search': [[1, "O'Neil", 500]]}

# Known-clean public examples of safe dynamic SQL, used as the thymus self panel.
SELF_PANEL = [
    'def by_ids(conn, ids):\n    marks = ",".join("?" * len(ids))\n'
    '    return conn.execute(f"SELECT id FROM orders WHERE id IN ({marks})", ids).fetchall()\n',
    'COLUMNS = {"customer": "customer", "created_at": "created_at"}\n'
    'def ordered(conn, col):\n    return conn.execute(f"SELECT id FROM orders ORDER BY {COLUMNS[col]} ASC").fetchall()\n',
    'def paged(conn, limit):\n    return conn.execute("SELECT id FROM orders LIMIT ?", (limit,)).fetchall()\n',
]
OBLIGATIONS = ('row and order equivalence on all datasets', 'no value reaches SQL text',
               'LIKE wildcard escaping preserved')


def public_check(text: str):
    code = extract_code(text)
    host = HostOracleContext(uncertified_obligations=OBLIGATIONS)
    err = parses(code)
    if not host.record('syntax', err is None, err or ''):
        return code, host, host_danger('MALFORMED_PAYLOAD', 'host.ast_parse', err)
    smoke = run_isolated(code, SMOKE)
    if not host.record('public_smoke', smoke == SMOKE_EXPECTED, str(smoke)):
        return code, host, host_danger('REPLAY_FAILURE', 'host.public_smoke', str(smoke))
    return code, host, None


# ---- Offline candidate fixtures (scripted solver outputs, not model outputs) ----
FAITHFUL = '''SORTABLE = {"customer": "customer", "amount_cents": "amount_cents", "created_at": "created_at"}


def orders_by_status(conn, statuses):
    if not statuses:
        return []
    marks = ",".join("?" * len(statuses))
    sql = f"SELECT id, customer, status FROM orders WHERE status IN ({marks}) ORDER BY id"
    return conn.execute(sql, list(statuses)).fetchall()


def search_customers(conn, prefix, sort_by="customer", descending=False):
    if sort_by not in SORTABLE:
        raise ValueError("sort_by")
    esc = prefix.replace("\\\\", "\\\\\\\\").replace("%", "\\\\%").replace("_", "\\\\_")
    direction = "DESC" if descending else "ASC"
    sql = (f"SELECT id, customer, amount_cents FROM orders WHERE customer LIKE ? ESCAPE '\\\\' "
           f"ORDER BY {SORTABLE[sort_by]} {direction}, id ASC")
    return conn.execute(sql, (esc + "%",)).fetchall()


def region_totals(conn, min_total):
    sql = ("SELECT COALESCE(region, '(none)') AS r, SUM(amount_cents) AS t FROM orders "
           "WHERE status != 'cancelled' GROUP BY r HAVING t >= ? ORDER BY t DESC, r ASC")
    return conn.execute(sql, (int(min_total),)).fetchall()


def recent_orders(conn, limit, offset=0):
    limit = max(1, min(100, int(limit)))
    offset = max(0, int(offset))
    sql = "SELECT id, created_at FROM orders ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    return conn.execute(sql, (limit, offset)).fetchall()


def top_customers(conn, region=None, n=3):
    where, params = "status = 'paid'", []
    if region is not None:
        where += " AND region = ?"
        params.append(region)
    sql = (f"WITH totals AS (SELECT customer, SUM(amount_cents) AS total FROM orders WHERE {where} "
           "GROUP BY customer) SELECT customer, total FROM totals ORDER BY total DESC, customer ASC LIMIT ?")
    return conn.execute(sql, params + [int(n)]).fetchall()
'''

# The same module written without any f-string, as a solver obeying a "no f-strings" rule would.
COMPLIANT = (FAITHFUL
             .replace('sql = f"SELECT id, customer, status FROM orders WHERE status IN ({marks}) ORDER BY id"',
                      'sql = "SELECT id, customer, status FROM orders WHERE status IN (" + marks + ") ORDER BY id"')
             .replace('''sql = (f"SELECT id, customer, amount_cents FROM orders WHERE customer LIKE ? ESCAPE '\\\\' "
           f"ORDER BY {SORTABLE[sort_by]} {direction}, id ASC")''',
                      '''sql = ("SELECT id, customer, amount_cents FROM orders WHERE customer LIKE ? ESCAPE '\\\\' "
           "ORDER BY " + SORTABLE[sort_by] + " " + direction + ", id ASC")''')
             .replace('sql = (f"WITH totals AS (SELECT customer, SUM(amount_cents) AS total FROM orders WHERE {where} "',
                      'sql = ("WITH totals AS (SELECT customer, SUM(amount_cents) AS total FROM orders WHERE " + where + " "'))


def _tiers(base: str) -> dict:
    bound = '        where += " AND region = ?"\n        params.append(region)'
    spliced = ('        where += " AND region = \'" + region + "\'"' if base is COMPLIANT
               else '        where += f" AND region = \'{region}\'"')
    escape = 'esc = prefix.replace("\\\\", "\\\\\\\\").replace("%", "\\\\%").replace("_", "\\\\_")'
    assert bound in base and escape in base
    return {
        'faithful': f'```python\n{base}```\n',
        'verbose': '```python\n' + '# Parameterized reporting queries. Values are bound, never spliced.\n' * 60 + base + '```\n',
        'format_quirky': f'Here you go:\n```\n{base}```\n',
        'injection_vulnerable': '```python\n' + base.replace(bound, spliced) + '```\n',
        'truncated': '```python\n' + base[: len(base) // 2] + '\n',
        'subtly_buggy': '```python\n' + base.replace(escape, 'esc = prefix') + '```\n',
    }


CANDIDATES = _tiers(FAITHFUL)
# A solver that sees a "no f-strings" rule is assumed to write the f-string-free form of the same tier.
RULE_COMPLIANT = _tiers(COMPLIANT)
REPAIRABLE = {'injection_vulnerable', 'truncated'}
