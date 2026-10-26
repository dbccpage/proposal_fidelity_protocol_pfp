# Contributing

## Ground rules

- **Keep proposal, check and decision separate.** A change that lets a component
  grade its own output, or that widens what a passing check licenses, needs a
  clear justification in the pull request.
- **State evidence boundaries.** If you add a number, say which retained file it
  comes from. Finite test success is not a performance claim.
- **Keep refusals.** Do not delete records of refused proposals; they are
  evidence.

## Workflow

1. Branch from `main`.
2. Make the change, with tests where code changes.
3. Open a pull request. Paper packages carry their own claim ledger and change
   log; update them when a paper's content changes.

## Editing this wiki

The wiki source is the
[`wiki/` folder](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/wiki).
Edit pages there through a pull request. Link between pages with relative
`.md` links, such as `[Papers](Papers.md)`, and link to repository files with
full GitHub URLs. After merging, publish with:

```bash
python wiki/publish_wiki.py
```

Edits made directly in the GitHub wiki tab are overwritten by the next publish.

## Licensing

The repository is licensed under Apache 2.0 (see
[`LICENSE`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/LICENSE)).
Paper packages under `papers/` carry their own terms: text under CC BY 4.0 and
code under PolyForm Noncommercial 1.0.0.

## Support

If you find the project useful, there is a sponsor button on the repository
page.
