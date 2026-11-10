# Pilot 25: do not substitute inside substituted data

New experiment 4/100. Does building a prompt by successive string replacements
accidentally rewrite the inserted data?

Two fixed templates place the question before or after the data. Both declare
`${question}` and `${data}`. A standard-library `Template.substitute` call inserts
the values once. The baseline replaces `${data}` first, then `${question}` across
the whole intermediate string. If the data contains `${question}`, that second
replacement changes the data. The default example displays both results.

This tests prompt construction, not model behavior. Preserving inserted text
does not make it trusted, establish role isolation inside a model, or prevent
prompt injection. The templates here are two local examples, not a new standard.

## Rerun

From this folder:

```powershell
py -3.12 -B run.py
py -3.12 -B run.py --input examples/request.json
py -3.12 -B check.py
```

Requests contain `template`, `question` and `data`; unknown fields are rejected.
The result shows both strings, whether they differ, and the one-pass result's
UTF-8 byte/codepoint counts. Token cost is not measured and no provider is called.
Input is UTF-8 JSON up to 16,384 bytes. Exit 0 means construction succeeded;
exit 2 means invalid input. It does not claim that either resulting prompt
elicits a correct answer from a model.

The focused replay requires four killed mutations and at least 98% coverage of
`run.py`. A failed gate prints `{"status":"FAILED","reason":...}` and exits 1.
Compact test, coverage and CLI results go to a temporary directory removed
afterwards, or to a new directory named by `--out`. Collection-wide adversarial review is deferred
until all 100 pilots are built.
