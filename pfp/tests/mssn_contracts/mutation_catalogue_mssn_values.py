"""Replayable decision mutants for the MSSN grammar bounded context."""

from operations.use_cases.verification.mutation_harness import Mutant

_TARGET = "pfp/domain/mssn_research"
_WITNESS = (
    "pfp/tests/mssn_contracts/test_mssn_domain_value_objects.py",
)

DEFAULT_TESTS = _WITNESS

MUTANTS = (
    Mutant(
        mutant_id="MSSN_VO_001",
        intent="Probability mass above one would be admitted.",
        target=f"{_TARGET}/grammar/lexical.py",
        anchor="if self.mass.numerator > self.mass.denominator:",
        applied="if self.mass.numerator < self.mass.denominator:",
        tests=_WITNESS,
    ),
    Mutant(
        mutant_id="MSSN_VO_002",
        intent="A 63-character digest would be admitted as a content identity.",
        target=f"{_TARGET}/shared_kernel/value_objects.py",
        anchor='if not re.fullmatch(r"[0-9a-fA-F]{64}", raw):',
        applied='if not re.fullmatch(r"[0-9a-fA-F]{63,64}", raw):',
        tests=_WITNESS,
    ),
    Mutant(
        mutant_id="MSSN_GRAMMAR_003",
        intent="A frontier with more candidates than its vocabulary would be admitted.",
        target=f"{_TARGET}/grammar/entities.py",
        anchor="if len(candidates) > vocabulary_size:",
        applied="if len(candidates) < vocabulary_size:",
        tests=("pfp/tests/mssn_contracts/test_grammar_ddd.py",),
    ),
    Mutant(
        mutant_id="MSSN_GRAMMAR_004",
        intent="A valid host receipt would bypass authority validation.",
        target=f"{_TARGET}/grammar/authority_policies.py",
        anchor=("if packet.proposal.requested_status == HorizonStatus.CERTIFIED_GREEN "
                "and packet.receipt is None:"),
        applied=("if packet.proposal.requested_status == HorizonStatus.CERTIFIED_GREEN "
                 "and packet.receipt is not None:"),
        tests=("pfp/tests/mssn_contracts/test_levels_15_to_21_grammar_ddd.py",),
    ),
    Mutant(
        mutant_id="MSSN_CODEC_005",
        intent="A ledger whose declared and actual entry counts agree would be refused.",
        target=("pfp/infrastructure/adapters/mssn_research/contracts/grammar/"
                "ledger_codec.py"),
        anchor="if actual < declared:",
        applied="if actual <= declared:",
        tests=("pfp/tests/mssn_contracts/test_epistemic_quarantine_repository.py",),
    ),
    Mutant(
        mutant_id="MSSN_LIFT_006",
        intent="An exact lift certificate type would be refused before evidence replay.",
        target=f"{_TARGET}/grammar/lift_policies.py",
        anchor="if type(cert) is not LiftNecessityCertificate:",
        applied="if type(cert) is LiftNecessityCertificate:",
        tests=("pfp/tests/mssn_contracts/test_lift_necessity_certificate.py",),
    ),
)
