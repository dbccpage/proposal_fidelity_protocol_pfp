"""Sealed equivalence and injection scenarios for task 2. Judged in the parent after freeze.

Expected rows come from independent reference queries run here, in the
parent; the child only receives datasets and calls.
"""
import random
import sqlite3

from .scenario import ANY, call, make, ok, raises, ref

PUBLIC_CONTRACT_TOKENS = {100, 'DESC', ':memory:', 'customer', 'amount_cents', 'created_at', 'paid', 'cancelled',
                          'status', 'region', 'orders', 'sort_by', '(none)', 'orders_by_status', 'search_customers',
                          'region_totals', 'recent_orders', 'top_customers', 'ValueError'}

DDL = ('CREATE TABLE orders(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, region TEXT, '
       'amount_cents INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);')


def _dataset(seed):
    rng = random.Random(seed)
    names = ['Ann', 'ann', 'Bo_b', 'Bob', '100%Co', 'Zed', "D'Arcy", 'a\\b']
    regions = [None, 'East', 'West', "Saint John's", '']
    statuses = ['paid', 'cancelled', 'pending', 'voided']
    return [[i, rng.choice(names), rng.choice(regions), rng.choice([0, 100, 100, 250, 999]),
             rng.choice(statuses), f'2026-0{rng.randint(1, 3)}-1{rng.randint(0, 2)}'] for i in range(1, 30)]


DATASETS = [[]] + [_dataset(s) for s in (11, 12, 13, 14, 15, 16, 17)]


def _db(rows):
    conn = sqlite3.connect(':memory:')
    conn.executescript(DDL)
    conn.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)', rows)
    return conn


# ---- independent reference queries (parent side) ----
def r_status(c, st):
    if not st:
        return []
    return c.execute('SELECT id, customer, status FROM orders WHERE status IN (%s) ORDER BY id'
                     % ','.join('?' * len(st)), st).fetchall()


def r_search(c, prefix, col, desc):
    pat = prefix.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    return c.execute('SELECT id, customer, amount_cents FROM orders WHERE customer LIKE ? ESCAPE ? '
                     'ORDER BY %s %s, id ASC' % (col, 'DESC' if desc else 'ASC'), (pat, '\\')).fetchall()


def r_totals(c, k):
    return c.execute("SELECT COALESCE(region, '(none)') r, SUM(amount_cents) t FROM orders WHERE status != "
                     "'cancelled' GROUP BY r HAVING t >= ? ORDER BY t DESC, r ASC", (int(k),)).fetchall()


def r_recent(c, limit, offset):
    return c.execute('SELECT id, created_at FROM orders ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?',
                     (max(1, min(100, int(limit))), max(0, int(offset)))).fetchall()


def r_top(c, region, n):
    extra, params = ('', []) if region is None else (' AND region = ?', [region])
    return c.execute("WITH t AS (SELECT customer, SUM(amount_cents) total FROM orders WHERE status = 'paid'"
                     + extra + ' GROUP BY customer) SELECT customer, total FROM t ORDER BY total DESC, customer ASC '
                     'LIMIT ?', params + [int(n)]).fetchall()


def _rows(result):
    return ok([list(r) for r in result])


def _equivalence(fn_name, ref_fn, argsets):
    steps = []
    for rows in DATASETS:
        conn = _db(rows)
        steps.append((make('db', 'c', rows=rows), ANY))
        for args in argsets:
            steps.append((call(fn_name, ref('c'), *args), _rows(ref_fn(conn, *args))))
    return steps


C = ref('c')
SCENARIOS = {
    'status_lists_including_empty': _equivalence('orders_by_status', r_status,
                                                 [([],), (['paid'],), (['paid', 'pending'],), (['nope'],)]),
    'search_wildcards_case_and_sorting': _equivalence(
        'search_customers', r_search, [(p, col, d) for p in ('a', 'Bo_', '100%', 'a\\', '')
                                       for col in ('customer', 'amount_cents', 'created_at') for d in (False, True)]),
    'region_totals_null_and_ties': _equivalence('region_totals', r_totals, [(0,), (200,), (10 ** 6,)]),
    'recent_clamping': _equivalence('recent_orders', r_recent, [(0, 0), (5, 2), (500, 0), (3, -4)]),
    'top_customers_regions': _equivalence('top_customers', r_top, [(None, 3), ('East', 2), ("Saint John's", 5),
                                                                   ('', 3), ('Nowhere', 3)]),
    'sort_injection_refused': [(make('db', 'c', rows=DATASETS[1]), ANY)] + [
        (call('search_customers', C, 'a', bad), raises('ValueError'))
        for bad in ('id; DROP TABLE orders', 'customer DESC --', 'amount_cents,(SELECT 1)')] + [
        (make('count', 'n', db='c'), ok(29))],
    'value_injection_payloads_are_data': [(make('db', 'c', rows=DATASETS[2]), ANY)] + [
        step for payload in ("x' OR '1'='1", "'; DELETE FROM orders; --", "East' UNION SELECT 'pwn', 1 --")
        for step in ((call('top_customers', C, payload, 3), ok([])), (call('search_customers', C, payload), ok([])),
                     (call('orders_by_status', C, [payload]), ok([])))] + [(make('count', 'n', db='c'), ok(29))],
}
