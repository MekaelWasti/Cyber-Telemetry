# AutoSignal v1

The notebook remains the research record. The runnable vertical slice is:

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
