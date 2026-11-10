# Historical evidence, retained without alteration

These three records support Section 4.1 and Appendix A. Their original bytes,
repository paths, retrieval revision, Git blob identities, and SHA-256 digests
are listed in [provenance.json](provenance.json). Retrieval at a revision is not
the date or source revision of the original execution.

The JSONL trace is the recorded ten-trial bout; its receipt preserves both
historical labels and a later checker replay. That receipt does not identify
the later checker's source revision. The gate record contains five probes in
four defect families at its declared audited commit. Its original floats and
wording are retained; they are not converted into a new exact-arithmetic proof.

Package tests freshly recount the trace, check the receipt's recorded results,
and inspect the five gate observations. They do not execute the models, the
native physics checker, or the historical gate. The collection's gate replay
script remains external and needs a repository checkout with the audited
commit. Its `--write` mode writes the record; the stub gate runtime has no
event sinks or model port.
