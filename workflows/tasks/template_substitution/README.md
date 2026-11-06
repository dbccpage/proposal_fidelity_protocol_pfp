# Template Substitution

Shows that building a prompt by successive string replacement can rewrite the inserted data, while a single template substitution does not.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/template_substitution/tests -q -p no:cacheprovider
python workflows/tasks/template_substitution/run.py
python workflows/tasks/template_substitution/run.py --input workflows/tasks/template_substitution/examples/request.json
```

See the wiki page `Test-Template-Substitution`.
