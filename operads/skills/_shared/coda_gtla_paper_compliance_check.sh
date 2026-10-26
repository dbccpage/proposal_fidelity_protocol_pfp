#!/usr/bin/env sh
# Deterministic checks for the CODA_GTLA paper-compliance contract + family.
# No new subsystem/crate (task §9): a narrow shell gate over the skill files.
# Exit 0 = all pass; exit 1 = one or more failures (listed). Run from repo root
# or anywhere: paths are resolved relative to this script's location.
#
#   sh .agents/skills/_shared/coda_gtla_paper_compliance_check.sh

set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)   # .../skills/_shared
skills=$(CDPATH= cd -- "$here/.." && pwd)           # .../skills
contract="$here/coda_gtla_paper_compliance.md"
fail=0
note() { printf '  [%s] %s\n' "$1" "$2"; }
bad()  { note FAIL "$1"; fail=1; }
ok()   { note ok   "$1"; }

MEMBERS="panep-math-and-physics-prof"

echo "== 1. shared contract present + required sections =="
if [ -f "$contract" ]; then
  ok "contract file exists"
  for anchor in \
    "twelve stages" \
    "AuthorityEffect::None" \
    "ExactRepair" "StabilizedSurvivor" "OpenObstruction" "OracleNeeded" \
    "LiftLicenseNeeded" "InfrastructureFailure" \
    "PaperCompliancePacket" "PaperRoleReceipt" "MISSING_CARRIER" "SCOPE_PROMOTION"; do
    if grep -qi -- "$anchor" "$contract"; then :; else bad "contract missing required token: $anchor"; fi
  done
  ok "contract required-token scan done"
else
  bad "contract file MISSING at $contract"
fi

echo "== 2. every family member references the contract + declares AuthorityEffect::None =="
for m in $MEMBERS; do
  f="$skills/$m/SKILL.md"
  if [ ! -f "$f" ]; then bad "member SKILL.md missing: $m"; continue; fi
  grep -q "coda_gtla_paper_compliance.md" "$f" || bad "$m does NOT reference the shared contract (MISSING_PROPAGATION)"
  # ceiling: AuthorityEffect::None, OR (for the firewall-home wizard) an explicit 'mints no authority' fence
  grep -q "AuthorityEffect::None" "$f" || grep -qi "mints no authority" "$f" \
    || bad "$m does NOT declare an AuthorityEffect::None ceiling / no-authority fence"
  grep -qi "coda-gtla-papers" "$f"              || bad "$m does NOT declare family coda-gtla-papers"
done
ok "member reference scan done"

echo "== 3. no member mints authority / self-certifies (heuristic) =="
for m in $MEMBERS; do
  f="$skills/$m/SKILL.md"
  [ -f "$f" ] || continue
  # A member must not claim it certifies its own authority or mints AuthorizedLocalResult.
  if grep -Eqi "mint[s]? (an )?authority|certif(y|ies) its own|self-certif" "$f"; then
    grep -Eqi "mints no authority|never .*AuthorizedLocalResult|no authority" "$f" \
      || bad "$m contains an authority-minting phrase without a no-authority fence (AUTHORITY_COLLISION)"
  fi
done
ok "authority-minting heuristic done"

echo "== 4. producer skills do not accept their own work =="
for m in paper-improver; do
  f="$skills/$m/SKILL.md"
  [ -f "$f" ] || continue
  # Producer role must state it does not self-accept; evaluator is separate.
  grep -Eqi "mints no authority|does not (evaluate|accept)|not .*accepted|independent evaluat" "$f" \
    || bad "$m (producer) lacks an explicit 'does not self-accept / independent evaluator' statement"
done
ok "producer self-accept scan done"

echo "== 5. proof-ledger path is the encyclopedia path (residual C5) =="
for m in $MEMBERS; do
  f="$skills/$m/SKILL.md"
  [ -f "$f" ] || continue
  # Flag the drifted path: research/proof_ledger_ NOT preceded by encyclopedia/proof_ledgers/
  if grep -Eq "research/proof_ledger_" "$f"; then
    grep -Eq "encyclopedia/proof_ledgers/proof_ledger_" "$f" \
      || bad "$m uses drifted proof-ledger path (STALE_RULE C5): research/proof_ledger_*"
  fi
done
ok "proof-ledger path scan done"

echo "== 6. _shared link resolution (contract + members) =="
# Resolve every ](../_shared/NAME) and ](./NAME) link target that points into _shared.
scan_links() {
  base_dir="$1"; file="$2"
  # extract the parenthetical of markdown links containing _shared or ./ constraints/family
  grep -oE '\]\((\.\./_shared/[a-zA-Z0-9_./-]+|\./[a-zA-Z0-9_./-]+)\)' "$file" 2>/dev/null \
    | sed -E 's/^\]\(//; s/\)$//' | while IFS= read -r link; do
      target=$(CDPATH= cd -- "$base_dir" 2>/dev/null && CDPATH= cd -- "$(dirname -- "$link")" 2>/dev/null && printf '%s/%s' "$(pwd)" "$(basename -- "$link")")
      if [ -z "$target" ] || [ ! -e "$target" ]; then
        printf 'BROKENLINK %s -> %s\n' "$file" "$link"
      fi
  done
}
broken=$( { scan_links "$here" "$contract"; for m in $MEMBERS; do f="$skills/$m/SKILL.md"; [ -f "$f" ] && scan_links "$skills/$m" "$f"; done; } )
if [ -n "$broken" ]; then printf '%s\n' "$broken" | while IFS= read -r l; do bad "$l"; done; else ok "all _shared links resolve"; fi

echo "== 7. family registered (prose + dict) + symmetry-hunter invariant =="
fr="$here/family_registry.md"
grep -qi "coda-gtla-papers" "$fr"               || bad "family_registry: 'coda-gtla-papers' missing"
sh_file="$skills/auto-symmetry-hunter/references/drift_catalog.md"
grep -qi "CODA_GTLA Paper-Compliance Invariant" "$sh_file" || bad "auto-symmetry-hunter: family invariant missing"
ok "family + invariant scan done"

echo ""
if [ "$fail" -eq 0 ]; then echo "coda_gtla_paper_compliance_check: PASS"; exit 0
else echo "coda_gtla_paper_compliance_check: FAIL"; exit 1; fi

