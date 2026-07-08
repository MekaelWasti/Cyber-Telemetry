# Next Phase: Graph Score vs. Strawman on the Dev Slice

Goal: one table where `v0_graph_sage_knn` and `raw_session_stats_knn` are compared
on the same sessions with the same metrics. Nothing else. The phase is done when
that table exists and the tests pass — whichever method wins.

Reminder of the pre-declared rule: if the graph loses or ties, that is the honest
v0 finding. Do not add edges or features to rescue it.

## Out of scope for this phase

- Holdout / full-set runs (next phase, only after this table exists)
- Steering, anchors, retrieval
- New edge types, new features, new baselines (IForest, LOF, text SVD)
- UMAP / datamapplot work beyond what already exists
- Any tuning of k, epochs, hidden size, rare-file thresholds

## Steps (in order)

### 1. One sessionization, shared by both methods

Right now `make_strawman_sessions` (user, host fallback) and the builder's
`_extract_bounded_sessions` (host+user pairs) produce different session sets,
so the two scores can't be compared row-for-row.

- Keep the strawman rule — it's the one frozen in SIMPLIFIED_PLAN.md.
- Delete `_extract_bounded_sessions` and pass `sessions` into the builder
  (or set `builder.sessions = sessions` after `build`).
- Done when: `len(sessions)` is the same number everywhere, and
  `sorted(np.concatenate(sessions)) == range(len(df))`.

### 2. Labels out of scoring

- Move `neighbour_distance_weighted_enrichment` out of the scoring section into
  an "evaluation diagnostics" section — it reads `label`, so it is a coherence
  diagnostic, not a discovery score. Pass labels in as an argument instead of
  reading the global `session_table`.
- Delete `neighbour_enrichment` (dead code, no return).
- Done when: the only discovery scores are label-free, and nothing in the
  scoring path references `red_team` or `label`.

### 3. Metric harness

Lift `discovery_metrics` from `simplified_triage_pipeline.py` as-is. For a score
vector + labels it returns: `average_precision`, `reviews_to_first_malicious`,
`found_at_/recall_at_/precision_at_{25,50,100,250}`.

- Add the `random_expected_reviews_to_first = N_sessions / (n_malicious + 1)`
  column so reviews-to-first is never read alone.
- Add a `random` score row (seeded `rng.random(n_sessions)`).
- Done when: `metric_summary` shows `random` and `raw_session_stats_knn` rows
  and random's numbers sit near expectation.

### 4. Graph score

Exactly plan §5, using what's already in the notebook:

- Build the minimal graph (parent_child / touches / touched_by — the builder
  already does this).
- Train the existing SAGE link-prediction encoder once per seed (42, 43, 44).
  Constant or minimal node features — no session-level aggregates.
- Mean-pool process embeddings into session embeddings per seed.
- Score each seed independently with the same `knn_distance_anomaly_scores(k=15)`.
- Done when: three score vectors exist, one per seed, over the shared sessions.

### 5. The comparison table

- One `metric_summary` with rows: `random`, `raw_session_stats_knn`,
  `v0_graph_sage_knn` (mean ± std across the three seeds).
- Plus `top_25_by_baseline_score` and `top_25_by_graph_score` with
  session_id, user, host, session_size, duration, label.
- Done when: the table renders top-to-bottom from a fresh kernel run.

### 6. Finish the bookkeeping

- Complete `get_slice_manifest`: add n_sessions, n_malicious_sessions,
  file-node count after rare-file filtering, git commit hash, config dump.
- Fill in the `run_discovery_pipeline` stub so it returns the five frames
  (manifest, session_table, baseline_scores, graph_scores, metric_summary).
- Fix the stale graph-builder markdown ("temporal relations" — it no longer has any).

### 7. Tests (cheap, from the plan's test list)

- Alignment: sessions partition all rows; graph node i == df row i.
- Label isolation: no feature column contains `red_team`/`label_*`; graph
  training functions never reference labels.
- Determinism: run twice with the same seeds → same manifest, same metrics.

## Exit criteria

- Fresh-kernel run produces the manifest, the comparison table, and both top-25 tables.
- All three tests pass.
- Result direction recorded in one sentence (graph beats / ties / loses strawman).

Next phase after this: holdout viability check, then the same pipeline on the
holdout with no changes — direction replication is the confirmation standard.
