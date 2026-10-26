"""Judge-packet audit harness for the current PFP challenge packages.

An offline, deterministic measurement of what the packages' dual-checker
judge packets accept and how they bind their evidence:

- trivial responders driven through each package's own checker functions;
- import and textual dependence between the two checkers and the reference;
- LF and CRLF replay of every recorded digest;
- a leakage lint over judge cases, participant examples and prompt builders;
- mutation-suite size and distinct payloads;
- independent recomputation of reference values where one is feasible.

Entry point: ``audit.run``. The harness makes no model or provider calls and
disables network access inside the subprocesses that import package code.
"""
