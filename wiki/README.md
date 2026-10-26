# Wiki source

These pages are the source of the
[project wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki).
Start at [Home](Home.md). Edit them here through pull requests, then publish
after merging:

```bash
python wiki/publish_wiki.py --dry-run   # show what would change
python wiki/publish_wiki.py             # push to the GitHub wiki
```

The script replaces every page in the GitHub wiki with the pages here and
converts `Page.md` links to wiki links. This README is not published.
