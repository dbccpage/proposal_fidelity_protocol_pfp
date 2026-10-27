# Task C011: Cycle-Rank Ladder — Minimum-L1 Coboundary Repair

## Current implementation boundary

Python challenge entrypoints delegate to the shared cohomology solver port and
independent certificate checker. The native adapter currently exposes C011;
C012–C020 return an explicit unavailable-operation refusal until the owning
native operation and independent certificate checks are bound. Checked
out-of-scope controls are not solved mathematical capabilities.

The local challenge swarm does not have a cohomology operation bound through
`adversary`. It returns `ADVERSARY_EXECUTION_UNAVAILABLE` and produces no
Adversary act trace or authorization receipt. The following problem specification
defines the intended mathematical contract, not proof of implemented capability.
Billing is unavailable; serialized input size is not measured token usage.

**AuthorityEffect:** None. **Protocol:** SG-CP v1. **Domain:** b_cohomology.

## 1. Problem Formulation

Input: A directed graph $G = (V, E)$ without self-loops (parallel edges allowed), rational claims $c \in \mathbb{Q}^E$, and strictly positive rational weights $w \in \mathbb{Q}^E$ ($w_e > 0$).
For a potential $\phi \in \mathbb{Q}^V$, the coboundary is $(\delta \phi)_e = \phi(\text{head}(e)) - \phi(\text{tail}(e))$.

The $L_1$ quotient obstruction is:
$$\Phi_1(c) = \min_{\phi \in \mathbb{Q}^V} \sum_{e \in E} w_e |c_e - (\delta \phi)_e|$$

The repair is $r_e = c_e - (\delta \phi)_e$, making $c - r = \delta \phi$ an exact coboundary.
By linear programming strong duality:
$$\Phi_1(c) = \max \left\{ \sum_{e \in E} c_e y_e : \sum_{e \in \text{in}(v)} y_e - \sum_{e \in \text{out}(v)} y_e = 0\ \forall v \in V,\ |y_e| \le w_e \right\}$$

A certificate $(\phi, y)$ is complete and optimal when:
1. $r_e = c_e - (\phi(\text{head}(e)) - \phi(\text{tail}(e)))$ on every edge.
2. $y$ is a circulation (net divergence is zero at every vertex).
3. Dual feasibility holds: $|y_e| \le w_e$ on every edge.
4. Complementary slackness / zero duality gap holds:
   $$\sum_{e \in E} w_e |r_e| = \sum_{e \in E} c_e y_e = \Phi_1(c)$$

## 2. Wire & Canonical JSON Contract

Rationals are serialized strictly as canonical strings:
- Integers: `"0"`, `"1"`, `"-5"` (no trailing `"/1"`).
- Non-integer fractions: `"5/12"`, `"-3/4"` (reduced to coprime numerator and denominator, denominator $> 1$).
- Binary floating point (`0.5`, `3.14`) is strictly forbidden.

### Output JSON Shapes

**Solved Case:**
```json
{
  "status": "SOLVED",
  "phi1": "8",
  "potential": {"a": "0", "b": "-3", "c": "-3", "d": "-2"},
  "repair": {"a->b": "4", "b->c": "2"},
  "dual": {"a->b": "1", "b->c": "2", "c->a": "2", "b->d": "-1", "d->a": "-1"}
}
```
*Note: Omitted repair and dual entries are interpreted as zero.*

**Out of Scope Case (Self-loop or nonpositive weight):**
```json
{
  "status": "OUT_OF_SCOPE",
  "witness": {"edge": "e1", "reason": "SELF_LOOP"}
}
```

**Refusal (Budget Exhausted):**
```json
{
  "status": "UNKNOWN",
  "refusal": "BUDGET_EXHAUSTED"
}
```
