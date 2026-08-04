# AutoSignal Phase 4 execution

Phase 4 runs one fixed question across three datasets:

> Given feature sets and relations proposed from each telemetry schema, where
> does malicious signal appear, which scorer retrieves it, and does graph
> learning add stable value beyond simpler methods and controls?

The runner does not search for new methods or tune parameters. Each partition
is capped at 25,000 review units and source rows. It executes the
frozen development and selection matrix, saves failures, and produces a compact
table that can be analyzed statistically in Phase 5.

## What is compared

- Datasets: ACME, UNSW-NB15, and CIC-IDS2017.
- Inputs: the three feature hypotheses and typed relations frozen for each
  dataset.
- Representations: raw features, structural statistics, Node2Vec, random and
  trained GraphSAGE, and untrained/trained DOMINANT-style reconstruction.
- Scores: kNN, Isolation Forest, HDBSCAN population score, and DOMINANT's own
  reconstruction score.
- Controls: random scores, random/untrained graph models, and one
  degree-preserving relation permutation.
- Repetitions: seeds 42, 137, and 314.
- Evaluation: AP and analyst-budget metrics, representation diagnostics,
  stability, and the one label-blind matched signal transform.

## Run it

Preflight without loading experiment samples:

```powershell
C:\Python314\python.exe experiments\phase4\run_matrix.py --preflight-only
```

Execute or resume all six development/selection cases and their graph controls:

```powershell
C:\Python314\python.exe experiments\phase4\run_matrix.py --resume
```

The confirmation role is rejected by the runner and remains sealed for Phase 6.

## Digestible outputs

The main outputs under
`artifacts/final_matrix/autosignal_final_matrix_001/tables/` are:

- `matrix_digest.csv`: one aggregated row per dataset, partition, method,
  representation, scorer, feature hypothesis, and graph variant;
- `method_results.csv`: the complete 912-row result table;
- `representation_results.csv`: the complete representation table;
- `failure_table.csv`: present only when a declared case fails.

Large per-review-unit scores stay in compressed Parquet files inside each case
directory. Coordinates and plots are deliberately omitted; they cannot affect
method selection and can be generated later for a small set of declared case
studies.
