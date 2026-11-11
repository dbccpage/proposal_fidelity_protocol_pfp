"""Sealed equivalence and injection tests for task 2 (isolated, post-freeze)."""
import random
import sqlite3

import candidate as m

PUBLIC_CONTRACT_TOKENS = {100, 'DESC', ':memory:', 'customer', 'amount_cents', 'created_at', 'paid', 'cancelled', 'status',
                          'region', 'orders', 'sort_by', '(none)'}

DDL = ('CREATE TABLE orders(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, region TEXT, '
       'amount_cents INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);')


def _db(rows):
    conn = sqlite3.connect(':memory:')
    conn.executescript(DDL)
    conn.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)', rows)
    return conn


def _dataset(seed):
    rng = random.Random(seed)
    names = ['Ann', 'ann', 'Bo_b', 'Bob', '100%Co', 'Zed', "D'Arcy", 'a\\b']
    regions = [None, 'East', 'West', "Saint John's", '']
    statuses = ['paid', 'cancelled', 'pending', 'voided']
    return [(i, rng.choice(names), rng.choice(regions), rng.choice([0, 100, 100, 250, 999]),
             rng.choice(statuses), f'2026-0{rng.randint(1, 3)}-1{rng.randint(0, 2)}') for i in range(1, 30)]


DATASETS = [[]] + [_dataset(s) for s in (11, 12, 13, 14, 15, 16, 17)]


# ---- independent reference queries ----
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


def _all_equal(ref, fn, argsets):
    for rows in DATASETS:
        c = _db(rows)
        for args in argsets:
            assert [tuple(r) for r in fn(c, *args)] == ref(c, *args), (fn.__name__, args)


def test_status_lists_including_empty():
    _all_equal(r_status, m.orders_by_status, [([],), (['paid'],), (['paid', 'pending'],), (['nope'],)])


def test_search_wildcards_case_and_sorting():
    sets = [(p, col, d) for p in ('a', 'Bo_', '100%', 'a\\', '') for col in ('customer', 'amount_cents', 'created_at')
            for d in (False, True)]
    _all_equal(r_search, m.search_customers, sets)


def test_region_totals_null_and_ties():
    _all_equal(r_totals, m.region_totals, [(0,), (200,), (10 ** 6,)])


def test_recent_clamping():
    _all_equal(r_recent, m.recent_orders, [(0, 0), (5, 2), (500, 0), (3, -4)])


def test_top_customers_regions():
    _all_equal(r_top, m.top_customers, [(None, 3), ('East', 2), ("Saint John's", 5), ('', 3), ('Nowhere', 3)])


def test_sort_injection_refused():
    c = _db(DATASETS[1])
    for bad in ('id; DROP TABLE orders', 'customer DESC --', 'amount_cents,(SELECT 1)'):
        try:
            m.search_customers(c, 'a', bad)
        except ValueError:
            continue
        raise AssertionError('unlisted sort column accepted')
    assert c.execute('SELECT COUNT(*) FROM orders').fetchone()[0] == 29


def test_value_injection_payloads_are_data():
    c = _db(DATASETS[2])
    for payload in ("x' OR '1'='1", "'; DELETE FROM orders; --", "East' UNION SELECT 'pwn', 1 --"):
        assert [tuple(r) for r in m.top_customers(c, payload, 3)] == []
        assert [tuple(r) for r in m.search_customers(c, payload)] == []
        assert [tuple(r) for r in m.orders_by_status(c, [payload])] == []
    assert c.execute('SELECT COUNT(*) FROM orders').fetchone()[0] == 29
