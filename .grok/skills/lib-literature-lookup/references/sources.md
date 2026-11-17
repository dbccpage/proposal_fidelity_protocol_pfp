# Sources (v1)

| Source | Endpoint family | Notes |
| -------- | ----------------- | ------- |
| `arxiv` | `export.arxiv.org/api/query` | Atom XML; good for math/physics preprints |
| `openalex` | `api.openalex.org/works` | Works search + DOI filter |
| `crossref` | `api.crossref.org/works` | DOI resolution + query |

Reserved (not implemented v1; skill may list them only after a follow-up PR):

- `semantic_scholar` ext
- `pubmed` ext

User-Agent identifies Sentinel research lookup; no API key required for these public endpoints in v1.
