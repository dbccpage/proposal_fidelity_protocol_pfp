# Template Substitution

Shows that building a prompt by successive string replacement can rewrite the inserted data, while a single template substitution does not.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/template_substitution/tests -q -p no:cacheprovider
python demos/template_substitution/run.py
python demos/template_substitution/run.py --input demos/template_substitution/examples/request.json
```

See the wiki page `Test-Template-Substitution`.
