Use as many agents as you can. Create comprehensive, code-accurate documentation for the PFP repository in a new `documentation/` directory, analyzing operators, EIS, Prompt Sieve, and workflows through a 5-step research, review, adversarial attack, and reconciliation process.

Integrity mode: [OPEN: What shortcuts should the team NOT be allowed to take?]

## Requirements

### R1. Operator Discovery and Classification
Identify and catalog every class of operator used across the repository, targeting 12 to 24 distinct operator types including skills, anti-skills, rules, anti-rules, agents, anti-agents, antibodies, and Discrete Deformation Calculus (DDC) operators. Document how operators remove obstruction or construct structure, and how they are indexed and reused by prompt family, lineage, domain, subdomain, and sub-subdomain.

### R2. EIS (Epistemic / Execution Immune System) Code-Grounded Documentation
Produce detailed documentation in `documentation/EIS/` explaining what is built in EIS based strictly on the actual code implementation (excluding unverified comments or docstring claims). Detail antibody types, collection mechanisms, and operational usage.

### R3. Prompt Sieve (P Sieve / pciv) Code-Grounded Documentation
Produce detailed documentation explaining Prompt Sieve implementation based strictly on the code: how seed prompts are ingested and processed, handling of nested prompts, prompt family formation, family tracking, and prompt evolution management.

### R4. Workflow and PFP Documentation
Document how PFP is used across all workflows in the repository. Provide a dedicated documentation file for every workflow under `documentation/workflows/`, describing its execution steps, operators, and integration points.

### R5. 5-Step Adversarial Documentation Process
For each documented file and component, execute a five-step cycle:
1. Research: inspect source code implementation.
2. Review: draft initial factual documentation.
3. Adversarial attack: challenge claims and test whether statements hold against the code.
4. Defense and recovery: substantiate or correct documentation using direct code citations.
5. Joint review: reconcile findings into final verified documentation.

## Acceptance Criteria

### Directory Layout & Coverage
- [ ] Folder `documentation/` exists with subdirectories for workflows, EIS, Prompt Sieve, and operators [OPEN: Directory layout for operators and p_sieve].
- [ ] Every workflow in `workflows/` has an individual documentation file in `documentation/workflows/`.
- [ ] Operator documentation identifies and details all operator classes (targeting 12 to 24 classes, including DDC and antibody types).
- [ ] EIS documentation covers antibody types, collection, and usage grounded in code citations.
- [ ] Prompt Sieve documentation covers seed prompt processing, nested prompts, family tracking, and evolution grounded in code citations.

### Code Fidelity & Adversarial Verification
- [ ] All statements describe actual code mechanisms rather than docstring or comment assertions.
- [ ] [OPEN: Storage location and format for the 5-step adversarial attack/review logs].
- [ ] [OPEN: Programmatic verification mechanism / validation script for documentation completeness and code ground truth].
