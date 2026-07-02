# Minimal Strawman Baseline and Simple Graph Triage Plan

## Summary

Build the smallest defensible pipeline first: fixed dataset slice → sessionization → strawman anomaly score → reviews-to-first-malicious metric → simple bipartite provenance graph → compare graph score against strawman. Do not optimize steering/retrieval yet. Do not add time, same-user, same-host, file-file projection, or extra GNN architectures in this phase.

The first contribution target is modest and testable:

> Given fixed cyber process telemetry, can a simple process-file-parent graph produce a useful unsupervised session anomaly score compared with a simple strawman baseline?

## Key Decisions

- Use **discovery/anomaly ranking** as the first task, not steering.
- Primary score: **session-level anomaly score**, where higher means “review sooner.”
- Primary metric: **reviews to first malicious**.
- Secondary metrics: `AP`, `recall@25`, `recall@50`, `recall@100`, `recall@250`.
- Default graph: explicit bipartite process-file graph plus parent-child process edges:
  - `process -> file touches`
  - `file -> process touched_by`
  - `process -> process parent_child`
- Exclude for v0:
  - same-user edges
  - same-host edges
  - temporal edges
  - file-file projection
  - same-process-name / same-command-line edges
  - steering / anchor retrieval
- Treat labels as evaluation-only.

## Dataset Plan

Do **not** start with the whole set as the first experiment. Start with a frozen, deterministic development slice, then validate later on the larger/full set.

1. **Dev slice**
   - Source: `Cyber Telemetry/Data/train-process_uber_summary.parquet`
   - Sort by `process_started`
   - Drop duplicate `pid_hash`
   - Use a fixed chronological slice rule, e.g. `tail(100_000)`
   - Record the slice manifest:
     - source file
     - row count
     - start/end timestamps
     - number of sessions
     - number of malicious sessions
     - malicious users/hosts
     - benign users/hosts
     - file-node count after rare-file filtering
   - This slice is for building and debugging the baseline pipeline only.

2. **Holdout**
   - Source: `Cyber Telemetry/Data/test-process_uber_summary.parquet`
   - Use the same preprocessing and scoring code with no tuning.
   - This is where claims start becoming meaningful.

3. **Full-set check**
   - Source: `Cyber Telemetry/Data/process_uber_summary.parquet`
   - Run only after the dev/holdout protocol works.
   - Use this to test stability and runtime, not to tune v0.

A slice is “good enough” only if it is chosen by a predeclared deterministic rule, not because the graph performs well on it. Report identity concentration explicitly so “easy slice” concerns are visible.

## Implementation Changes

### 1. Create One Clean Pipeline Entry Point

Add or refactor toward one function:

```python
run_minimal_discovery_pipeline(df, config) -> results
```

It should return:

```python
{
    "slice_manifest": DataFrame,
    "session_table": DataFrame,
    "baseline_scores": DataFrame,
    "graph_scores": DataFrame,
    "metric_summary": DataFrame,
}
```

No presentation maps, steering widgets, or iterative retrieval in this pipeline.

### 2. Define The Strawman Baseline First

Implement one baseline before graph learning:

```text
session raw stats -> StandardScaler -> kNN distance anomaly score
```

Session raw stats should include only simple aggregates:

- session size
- duration
- mean/std of existing numeric process fields
- unique process names
- unique filenames
- rare-file count
- parent-child edge count if available

This becomes the first fixed baseline: `raw_session_stats_knn`.

### 3. Define The First Score

Use one score consistently:

```python
score = mean distance to k nearest sessions
```

Default:

```python
k = 15
```

Higher score means more anomalous. Do not introduce summed rank or ensembles until this baseline is stable.

### 4. Build The Minimal Graph

Refactor graph construction so the v0 default graph emits only:

```text
process nodes
file nodes
parent_child edges
touches edges
touched_by edges
```

Same-user and same-host may still be counted in diagnostics, but they must not be in the default graph.

Use rare-file filtering:

```python
RARE_FILE_MIN_DEGREE = 2
RARE_FILE_MAX_DEGREE = 15
```

Keep these fixed for v0 and report them in the manifest.

### 5. Graph Score

Train the existing self-supervised SAGE/link-prediction model on the minimal graph.

Convert process embeddings to session embeddings by mean pooling.

Graph anomaly score:

```python
v0_graph_score = mean distance to k nearest session embeddings
```

Compare directly against `raw_session_stats_knn`.

### 6. Minimal Output Tables

The notebook should show only these tables for v0:

1. `slice_manifest`
2. `edge_summary`
3. `metric_summary`
4. `top_25_by_baseline_score`
5. `top_25_by_graph_score`

`metric_summary` columns:

```text
method
average_precision
reviews_to_first_malicious
found_at_25
recall_at_25
found_at_50
recall_at_50
found_at_100
recall_at_100
found_at_250
recall_at_250
```

## Test Plan

- **Alignment test**
  - Assert `process_df["pid_hash"]` order matches `builder.process_ids`.
  - Assert every session index is within `process_df`.

- **Label isolation test**
  - Assert `red_team` is used only in `session_labels` and metric evaluation.
  - Graph training must not read labels.

- **Determinism test**
  - Run the dev slice twice with the same seed.
  - Confirm identical slice manifest and near-identical metrics.

- **Sanity controls**
  - Add `random_score`.
  - Confirm random recall is near expected review-budget rate.
  - Add `label_shuffle_score_eval` later, but not required for first pass.

- **Acceptance criteria for v0**
  - Pipeline runs top-to-bottom on frozen dev slice.
  - Produces one baseline anomaly score and one graph anomaly score.
  - Reports reviews-to-first-malicious for both.
  - Produces a slice manifest sufficient to reproduce the run.
  - Does not include steering, identity expansion, time edges, or extra relations.

## Assumptions

- “File-to-file operations” is interpreted as an explicit **process-file bipartite graph**, not a projected file-file graph.
- The first defensible strawman is `raw_session_stats_knn`; Isolation Forest, LOF, text SVD, and identity baselines come after v0 is stable.
- The current `tail(100_000)` train slice can remain a dev slice, but it should not be treated as confirmatory.
- The first real validation target is the provided `test-process_uber_summary.parquet`.
