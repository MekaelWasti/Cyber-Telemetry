# Minimal Strawman Baseline and Simple Graph Triage Plan (revised)

## Summary

Build the smallest defensible pipeline first: fixed dataset slice → sessionization → strawman anomaly score → reviews-to-first-malicious metric → simple bipartite provenance graph → compare graph score against strawman. Do not optimize steering/retrieval yet. Do not add time, same-user, same-host, file-file projection, or extra GNN architectures in this phase.

The first contribution target is modest and testable:

> Given fixed cyber process telemetry, can a simple process-file-parent graph produce a useful unsupervised session anomaly score compared with a simple strawman baseline?

## Expected Outcomes (pre-declared)

Prior work (RESEARCH_SUMMARY.md) found the learned graph geometry is weak as a *standalone* anomaly detector and that identity was the main discriminator — and v0 deliberately excludes identity edges. So a graph loss is a plausible, acceptable v0 result. Decision rule, fixed in advance:

- **Graph beats strawman** on the dev slice → attempt confirmation on the holdout; only then treat as a positive result.
- **Graph loses or ties** → record it as the honest v0 finding; the follow-up is the steering/few-shot framing, **not** adding edges back to rescue the discovery score.

Either way, v0 succeeds if the protocol runs end-to-end and produces a reproducible comparison. The outcome must not drive changes to the v0 graph or features.

## Key Decisions

- Use **discovery/anomaly ranking** as the first task, not steering.
- Primary score: **session-level anomaly score**, where higher means "review sooner."
- Co-primary metrics: **reviews to first malicious** (headline, analyst-facing) and **average precision** (stability). Reviews-to-first is a single order statistic over few, correlated positives — always report it next to its random expectation (≈ N_sessions / (n_malicious + 1)) and never interpret it alone.
- Secondary metrics: `recall@25`, `recall@50`, `recall@100`, `recall@250` (with matching `found_at_*` and `precision_at_*` columns).
- Default graph: explicit bipartite process-file graph plus parent-child process edges:
  - `process -> file touches`
  - `file -> process touched_by`
  - `process -> process parent_child`
- **Seed policy:** the SAGE encoder is trained on seeds **42/43/44**; graph metrics are reported as **mean ± std across seeds** (each seed's embedding scored independently). The kNN strawman is deterministic and reported once.
- **Refit policy:** the method is defined as fully unsupervised **per dataset**. StandardScaler, rare-file degree thresholds, and kNN neighborhoods are refit on whatever slice is being scored (dev, holdout, full). Nothing is carried over from the dev slice except frozen hyperparameters and code.
- Exclude for v0:
  - same-user edges
  - same-host edges
  - temporal edges
  - file-file projection
  - same-process-name / same-command-line edges
  - steering / anchor retrieval
- Treat labels as evaluation-only.

## Sessionization (frozen for v0)

Sessions are the evaluation unit, so the rule is fixed here and recorded in the manifest:

- Group processes by identity (user; hosts fall back to host identity for rows with no user).
- Split a group into a new session after **5 minutes of inactivity** or **30 minutes total duration**.
- A session is labeled **malicious** if any process in it carries the `red_team` flag. Labels are used only at evaluation time.

Any change to this rule is a new experiment version, not a tweak.

## Dataset Plan

Do **not** start with the whole set as the first experiment. Start with a frozen, deterministic development slice, then validate later on the larger/full set.

1. **Dev slice**
   - Source: `Data/train-process_uber_summary.parquet`
   - Sort by `process_started`
   - Drop duplicate `pid_hash`
   - Use a fixed chronological slice rule, e.g. `tail(100_000)`
   - Record the slice manifest:
     - source file
     - git commit hash of the pipeline code + full config dump
     - row count
     - start/end timestamps
     - number of sessions
     - number of malicious sessions
     - malicious users/hosts
     - benign users/hosts
     - file-node count after rare-file filtering
   - This slice is for building and debugging the baseline pipeline only.

2. **Holdout**
   - Source: `Data/test-process_uber_summary.parquet`
   - **Viability check first:** before building any claim on it, confirm the holdout contains `red_team` labels and at least 1 malicious session; record malicious session/user/host counts in a holdout manifest. If it has no red-team activity, the confirmatory set must be redesigned (e.g., a chronologically earlier train slice) — decide that before looking at any scores.
   - Use the same preprocessing and scoring code with no tuning (per-slice refits only, per the refit policy).
   - **Confirmation rule (pre-declared):** the v0 claim holds only if the *direction* of the dev-slice result (graph vs. strawman, on both co-primary metrics) replicates on the untouched holdout. No significance testing over correlated positives; direction-on-holdout is the standard.

3. **Full-set check**
   - Source: `Data/process_uber_summary.parquet`
   - Run only after the dev/holdout protocol works.
   - Use this to test stability and runtime, not to tune v0.

A slice is "good enough" only if it is chosen by a predeclared deterministic rule, not because the graph performs well on it. Report identity concentration explicitly so "easy slice" concerns are visible.

## Implementation Changes

### 1. Create One Clean Pipeline Entry Point

Add one thin function (the notebook is still under construction; `run_v1_pipeline` in `simplified_triage_pipeline.py` already contains extra baselines and steering views — those stay in the module but are **not** part of v0 reporting):

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

Keep these fixed for v0 and report them in the manifest (degrees are computed per slice, per the refit policy).

### 5. Graph Score

Train the existing self-supervised SAGE/link-prediction model on the minimal graph (seeds 42/43/44 per the seed policy).

Convert process embeddings to session embeddings by mean pooling. Note the deliberate asymmetry: the graph score sees only process-level structure (no session size/duration features), so a win or loss against the strawman is interpretable as structure vs. aggregates.

Graph anomaly score:

```python
v0_graph_score = mean distance to k nearest session embeddings
```

Compare directly against `raw_session_stats_knn`, reporting mean ± std over seeds.

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
random_expected_reviews_to_first
found_at_25 / recall_at_25 / precision_at_25
found_at_50 / recall_at_50 / precision_at_50
found_at_100 / recall_at_100 / precision_at_100
found_at_250 / recall_at_250 / precision_at_250
```

Graph rows additionally carry `± std` across seeds.

## Test Plan

- **Alignment test**
  - Assert `process_df["pid_hash"]` order matches `builder.process_ids`.
  - Assert every session index is within `process_df`.

- **Label isolation test**
  - Assert `red_team` is used only in `session_labels` and metric evaluation.
  - Graph training must not read labels.

- **Determinism test**
  - Run the dev slice twice with the same seeds.
  - Confirm identical slice manifest and near-identical metrics.

- **Sanity controls**
  - Add `random_score`.
  - Confirm random recall is near expected review-budget rate, and random reviews-to-first is near N/(m+1).
  - Add `label_shuffle_score_eval` later, but not required for first pass.

- **Acceptance criteria for v0**
  - Pipeline runs top-to-bottom on frozen dev slice.
  - Produces one baseline anomaly score and one graph anomaly score (mean ± std over 3 seeds).
  - Reports both co-primary metrics for both methods, with the random expectation alongside.
  - Produces a slice manifest (incl. git hash + config) sufficient to reproduce the run.
  - Holdout viability check has been run and recorded.
  - Does not include steering, identity expansion, time edges, or extra relations.

## Assumptions

- "File-to-file operations" is interpreted as an explicit **process-file bipartite graph**, not a projected file-file graph.
- The first defensible strawman is `raw_session_stats_knn`; Isolation Forest, LOF, text SVD, and identity baselines exist in `simplified_triage_pipeline.py` but enter reporting only after v0 is stable.
- The current `tail(100_000)` train slice can remain a dev slice, but it should not be treated as confirmatory.
- The first real validation target is `Data/test-process_uber_summary.parquet`, contingent on the holdout viability check.
0 is stable.
- The current `tail(100_000)` train slice can remain a dev slice, but it should not be treated as confirmatory.
- The first real validation target is the provided `test-process_uber_summary.parquet`.
0 is stable.
- The current `tail(100_000)` train slice can remain a dev slice, but it should not be treated as confirmatory.
- The first real validation target is the provided `test-process_uber_summary.parquet`.
