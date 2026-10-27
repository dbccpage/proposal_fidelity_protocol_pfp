# OEWAS008 narrowing verification and retirement hold

AuthorityEffect: None. Full epic status: **RESEARCH_HOLD**.

The existing specialization contract passes **23 tests**, including real native checks. Each of the three Python widening guards was independently bypassed in a fresh pytest process: the existing refusal test failed at the intended port, terminal or budget boundary, while the positive narrowing control passed. Exact original bytes were restored after every probe, and the same 23 tests passed again. This is reuse and verification of existing GREEN behavior; no production defect, new test, migration or completion is asserted.

The [execution receipt](oewas_008_narrowing_20261010.json) retains exact commands, exit statuses, tool-returned output, before/mutant/restored digests and tested scope. Runtime: Python 3.13.11, pytest 9.1.1, uv 0.9.28. One existing test file ran per batch; no broad suite or Cargo build ran.

## Verified bounded behavior

| Public boundary | Input/control | Observed result |
| --- | --- | --- |
| [specialize](../../adversary/domain/specialization.py) | Child adds ports, routing terminals or budget beyond its immediate parent; valid narrowed child control | Typed PORT_WIDENING, TERMINAL_WIDENING and BUDGET_WIDENING refusals; all three actual guard bypasses detected |
| [check_specialization / native_base](../../adversary/infrastructure/specialization_check.py) | Actual native base; one single-port/terminal narrow child; structurally valid paid child | Narrow child accepted with AuthorityEffect None; paid child refused BUDGET_WIDENING |
| [OewasContainer.api.compile_projection](../infrastructure/bootstrap.py) | One temporary SQLite catalog with a RETIRED operation, a replacement declaration satisfying the existing lifecycle predicate, and an existing alias to that replacement | Both operation IDs emitted; lifecycle/admission, aliases and replacement-route fields absent |
| [HigherOperadAdapter.authorize_term](../infrastructure/operad/higher_operad_adapter.py) | Retired and replacement operation terms | Both refuse LICENSE_WITNESS_REQUIRED |

The projection's exact five fields are catalog_id, epoch, operations, skills and target_format. Its independently recomputed payload SHA-256 is `9dabe84e3163916f24b9a86ddf4b2b4367b1fd9c93ce21eb833514db671a4c3a`. The stored retired lifecycle predicate is false and the replacement predicate is true. Those lifecycle fields were seeded as temporary declarations: the observation does not validate their executors, activate a route or admit a production capability. Both terms' common witness refusal does not demonstrate a retirement-specific access decision.

## Source and native custody

Python source/test base: `ae33a85a60559c727295be055cff79d0c8a20a5c`, branch `codex/oewas-008-narrowing`. Production and existing test bytes are unchanged from that base. The specialization module restored to SHA-256 `38e142b00a7a0a57f90ad9ae863bd05ca84b3d69e551d9a97add661962c27ace`.

The external host is the published [C011 candidate / PR704](https://github.com/dbccpage/the_symbol_game/pull/704), source commit `788493dd6b6e09b62754286e23d62a0332e3293f`. Its native build snapshot records base3d06 plus that candidate's pinned source inventory; it is separate from this Python base. The host stayed SHA-256 `70e90235311421dda175bddc76b6c848171edb638b36dbef2eab1995422ef4b9` (28,354,048 bytes). Both inventory blobs were read from that immutable commit and independently matched their supplied pins: original build snapshot `96b6da603d449e3cd8fadac65822e31db7a18339243dcd206f344dfe40abe8d7`; later final candidate inventory `e7f9cd51852dcf57f31796c4d9ded09204149d6d27bd5718511003c5bc4d6085`. This receipt does not attest a reproducible native build.

Native specialization_validate checks the candidate against the Adversary base. The mutation-tested Python specialize relation checks the immediate parent. These distinct boundaries do not establish all-caller route coverage or retirement enforcement.

## Owned residuals blocking estate migration

OEWAS008 and its projection/host owners must agree lifecycle and retirement representation in the existing projection payload and bind its actual consuming verification port before a retirement RED test. No native consumer of this payload has been bound by this work; the current producer cannot supply the absent fields. Another registry would not resolve that dependency.

OEWAS008 owns reviewed old-to-replacement routing, real caller coverage, reference closure, recoverable archived source bytes and rollback. OEWAS004 owns package parity, Adversary SAGA6 owns runtime narrowing, and each host owner supplies activation evidence. These obligations remain open. This evidence does not test four-host package rollback, old-receipt transplantation at a retirement verifier, disabled legacy executable access or estate-wide closure.

No live package was migrated, moved or deleted. No source feature, retirement registry, test hierarchy, authorization witness, host binary or epic plan was changed. Preserve that hold until the real consumer, caller coverage and archived bytes are available.
