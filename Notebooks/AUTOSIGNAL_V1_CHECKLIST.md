# AutoSignal v1 — Verification Checklist

This document records what the current AutoSignal core implements, what should
be checked before presenting it as the shippable v1, and which checks belong to
later signal-analysis work.

The goal is a sound, understandable term-project system—not a production SOC
platform.

## Current v1 contract

The scientific workflow comes from the localization notebook:

```text
telemetry
  -> validated agent configuration
  -> deterministic preprocessing
  -> one canonical session assignment
  -> raw session representation
  -> typed structural representation
  -> Node2Vec topology representation
  -> relational GraphSAGE representation
  -> shared kNN anomaly scoring
  -> aligned AP / Recall@K / review metrics
  -> session rankings and 2D coordinates
```

Implemented:

- [x] Parameterized timestamp, session identity, label, and feature columns
- [x] Parameterized arbitrary typed graph relations
- [x] Three agent-proposed feature hypotheses
- [x] Raw session kNN per feature hypothesis
- [x] Typed structural statistics once per graph
- [x] Node2Vec once per graph
- [x] Random and trained GraphSAGE per feature hypothesis
- [x] One shared session ordering across every method
- [x] Score-only operation when labels are unavailable
- [x] Standard result payload for the frontend
- [x] Method comparison table
- [x] Session ranking table
- [x] Interactive and static DataMapPlot views of UMAP representations
- [x] Sidebar progress tied to real pipeline stages
- [x] Configuration, graph, session, and preprocessing diagnostics
- [x] Result-payload export
- [x] Renamed-schema, label-isolation, alignment, and serialization tests

## Essential checks before calling v1 complete

### 1. Configuration and input consistency

- [ ] Confirm every configuration column exists in the actual pipeline input.
- [ ] Confirm the raw bundled Parquet uses `process_started`, while a derived
      CSV may use `_time`.
- [ ] Confirm `label_col` is never present in `selected_columns`.
- [ ] Confirm detector outputs, Sigma hits, MITRE annotations, LOLBAS fields,
      and other label-derived columns are excluded from features.
- [ ] Confirm every selected feature belongs to at least one feature set.
- [ ] Confirm every graph relation uses the standard keys and correct direction.
- [ ] Confirm relation endpoint node types match what their columns represent.

### 2. Sessionization

- [ ] Record the number of input rows and resulting sessions.
- [ ] Record the singleton-session fraction.
- [ ] Inspect median, p95, and maximum session sizes.
- [ ] Inspect median and p95 session durations.
- [ ] Confirm timestamp parse success is acceptably high.
- [ ] Confirm rows with missing users are retained using a missing-value
      sentinel rather than dropped.
- [ ] Check whether missing users merge too much unrelated host activity.
- [ ] Check the percentage of rows missing every session grouping field.
- [ ] Inspect several sessions manually to confirm that their rows form
      reasonable behavioral units.

High singleton prevalence is not automatically a code defect. It may indicate:

- a small or discontinuous slice;
- overly specific grouping columns;
- an inactivity threshold that is too short for the dataset cadence; or
- telemetry where one-row sessions are genuinely common.

For a controlled experiment, freeze the session assignment before comparing
representations or hyperparameters.

### 3. Feature preprocessing

- [ ] Inspect missingness for every selected column.
- [ ] Confirm median imputation is reasonable for continuous measurements.
- [ ] Confirm missing aggregate counters do not actually mean “zero activity”
      before treating them as ordinary missing measurements.
- [ ] Confirm automatic `log1p` is applied only to nonnegative, strongly skewed
      measurements.
- [ ] Confirm constant features are removed or reported.
- [ ] Confirm every final feature matrix contains only finite values.
- [ ] Inspect feature diagnostics when two hypotheses produce identical scores;
      the selected columns may be constant, extremely sparse, or imputed to
      nearly identical values.

### 4. Graph construction

- [ ] Record node counts by node type.
- [ ] Record edge counts and row coverage for every relation.
- [ ] Measure parent-process resolution within the selected slice.
- [ ] Inspect the number of external parent nodes.
- [ ] Measure the fraction of isolated primary nodes.
- [ ] Inspect connected-component sizes.
- [ ] Inspect maximum and p95 degree by relation.
- [ ] Identify host, user, or executable hubs that may dominate topology.
- [ ] Verify that every relation expresses an observed semantic relationship,
      not merely two columns that coexist in a row.

### 5. Method alignment and metrics

- [x] Every completed method returns one score per canonical session.
- [ ] Display the malicious-session count and base prevalence with every run.
- [ ] Warn when there are too few malicious sessions for stable interpretation.
- [ ] Confirm that Recall@K increments match the number of malicious sessions.
- [ ] Compare AP with both random ranking and the malicious-session base rate.
- [ ] Confirm higher scores always mean higher review priority.
- [ ] Confirm the exact dataframe slice, configuration, seed, `k`, and epochs
      are stored with every exported result.

When comparing configurations:

- [ ] Freeze the exact dataframe slice.
- [ ] Freeze canonical sessions.
- [ ] Freeze labels and evaluation budgets.
- [ ] Change one variable at a time where possible.
- [ ] Do not treat runs with different row counts as a controlled
      hyperparameter comparison; they contain different evaluated populations.

### 6. Frontend

- [x] Bundled dataset runs through the complete dashboard.
- [x] Uploaded CSV and Parquet paths are supported.
- [x] Agent JSON can be pasted or uploaded.
- [x] Failed methods remain visible rather than disappearing.
- [x] Result payload can be downloaded.
- [ ] Manually inspect the dashboard at the intended presentation resolution.
- [ ] Confirm long method and hypothesis names remain readable.
- [ ] Confirm chart tooltips communicate the metric and method clearly.
- [ ] Confirm the displayed configuration is the exact configuration used.
- [ ] Confirm the dashboard labels UMAP coordinates as visualization artifacts,
      not anomaly scores.
- [ ] Confirm DataMapPlot pan, zoom, and hover remain responsive at the intended
      demo row count.
- [ ] Confirm demo labels are hidden by default and revealed only by the toggle.
- [ ] Confirm switching methods changes the projection without changing session
      IDs or score alignment.

The JSON copied from a Streamlit chart is a Vega-Lite specification, not the
underlying result table. Use the exported AutoSignal payload for scientific
comparisons.

## Notebook-derived behavior versus generalized implementation

The current engine preserves the notebook’s method families and experimental
flow, but it is not intended to reproduce every notebook number exactly.

Notebook-derived:

- activity-window sessions;
- session pooling;
- scaling and kNN scoring;
- AP, Recall@K, precision, and reviews-to-first metrics;
- typed heterogeneous graphs;
- structural representations;
- Node2Vec topology embeddings;
- relational GraphSAGE;
- random-init versus trained GraphSAGE comparison; and
- session-level embedding projections.

Generalized or newly added:

- strict JSON validation and leakage checks;
- automatic imputation and conditional `log1p`;
- primary graph-node inference;
- support for external parent nodes;
- generic mean/std/max/sum session pooling;
- generic per-relation structural degree channels;
- constant initial features for non-primary node types;
- dependency-light Node2Vec with `p=q=1`;
- dynamic GraphSAGE edge types and relation decoders;
- standardized result payloads;
- UMAP frontend coordinates and DataMapPlot rendering; and
- frontend integration and regression tests.

### Numerical equivalence check

- [ ] If exact notebook equivalence matters, run the notebook and engine on the
      same frozen rows, sessions, columns, relations, seeds, and hyperparameters.
- [ ] Compare session IDs before comparing scores.
- [ ] Compare feature matrices and embeddings before comparing final metrics.
- [ ] Document expected differences caused by generalized pooling,
      preprocessing, structural channels, or the `p=q=1` Node2Vec
      implementation.

The project can be correct without exact numerical equivalence, but it should
not claim exact reproduction unless this check is performed.

## Signal-analysis checks to add after the core v1

These strengthen the research contribution but are not blockers for the
working dashboard.

### Stability

- [ ] Run stochastic methods across at least three recorded seeds.
- [ ] Report mean, standard deviation, median, and paired method differences.
- [ ] Check whether method ordering is stable across seeds.
- [ ] Check whether conclusions survive reasonable session-window changes.

### Topology gatekeeper

- [ ] Rewire configured relations while preserving appropriate degree
      structure.
- [ ] Compare real-graph and rewired-graph results using paired seeds.
- [ ] Test important relation families individually and through ablation.
- [ ] Distinguish topology signal from host, user, executable, or degree hubs.
- [ ] Report `supported`, `shortcut_detected`, or `inconclusive`.

### Representation interpretation

- [ ] Compare raw features, structural statistics, Node2Vec, random GraphSAGE,
      and trained GraphSAGE.
- [ ] Do not interpret trained GraphSAGE as adding signal when it does not
      consistently beat its random-init control.
- [ ] Localize signal by feature hypothesis.
- [ ] Localize signal by relation type.
- [ ] Examine which sessions, nodes, and neighborhoods produce retrieval gains.

### Evaluation discipline

- [ ] Use development data for representation and configuration selection.
- [ ] Freeze the selected configuration before holdout evaluation.
- [ ] Do not use the sealed holdout to revise feature hypotheses or topology.
- [ ] Record how many hypotheses and method variants were considered.
- [ ] Treat very small malicious-session counts as exploratory evidence.

## Known v1 boundaries

Not yet implemented:

- [ ] Direct LLM API invocation from the dashboard
- [ ] Multi-seed aggregation controls in the dashboard
- [ ] Degree-preserving graph rewiring
- [ ] Automated relation ablations
- [ ] Frozen holdout execution path
- [ ] Additional signal filters and amplification analyses
- [x] UMAP projection and DataMapPlot rendering

These are extensions. They do not invalidate the current vertical slice.

## Defensible project description

Use:

> AutoSignal is a schema-adaptive framework for comparing and localizing
> malicious behavioral signal across numeric, structural, topological, and
> learned telemetry representations.

Do not currently claim:

- a production intrusion detector;
- guaranteed support for every possible telemetry schema;
- exact numerical reproduction of every notebook experiment;
- statistically validated topology signal before null controls;
- superiority of trained GraphSAGE when it does not beat random initialization;
  or
- a representation winner based on an unlabeled score-only run.

## Commands

Run the dashboard:

```powershell
C:\Python314\python.exe -m streamlit run Notebooks\main.py
```

Run the current acceptance tests:

```powershell
C:\Python314\python.exe -m unittest Notebooks\test_autosignal_engine.py -v
```
