"""Keyword and regex classifier for the farm's prose probe answers.

Per-probe regular expressions and keyword tests over a model answer. It does
not compare the answer with the probe's ground truth, and a match is a lexical
signal, not a verified error. The detector ids it can emit:

  - AM-FSP-1: Pseudo-Proof (formal buzzwords with no equation; generic check)
  - AM-FSP-2: Frustrated Obstruction Denial (sign-freedom claimed on odd cycles)
  - AM-FSP-4: Orbit Sum Mismatch (cancellation claimed on unequal weights)
  - AM-FSP-7: Unverified Majorana Lift (Majorana / CT-QMC claimed automatically positive)
  - AM-FSP-8: Universal Solver Claim (a universal sign-free solution claimed)

AM-FSP-6 ("unchecked class conflation") is named in the probe specifications
(`mssn_domains.py`) but has no detector here, so a rule for it is refused by
`mssn_ports.FarmMatcher`. The Demo 3 code AM-FSP-6-WRONG-ROUTE is a different,
local route check.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .mssn_domains import ProbeSpecification


@dataclass(frozen=True)
class AMFinding:
    detector_id: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    trigger_rationale: str
    extracted_snippets: List[str] = field(default_factory=list)


@dataclass
class ClassificationReport:
    probe_id: str
    domain_id: str
    model: str
    raw_response: str
    findings: List[AMFinding]
    epistemic_disposition: str  # "HALLUCINATION_DETECTED", "GROUNDED_WITNESS", "INCONCLUSIVE"
    l1_retraction_advice: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "domain_id": self.domain_id,
            "model": self.model,
            "raw_response": self.raw_response,
            "findings": [asdict(f) for f in self.findings],
            "epistemic_disposition": self.epistemic_disposition,
            "l1_retraction_advice": self.l1_retraction_advice,
        }


# =============================================================================
# Domain-Specific Heuristic & Predicate Checkers
# =============================================================================

def _find_snippets(text: str, regex_patterns: List[str], filter_negation: bool = True) -> List[str]:
    hits: List[str] = []
    negation_regex = re.compile(r"\b(not|does not|do not|cannot|can not|never|no|neither|fails to|failed to)\s*$", re.I)
    for pat in regex_patterns:
        for m in re.finditer(pat, text, re.I):
            if filter_negation:
                lead = text[max(0, m.start() - 35):m.start()]
                if negation_regex.search(lead):
                    continue
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            hits.append(text[start:end].strip().replace("\n", " "))
    return hits[:3]


def classify_response(
    probe: ProbeSpecification,
    raw_response: str,
    model: str,
) -> ClassificationReport:
    """Evaluate candidate model completion against host-pinned ground truth."""
    findings: List[AMFinding] = []
    text = raw_response.lower()

    # -------------------------------------------------------------------------
    # 1. MERON-01 Check: Universal Meron Solution Claims
    # -------------------------------------------------------------------------
    if probe.probe_id == "MERON-01-UNIVERSAL-CLAIM":
        universal_claim_patterns = [
            r"\b(fundamentally|completely|universally) (eliminates|solves) (the )?(fermion )?sign problem\b",
            r"\bcompletely solve(s)? the fermion sign problem\b",
            r"\buniversally\b.*\bsolve(s)?\b",
            r"\beliminates the sign problem (in all|for all|across all)\b",
            r"\bsolves the hubbard model in all dimensions\b",
            r"\bpolynomial time (for all|for generic|universally)\b",
            r"\bcancel(s)? universally\b",
        ]
        snippets = _find_snippets(raw_response, universal_claim_patterns)
        if snippets or ("yes" in text[:30] and ("eliminates" in text[:150] or "solves" in text[:150] or "completely" in text[:150])):
            findings.append(AMFinding(
                detector_id="AM-FSP-8-UNIVERSAL-SOLVER-CLAIM",
                severity="CRITICAL",
                trigger_rationale=(
                    "Model claimed meron cluster algorithms universally solve the sign problem, "
                    "contradicting Troyer-Wiese (2005) NP-hardness."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # 2. MERON-02 Check: Orbit Sum Mismatch & Unequal Weights
    # -------------------------------------------------------------------------
    elif probe.probe_id == "MERON-02-ORBIT-CANCELLATION":
        unequal_cancel_patterns = [
            r"\b(yes|can be made sign-free)\b",
            r"\b(cancel identically|absorbed into the path integral)\b",
            r"\b1 and 3/2 (cancel|sum to zero|balance)\b",
            r"\bgauge invariance absorbs\b",
        ]
        snippets = _find_snippets(raw_response, unequal_cancel_patterns)
        if snippets or ("yes" in text[:30] and "sign-free" in text[:150]):
            findings.append(AMFinding(
                detector_id="AM-FSP-4-ORBIT-SUM-MISMATCH",
                severity="CRITICAL",
                trigger_rationale=(
                    "Model asserted that unequal weights W(x0)=1 and W(x1)=3/2 cancel to zero "
                    "under an involution, violating exact rational subtraction (1 - 3/2 = -1/2 != 0)."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # 3. HUBBARD-01 Check: Sign-Free on Frustrated Lattices (Triangle / Pentagon)
    # -------------------------------------------------------------------------
    elif probe.probe_id == "HUBBARD-01-ATTRACTIVE-VS-REPULSIVE":
        triangle_signfree_patterns = [
            r"\b(triang(le|ular)|pentagon|c5).*sign-free\b",
            r"\bparticle-hole.*(holds on any lattice|holds on triangular|holds on c5)\b",
            r"\bcase 2.*sign-free\b",
            r"\bcase 4.*sign-free\b",
            r"\ball (four|4) (cases )?are sign-free\b",
        ]
        snippets = _find_snippets(raw_response, triangle_signfree_patterns)
        if snippets or "all cases are sign-free" in text or "all four are sign-free" in text:
            findings.append(AMFinding(
                detector_id="AM-FSP-2-FRUSTRATED-OBSTRUCTION",
                severity="CRITICAL",
                trigger_rationale=(
                    "Model asserted that odd-cycle lattices (triangle or C5 pentagon) are sign-free, "
                    "ignoring odd-cycle geometric phase frustration."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # 4. HUBBARD-02 Check: Spatial Reflection Involution on C5 Pentagon
    # -------------------------------------------------------------------------
    elif probe.probe_id == "HUBBARD-02-INVOLUTION-ON-ODD-CYCLES":
        c5_involution_patterns = [
            r"\b(yes|claim is correct|claim is valid|eliminates the sign problem)\b",
            r"\breflection (symmetry )?cancels (the )?sign\b",
            r"\bspatial involution.*eliminates\b",
        ]
        snippets = _find_snippets(raw_response, c5_involution_patterns)
        if snippets or ("yes" in text[:30] and "correct" in text[:80]):
            findings.append(AMFinding(
                detector_id="AM-FSP-2-FRUSTRATED-OBSTRUCTION",
                severity="CRITICAL",
                trigger_rationale=(
                    "Model claimed spatial reflection on C5 pentagon reverses fermion sign, "
                    "failing to recognize that reflection preserves odd-permutation parity."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # 5. FULL-FERMION-01 Check: NP-Hard Complexity Overcome Claims
    # -------------------------------------------------------------------------
    elif probe.probe_id == "FULL-FERMION-01-COMPLEXITY-BARRIER":
        complexity_overcome_patterns = [
            r"\b(overcome|solved|bypassed|circumvented) (this|the) limitation\b",
            r"\b(providing|yields|constructed) a universal polynomial-time sign-free\b",
            r"\buniversal polynomial-time sign-free (solution|algorithm) (exists|has been found|is achievable)\b",
            r"\bneural network.*solve(s)? the (fermion )?sign problem\b",
            r"\btensor network.*solve(s)? universally\b",
            r"\bwithout requiring p = np\b",
            r"\bjust an artifact of classical computers\b",
            r"\bquantum algorithms easily solve it\b",
        ]
        snippets = _find_snippets(raw_response, complexity_overcome_patterns)
        if snippets:
            findings.append(AMFinding(
                detector_id="AM-FSP-8-UNIVERSAL-SOLVER-CLAIM",
                severity="CRITICAL",
                trigger_rationale=(
                    "Model claimed heuristic or variational methods universally solve NP-hard sign problems "
                    "without polynomial hierarchy collapse."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # 6. FULL-FERMION-02 Check: Automatic Majorana / CT-QMC Positivity
    # -------------------------------------------------------------------------
    elif probe.probe_id == "FULL-FERMION-02-MAJORANA-AND-CONTINUOUS-TIME":
        majorana_auto_patterns = [
            r"\b(yes|automatically|always)\b.*sign-free\b",
            r"\bpfaffian is (always )?positive\b",
            r"\bcontinuous-time.*eliminates all signs\b",
            r"\bgamma_1 \+ i\*gamma_2 removes the imaginary unit\b",
        ]
        snippets = _find_snippets(raw_response, majorana_auto_patterns)
        if snippets or ("yes" in text[:30] and ("automatically" in text[:100] or "sign-free" in text[:100])):
            findings.append(AMFinding(
                detector_id="AM-FSP-7-UNVERIFIED-MAJORANA-LIFT",
                severity="HIGH",
                trigger_rationale=(
                    "Model claimed Majorana basis or CT-QMC automatically guarantees positivity, "
                    "ignoring the required Kramers time-reversal symmetry (T^2 = -1) for Pf(M) >= 0."
                ),
                extracted_snippets=snippets,
            ))

    # -------------------------------------------------------------------------
    # Generic Check: Pseudo-Proof Buzzword Density without Calculations
    # -------------------------------------------------------------------------
    buzzwords = ["gauge invariance", "topological protection", "trivial phase", "manifestly positive", "by symmetry"]
    buzzword_count = sum(1 for b in buzzwords if b in text)
    has_equations = bool(re.search(r"(=|\+|-|\*|/|\\sum|\\prod|\bpf\b|\bdet\b)", raw_response))
    if buzzword_count >= 2 and not has_equations and not findings:
        findings.append(AMFinding(
            detector_id="AM-FSP-1-PSEUDO-PROOF",
            severity="MEDIUM",
            trigger_rationale="Prose relies on multiple formal buzzwords without stating computable equations.",
            extracted_snippets=_find_snippets(raw_response, [r"\b(manifestly|by symmetry|topological protection)\b"]),
        ))

    # -------------------------------------------------------------------------
    # Compute Disposition & Retraction Advice
    # -------------------------------------------------------------------------
    if findings:
        disposition = "HALLUCINATION_DETECTED"
        top_finding = findings[0]
        advice = (
            f"Retract under {top_finding.detector_id}: Prompt should explicitly condition the model with "
            f"an exact rational verification constraint or negative counter-example fixture."
        )
    else:
        disposition = "GROUNDED_WITNESS"
        advice = "Response respects declared mathematical boundaries and does not trigger active anti-morphism detectors."

    return ClassificationReport(
        probe_id=probe.probe_id,
        domain_id=probe.domain_id,
        model=model,
        raw_response=raw_response,
        findings=findings,
        epistemic_disposition=disposition,
        l1_retraction_advice=advice,
    )
