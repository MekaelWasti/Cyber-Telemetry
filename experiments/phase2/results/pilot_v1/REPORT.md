# AutoSignal Phase 2 Pilot — Technical Summary

- Pilot: `phase2_pilot_001`
- Overall technical pass: **True**
- Same-seed reproducibility pass: **True**
- Resource budget pass: **True**
- Total measured wall time: **261.26 seconds**
- Peak measured RSS: **1.54 GiB**
- CoLA gate: **deferred**

This pilot is correctness/feasibility evidence only. It is not a final
performance estimate and is not confirmation-eligible. AP, Recall@K,
and UMAP appearance were not used for pass/fail or scope decisions.

## Cases

- `acme_dev_head_1000_repro_a`: 1,000 rows, 966 sessions, 8 malicious sessions, 41.29s, peak RSS 0.74 GiB.
- `acme_dev_head_1000_repro_b`: 1,000 rows, 966 sessions, 8 malicious sessions, 28.43s, peak RSS 0.78 GiB.
- `acme_dev_head_5000_multiseed`: 5,000 rows, 4,385 sessions, 21 malicious sessions, 191.54s, peak RSS 1.54 GiB.

## CoLA decision

- No label-blind CoLA context-sampler prototype is frozen or tested.
- Retrieval performance was intentionally not used to activate CoLA.

The label-blind graph-coverage prerequisites did pass: every primary node had
at least one incident relation, at least 60.6% had degree two or greater, and
the largest primary node accounted for at most 1.47% of incident edge
endpoints. CoLA remains deferred because coverage alone does not establish or
test the required contextual-mismatch hypothesis.

## Runtime observation

On the 5,000-row/two-seed case, coordinate projection was the largest
instrumented cost at 84.89 seconds. Representation evaluation used 21.24
seconds, scorers used 29.94 seconds, and method artifact/signal generation used
7.19 seconds. Final experiment execution should cache each representation and
its coordinates rather than recomputing them across reports.

## Known scope limits

- Only the local ACME development schema was exercised.
- Physical parquet head slices are engineering slices, not temporal slices.
- The grouped/forward-temporal linear probe remains unimplemented; its
  current stratified result is exploratory only.
- The sealed test parquet and combined train/test parquet were not read.
