PRAGMA foreign_keys = ON;

-- Relational Normal Forms Schema and BQNF Incremental Maintenance
-- AuthorityEffect: None.

-- ============================================================================
-- 1. 0NF to 1NF: Atomic Domain Normalization
-- ============================================================================

-- 0NF: Non-atomic repeated groups (CSV courses)
CREATE TABLE IF NOT EXISTS student_records_0nf (
    student_id INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL,
    course_list_csv TEXT NOT NULL -- Unparsed non-atomic string
);

-- 1NF: Decomposed into atomic rows with declared composite candidate key
-- Assumed FDs on this heading:
--   student_id -> student_name               (partial dependency on student_id)
--   course_code -> course_title              (partial dependency on course_code)
--   (student_id, course_code) -> instructor_id, instructor_office
--   instructor_id -> instructor_office       (transitive dependency)
CREATE TABLE IF NOT EXISTS student_enrollments_1nf (
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    course_code TEXT NOT NULL,
    course_title TEXT NOT NULL,
    instructor_id INTEGER NOT NULL,
    instructor_office TEXT NOT NULL,
    PRIMARY KEY (student_id, course_code)
);

-- ============================================================================
-- 2. 1NF to 2NF: Elimination of Partial Functional Dependencies
-- ============================================================================

-- 2NF separates BOTH partial dependencies:
--   1. student_id -> student_name
--   2. course_code -> course_title
-- leaving only full dependencies on the registration key (student_id, course_code).

CREATE TABLE IF NOT EXISTS students_2nf (
    student_id INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses_2nf (
    course_code TEXT PRIMARY KEY NOT NULL,
    course_title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_registrations_2nf (
    student_id INTEGER NOT NULL REFERENCES students_2nf(student_id),
    course_code TEXT NOT NULL REFERENCES courses_2nf(course_code),
    instructor_id INTEGER NOT NULL,
    instructor_office TEXT NOT NULL,
    PRIMARY KEY (student_id, course_code)
);

-- ============================================================================
-- 3. 2NF to 3NF & BCNF: Elimination of Transitive Dependencies
-- ============================================================================

-- In student_registrations_2nf, the transitive dependency:
--   instructor_id -> instructor_office
-- violates 3NF and BCNF because instructor_id is not a candidate key.
-- BCNF decomposes into relations where EVERY non-trivial determinant is a superkey:
-- We retain the declared dependency (student_id, course_code) -> instructor_id without
-- inventing an undeclared course_code -> instructor_id functional dependency.

CREATE TABLE IF NOT EXISTS instructors_bcnf (
    instructor_id INTEGER PRIMARY KEY,
    instructor_office TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_registrations_bcnf (
    student_id INTEGER NOT NULL REFERENCES students_2nf(student_id),
    course_code TEXT NOT NULL REFERENCES courses_2nf(course_code),
    instructor_id INTEGER NOT NULL REFERENCES instructors_bcnf(instructor_id),
    PRIMARY KEY (student_id, course_code)
);

-- ============================================================================
-- 4. 4NF: Elimination of Independent Multivalued Dependencies (MVDs)
-- ============================================================================

-- MVD: instructor_id ->> skill | language
-- 4NF Decomposition:
CREATE TABLE IF NOT EXISTS instructor_skills_4nf (
    instructor_id INTEGER NOT NULL REFERENCES instructors_bcnf(instructor_id),
    skill TEXT NOT NULL,
    PRIMARY KEY (instructor_id, skill)
);

CREATE TABLE IF NOT EXISTS instructor_languages_4nf (
    instructor_id INTEGER NOT NULL REFERENCES instructors_bcnf(instructor_id),
    language TEXT NOT NULL,
    PRIMARY KEY (instructor_id, language)
);

-- ============================================================================
-- 5. 5NF (PJNF) & SKNF: Project-Join Higher-Cell Integrity (Shell_2 vs Fill_2)
-- ============================================================================

-- 3-way cyclic relationship: Consultant (C), Company (Co), Product (P)
CREATE TABLE IF NOT EXISTS consulting_fill2 (
    consultant_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    PRIMARY KEY (consultant_id, company_id, product_id)
);

-- Binary projections:
CREATE VIEW IF NOT EXISTS proj_consultant_company AS
SELECT DISTINCT consultant_id, company_id FROM consulting_fill2;

CREATE VIEW IF NOT EXISTS proj_company_product AS
SELECT DISTINCT company_id, product_id FROM consulting_fill2;

CREATE VIEW IF NOT EXISTS proj_consultant_product AS
SELECT DISTINCT consultant_id, product_id FROM consulting_fill2;

-- Reconstructed boundary shell (Shell_2):
CREATE VIEW IF NOT EXISTS consulting_shell2 AS
SELECT 
    cc.consultant_id,
    cc.company_id,
    cp.product_id
FROM proj_consultant_company cc
JOIN proj_company_product cp ON cc.company_id = cp.company_id
JOIN proj_consultant_product prod 
  ON cc.consultant_id = prod.consultant_id 
 AND cp.product_id = prod.product_id;

-- NOTE: The shell-versus-fill query on one table body tests whether that specific body
-- satisfies the declared join dependency. It is NOT a schema-level 5NF membership test.
CREATE VIEW IF NOT EXISTS consulting_spurious_tuples AS
SELECT * FROM consulting_shell2
EXCEPT
SELECT * FROM consulting_fill2;

-- ----------------------------------------------------------------------------
-- 5NF Counterexample: Darwen, Date, Fagin (2012) Theorem 6.1
-- Schema R(A, B, C) with candidate keys (A,B), (A,C), (B,C)
-- and declared join dependency *[(A,B), (B,C), (A,C)].
-- Every component contains a candidate key, so this schema is in SKNF (5NFR).
-- However, candidate key constraints ALONE do not logically imply the join dependency!
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parity_counterexample_4tuple (
    a INTEGER NOT NULL,
    b INTEGER NOT NULL,
    c INTEGER NOT NULL,
    PRIMARY KEY (a, b, c),
    UNIQUE (a, b),
    UNIQUE (a, c),
    UNIQUE (b, c)
);

-- Four-tuple parity instance (even parity: a + b + c is even)
INSERT OR IGNORE INTO parity_counterexample_4tuple (a, b, c) VALUES
    (0, 0, 0),
    (0, 1, 1),
    (1, 0, 1),
    (1, 1, 0);

-- Pairwise binary projections:
CREATE VIEW IF NOT EXISTS proj_parity_ab AS SELECT DISTINCT a, b FROM parity_counterexample_4tuple;
CREATE VIEW IF NOT EXISTS proj_parity_bc AS SELECT DISTINCT b, c FROM parity_counterexample_4tuple;
CREATE VIEW IF NOT EXISTS proj_parity_ac AS SELECT DISTINCT a, c FROM parity_counterexample_4tuple;

-- Ternary join of the three projections (produces all 2^3 = 8 triples):
CREATE VIEW IF NOT EXISTS parity_joined AS
SELECT ab.a, ab.b, bc.c
FROM proj_parity_ab ab
JOIN proj_parity_bc bc ON ab.b = bc.b
JOIN proj_parity_ac ac ON ab.a = ac.a AND bc.c = ac.c;

-- Spurious tuples generated by the ternary join (exactly the 4 odd-parity tuples):
CREATE VIEW IF NOT EXISTS parity_spurious_tuples AS
SELECT * FROM parity_joined
EXCEPT
SELECT * FROM parity_counterexample_4tuple;

-- ============================================================================
-- 6. 6NF: Irreducible Binary Decomposition & Cross-Table Invariant View
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_names_6nf (
    student_id INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL
);

-- Note: REAL in SQLite represents IEEE-754 floating point (approximate numeric).
CREATE TABLE IF NOT EXISTS student_gpa_6nf (
    student_id INTEGER PRIMARY KEY,
    gpa REAL NOT NULL -- Approximate float representation in SQLite
);

-- Relational shape alone does not enforce that every student has both name and GPA.
-- This view checks cross-table key completeness:
CREATE VIEW IF NOT EXISTS unmatched_student_6nf_keys AS
SELECT student_id, 'missing_from_gpa' AS reason FROM student_names_6nf
WHERE student_id NOT IN (SELECT student_id FROM student_gpa_6nf)
UNION ALL
SELECT student_id, 'missing_from_names' AS reason FROM student_gpa_6nf
WHERE student_id NOT IN (SELECT student_id FROM student_names_6nf);

-- ============================================================================
-- 7. BQNF: Boundary-Quotient Normal Form (Data in Motion under CDC)
-- ============================================================================
-- Note: Amounts and sketches are stored as REAL (approximate) in SQLite.
-- The Zero-Float Law (ZFNF) in production kernels requires exact rational arithmetic.

CREATE TABLE IF NOT EXISTS base_sales (
    sale_id INTEGER PRIMARY KEY,
    region TEXT NOT NULL,
    amount REAL NOT NULL -- Approximate currency value
);

-- Maintained Materialized Aggregate Cache (Additive SPJA + Non-Invertible Extrema + Quantiles)
CREATE TABLE IF NOT EXISTS region_sales_cache (
    region TEXT PRIMARY KEY NOT NULL,
    total_sales REAL NOT NULL, -- Approximate sum
    sale_count INTEGER NOT NULL,
    min_amount REAL,           -- Approximate min
    max_amount REAL,           -- Approximate max
    median_amount REAL         -- Approximate quantile
);

-- CDC Log table (Change Data Capture)
CREATE TABLE IF NOT EXISTS sales_cdc_log (
    cdc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    op_type TEXT NOT NULL CHECK (op_type IN ('INSERT', 'UPDATE', 'DELETE')),
    sale_id INTEGER NOT NULL,
    old_region TEXT,
    new_region TEXT,
    old_amount REAL,
    new_amount REAL,
    processed INTEGER NOT NULL DEFAULT 0 CHECK (processed IN (0, 1)),
    CHECK ((op_type = 'INSERT' AND new_region IS NOT NULL AND new_amount IS NOT NULL)
        OR (op_type = 'DELETE' AND old_region IS NOT NULL AND old_amount IS NOT NULL)
        OR (op_type = 'UPDATE' AND old_region IS NOT NULL AND old_amount IS NOT NULL
            AND new_region IS NOT NULL AND new_amount IS NOT NULL))
);

-- Auxiliary Priority Queue Cochain for Non-Invertible Aggregates (MIN / MAX)
CREATE TABLE IF NOT EXISTS region_extremum_cochain (
    region TEXT NOT NULL,
    amount REAL NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (region, amount)
);

CREATE INDEX IF NOT EXISTS idx_region_extremum_cochain_lookup 
ON region_extremum_cochain(region, amount ASC);

-- Extrema Repair Audit Log (tracking exact cochain repair vs bounded fallback recomputation)
CREATE TABLE IF NOT EXISTS extrema_repair_log (
    repair_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT NOT NULL,
    op_type TEXT NOT NULL,
    affected_amount REAL,
    is_destructive INTEGER NOT NULL CHECK (is_destructive IN (0, 1)), -- 1 if deleted/updated amount was current min or max
    cochain_available INTEGER NOT NULL CHECK (cochain_available IN (0, 1)), -- 1 if cochain provided next extremum
    terminal_route TEXT NOT NULL, -- 'Repair', 'Recompute', 'Preserve'
    old_min REAL,
    new_min REAL,
    old_max REAL,
    new_max REAL,
    recomputation_fallback_executed INTEGER NOT NULL DEFAULT 0 CHECK (recomputation_fallback_executed IN (0, 1))
);

-- Auxiliary Quantile Sketch Cochain for Non-Invertible Quantiles (MEDIAN / Percentiles)
CREATE TABLE IF NOT EXISTS region_quantile_cochain (
    region TEXT NOT NULL,
    bucket_id INTEGER NOT NULL,
    lower_bound REAL NOT NULL,
    upper_bound REAL NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (region, bucket_id)
);

CREATE INDEX IF NOT EXISTS idx_region_quantile_cochain_lookup
ON region_quantile_cochain(region, bucket_id ASC);

-- Quantile Repair Audit Log (tracking epsilon-BQNF sketch tolerance vs bounded fallback recomputation)
CREATE TABLE IF NOT EXISTS quantile_repair_log (
    repair_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT NOT NULL,
    op_type TEXT NOT NULL,
    affected_amount REAL,
    estimated_median REAL,
    true_median REAL,
    error_delta REAL,
    tolerance REAL,
    within_tolerance INTEGER NOT NULL CHECK (within_tolerance IN (0, 1)), -- 1 if error_delta <= tolerance
    terminal_route TEXT NOT NULL, -- 'Repair', 'Recompute', 'Preserve'
    recomputation_fallback_executed INTEGER NOT NULL DEFAULT 0 CHECK (recomputation_fallback_executed IN (0, 1))
);
