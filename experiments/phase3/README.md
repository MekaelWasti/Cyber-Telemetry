# AutoSignal Phase 3 frozen matrix

`matrix_v1.json` is the authoritative, immutable specification for the core
AutoSignal experiment. Its SHA-256 is:

```text
c56ca6f3cc5d794fc6da3b09dd273b5a07c461ceba1165017608bb559f190b68
```

The matrix uses ACME, UNSW-NB15, and CIC-IDS2017. LANL is a deferred extension
and cannot block or alter the core study. Any semantic change requires a new
`matrix_v2.json`; do not edit `matrix_v1.json` after execution begins.

## Frozen shape

| Dataset | Development | Selection | Sealed confirmation |
|---|---|---|---|
| ACME | First 70% of train time range | Last 30% of train time range | `test-process_uber_summary.parquet` |
| UNSW-NB15 | Raw files 1–2 | Raw file 3 | Raw file 4 |
| CIC-IDS2017 | Monday–Wednesday | Thursday | Friday |

Each partition retains at most 25,000 review units and 25,000 source rows using
the label-blind hash rule in the matrix. ACME samples complete canonical
activity sessions after sessionization; the network datasets sample flow rows
before graph creation.
Confirmation samples and labels are not materialized until Phase 6.

Every development and selection partition runs all three frozen feature
hypotheses, seeds `42`, `137`, and `314`, and these method families:

- random score;
- raw session/flow features;
- typed structural statistics;
- Node2Vec (`p=q=1`);
- random and trained GraphSAGE;
- untrained and trained DOMINANT-style reconstruction;
- kNN, Isolation Forest, and HDBSCAN population scoring where applicable;
- one label-blind, regime-matched signal transform;
- one target-permuted graph null preserving relation degree sequences.

This produces 152 declared method rows and 65 representation rows per dataset
partition: 912 method rows and 390 representation rows in Phase 4. Valid
abstentions and failures remain rows rather than silently shrinking the matrix.

## Validation

From the repository root:

```powershell
C:\Python314\python.exe experiments\phase3\validate_matrix.py
```

The validator checks all 15 source fingerprints and row counts, loader/config
compatibility, partition isolation, sealed-confirmation rules, and declared
matrix cardinality. It does not parse any label column or compute results.

## Interpretation boundary

The matrix freezes the procedure, not an assumption that one method must win on
all datasets. A method-family portability claim requires a favorable direction
on at least two datasets with no statistically supported reversal. The weak
flow-to-port topology in CIC-IDS2017 may legitimately cause graph methods or
their null controls to abstain.
