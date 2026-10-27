"""Unit tests for PFP domain models across all 10 core dimensions.

Covers:
  1. stages
  2. modes
  3. prompts
  4. packets
  5. demos
  6. gates
  7. contracts
  8. schemas
  9. normal_forms
  10. rewrites & wires

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import unittest

from pfp.domain.contracts.contracts import (
    ContractAuditReceipt,
    ContractSpec,
    Precondition,
)
from pfp.domain.contracts.gates import GateReceipt, GateSpec, GateVerdict, AdversaryGateId
from pfp.domain.contracts.schemas import (
    SchemaCatalog,
    SchemaSpec,
    SchemaValidationResult,
)
from pfp.domain.homology.carrier import Carrier, Edge, ProtoSupport
from pfp.domain.homology.cochain import (
    BoundaryMatrix,
    Cochain,
    IntegerChain,
    IntegerMatrix,
)
from pfp.domain.homology.ddc import DDCStep, DDCTape
from pfp.domain.normal_forms.contracts import (
    NFClassification,
    NFIdentity,
    NFPurpose,
    NormalFormContract,
    NormalFormVerificationReceipt,
)
from pfp.domain.prompts.packets import (
    PacketEnvelope,
    PacketVerificationReceipt,
    canonical_json_bytes,
    sha256_canonical_hex,
)
from pfp.domain.prompts.prompts import PromptPacket, PromptSlot, PromptTemplate
from pfp.domain.rewriting.rewrites import (
    Binding,
    Boundary,
    ComparisonTrial,
    RewriteReceipt,
    RewriteRequest,
    Segment,
    parse_boundary,
)
from pfp.domain.rewriting.wires import (
    AppTerm,
    AtomTerm,
    SyntaxProfile,
    TokenLegend,
    VoidTerm,
    WireCodec,
    WirePacket,
)
from pfp.domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from pfp.domain.stages.modes import (
    ModeCluster,
    ModeFile,
    ModesManifest,
    ModeSummary,
    VerifierContract,
)
from pfp.domain.stages.stages import (
    ControllerStageRef,
    Executor,
    InputContract,
    Stage1Response,
    Stage5Response,
    StageController,
    StageFile,
    StageName,
)


class TestPfpDomainModels(unittest.TestCase):
    """Test Pydantic v2 validation and invariants across all 10 PFP domain areas."""

    def test_01_stages_models(self) -> None:
        """Test StageFile, StageController, InputContract, and Stage Responses."""
        input_c = InputContract(preserve_original_seed=True, candidate_source_stage=4)
        self.assertTrue(input_c.preserve_original_seed)

        stage_ref = ControllerStageRef(
            stage=1,
            name=StageName.ADMIT,
            executor=Executor.HOST,
            requires=[],
        )
        self.assertEqual(stage_ref.stage, 1)

        # Invalid stage order check
        with self.assertRaises(ValueError):
            ControllerStageRef(
                stage=2,
                name=StageName.ADMIT,  # Wrong name for stage 2
                executor=Executor.MODEL,
                requires=[1],
            )

        resp1 = Stage1Response(
            stage=1,
            demo_id="demo_000",
            should_continue=True,
            admission_proposal={
                "status": "needs_declaration",
                "grammar": "finite",
                "equality_test": "exact bytes",
                "coefficient_profile": "declared",
                "missing_declarations": ["grammar"],
                "reason": "proposal only; the host still checks",
            },
        )
        self.assertTrue(resp1.should_continue)
        self.assertEqual(resp1.admission_proposal.status, "needs_declaration")

    def test_02_modes_models(self) -> None:
        """Test ModeFile, ModesManifest, and VerifierContract."""
        contract = VerifierContract(verifier_type="deterministic_evaluator", fail_closed=True)
        self.assertTrue(contract.fail_closed)

        mode_file = ModeFile(
            mode_id=1,
            name="Hieroglyphics & Glyph Alphabets",
            cluster=ModeCluster.CLUSTER_I__CARRIER___REPRESENTATION,
            core_mechanism="Symbolic token alphabet binding",
            substrate="ASCII / Unicode 38-glyph alphabet",
            paper_reference="coda_030",
            winning_condition="All expressions parse into valid carrier terms",
            verifier_contract=contract,
        )
        self.assertEqual(mode_file.mode_id, 1)

    def test_03_prompts_models(self) -> None:
        """Test PromptTemplate, PromptSlot, and PromptPacket."""
        slot = PromptSlot(name="seed", required=True)
        self.assertTrue(slot.required)

        template = PromptTemplate(
            template_id="tpl_pfp_default",
            version="1.0.0",
            system_format="System instructions for {mode}",
            user_format="Solve seed {seed}",
            slots=[slot],
        )
        self.assertEqual(template.template_id, "tpl_pfp_default")

        packet = PromptPacket(
            demo_id="demo_000",
            stage=1,
            system="System instructions for mode_01",
            user="Solve seed seed_alpha",
            response_schema={"type": "object"},
            authority_effect="None",
        )
        self.assertEqual(packet.demo_id, "demo_000")

    def test_04_packets_rfc8785(self) -> None:
        """Test RFC 8785 canonical JSON bytes and SHA-256 hash."""
        obj1 = {"b": 2, "a": 1}
        obj2 = {"a": 1, "b": 2}
        b1 = canonical_json_bytes(obj1)
        b2 = canonical_json_bytes(obj2)
        self.assertEqual(b1, b2)
        self.assertEqual(b1, b'{"a":1,"b":2}')

        h1 = sha256_canonical_hex(obj1)
        h2 = sha256_canonical_hex(obj2)
        self.assertEqual(h1, h2)

        env = PacketEnvelope(
            schema_id="env_001",
            task_data={"mode": "mode_02_packets"},
            protected_boundary="<envelope>",
            budget=1000,
            candidate_payload={"task": "cochain_check"},
            authority_effect="None",
        )
        self.assertTrue(len(env.envelope_hash) == 64)

    def test_05_demos_models(self) -> None:
        """Test DemoSpec, CheckResult, DemoRunReceipt."""
        spec = DemoSpec(
            id="demo_test",
            title="Test Demo",
            profile="exact",
            seed="seed_001",
        )
        self.assertEqual(spec.id, "demo_test")

        chk = CheckResult(name="check_matrix_rank", passed=True)
        receipt = DemoRunReceipt(
            demo_id="demo_test",
            runner_id="test_runner",
            all_passed=True,
            duration_sec=0.01,
            checks=[chk],
        )
        self.assertTrue(receipt.all_passed)
        self.assertEqual(len(receipt.checks), 1)

    def test_06_gates_models(self) -> None:
        """Test Adversary Gate specifications and verdicts."""
        spec = GateSpec(
            gate_id=AdversaryGateId.PFP_13_ADVERSARY.value,
            name="Adversary",
            character="Adversary",
            role="Reality anchor and final tribunal check",
            doctrine="Fail closed reality check",
            objective="Audit candidate validity against exact oracle",
        )
        self.assertEqual(spec.gate_id, "PFP-13-REALITY-GATE")

        verdict = GateVerdict(
            gate_id=AdversaryGateId.PFP_13_ADVERSARY.value,
            passed=True,
            character="Adversary",
            observation="Replay verified",
        )
        receipt = GateReceipt(
            candidate_id="cand_test",
            all_passed=True,
            terminal_disposition="Pass",
            verdicts=[verdict],
        )
        self.assertTrue(receipt.all_passed)

    def test_07_contracts_models(self) -> None:
        """Test ContractSpec and ContractAuditReceipt."""
        pre = Precondition(name="non_empty_seed", predicate="len(seed) > 0")
        spec = ContractSpec(
            contract_id="contract_transition",
            title="Stage Transition Contract",
            version="1.0.0",
            entry_preconditions=[pre],
            winning_condition="All preconditions and postconditions hold",
        )
        self.assertEqual(len(spec.entry_preconditions), 1)

        receipt = ContractAuditReceipt(
            contract_id="contract_transition",
            is_compliant=True,
        )
        self.assertTrue(receipt.is_compliant)

    def test_08_schemas_models(self) -> None:
        """Test SchemaSpec, SchemaCatalog, and SchemaValidationResult."""
        spec = SchemaSpec(
            schema_id="schema_test",
            title="Test Schema",
            definition={"type": "object", "properties": {"val": {"type": "integer"}}},
        )
        catalog = SchemaCatalog(schemas={"schema_test": spec})
        self.assertIn("schema_test", catalog.schemas)

        res = SchemaValidationResult(schema_id="schema_test", is_valid=True)
        self.assertTrue(res.is_valid)

    def test_09_normal_forms_models(self) -> None:
        """Test NormalFormContract and NormalFormVerificationReceipt."""
        ident = NFIdentity(
            id="nf.coda.test",
            name="Test Normal Form",
            short_name="TNF",
            version="v0",
        )
        purpose = NFPurpose(
            excludes_anomaly="Unverified claims",
            preserves_invariant="Epistemic truth",
        )
        contract = NormalFormContract(
            identity=ident,
            classification=NFClassification(),
            purpose=purpose,
            terminal_routes=["Accept", "Refuse"],
        )
        self.assertEqual(contract.identity.id, "nf.coda.test")

        receipt = NormalFormVerificationReceipt(
            normal_form_id="nf.coda.test",
            is_confluent=True,
            is_in_normal_form=True,
            chase_steps_count=0,
            terminal_route="Accept",
            defects_remaining=0,
        )
        self.assertTrue(receipt.is_confluent)

    def test_10_rewrites_and_wires(self) -> None:
        """Test boundary rewriting and Wire algebraic codec."""
        b = parse_boundary("<ab>")
        self.assertEqual(b.atom, "ab")

        seg = Segment(role="task", boundary="<task>", text="Solve seed")
        bind = Binding(symbol="d0", target_role="task", description="boundary symbol")
        self.assertEqual(bind.symbol, "d0")

        req = RewriteRequest(
            request_id="req_01",
            raw_prompt="The map d0 d0 is evaluated.",
            segments=[seg],
            bindings=[bind],
        )
        self.assertEqual(req.request_id, "req_01")

        # Wire codec tests
        v = VoidTerm()
        atom = AtomTerm(value="d0")
        app = AppTerm(operator="d1", arguments=[atom])
        self.assertEqual(WireCodec.serialize(v), "()")
        self.assertEqual(WireCodec.serialize(atom), "d0")
        self.assertEqual(WireCodec.serialize(app), "(d1 d0)")

        parsed = WireCodec.parse_s_expression("(d1 d0)")
        self.assertIsInstance(parsed, AppTerm)
        self.assertEqual(WireCodec.serialize(parsed), "(d1 d0)")


if __name__ == "__main__":
    unittest.main()
