# Steering: compact prompt profiles

Long runs pile up history: earlier findings, certificates, procedures and raw
replies. The source project hit a real prompt overflow on a long run and fixed
it by changing what each role's prompt carries, not by raising the limit. The
fix keeps everything on disk and replaces repeated material in the prompt with
labelled digest references.

## What the source did

Three role-prompt profiles were kept side by side:

| Profile | What a role sees |
| --- | --- |
| `legacy-v1` | The historical prepared prompt, kept so old prompts and receipts replay with their original meaning |
| `compact-v1` | Role-relevant context, the complete task and operator guidance, and a digest of the full action |
| `compact-v2` | Current findings and typed answers in full; duplicated historical findings, observed procedures, certificates and raw replies as digest references |

Rules for `compact-v2`:

- every procedure step keeps its operation, input and output types, effects,
  residuals and evidence fields, plus the digest of the original step;
- omitted text is marked as a digest reference, and **a model must not claim to
  have read omitted text**;
- unresolved findings for the current action stay in full;
- writing targets were 150 characters per summary and 200 per finding, below
  unchanged hard schema ceilings. A provider can still exceed them; PFP keeps
  the actual bytes and refuses them;
- the profile also asks for strict provider JSON with reasoning disabled through
  the decoding contract. A provider or model that cannot honour those settings
  is refused instead of silently falling back.

The overflow was tested offline by replaying the exact over-long run: the old
binding stays frozen, the new profile fits the prompt limit, and changing a
certificate changes the projected digest so an old reply cannot be rebound to it.

## Replicate it here

The profiles live in the local swarm, which now runs (see
[running the local swarm](Steering.md#running-the-local-swarm)); select one with `teamwork start --response-profile compact-v2`
(`ops/adversary/use_cases/teamwork_pfp.py` and `ops/adversary/use_cases/teamwork.py`,
selected with `--response-profile` in `ops/adversary/entrypoints/teamwork_cli.py`).

The technique itself needs nothing special. When a prompt would repeat material
the host already holds, replace it with a line such as
`[omitted: certificate sha256:...; not shown to you]`, keep the full bytes in
the run folder, and bind the digest into the prompt's own digest so the reply is
tied to exactly what was shown. The
[provider byte ceilings](Test-Provider-Byte-Ceilings.md) demo shows the
refusal side for a prompt that is still too large.

## How it relates to PFP, EIS and PCIV

- **PFP.** The prompt digest covers the references, so compaction does not
  weaken the binding between prompt and reply. Schema validity is still not task
  acceptance.
- **PCIV.** Compaction is a mutation of the prompt template with a measurable
  effect (fits or overflows) and a fixed task, which is how variants should be
  compared.
- **EIS.** Admitted guidance is never compacted away; it is part of the current
  prompt, not history.

## Where the code lives

`ops/adversary/use_cases/teamwork_pfp.py`, `ops/adversary/use_cases/teamwork.py`,
`ops/adversary/infrastructure/teamwork_remote.py` and
`ops/adversary/entrypoints/teamwork_cli.py`.
