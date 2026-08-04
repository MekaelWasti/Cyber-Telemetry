# AutoSignal Phase 5 result

## What was tested

The same frozen AutoSignal procedure was evaluated on ACME process telemetry, UNSW-NB15, and CIC-IDS-2017. Development and selection slices were kept separate. Agent-proposed feature hypotheses and typed relations were evaluated with raw, structural, Node2Vec, GraphSAGE, DOMINANT-style, Isolation Forest, kNN, HDBSCAN-population, random, untrained, and relation-permuted controls.

The score suite used average precision, Recall/Precision@100, reviews to the first malicious item, seed top-100 overlap, paired cluster-bootstrap uncertainty (2,000 replicates), and Holm correction within dataset.

## Execution integrity

- Cases complete: 12/12
- Failed cases: 0
- Method rows: 912 (expected 912)
- Representation rows: 390 (expected 390)
- Sealed confirmation partitions were not evaluated.

## Intrinsic selection-slice outcomes

| Dataset | Recommend | Explore | Abstain | Confirmation candidate |
|---|---:|---:|---:|---|
| acme_process_telemetry | 0 | 21 | 6 | none; keep confirmation sealed |
| cic_ids_2017_ml_csv | 0 | 19 | 8 | none; keep confirmation sealed |
| unsw_nb15_raw | 0 | 13 | 14 | none; keep confirmation sealed |

This table counts the 27 intrinsic configurations per dataset. The full machine-readable outcome table also retains matched-transform variants; none of them reached Recommend.

## Best selection result per dataset

- **acme_process_telemetry:** Explore - `graphsage_trained` + `isolation_forest`; AP 0.0498, Recall@100 0.6667, Precision@100 lift 5.49x.
- **cic_ids_2017_ml_csv:** Explore - `raw_session` + `isolation_forest`; AP 0.0373, Recall@100 0.0000, Precision@100 lift 0.00x.
- **unsw_nb15_raw:** Explore - `dominant_style_trained` + `dominant_joint_reconstruction`; AP 0.5845, Recall@100 0.0000, Precision@100 lift 0.00x.

## Inference limitation

The frozen 2,000-draw bootstrap and the conservative two-sided finite-sample p-value have a minimum raw p-value of 2/2001. With the predeclared Holm families instantiated for every relevant configuration, the smallest attainable adjusted p-value is therefore above 0.05 in every dataset. The adjusted-inference gate cannot pass under this exact operationalization. This is a design-resolution limitation, not evidence that all methods are equal.

| Dataset | Holm family size | Smallest attainable adjusted p |
|---|---:|---:|
| acme_process_telemetry | 146 | 0.1459 |
| cic_ids_2017_ml_csv | 158 | 0.1579 |
| unsw_nb15_raw | 153 | 0.1529 |

## Direct method-family findings

- Raw Isolation Forest beat raw kNN in median AP direction on 2/3 datasets; this direction-only result did not satisfy the full recommendation gate.
- Trained DOMINANT-style reconstruction beat its untrained control in direction on 3/3 datasets, but no DOMINANT configuration satisfied inference, analyst-budget, stability, and control requirements together.
- Trained GraphSAGE beat random GraphSAGE in direction on 0/3 datasets. Link-reconstruction training therefore showed no portable added value here.
- Observed GraphSAGE relations beat their permuted control in direction on 1/3 datasets; Node2Vec did so on 2/3.
- Matched amplification beat its own intrinsic score in direction on 0/3 datasets, so amplification should not be carried forward.
- The best intrinsic UNSW and CIC AP configurations had Recall@100 near zero. High global ranking AP did not translate into the first 100 analyst reviews.

## Cross-dataset reading

- Families passing the frozen direction-only portability rule: dominant_trained_vs_untrained, node2vec_observed_vs_permuted, raw_hdbscan_vs_raw_knn, raw_isolation_forest_vs_raw_knn.
- Families with a statistically supported reversal: none.
- A result is not called portable merely because it wins one dataset or one feature hypothesis.

## Next gate

Only configurations marked Recommend may be taken to Phase 6. If a dataset has no Recommend row, its confirmation labels remain sealed and the result is reported as Explore or Abstain rather than rescued post hoc.

Supporting details are in `comparisons.csv`, `outcomes.csv`, `portability_summary.csv`, `case_study_manifest.csv`, and `cluster_diagnostics.csv`.
