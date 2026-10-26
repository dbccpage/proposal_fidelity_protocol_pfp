-- Coverage receipts concern structural exhaustiveness, not verifier truth or authority.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS nf_candidate_problems (
    problem_id TEXT PRIMARY KEY NOT NULL,
    carrier_digest TEXT NOT NULL,
    declared_count INTEGER NOT NULL CHECK (typeof(declared_count) = 'integer' AND declared_count > 0),
    authority_effect TEXT NOT NULL DEFAULT 'None' CHECK (authority_effect IS NOT DISTINCT FROM 'None')
);
CREATE TABLE IF NOT EXISTS nf_candidate_carrier (
    problem_id TEXT NOT NULL REFERENCES nf_candidate_problems(problem_id),
    candidate_id TEXT NOT NULL CHECK (length(candidate_id) > 0),
    input_digest TEXT NOT NULL,
    PRIMARY KEY (problem_id, candidate_id),
    UNIQUE (problem_id, candidate_id, input_digest)
);
CREATE TABLE IF NOT EXISTS nf_candidate_checks (
    problem_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('accept', 'reject', 'refuse')),
    evidence_digest TEXT NOT NULL,
    PRIMARY KEY (problem_id, candidate_id),
    FOREIGN KEY (problem_id, candidate_id, input_digest)
        REFERENCES nf_candidate_carrier(problem_id, candidate_id, input_digest)
);
CREATE VIEW IF NOT EXISTS nf_candidate_coverage AS
SELECT p.problem_id,
    CASE WHEN p.declared_count IS NULL OR p.declared_count < 1
        OR p.authority_effect IS DISTINCT FROM 'None'
        OR p.carrier_digest IS NULL
        OR (SELECT COUNT(*) FROM nf_candidate_carrier c WHERE c.problem_id = p.problem_id)
            IS DISTINCT FROM p.declared_count
        OR (SELECT COUNT(*) FROM nf_candidate_checks k WHERE k.problem_id = p.problem_id)
            IS DISTINCT FROM p.declared_count
        OR EXISTS (SELECT candidate_id FROM nf_candidate_carrier WHERE problem_id = p.problem_id
                   EXCEPT SELECT candidate_id FROM nf_candidate_checks WHERE problem_id = p.problem_id)
        OR EXISTS (SELECT candidate_id FROM nf_candidate_checks WHERE problem_id = p.problem_id
                   EXCEPT SELECT candidate_id FROM nf_candidate_carrier WHERE problem_id = p.problem_id)
        OR EXISTS (SELECT 1 FROM nf_candidate_checks k
                   JOIN nf_candidate_carrier c
                     ON k.problem_id = c.problem_id AND k.candidate_id = c.candidate_id
                   WHERE k.problem_id = p.problem_id
                     AND k.input_digest IS DISTINCT FROM c.input_digest)
        THEN 0 ELSE 1 END AS exhaustive,
    p.authority_effect
FROM nf_candidate_problems p;
