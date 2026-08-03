# AutoSignal v1

The notebook remains the research record. The runnable vertical slice is:

- `AutoSignal Experiment Workbench.ipynb` — organized research interface for
  fast single-slice runs, cached results, trained-versus-random controls,
  signal inspection, paired AP bootstrapping, and opt-in batch experiments.
- `autosignal_engine.py` — validated configuration, preprocessing,
  sessionization, graph construction, method battery, and result payload.
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

For research iteration, open `AutoSignal Experiment Workbench.ipynb`, select
the `GraphTriage` environment, and edit the settings cell near the top. The
default run uses one seed, two GraphSAGE epochs, 99 signal permutations, and a
1,000-row tail slice. Batch execution is disabled until `RUN_BATCH=True`.

## Test

```powershell
C:\Python314\python.exe -m unittest Notebooks\test_autosignal_engine.py -v
```

## Execution contract

- Sessions are created once and shared by every method.
- Raw session kNN and GraphSAGE run once per feature hypothesis.
- Typed structural statistics and Node2Vec run once per configured topology.
- Labels are evaluation-only. With `label_col: null`, AutoSignal runs in
  `score_only` mode and produces rankings without AP or Recall@K.
- Method failures remain visible in `method_results`; they are not silently
  omitted.
- The agent configuration must reference the columns present in the actual
  pipeline input. For example, the bundled raw Parquet uses
  `process_started`; a derived CSV may instead contain `_time`.

The frontend result payload includes method metrics, aligned session scores,
UMAP coordinates, session and graph manifests, preprocessing diagnostics, and
the exact validated configuration.

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
