# C015: Persistent Homology Barcodes with Reduction Certificates

## Problem Statement

Given a filtered simplicial complex $K = (\sigma_0, \sigma_1, \dots, \sigma_{N-1})$ ($N \le 2000$, dimension $\le 3$) over $\mathbb{F}_2$:
1. Simplices must be ordered compatibly with faces: every codimension-1 face of $\sigma_j$ must appear earlier in the sequence ($\sigma_i$ with $i < j$). If not, return status `OUT_OF_SCOPE` with a witness of the offending simplex and missing face.
2. Filtration values must be non-decreasing: $\operatorname{val}(\sigma_j) \ge \operatorname{val}(\sigma_{j-1})$.
3. Compute the $\mathbb{F}_2$ persistence pairing and value barcode via column reduction $R = D \cdot V$ where $V$ is upper unitriangular and $R$ has distinct lowest rows.
4. Return:
   - `pairs`: list of `[str(i), str(j)]` for persistence pairs ($low(j) = i$).
   - `essential`: list of `str(i)` for cycle classes never killed.
   - `barcode`: mapping degree `"0"`, `"1"`, `"2"`, `"3"` to list of intervals `[start, end]`. Zero-length intervals ($\operatorname{val}(i) == \operatorname{val}(j)$) must be dropped from `barcode`.
   - `R_columns`: sparse dictionary of row indices for columns of $R$ that differ from $D$.
   - `V_columns`: sparse dictionary of row indices for columns of $V$ that differ from standard unit basis vectors.

## Output Contract

```json
{
  "id": "case_id",
  "status": "SOLVED",
  "pairs": [["1", "3"], ["2", "4"]],
  "essential": ["0"],
  "barcode": {
    "0": [["0", "1/2"], ["0", "inf"]],
    "1": [["1", "2"]],
    "2": []
  },
  "R_columns": {"3": ["0", "1"]},
  "V_columns": {"3": ["1", "3"]}
}
```
