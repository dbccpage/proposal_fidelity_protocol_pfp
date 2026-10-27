"""Runtime action adapter using the one OEOS native process seam.

Invocation and convenience methods return the complete railway outcome, not
bare action results. Callers retain that record before inspecting its payload.
AuthorityEffect: None (const).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from operating_system.adapters.rust_host import ffi as native_host
from operations.domain.rop.result import Err, Refusal, Result
from pfp.domain.lean_bridge.models import STANDARD_LEAN_AXIOMS

if TYPE_CHECKING:
    from pfp.domain.cochain import (
        CochainDisposition,
        PrimeTriadContext,
        PromptCellComplex,
    )
    from pfp.domain.ports.prompt_cochain_port import PromptCochainHost


def find_core_symbol_game_binary() -> Path:
    """Locate the native executable, by asking the one seam that owns that job.

    This used to search four hardcoded `target/{debug,release}` paths of its
    own. That made it a second place deciding where the host lives, against
    `RULE_FFI_SEAM_ISOLATION_001` and the Parity Seam Isolation Invariant, and
    it drifted from the canonical seam in a way that mattered: it ignored
    `CORE_SYMBOL_GAME_HOST`, which CLAUDE.md documents as the supported way to
    point at a binary built elsewhere. Anyone relying on that variable would
    have been silently served a stale `target/debug` build, or none.

    Delegating restores one answer to "where is the host", and picks up the
    environment override and the refusal vocabulary for free.
    """
    from operating_system.adapters.rust_host.ffi import (
        locate_host_binary,
    )

    located = locate_host_binary()
    if located.is_err:
        # The seam returns a typed refusal rather than raising; this module's
        # contract with its callers is an exception, so translate at the
        # boundary and carry the refusal's own code and message through.
        refusal = located.unwrap_err()
        raise FileNotFoundError(
            f"{getattr(refusal, 'code', 'HOST_BINARY_NOT_FOUND')}: "
            f"{getattr(refusal, 'message', refusal)}"
        )
    return located.unwrap().binary


class RustSymbolGameHost:
    """Action payload construction; OEOS alone locates and spawns the host."""

    def __init__(self, binary_path: str | Path | None = None) -> None:
        if binary_path is not None:
            self._binary_path = Path(binary_path).resolve()
        else:
            self._binary_path = find_core_symbol_game_binary()
        self._host = native_host.RustSymbolGameHost(
            binary=self._binary_path, timeout_seconds=30
        )

    @property
    def binary_path(self) -> Path:
        return self._binary_path

    def invoke_runtime(
        self, action: str, payload: Any
    ) -> Result[Mapping[str, Any], Refusal]:
        """Return the canonical seam's full per-call outcome or typed refusal."""
        return self._host.invoke_runtime(action, payload)

    def invoke(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch without extracting or relabeling the native outcome."""
        return self.invoke_runtime(action, payload)

    def canonical_wire(self, value: Any) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("canonical_wire", value)

    def canonical_unwire(self, wire: Any) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("canonical_unwire", wire)

    def canonical_json(self, value: Any) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("canonical_json", value)

    def canonical_bytes_hex(self, value: Any) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("canonical_bytes_hex", value)

    def domain_digest(
        self, domain: str, value: Any
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("domain_digest", {"domain": domain, "value": value})

    def parse_unified_diff(self, patch_text: str) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("parse_unified_diff", patch_text)

    def create_code_change_proposal(
        self,
        *,
        task_id: str,
        objective: str,
        base_revision: str,
        owned_paths: Sequence[str],
        protected_paths: Sequence[str],
        candidate_budget: int = 4,
        operation_budget: int = 16,
        required_gates: Sequence[str] = ("gate_ownership", "gate_syntax"),
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = {
            "task_id": task_id,
            "objective": objective,
            "base_revision": base_revision,
            "owned_paths": list(owned_paths),
            "protected_paths": list(protected_paths),
            "candidate_budget": candidate_budget,
            "operation_budget": operation_budget,
            "required_gates": list(required_gates),
        }
        return self.invoke("create_code_change_proposal", payload)

    def submit_patch_candidate(
        self,
        *,
        run_root: dict[str, Any],
        expected_task_packet_sha256: str,
        candidate_id: str,
        producer_id: str,
        patch_text: str,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Admit one patch. ``expected_task_packet_sha256`` is the digest the
        caller received at create and must keep; the host refuses a mismatch."""
        payload = {
            "run_root": run_root,
            "expected_task_packet_sha256": expected_task_packet_sha256,
            "candidate_id": candidate_id,
            "producer_id": producer_id,
            "patch_text": patch_text,
        }
        return self.invoke("submit_patch_candidate", payload)

    def evaluate_patch_gates(
        self,
        *,
        run_root: dict[str, Any],
        expected_task_packet_sha256: str,
        expected_run_root_digest: str,
        patch_artifact: dict[str, Any],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Run the gates on an admitted patch.

        ``expected_task_packet_sha256`` is the create-time digest and
        ``expected_run_root_digest`` the rolling digest the last submit
        returned (``result["run_root_digest"]``); the caller keeps both, and the
        host refuses a run root that carries different ones.
        """
        payload = {
            "run_root": run_root,
            "expected_task_packet_sha256": expected_task_packet_sha256,
            "expected_run_root_digest": expected_run_root_digest,
            "patch_artifact": patch_artifact,
        }
        return self.invoke("evaluate_patch_gates", payload)

    def intake_research_sources(
        self,
        bundle_id: str,
        sources: Sequence[tuple[str, str, str]],  # (art_id, path, hex_or_raw_string)
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = {
            "bundle_id": bundle_id,
            "sources": [list(s) for s in sources],
        }
        return self.invoke("intake_research_sources", payload)

    def score_discrete_proposal(
        self,
        obstructions: Sequence[str],
        proposal: dict[str, Any],
        admitted_constructors: Sequence[str] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = {
            "obstructions": list(obstructions),
            "proposal": proposal,
            "admitted_constructors": list(admitted_constructors)
            if admitted_constructors is not None
            else None,
        }
        return self.invoke("score_discrete_proposal", payload)

    def rank_candidate_proposals(
        self,
        obstructions: Sequence[str],
        proposals: Sequence[dict[str, Any]],
        admitted_constructors: Sequence[str] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = {
            "obstructions": list(obstructions),
            "proposals": list(proposals),
            "admitted_constructors": list(admitted_constructors)
            if admitted_constructors is not None
            else None,
        }
        return self.invoke("rank_candidate_proposals", payload)

    def classify_gauge_board(
        self,
        d0: dict[str, Any],
        d1: dict[str, Any],
        cochain: Sequence[int | bool],
    ) -> Result[Mapping[str, Any], Refusal]:
        payload = {
            "d0": d0,
            "d1": d1,
            "cochain": list(cochain),
        }
        return self.invoke("classify_gauge_board", payload)

    def exact_determinant(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_determinant", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_is_positive_definite(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_is_positive_definite", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_ldlt(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_ldlt", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_rank(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_rank", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_leading_minors(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_leading_minors", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_char_poly(
        self, matrix_rows: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_char_poly", {"matrix": {"rows": [list(r) for r in matrix_rows]}})

    def exact_verify_boundary_closed(
        self, faces: Sequence[Sequence[tuple[int, int, int]]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke("exact_verify_boundary_closed", {"faces": [[list(t) for t in f] for f in faces]})

    def exact_verify_simplicial_boundary_law(
        self, simplices: Sequence[Sequence[int]]
    ) -> Result[Mapping[str, Any], Refusal]:
        return self.invoke(
            "exact_verify_simplicial_boundary_law",
            {"simplices": [list(s) for s in simplices]},
        )

    def exact_ordered_loop_product(
        self,
        tables_rows: Sequence[Sequence[Sequence[str]]],
        word: Sequence[tuple[int, bool]],
    ) -> Result[Mapping[str, Any], Refusal]:
        tables = [{"rows": [list(r) for r in t]} for t in tables_rows]
        return self.invoke("exact_ordered_loop_product", {"tables": tables, "word": [list(w) for w in word]})

    def exact_is_ordered_closure(
        self,
        tables_rows: Sequence[Sequence[Sequence[str]]],
        word: Sequence[tuple[int, bool]],
    ) -> Result[Mapping[str, Any], Refusal]:
        tables = [{"rows": [list(r) for r in t]} for t in tables_rows]
        return self.invoke("exact_is_ordered_closure", {"tables": tables, "word": [list(w) for w in word]})

    def verify_l1_certificate(
        self,
        matrix_rows: Sequence[Sequence[str]],
        omega: Sequence[str],
        p: Sequence[str],
        y: Sequence[str],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Verify exact rational L1 quotient distance certificate through native host.

        Verifies Phi1(omega) = min_p ||omega - B*p||_1 = max { <y, omega> : B^T*y = 0, ||y||_inf <= 1 }.
        """
        payload = {
            "matrix": {"rows": [list(r) for r in matrix_rows]},
            "omega": list(omega),
            "p": list(p),
            "y": list(y),
        }
        return self.invoke("verify_l1_certificate", payload)

    def exact_solve_l1_primal_dual(
        self,
        matrix_rows: Sequence[Sequence[str]],
        target: Sequence[str],
        weights: Sequence[str] | None = None,
        budget: int | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Solve exact weighted L1 projection / gauge fixing over Q using core_solvers.

        Returns minimizer alpha, residual z = target - B*alpha, dual witness y,
        and optimal value Phi1, certified against core_functional.
        """
        payload: dict[str, Any] = {
            "matrix": {"rows": [list(r) for r in matrix_rows]},
            "target": list(target),
        }
        if weights is not None:
            payload["weights"] = list(weights)
        if budget is not None:
            payload["budget"] = budget
        return self.invoke("exact_solve_l1_primal_dual", payload)

    def functional_evaluate(
        self, payload: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Phi1, Gamma2 and the diagnostic class, produced by core_functional.

        Build ``payload`` with the OEOS ``theory_requests`` builders. The seam
        refuses an answer whose ``input_digest`` is not this payload's digest.
        """
        return self.invoke("functional_evaluate", payload)

    def functional_verify(
        self, request: Mapping[str, Any], receipt: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Re-evaluate ``request`` and report the receipt fields it does not reproduce."""
        return self.invoke(
            "functional_verify", {"request": dict(request), "receipt": dict(receipt)}
        )

    def ddc_verify_tape(
        self,
        initial_state: Mapping[str, Any],
        steps: Sequence[Mapping[str, Any]],
        genesis_root: str | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Replay a DDC tape through verify_step and return the first violation or head hash.

        The payload is ``DdcVerifyTapeRequestV1``: ``initial_state`` and
        ``steps`` are required, ``genesis_root`` is optional, and the host
        denies any other field.
        """
        payload: dict[str, Any] = {
            "initial_state": dict(initial_state),
            "steps": [dict(step) for step in steps],
        }
        if genesis_root is not None:
            payload["genesis_root"] = genesis_root
        return self.invoke("ddc_verify_tape", payload)

    def prime_admit(
        self, declaration: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Execute the Prime 000 admission gate."""
        return self.invoke("prime_admit", declaration)

    def prime_replay_decide(
        self, payload: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Replay a Prime tape and return the terminal or refusal outcome."""
        return self.invoke("prime_replay_decide", payload)

    def lggr_classify(
        self, e1: bool, e2: bool, eg: bool, trace_id: str | None = None
    ) -> Result[Mapping[str, Any], Refusal]:
        """Classify evaluator gluing defect Δ_E = E_g - E_1 E_2 exactly."""
        payload: dict[str, Any] = {"e1": e1, "e2": e2, "eg": eg}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        return self.invoke("lggr_classify", payload)

    def lggr_soundness(
        self, d_matrix: Sequence[Sequence[str]], q_matrix: Sequence[Sequence[str]]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Check exact LGGR V soundness rank(Q·D) = rank(D) with unsoundness witness."""
        payload = {
            "d": {"rows": [list(row) for row in d_matrix]},
            "q": {"rows": [list(row) for row in q_matrix]},
        }
        return self.invoke("lggr_soundness", payload)

    def pharmacy_detect(
        self,
        candidate_json: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch candidate text or JSON object to the native pharmacy detector."""
        payload: dict[str, Any] = {"candidate": candidate_json}
        if context is not None:
            payload["context"] = context
        return self.invoke("pharmacy_detect", payload)

    def verify_phi1_form(
        self,
        weights: Sequence[str],
        residual_at_achiever: Sequence[str],
        dual: Sequence[str],
        coboundaries: Sequence[Sequence[str]],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch exact rational primal-dual certificate verification to native certifier."""
        payload = {
            "weights": list(weights),
            "residual_at_achiever": list(residual_at_achiever),
            "dual": list(dual),
            "coboundaries": [list(row) for row in coboundaries],
        }
        return self.invoke("verify_phi1_form", payload)

    def stabilizer_solve(self, case: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch finite quantum Hamiltonian solve to native Rust stabilizer solver."""
        return self.invoke_runtime("stabilizer_solve", {"case": dict(case)})

    def stabilizer_check(
        self, case: Mapping[str, Any], result: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch certificate check to native Rust total stabilizer checker."""
        return self.invoke_runtime(
            "stabilizer_check", {"case": dict(case), "result": dict(result)}
        )

    def jcs_canonicalize(
        self,
        value: Any = None,
        raw_json: str | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch JSON to native Rust RFC 8785 canonicalizer."""
        payload: dict[str, Any] = {}
        if value is not None:
            payload["value"] = value
        if raw_json is not None:
            payload["raw"] = raw_json
        return self.invoke_runtime("jcs_canonicalize", payload)

    def jcs_digest(
        self,
        value: Any = None,
        raw_json: str | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch JSON to native Rust RFC 8785 SHA-256 digest calculator."""
        payload: dict[str, Any] = {}
        if value is not None:
            payload["value"] = value
        if raw_json is not None:
            payload["raw"] = raw_json
        return self.invoke_runtime("jcs_digest", payload)

    def verify_decode_receipt(
        self, receipt: Mapping[str, Any]
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch decode control receipt to native Rust verifier."""
        return self.invoke_runtime("verify_decode_receipt", {"receipt": dict(receipt)})

    def detect_stationary_attractor(
        self,
        history: Sequence[Mapping[str, Any]],
        decided_variables: Sequence[str] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch turn history to native Rust stationary attractor detector."""
        payload: dict[str, Any] = {
            "history": [dict(rec) for rec in history],
            "decided_variables": list(decided_variables) if decided_variables is not None else [],
        }
        return self.invoke_runtime("detect_stationary_attractor", payload)

    def lean_scan_sources(
        self,
        sources: Sequence[Mapping[str, str]],
        forbidden_constructs: Sequence[str] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch Lean 4 source files to native Rust scanner."""
        payload: dict[str, Any] = {
            "sources": [dict(s) for s in sources],
            "forbidden_constructs": list(forbidden_constructs) if forbidden_constructs is not None else [],
        }
        return self.invoke_runtime("lean_scan_sources", payload)

    def lean_audit_report(
        self,
        axioms_output: str,
        policy: Sequence[str] | None = None,
        required_declarations: Sequence[str] | None = None,
        build_success: bool = True,
        harness_elaborated: bool = True,
        forbidden_findings: Sequence[Mapping[str, Any]] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch Lean verification components to native Rust auditor."""
        payload: dict[str, Any] = {
            "axioms_output": axioms_output,
            "policy": list(policy) if policy is not None else list(STANDARD_LEAN_AXIOMS),
            "required_declarations": list(required_declarations) if required_declarations is not None else [],
            "build_success": build_success,
            "harness_elaborated": harness_elaborated,
            "forbidden_findings": [dict(f) for f in forbidden_findings] if forbidden_findings is not None else [],
        }
        return self.invoke_runtime("lean_audit_report", payload)

    def decompose_task(
        self,
        basis_kind: str,
        vertices: Sequence[str] | None = None,
        edges: Sequence[Mapping[str, Any]] | None = None,
        tree_edges: Sequence[Mapping[str, Any]] | None = None,
        case: Mapping[str, Any] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch task decomposition to native Rust cycle basis or stabilizer basis decomposer."""
        payload: dict[str, Any] = {
            "basis_kind": basis_kind,
            "vertices": list(vertices) if vertices is not None else [],
            "edges": [dict(e) for e in edges] if edges is not None else [],
            "tree_edges": [dict(te) for te in tree_edges] if tree_edges is not None else [],
            "case": dict(case) if case is not None else None,
        }
        return self.invoke_runtime("decompose_task", payload)

    def prime_descent(
        self,
        *,
        run_id: str,
        carrier: Mapping[str, Any],
        omega: Sequence[int],
        max_steps: int = 64,
        grant: Mapping[str, Any] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch prime descent coordination to native Rust engine."""
        payload: dict[str, Any] = {
            "run_id": run_id,
            "carrier": dict(carrier),
            "omega": list(omega),
            "max_steps": max_steps,
        }
        if grant is not None:
            payload["grant"] = dict(grant)
        return self.invoke_runtime("prime_descent", payload)

    def evaluate_prompt_cochain(
        self,
        *,
        complex: Mapping[str, Any],
        cochain: Sequence[Any],
        primal_potential: Sequence[Any] | None = None,
        dual_witness: Sequence[Any] | None = None,
        triad_context: Mapping[str, Any] | None = None,
        budget: int | None = None,
        source_bytes: str | None = None,
        expected_source_hash: str | None = None,
        protected_answers: Mapping[str, str] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Dispatch prompt-to-cochain evaluation to native Rust host."""
        payload: dict[str, Any] = {
            "complex": dict(complex),
            "cochain": list(cochain),
        }
        if primal_potential is not None:
            payload["primal_potential"] = list(primal_potential)
        if dual_witness is not None:
            payload["dual_witness"] = list(dual_witness)
        context = dict(triad_context) if triad_context is not None else {}
        for key, value in (
            ("remaining_budget", budget),
            ("source_bytes", source_bytes),
            ("expected_source_hash", expected_source_hash),
            ("protected_answers", dict(protected_answers) if protected_answers is not None else None),
        ):
            if value is not None:
                if key in context:
                    return Err(
                        Refusal(
                            "COCHAIN_CONTEXT_CONFLICT",
                            f"triad_context and a convenience argument both supply {key}",
                        )
                    )
                context[key] = value
        if triad_context is not None or context:
            payload["triad_context"] = context
        return self.invoke_runtime("cochain_evaluate", payload)



# Global singleton instance for thin Python wrappers
_DEFAULT_HOST: RustSymbolGameHost | None = None


def get_default_host() -> RustSymbolGameHost:
    global _DEFAULT_HOST
    if _DEFAULT_HOST is None:
        _DEFAULT_HOST = RustSymbolGameHost()
    return _DEFAULT_HOST


def evaluate_prompt_cochain(
    *,
    complex: Mapping[str, Any],
    cochain: Sequence[Any],
    primal_potential: Sequence[Any] | None = None,
    dual_witness: Sequence[Any] | None = None,
    triad_context: Mapping[str, Any] | None = None,
    budget: int | None = None,
    source_bytes: str | None = None,
    expected_source_hash: str | None = None,
    protected_answers: Mapping[str, str] | None = None,
    host: RustSymbolGameHost | None = None,
) -> Result[Mapping[str, Any], Refusal]:
    """Top-level FFI function delegating prompt-to-cochain evaluation to RustSymbolGameHost."""
    target_host = host if host is not None else get_default_host()
    return target_host.evaluate_prompt_cochain(
        complex=complex,
        cochain=cochain,
        primal_potential=primal_potential,
        dual_witness=dual_witness,
        triad_context=triad_context,
        budget=budget,
        source_bytes=source_bytes,
        expected_source_hash=expected_source_hash,
        protected_answers=protected_answers,
    )


def evaluate_prompt_cochain_disposition(
    *,
    complex: PromptCellComplex | Mapping[str, Any],
    cochain: Sequence[Any],
    primal_potential: Sequence[Any] | None = None,
    dual_witness: Sequence[Any] | None = None,
    triad_context: PrimeTriadContext | Mapping[str, Any] | None = None,
    host: PromptCochainHost | None = None,
) -> CochainDisposition:
    """Resolve the adapter default before the domain serializes or evaluates input."""
    target_host = host if host is not None else get_default_host()
    from pfp.domain.cochain import (
        evaluate_prompt_cochain as evaluate_domain_cochain,
    )

    return evaluate_domain_cochain(
        complex=complex,
        cochain=cochain,
        primal_potential=primal_potential,
        dual_witness=dual_witness,
        triad_context=triad_context,
        host=target_host,
    )

