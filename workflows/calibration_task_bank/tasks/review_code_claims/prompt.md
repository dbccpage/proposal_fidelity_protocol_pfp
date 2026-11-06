Review a list of claims about the Python function below and flag the ones that are wrong.

```python
def tally(words):
    counts = {}
    for word in words:
        key = word.strip().lower()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
```

Claims to review:

- `c1`: tally(["b", "a", "B"]) returns [("b", 2), ("a", 1)].
- `c2`: tally([]) raises an exception.
- `c3`: tally(["  ", ""]) returns [].
- `c4`: Words with equal counts are ordered in reverse alphabetical order.
- `c5`: tally(["x", "y", "x", "y"]) returns [("x", 2), ("y", 2)].
- `c6`: tally modifies the list it is given.
- `c7`: tally(["A"]) returns [("A", 1)].
- `c8`: tally([" Hi", "hi "]) returns [("hi", 2)].
- `c9`: The function passed its unit test suite before this review.

Some claims are true, some are false, and some cannot be supported by the information given.
Flag every claim that is false or not supported. Do not flag true claims.

Write one JSON object of the form {"flagged_claims": ["<id>", "<id>"]} listing the flagged claim ids.
The file must contain only the JSON object, with no code fence and no other text.
