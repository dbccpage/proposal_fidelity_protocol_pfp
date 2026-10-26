-- Omega Engine Agentic Governance Swarm (OEAGS) Database Schema
-- WAL Journal Mode with Transactional Outbox & Context Tables

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 1. Governance Event Journal
CREATE TABLE IF NOT EXISTS governance_events (
    event_id TEXT PRIMARY KEY NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    version INTEGER NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_gov_events_aggregate ON governance_events(aggregate_id, version);
CREATE INDEX IF NOT EXISTS idx_gov_events_type ON governance_events(event_type);

-- 2. Transactional Outbox for Cross-Process Dispatching
CREATE TABLE IF NOT EXISTS governance_outbox (
    outbox_id TEXT PRIMARY KEY NOT NULL,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    processed_at TEXT,
    FOREIGN KEY (event_id) REFERENCES governance_events(event_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gov_outbox_status ON governance_outbox(status, created_at);

-- 3. Council Deliberation Sessions
CREATE TABLE IF NOT EXISTS council_sessions (
    session_id TEXT PRIMARY KEY NOT NULL,
    council_name TEXT NOT NULL,
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    votes_json TEXT NOT NULL,
    decision_json TEXT,
    motion_text TEXT,
    finalization_request_json TEXT,
    attendance_json TEXT,
    resumption_json TEXT,
    fixture_observations_json TEXT,
    action_proposals_json TEXT,
    action_owner_responses_json TEXT,
    action_attempts_json TEXT,
    action_reviews_json TEXT,
    action_follow_up_json TEXT,
    statements_json TEXT,
    appeal_json TEXT,
    decree_json TEXT,
    blackrod_veto_reason TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    storage_revision INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_council_sessions_status ON council_sessions(status);
CREATE INDEX IF NOT EXISTS idx_council_sessions_name ON council_sessions(council_name);

-- 4. Agent Identities & Authority Ceilings
CREATE TABLE IF NOT EXISTS agent_identities (
    agent_id TEXT PRIMARY KEY NOT NULL,
    persona_name TEXT NOT NULL,
    status TEXT NOT NULL,
    ceiling_level TEXT NOT NULL,
    code_hash TEXT,
    code_hash_kind TEXT,
    capabilities_json TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

-- 5. Swarm Tasks & DAG Work Nodes
CREATE TABLE IF NOT EXISTS swarm_tasks (
    task_id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    dependencies_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_swarm_tasks_session ON swarm_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_swarm_tasks_status ON swarm_tasks(status);

-- 6. Change Control Proposals
CREATE TABLE IF NOT EXISTS change_proposals (
    proposal_id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    target_ref TEXT NOT NULL DEFAULT 'main',
    carrier_oid TEXT,
    carrier_oid_kind TEXT,
    manifest_json TEXT NOT NULL,
    firewall_result_json TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 7. Evidence Custody Records
CREATE TABLE IF NOT EXISTS evidence_records (
    evidence_id TEXT PRIMARY KEY NOT NULL,
    artifact_ref TEXT NOT NULL,
    digest_algorithm TEXT NOT NULL,
    digest_hex TEXT NOT NULL,
    status TEXT NOT NULL,
    observations_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_records_digest ON evidence_records(digest_hex);

-- 8. Policy Compliance Evaluations & Deviations
CREATE TABLE IF NOT EXISTS policy_compliance_records (
    record_id TEXT PRIMARY KEY NOT NULL,
    rule_id TEXT NOT NULL,
    disposition TEXT NOT NULL,
    justification TEXT NOT NULL DEFAULT '',
    adopter TEXT NOT NULL DEFAULT '',
    expires_at TEXT,
    compensating_controls_json TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    evaluated_at TEXT NOT NULL
);

-- 9. CI/CD Process Flow & Verification Campaigns
CREATE TABLE IF NOT EXISTS cicd_campaigns (
    campaign_id TEXT PRIMARY KEY NOT NULL,
    change_reference TEXT NOT NULL,
    target_commit TEXT NOT NULL,
    consensus_status TEXT NOT NULL,
    results_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_audit_campaigns (
    campaign_id TEXT PRIMARY KEY NOT NULL,
    pr_number INTEGER NOT NULL,
    target_commit TEXT NOT NULL,
    consensus_status TEXT NOT NULL,
    results_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 10. One-attempt queued task halt intents and latest independent readback.
CREATE TABLE IF NOT EXISTS queued_halt_incidents (
    request_id TEXT PRIMARY KEY NOT NULL,
    incident_id TEXT UNIQUE NOT NULL,
    request_digest TEXT NOT NULL,
    request_json TEXT NOT NULL,
    mandate_json TEXT NOT NULL,
    before_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('REQUESTED', 'REFUSED', 'UNKNOWN', 'OBSERVED_APPLIED')),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    after_json TEXT,
    residual_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS queued_halt_incidents_preserve_intent
BEFORE UPDATE ON queued_halt_incidents
WHEN NEW.request_id != OLD.request_id OR NEW.incident_id != OLD.incident_id
    OR NEW.request_digest != OLD.request_digest OR NEW.request_json != OLD.request_json
    OR NEW.mandate_json != OLD.mandate_json OR NEW.before_json != OLD.before_json
    OR NEW.created_at != OLD.created_at OR NEW.revision != OLD.revision + 1
    OR OLD.status IN ('REFUSED', 'OBSERVED_APPLIED')
    OR NEW.status = 'REQUESTED'
    OR (OLD.status = 'UNKNOWN' AND NEW.status = 'REFUSED')
BEGIN
    SELECT RAISE(ABORT, 'queued halt intent or final result is immutable');
END;

CREATE TRIGGER IF NOT EXISTS queued_halt_incidents_no_delete
BEFORE DELETE ON queued_halt_incidents
BEGIN
    SELECT RAISE(ABORT, 'queued halt incidents are retained');
END;
