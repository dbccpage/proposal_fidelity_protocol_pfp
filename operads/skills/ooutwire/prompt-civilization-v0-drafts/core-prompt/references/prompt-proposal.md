# Prompt proposal wire

Supply an exact JSON object with these fields and no others:

```json
{
  "objective": "One bounded intended outcome",
  "claim_mode": "none | investigate | verify | prove",
  "in_scope": ["Included work"],
  "out_of_scope": ["Excluded work"],
  "inputs": ["Path, URL, artifact, or supplied fact"],
  "constraints": ["Must remain true"],
  "acceptance_criteria": ["Replayable completion check"],
  "evidence_requirements": ["Independent checker or source requirement"],
  "requested_effects": ["workspace-write, git-push, external-message, ..."],
  "candidate_budget": 3,
  "operation_budget": 20,
  "nonclaims": ["What this prompt will not establish"],
  "unresolved_questions": [],
  "proposed_prompt": "Candidate instruction shown to the operator"
}

```

Use empty arrays rather than invented content. A consequential prompt cannot be approved with missing acceptance criteria or unresolved material questions. `verify` and `prove` require explicit evidence requirements.
