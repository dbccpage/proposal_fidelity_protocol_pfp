# Preserved first-attempt diagnostic

The first full attempt reached source/native row, prefix, membership and mapping
comparison, replayed the original endpoint witness, ran all three mutation refusals,
and checked post-run input hashes. Its outer process then exited 1 while constructing
the final receipt: the command supplied a relative build-receipt path and the helper
called `relative_to` against the absolute paper directory. No closed execution
receipt exists for this attempt. The retained comparisons and transport files are
diagnostic evidence; they are not the final custody result.

The next identity supplies the same build receipt by absolute path and leaves the
source algorithms, wrapper and helper unchanged. Nothing in this directory is
overwritten or relabeled as a closed run.
