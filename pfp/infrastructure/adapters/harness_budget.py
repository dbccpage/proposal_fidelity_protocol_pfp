"""Campaign restrictions over the existing atomic provider ledger, not a second wallet."""

import json
import sqlite3

from omega_engine_operads.domain.autopoiesis.research import PHASE_CAPS
from omega_engine_woland.domain.providers.types import ProviderError
from omega_engine_woland.infrastructure.providers.budget_ledger import SqliteBudgetLedger


class HarnessBudgetLedger(SqliteBudgetLedger):
    def __init__(self, path, *, spec, phase):
        if phase not in PHASE_CAPS:
            raise ValueError("UNKNOWN_BUDGET_PHASE")
        self.phase = phase
        super().__init__(path, budget_id=spec.budget_id)
        with sqlite3.connect(path, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS campaign_binding (singleton INTEGER PRIMARY KEY CHECK(singleton=1), binding TEXT NOT NULL)"
            )
            binding = json.dumps(spec.to_dict(), sort_keys=True)
            row = db.execute("SELECT binding FROM campaign_binding WHERE singleton=1").fetchone()
            if row and row[0] != binding:
                raise ValueError("ORIGINAL_CAMPAIGN_BINDING_CHANGED")
            foreign = db.execute(
                "SELECT id FROM provider_budget WHERE id != ?", (spec.budget_id,)
            ).fetchall()
            if foreign:
                raise ValueError("FOREIGN_BUDGET")
            db.execute("INSERT OR IGNORE INTO campaign_binding VALUES (1, ?)", (binding,))
            db.commit()

    def guard(self, state, identity, quote):
        pending = [a for a in state["attempts"].values() if a["state"] != "Settled"]
        if any(a["state"] not in ("Reserved", "Dispatched") for a in pending):
            raise ProviderError("UNRECONCILED_COST")
        if len(pending) >= 2:
            raise ProviderError("CAMPAIGN_CONCURRENCY_LIMIT")
        settlements = {
            s["binding"]["attempt_id"]: s["binding"]["billed_microusd"]
            for s in state["settlements"].values()
        }
        charged = sum(
            settlements.get(a["attempt_id"], a["receipt"]["cost_microusd"])
            for a in state["attempts"].values()
            if a.get("phase") == self.phase
        )
        if charged + quote.cost_microusd > PHASE_CAPS[self.phase]:
            raise ProviderError("CAMPAIGN_PHASE_BUDGET_EXCEEDED")
        identity["phase"] = self.phase

    def snapshot(self):
        with self.transaction(sum(PHASE_CAPS.values())) as state:
            return json.loads(json.dumps(state))
