# SQL & Database Test Construction Reference

## 1. Required Database Test Patterns

When a production surface touches a database (PostgreSQL, SQLite, SQL Server, DuckDB), the builder must construct tests satisfying these criteria:

### 1. Transactional Isolation

Every mutating test runs inside a transaction that rolls back (or an equivalent isolated schema / tempfile container). Shared mutable DB state across tests is strictly forbidden.

### 2. Constraint Rejection Matrix (Landau Class 2)

For every `UNIQUE`, `FOREIGN KEY`, `CHECK`, or `NOT NULL` constraint the schema declares, write a negative test asserting the exact error code or domain exception upon violation.

### 3. Migration Round-Trip

Execute `up → down → up` migration cycles, then assert data integrity and clean schema reconstruction after the cycle.

### 4. SQL Injection Negative

Where dynamic or raw SQL queries exist, pass malicious injection payloads through the parameterized query builder and assert safe escaping or rejection.

### 5. Concurrent Conflict & Lock Contention

When the story claims concurrency safety on constrained tables, simulate colliding writers; assert that transactions serialize cleanly or fail with explicit retryable error envelopes, never silent corruption.

### 6. Query Count / N+1 Budget

When an execution query budget is claimed, assert an upper bound on the number of statements executed during the operation.

---

## 2. Landau Class 1 SQL Examples

- **Conservation Identity:** Total row count (or balance sum) is invariant across a rolled-back transaction.
- **Exactness:** A `CHECK` constraint rejects every value outside its predicate and accepts every value inside it (property over generated domain).
