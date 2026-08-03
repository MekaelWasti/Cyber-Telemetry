# AutoSignal v1

Project status, decision gates, and the non-stale end-to-end procedure live in
[`../LIVING_RESEARCH_PROCEDURE.md`](../LIVING_RESEARCH_PROCEDURE.md). Update
that document in place when a phase or scientific decision changes.

The notebook remains the research record. The runnable vertical slice is:

- `AutoSignal Experiment Workbench.ipynb` — organized research interface for
  fast single-slice runs, cached results, trained-versus-random controls,
  signal inspection, paired AP bootstrapping, and opt-in batch experiments.
- `autosignal_engine.py` — validated configuration, preprocessing,
  sessionization, graph construction, method battery, and result payload.
- `autosignal_analysis.py` — full-space representation diagnostics,
  Isolation Forest, HDBSCAN rare-population scoring, and cross-seed geometry
  stability.
- `main.py` — Streamlit analyst dashboard.
- `sample_agent_config.json` — ACME configuration matching the bundled raw
  Parquet file.
- `test_autosignal_engine.py` — renamed-schema, score-alignment, and
  label-isolation acceptance tests.

## Run

From the repository root:

```powershell
C:\Python314\python.exe -m streamlit run Notebooks\main.py
```

Then open <http://localhost:8501>.

For research iteration, open `AutoSignal Experiment Workbench.ipynb` with the
Python 3 kernel backed by the same environment as `C:\Python314\python.exe`,
then edit the settings cell near the top. The verified package versions are in
`requirements-autosignal.txt`. The default run uses one seed, two GraphSAGE
epochs, 99 signal permutations, and a 1,000-row tail slice. Batch execution is
disabled until `RUN_BATCH=True`.

## Test

```powershell
C:\Python314\python.exe -m unittest Notebooks\test_autosignal_engine.py -v
```

## Phase 2 pilot

The immutable correctness/feasibility specification is
`../experiments/phase2/pilot_v1.json`. Preflight it without running models:

```powershell
C:\Python314\python.exe Notebooks\run_phase2_pilot.py `
  --spec experiments\phase2\pilot_v1.json `
  --preflight-only
```

Remove `--preflight-only` to execute the frozen pilot. It reads only the ACME
development parquet; the test parquet and combined train/test parquet are
explicitly excluded. Full evidence payloads are written under
`artifacts/pilots/phase2/`, while compact technical summaries are mirrored to
`experiments/phase2/results/pilot_v1/`. Pilot AP and Recall values are
exploratory and cannot select methods or support confirmation claims.

## Execution contract

- Sessions are created once and shared by every method.
- Raw session and GraphSAGE representations run once per feature hypothesis.
- Typed structural statistics and Node2Vec run once per configured topology.
- Each standard representation is registered once and scored with shared kNN,
  Isolation Forest, and—when its assumptions hold—HDBSCAN rare-population
  scoring. HDBSCAN explicitly abstains when it cannot identify multiple
  coherent populations or a dominant reference population.
- A sparse heterogeneous DOMINANT-style method reconstructs primary-node
  attributes and sampled typed relations. Both trained and untrained variants
  are retained as a control. This is an adaptation, not an exact reproduction
  of homogeneous dense-adjacency DOMINANT.
- Labels are evaluation-only. With `label_col: null`, AutoSignal runs in
  `score_only` mode and produces rankings without AP or Recall@K.
- Method failures remain visible in `method_results`; they are not silently
  omitted.
- The agent configuration must reference the columns present in the actual
  pipeline input. For example, the bundled raw Parquet uses
  `process_started`; a derived CSV may instead contain `_time`.

The frontend result payload includes method metrics, aligned session scores,
UMAP coordinates, full-space representation diagnostics, scorer diagnostics,
DOMINANT and cluster score components, cross-seed stability, session and graph
manifests, preprocessing diagnostics, and the exact validated configuration.

`representation_key` identifies one original high-dimensional `X`.
`scorer` identifies the label-free `X -> s` rule. This separation is deliberate:
representation diagnostics are computed once per `X`, while several scorers
may produce different rankings from that same representation.

Full-space representation checks use development labels only and include:

- malicious-neighbor purity with a permutation reference;
- label silhouette where defined;
- an out-of-fold stratified linear-probe AP diagnostic; and
- rotation-invariant cross-seed distance/neighborhood stability.

The current linear probe is explicitly a development-only stratified probe. It
is not yet a grouped-host or forward-temporal generalization estimate.

## Important TODO: feature-agent input contract

The feature/schema agent must receive an explicit feature catalog together with
the dataset profile. Column names, dtypes, missingness, and cardinality are not
enough for defensible feature hypotheses; without feature semantics the agent
is guessing.

The catalog should describe each raw or engineered feature's name, meaning,
entity/granularity, units, derivation, valid aggregation, availability time,
missing/sentinel behavior, and leakage restrictions. The agent must be
constrained to cataloged features, cite the catalog entries used by every
proposal, and return unsupported requirements separately rather than inventing
columns. Labels and post-outcome information must remain excluded from this
feature-proposal input.

This contract is not implemented yet. Before automated feature-hypothesis
generation is treated as part of the scientific workflow, add the catalog to
the agent prompt/API, validate every proposed feature against it, and persist
the catalog version in the run manifest.

## Signal diagnosis

Every completed representation except the random-score baseline is diagnosed
on its original session matrix. AutoSignal builds a symmetric session kNN
graph, computes the intrinsic, neighbor-support, local-residual, and
one-vs-two-hop pocket channels, then compares the three candidate regimes with
a label-blind permutation null.

The **Signal diagnosis** tab lets you switch among method families, feature
hypotheses, and seeds without rerunning the analysis. It displays:

- the dominant regime and family-wise-corrected evidence;
- an interactive UMAP colored by any diagnostic channel;
- the single regime-matched ranking and its session-level rank changes;
- original-versus-matched development metrics when labels are available.

Changing graph relations or feature-set definitions still requires editing the
validated JSON and running AutoSignal again. Browsing several representations
is exploratory: the displayed family-wise p-values correct the three regimes
within one representation, not selection across many representations.

## Current cluster scorer contract

The cluster-level scorer uses scikit-learn HDBSCAN on standardized full-space
`X`. It tests one narrow hypothesis: a relatively rare, internally coherent
population may be separated from a dominant reference population even when its
members are not pointwise kNN outliers.

For a non-dominant cluster `c`, the fixed population score is:

```text
-log(cluster_fraction) * centroid_separation_from_dominant / global_rms
```

Noise receives zero in this scorer because isolated-point behavior is already
tested by kNN and Isolation Forest. If HDBSCAN finds fewer than two populations,
or the largest population is less than 1.25 times the second largest, the
scorer abstains instead of inventing a normal reference cluster.
