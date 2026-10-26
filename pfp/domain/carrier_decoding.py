"""Constrained decoding against a declared carrier.

WP-7 of the OEv1.0 Symbol Game build, and the part of the design that is not
prompt engineering: instead of asking a model to stay inside the carrier, the
decoder is configured so that leaving it is not expressible, and the emission is
then measured rather than trusted.

What you can actually get, per provider
---------------------------------------

The guarantee is not uniform, and pretending otherwise would be the same class
of overclaim this subsystem exists to refuse. Three tiers, and only the first is
exact:

* ``GRAMMAR`` -- the sampler is restricted to a formal language before any token
  is drawn. Output outside the carrier is unrepresentable, not merely unlikely.
  Requires a backend that accepts a grammar.
* ``LOGIT_BIAS`` -- an OpenAI-compatible API accepts a per-token bias in
  ``[-100, +100]``. A bias of ``-100`` is documented as a ban and is
  overwhelming in practice, but it is a **bounded** additive term, not
  ``-inf``. Softmax of a large negative logit is very small and is not zero.
  This tier is a strong bias, and this module will not call it exact.
* ``UNCONSTRAINED`` -- nothing can be imposed at decode time. The reply is
  ordinary text and only verification stands between it and the receipt.

A correction this module carries
--------------------------------

An earlier framing said masking non-carrier logits gives "exact zeros -- a
genuine projection onto the carrier face". Through a hosted API that is false
twice over: the bias is bounded rather than ``-inf``, so the probabilities are
small rather than zero; and even where the support really is restricted, the
renormalised restriction is the KL/I-projection of the distribution onto the
carrier-supported family, not a Euclidean projection onto a face.

Exactness is available, but it comes from a grammar-constrained sampler, not
from a prompt and not from a bias parameter.

Verification is unconditional
-----------------------------

Whatever tier applied, [`verify_emission`] runs and the result is recorded. A
run that could not be constrained is not thereby excused from being checked; it
is the run that needs checking most.

AuthorityEffect: None. A verified emission is evidence about an emission, and
nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .glyph_calculus import Carrier, Finding
from .ports.decode_control_port import ControlKind, DecodeControlSpec, GrammarMask

__all__ = [
    "BLIND_SPOT_TOKEN_BOUNDARY",
    "CONSTRAINT_BY_PROVIDER",
    "ConstraintMode",
    "DecodingReceipt",
    "carrier_gbnf",
    "integer_slots_control",
    "integer_slots_gbnf",
    "logit_bias_ban",
    "parse_integer_slots",
    "resolve_constraint",
    "verify_emission",
]

#: An OpenAI-compatible bias low enough to be documented as a ban. It is a
#: bound, not an infinity, which is exactly why LOGIT_BIAS is not exact.
OPENAI_BAN_BIAS = -100

#: The blind spot a per-token ban cannot close, named rather than implied.
#:
#: The predicate is over TOKENS; the property is over the emitted STRING. On a
#: byte-level BPE vocabulary a single token can decode to a fragment of a
#: multi-byte character, so two pieces that each look admissible can concatenate
#: into a character the carrier does not declare -- and two that each look
#: inadmissible can concatenate into one it does. Banning per token cannot see
#: across that boundary.
#:
#: This is why `verify_emission` runs unconditionally and why LOGIT_BIAS is not
#: exactness. The bias reduces the chance; the measurement is what establishes
#: anything.
BLIND_SPOT_TOKEN_BOUNDARY = "token_boundary_vs_character_boundary"


class ConstraintMode(str, Enum):
    """How hard the carrier was enforced at decode time."""

    GRAMMAR = "grammar"
    LOGIT_BIAS = "logit_bias"
    UNCONSTRAINED = "unconstrained"

    @property
    def rank(self) -> int:
        """Ordering for "at least as strong as". Not a score."""
        return {
            ConstraintMode.UNCONSTRAINED: 0,
            ConstraintMode.LOGIT_BIAS: 1,
            ConstraintMode.GRAMMAR: 2,
        }[self]

    @property
    def is_exact(self) -> bool:
        """Whether output outside the carrier was *unrepresentable*.

        Only a grammar-constrained sampler earns this. A bounded bias makes
        the wrong token very unlikely, which is a different claim and a weaker
        one.
        """
        return self is ConstraintMode.GRAMMAR


#: What each provider gateway can impose. Keyed by the provider's wire name so
#: this module does not import the swarm's provider enum, which would couple
#: the Symbol Game domain to the research host.
#:
#: `local` is grammar-capable because the llama.cpp backend behind Ollama
#: accepts GBNF. `anthropic` and `gemini` expose no per-token bias at all.
CONSTRAINT_BY_PROVIDER: dict[str, ConstraintMode] = {
    "fixture": ConstraintMode.GRAMMAR,
    "local": ConstraintMode.GRAMMAR,
    "openai": ConstraintMode.LOGIT_BIAS,
    "groq": ConstraintMode.LOGIT_BIAS,
    "grok": ConstraintMode.LOGIT_BIAS,
    "deepseek": ConstraintMode.LOGIT_BIAS,
    "openrouter": ConstraintMode.LOGIT_BIAS,
    "nvidia": ConstraintMode.LOGIT_BIAS,
    "anthropic": ConstraintMode.UNCONSTRAINED,
    "gemini": ConstraintMode.UNCONSTRAINED,
}


def provider_capability(provider: str) -> ConstraintMode:
    """The strongest constraint this provider *can* impose.

    A capability, **not** a receipt field. What a provider is able to do and
    what a given run actually did are different facts, and conflating them is
    how a receipt comes to assert a guarantee nobody supplied: the mode was
    read from this table by provider name, so a run against ``local`` reported
    "non-carrier output was unrepresentable" whether or not a grammar was ever
    handed to a sampler.

    An unknown provider resolves DOWN to ``UNCONSTRAINED``. Guessing upward
    would invent an entitlement.
    """
    return CONSTRAINT_BY_PROVIDER.get(provider.strip().lower(), ConstraintMode.UNCONSTRAINED)


# Retained under the old name for callers that want the capability, so the
# rename cannot silently change anyone's meaning.
resolve_constraint = provider_capability


def carrier_gbnf(carrier: Carrier) -> str:
    """A GBNF grammar admitting exactly non-empty strings over the carrier.

    This is the mechanism that makes the guarantee exact: the sampler cannot
    draw a token that would take the output outside the language, so no
    non-carrier emission exists to be caught later.
    """
    alternatives = " | ".join(f'"{member.char}"' for member in carrier.members)
    return f"root ::= sym+\nsym  ::= {alternatives}\n"


def _check_integer_slot_count(k: int) -> None:
    if type(k) is not int or not 3 <= k <= 12:
        raise ValueError("C004 requires an exact integer slot count from 3 to 12")


def integer_slots_gbnf(k: int) -> str:
    """C004's exactly k signed ASCII integers, separated by one ASCII space.

    Unlike ``carrier_gbnf``, this language constrains slot structure. Integer
    magnitude is unrestricted; the original task bounds the input claims, not
    the proposed repair. The carrier excludes a plus sign. Leading zeros and
    negative zero remain integers and are not silently normalized.

    This supplies GBNF for a compatible sampler; constructing or requesting it
    is not evidence that a tokenizer-aware sampler enforced it. The original
    local masks, pinned model/tokenizer, F-null token identity, reasoning-span
    arm and paired ladder protocol remain separate experiment requirements.
    """
    _check_integer_slot_count(k)
    slots = ' " " '.join(["integer"] * k)
    return f'root ::= {slots}\ninteger ::= "-"? [0-9]+\n'


def integer_slots_control(
    k: int, *, temperature: str = "0", max_tokens: int = 64
) -> DecodeControlSpec:
    """Hand the C004 slot grammar to the existing decode-control port.

    Token caps may truncate an otherwise constrained emission; callers still
    check the actual output and retain the runner's original token IDs.
    """
    return DecodeControlSpec(
        control_kind=ControlKind.GBNF,
        grammar_mask=GrammarMask(integer_slots_gbnf(k), grammar_type="gbnf"),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def parse_integer_slots(text: str, k: int) -> tuple[str, ...] | None:
    """Check the complete emitted shape independently of a runner's claim.

    Return the exact integer strings without stripping, coercing or repairing
    the response. Shape acceptance says nothing about zero sum or weighted L1
    optimality; those require the independent mathematical judges.
    """
    _check_integer_slot_count(k)
    if type(text) is not str:
        return None
    slots = tuple(text.split(" "))
    if len(slots) != k or any(re.fullmatch(r"-?[0-9]+", slot) is None for slot in slots):
        return None
    return slots


def logit_bias_ban(
    token_ids: dict[str, int],
    carrier: Carrier,
    *,
    protected_ids: frozenset[int],
) -> dict[int, int]:
    """Ban every token that could take the emission outside the carrier.

    `token_ids` maps a decoded piece to its id in the model's vocabulary; the
    caller supplies it because tokenisation is a property of the model, not of
    the carrier.

    The result is a *bias*, and the receipt must not describe it as a mask.

    The predicate, and the bug it replaces
    --------------------------------------

    A token is admissible when **every character it decodes to** is a declared
    carrier member -- ``set(piece) <= allowed``, not ``piece in allowed``.

    The old membership test compared a whole token against a set of single
    characters, so it banned every multi-character piece, including `"alpha
    beta"` spelled as one token of two carrier glyphs. On a vocabulary that
    merges carrier symbols into single pieces -- which is exactly what BPE does
    to a small repeated alphabet -- that bans the carrier language itself and
    leaves the model no admissible token at all. The ban was not "ban
    non-carrier"; it was "ban everything but single-glyph tokens".

    The empty piece is admissible under the subset test, since the empty set is
    a subset of anything. That is correct: an empty decode contributes no
    character and cannot leave the carrier.

    Why `protected_ids` is required and not defaulted
    -------------------------------------------------

    EOS decodes to no carrier glyph, so the subset test bans it -- and a model
    that cannot emit EOS **cannot stop**. The ban intended to constrain the
    alphabet would instead prevent termination, and the failure would look like
    a hang rather than a constraint bug. The same holds for any control or
    whitespace token a backend needs.

    The caller must therefore say which ids are exempt, and pass an explicit
    empty set if it truly has none. Defaulting to empty would make the
    dangerous choice the silent one, the way defaulting a decode tier upward
    once made an unearned guarantee the silent one.

    What this still cannot do
    -------------------------

    See :data:`BLIND_SPOT_TOKEN_BOUNDARY`. The predicate is per token and the
    property is per string.
    """
    allowed = carrier.glyphs
    return {
        token_id: OPENAI_BAN_BIAS
        for piece, token_id in token_ids.items()
        if token_id not in protected_ids and not set(piece) <= allowed
    }


def verify_emission(text: str, carrier: Carrier) -> tuple[Finding, ...]:
    """Measure whether the emission stayed inside the carrier.

    Runs whatever the constraint tier was. This is the acceptance criterion for
    WP-7 -- emitted symbols are a subset of the carrier, established from the
    run rather than requested in the prompt.
    """
    return carrier.check_term(text)


@dataclass(frozen=True, slots=True)
class DecodingReceipt:
    """What constrained this run, and what the emission actually contained.

    Carried into `calculus_receipt` so a reader can tell an exact guarantee
    from a strong bias from no guarantee at all. A receipt that recorded only
    "constrained: true" would be worse than none, because it would give a
    reader a documented reason to believe something untrue.
    """

    provider: str
    #: What the caller says it ACTUALLY applied to the sampler.
    mode: ConstraintMode
    #: What the provider is capable of, for comparison. A gap between the two
    #: is not an error -- it is the fact that a lever was available and not
    #: pulled, which a reader is entitled to see.
    capability: ConstraintMode
    violations: tuple[Finding, ...]

    @classmethod
    def measure(
        cls,
        provider: str,
        text: str,
        carrier: Carrier,
        *,
        applied: ConstraintMode = ConstraintMode.UNCONSTRAINED,
    ) -> "DecodingReceipt":
        """Record what a run actually did, not what its provider could have done.

        `applied` is what the caller handed to the sampler, and it defaults DOWN
        to ``UNCONSTRAINED``: a caller that says nothing gets no guarantee. It
        was previously derived from the provider name, which meant the receipt
        claimed exactness for any run against a grammar-capable provider
        whether or not a grammar was ever built -- a lever that cannot be shown
        to have fired must not appear in a receipt as though it had.

        Claiming more than the provider can deliver is refused outright rather
        than silently clamped, because a caller asserting a tier the API cannot
        supply has a bug the receipt should not paper over.
        """
        capability = provider_capability(provider)
        if applied.rank > capability.rank:
            raise ValueError(
                f"run claims {applied.value} but provider {provider!r} can only "
                f"supply {capability.value}; a receipt may not assert a "
                "constraint the API cannot impose"
            )
        return cls(
            provider=provider,
            mode=applied,
            capability=capability,
            violations=verify_emission(text, carrier),
        )

    @property
    def emission_within_carrier(self) -> bool:
        return not self.violations

    @property
    def guarantee(self) -> str:
        """One line a human can read without having to know the tiers."""
        if not self.emission_within_carrier:
            return "violated: the emission left the carrier"
        if self.mode.is_exact:
            return "exact: non-carrier output was unrepresentable, and none appeared"
        if self.mode is ConstraintMode.UNCONSTRAINED and self.capability.is_exact:
            return (
                "checked only: nothing constrained this run, though the provider "
                "could have -- an available lever was not pulled"
            )
        if self.mode is ConstraintMode.LOGIT_BIAS:
            return (
                "biased: non-carrier tokens were banned by a bounded bias, "
                "not made impossible, and the ban is per token while the "
                f"property is per string ({BLIND_SPOT_TOKEN_BOUNDARY}); "
                "the emission was checked and is clean"
            )
        return "checked only: nothing constrained this run; the emission is clean"

    def to_wire(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "constraint_applied": self.mode.value,
            "constraint_available": self.capability.value,
            "constraint_is_exact": self.mode.is_exact,
            "emission_within_carrier": self.emission_within_carrier,
            "violations": [str(finding) for finding in self.violations],
        }
