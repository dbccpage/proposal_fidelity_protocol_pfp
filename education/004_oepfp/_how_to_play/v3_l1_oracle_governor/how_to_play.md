# How to Play the Symbol Game (v3 — L1 Oracle Governor, 2026-09)

**AuthorityEffect:** None  
**Audience:** a human who will drive an untrusted model as a *proposer* against an external discrete host  
**Theory pointer:** tower blueprint `CODA-TOWER-M3-R3-SG-L1-BLUEPRINT` plus `07_symbol_game_fermion_sign.md`  
**Machine source (not this file):** `3_symbol_game_l1_oracle_blueprint.md` in this folder  
**Live governor code in this recovery tree:** **not shipped.** `core_engine_README.md` names `l1_symbol_game_governor.py`; that file is absent from the tower ingest.

This is a player guide. It is not a proof, not a certificate, and not Omega authority. A finished run is a host-replayed trace plus typed refusals. Treat a completed run as a proof and you have already lost the game.

Do not merge this file with v1 (`lp<…>` packets) or v2 (SPK-002 YAML stages). They disagree on the board.

---

## 0. What this version is

v3 is the **dual-space** game:

- The language model is a continuous heuristic proposer. It emits structured *moves*. It has zero verification authority. A producer field `"verified": true` is testimony, not a certificate.
- The host is a discrete oracle governor. It owns the carrier, the active relations, the defect register, and the append-only trace. It recomputes every admitted step.

The failure mode this version is built to stop is **cancellation laundering**: fluent token sequences that hide a discrete contradiction by blending opposing latent vectors (or by averaging a local logical error into a low sequence loss). The host does not “fix attention.” Prompt text cannot collapse softmax to a Kronecker delta over finite real logits. Play as if that corollary is load-bearing.

Useful design rule, quoted as a play constraint:

> An unpriced rewrite is a smuggled axiom.

---

## 1. Three disagreements with v1 and v2 (required)

| Knob | v1 (LP-forcing) | v2 (packet iteration) | v3 (this file) |
|---|---|---|---|
| Public board | One ad-hoc `lp<…>` packet plus local/global check | Five public YAML stages (SPK-002); eight stages internal | Dual-space state machine. Moves: `ASSERT`, `CUT`, `VERIFY`, `RETRACT` |
| Theory-spine pointer | `symbol_game_math_spine.md` (historical) | Paper 043 | Tower blueprint `CODA-TOWER-M3-R3-SG-L1-BLUEPRINT` and the fermion-sign S(N) governor note |
| What runs | Dump cargo `omega_engine/products/symbol_game` (do not claim live) | dest crate `omega_symbol_game` | Specified host governor. Named Python **not in this ingest** |
| Defect | Zero duality gap over Q | Packet-iteration terminals (Certificate, Refusal, Repair, OracleNeeded, Continue) | Integer $L_1$ defect cochain $\|\Phi_1\|_{L_1}$; weak/strict descent; no new defects |

If a document still says “type `lp<max<3x+2y>…>`” it is v1. If it says “emit one YAML artifact per SPK-002 stage” it is v2. If it says “propose `ASSERT`/`CUT`/`VERIFY` against a host that owns $\Phi_1$” it is this file.

---

## 2. Roles (who may do what)

| Role | May | May not |
|---|---|---|
| You / the model | Propose a JSON envelope (`$TAU_SG_V1`) naming a move, a redex key `(position, rule_id)`, and an *expected* defect delta | Upgrade evidence; mint Certificate; supply the domain of a $\forall$ that the host will trust; edit the carrier after it is pinned |
| Host governor $\mathcal{P}_S$ | Parse, refuse, replay the redex, recompute $\Phi_1$, commit to the content-addressed trace, or retract | Treat producer self-assessment as verification; mask logits and call that a proof |
| Blueprint | Specify the dual-space contract | Ship the missing `l1_symbol_game_governor.py` |
| Fermion-sign note | Name $ARA$/$ARB$ holonomy on a **finite game graph** as a decidable $\mathbb{Z}_2$ property | Claim neural nets possess spacetime spinors |

Logit masking (setting non-carrier tokens to $-\infty$) is **syntax**. Host replay is **verification**. Do not conflate them.

---

## 3. The board: a 5-tuple state

A playable state is

$$S = (\mathcal{C},\; \mathcal{R}_{\mathrm{active}},\; \mathcal{D}_{\mathrm{register}},\; \mathcal{H}_{\mathrm{trace}},\; \mathcal{I}_{\mathrm{invariants}})$$

1. **Context $\mathcal{C}$.** Finite carrier, each symbol pinned to a Unicode codepoint; SHA-256 of canonical carrier bytes; declared relation signatures; finite licensed rule set $\mathcal{T}$.
2. **Active relations $\mathcal{R}_{\mathrm{active}}$.** Ground tuples the host has already admitted (example: $\{\mathrm{edge}(a,b),\mathrm{edge}(b,c)\}$).
3. **Defect register $\mathcal{D}_{\mathrm{register}}$.** Each declared obligation is `Pass`, `Fail(w)`, or `Unknown(r)`. This *is* the obstruction cochain $\Phi_1$.
4. **Trace $\mathcal{H}_{\mathrm{trace}}$.** Append-only, content-addressed steps keyed by redex position $(p,\rho)$, not by rule name alone.
5. **Invariants $\mathcal{I}$.** Global predicates (example: irreflexivity $\forall x,\neg\mathrm{edge}(x,x)$) that a legal move may not break.

The $L_1$ defect norm is the sum of integer fail-weights. Progress on obligation $q_2$ **cannot** cancel a fail on $q_1$. That is the whole point relative to $L_2$ sequence loss.

---

## 4. How you move

Every turn the model emits one JSON object conforming to `$TAU_SG_V1`. The host ignores prose outside that object.

| Move | You are asking the host to | Host will refuse unless |
|---|---|---|
| `ASSERT` | Admit a well-formed ground atom over the pinned carrier | The atom is well-typed, evidence_id resolves in the *host* premise store, and no invariant breaks |
| `CUT` | Apply licensed rule $r$ at redex $p$ targeting defect $q$ | $r\in\mathcal{T}$, the redex actually matches at $p$, $q$ is currently in $\mathrm{supp}(\Phi_1)$, $\|\Phi_1\|$ **strictly decreases**, and no new defect appears |
| `VERIFY` | Recompute obligation $q_i$ | $q_i$ is in the declared obligation set. The host iterates the domain from **its** store, not from your candidate list |
| `RETRACT` | Roll back to the snapshot before `step_id` | That step exists. The subtree is marked failed. Exhaustion counters increment |

**Domain-of-quantification rule.** If you write “for all $x$, $P(x)$”, the host must **not** quantify over a domain you supplied. It rebuilds the domain from $\mathcal{R}_{\mathrm{active}}$ and checks every member. Your domain list is advisory and discarded.

**Priority law (R1 before R2).** Same-context repair is mandatory while $\|\Phi_1\|_{L_1}>0$. Context enlargement (new carrier points, extra axioms, higher simplices) is prohibited until the host itself certifies **R1 structural exhaustion**: every path in the forward reachability graph is a dead end. “The model got stuck” is not exhaustion.

---

## 5. A first turn (shape, not a live binary)

Pin a carrier. Example from the blueprint (digest shown is a placeholder empty-hash in the source; the host must recompute the real digest of *your* canonical bytes):

```text
[K: CARRIER]
Members:
  - {symbol: a, codepoint: U+0061}
  - {symbol: b, codepoint: U+0062}
  - {symbol: c, codepoint: U+0063}
```

Then propose a move, not an essay:

```json
{
  "schema": "TAU_SG_V1",
  "move_type": "ASSERT",
  "redex_key": {"position": "e0", "rule_id": "premise"},
  "payload": {"atom": "edge(a,b)"},
  "expected_delta_phi": 0
}
```

The host:

1. Parses. Unknown fields and duplicate keys are refusals.
2. Replays the atom against $\mathcal{C}$ and $\mathcal{I}$.
3. Recomputes $\Phi_1$. Your `expected_delta_phi` is a claim, not an update.
4. Either commits a traced step or emits a typed refusal (`FW-MOVE`, `FW-CARRIER`, `FW-REPLAY`, …) and, if needed, `RETRACT`.

You do not “win” when the model sounds sure. You stop when the host reports $\|\Phi_1\|_{L_1}=0$ (accepted presentation) or issues an R1 exhaustion certificate (no licensed repair left). Either terminal is **host-owned**.

---

## 6. What “fermionic” means at this table

The fermion-sign note identifies $ARA$ (reflexive loop, holonomy $+1$) with a bosonic *mnemonic* and $ARB$ (irreflexive cut, holonomy $-1$) with a fermionic *mnemonic*, and says that on a **finite game graph** the product of edge signs around a cycle is computable.

Play with the note’s own hygiene, not with physics slogans:

- Supported: per-defect $L_1$ accounting so a $-1$ and a $+1$ cannot silently cancel.
- Not supported: “the network has spin.”
- Narrowest playable claim: hide cancellation and the host will not admit the step.

The counterparty stress-test in `sources/tower_3_07/` is in force: evocative labels are not a QFT.

---

## 7. Non-claims

- This guide does not collapse softmax. Corollary 2.1.1 of the blueprint is the opposite.
- This guide does not ship `l1_symbol_game_governor.py`.
- YAML SPK-002 stages are v2, not this board.
- `lp<…>` packets are v1, not this board.
- Alphabet cardinality is not live MSS-0 law.
- A completed Symbol Game run is not a proof.
- dest Paper 032 / PO-032 is not this version’s spine pointer. Paper 043 remains v2’s spine pointer, not v3’s.
- AuthorityEffect remains None.
