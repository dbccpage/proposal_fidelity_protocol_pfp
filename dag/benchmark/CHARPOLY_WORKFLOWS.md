# Run the native charpoly workflow

The registered `qm_charpoly_checked_v1` and `qm_charpoly_ungated_v1` plans connect the sealed public QM task to an exact native check of a proposed intermediate characteristic polynomial. The full answer remains independently graded. Neither plan implements the complete PFP host or EIS/PCIV/OPERADS integration.

The current native build helper targets this Windows/MSVC environment and requires Rust plus the locked dependencies already available in the Cargo cache. It uses an isolated Cargo workspace and does not fetch dependencies. Missing build tools, cache entries or verified native custody cause refusal.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 dag/benchmark/native_sidecar_host/build_native.py
.\.venv\Scripts\python.exe -B -X utf8 -m pytest dag/benchmark/test_native_sidecar.py dag/benchmark/test_qm_native_charpoly.py dag/benchmark/test_charpoly_workflows.py dag/benchmark/test_charpoly_runner.py -q
```

Start a fresh Python process after building. The workflow captures the current verified source, lock, build receipt and executable hashes; historical validation manifests do not force reuse of their old executable. Changes after plan preparation require a new manifest. Rebuilding does not promise a bit-identical executable.

Prepare two attempts without provider access:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 dag/benchmark/live_campaign.py prepare --campaign-id MY-NEW-CAMPAIGN --model deepseek/deepseek-v3.2 --endpoint atlas-cloud/fp8 --plans qm_charpoly_checked_v1 qm_charpoly_ungated_v1 --repetitions 1 --cap-microusd 200000 --order-seed 67231 --max-output-tokens 16000 --output MY-NEW-MANIFEST.json
.\.venv\Scripts\python.exe -B -X utf8 dag/benchmark/live_campaign.py initialize --manifest MY-NEW-MANIFEST.json --ledger MY-NEW-LEDGER.sqlite3
```

Use fresh paths and the exact run IDs recorded in the manifest. With `OPENROUTER_API_KEY` supplied privately in the environment, explicit dispatch is:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 dag/benchmark/live_campaign.py run --ledger MY-NEW-LEDGER.sqlite3 --run-id EXACT-MANIFEST-RUN-ID --output MY-NEW-RUN-DIRECTORY
```

The shared ledger caps each whole run at USD0.10, including any repair. Provider price/context enforcement remains an external premise. Do not repeat a run after an observation timeout; inspect its existing process and durable ledger. Unknown billing stops later calls.

The checked plan asks for a polynomial, verifies it exactly, permits one correction and gates synthesis. The unchecked control retains the same candidate and synthesis instructions without feedback or a mathematical gate. A native infrastructure failure stops both. Rejected raw responses remain in the evidence; at most8,192UTF8bytes are forwarded for repair.

Only synthesis text is `answer_text`. A valid intermediate certificate can coexist with a false final solution. After the run is frozen, grade the final text under the unchanged rubric without sending scores or reference content to any model request. Report money, total input/output tokens, wall time and correctness together; certificate acceptance is a separate metric.

Validation:249tests and48subtests across `charpoly_validation.xml` and `charpoly_helper_validation.xml`, plus `charpoly_rebuild_validation.json`. The independent implementation review is `charpoly_workflows_review.json`. These are local software/native controls, not evidence of a live accuracy improvement. The older native-sidecar documents describe the earlier standalone checkpoint; this document describes its subsequent runner integration.
