# AutoSignal Phase 5 analysis

Phase 5 turns the frozen Phase 4 artifacts into four compact questions:

1. Which method/scorer configurations beat random at the analyst budget?
2. Do graph methods beat their declared random, untrained, or permuted control?
3. Are effects stable across seeds and separate dataset slices?
4. Is any configuration strong enough to justify opening a sealed confirmation
   partition in Phase 6?

Run:

```powershell
C:\Python314\python.exe experiments\phase5\analyze_results.py
```

The command validates the complete 912-row/390-representation Phase 4 matrix,
reconstructs only the already-open development and selection samples, performs
the frozen 2,000-replicate paired cluster bootstrap, applies Holm correction
within dataset, and writes:

- `REPORT.md`: the short human-facing result;
- `comparisons.csv`: paired AP and Recall@100 effects with uncertainty;
- `outcomes.csv`: deterministic Recommend/Explore/Abstain assignments;
- `confirmation_candidates.csv`: at most one eligible Phase 6 choice per
  dataset;
- `portability_summary.csv`: the cross-dataset direction rule;
- `case_study_manifest.csv`: examples selected by declared evidence category.
- `cluster_diagnostics.csv`: the frozen bootstrap cluster key and cluster count
  for each open partition.

The analysis uses a conservative two-sided finite-sample bootstrap p-value,
`2 * min((nonpositive + 1)/(B + 1), (nonnegative + 1)/(B + 1))`. The report
explicitly warns when the frozen number of bootstrap draws cannot resolve the
Holm threshold for the instantiated comparison family.

Confirmation partitions remain sealed. The analysis does not generate figures
or add methods.
