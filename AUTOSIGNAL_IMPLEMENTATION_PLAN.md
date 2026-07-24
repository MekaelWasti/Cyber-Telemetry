# AutoSignal implementation plan

AutoSignal turns the completed localization notebook into a reusable, guarded
pipeline. The notebook remains the research record; production code lives in
the `autosignal` package and is tested independently.

## Research contract

AutoSignal has three explicit run modes:

1. `score_only`: build sessions, representations, anomaly scores, and 2D
   coordinates without reading a label column. This is the correct mode for
   genuinely unseen telemetry.
2. `development`: evaluate predeclared representations on labeled development
   data and permit a metric-based selection. Feature permutations may only be
   compared in this mode.
3. `locked_evaluation`: evaluate one already-frozen configuration. Metrics are
   reported, but the engine does not select or revise a winner.

AP and Recall@K are undefined without labels. Consequently, the schema agent
may propose mappings and features for unseen data, but it may not claim that a
representation won unless the engine ran in `development` mode with legitimate
evaluation labels.

The completed ACME holdout is sealed. AutoSignal development must not rerun,
overwrite, or use it to choose schemas, feature sets, or model parameters.

## Architecture

```text
dataframe
  -> strict JSON-safe EngineConfig
  -> canonical column adapter
  -> deterministic sessionizer
  -> raw / M1 / M2 / M3 representations
  -> shared StandardScaler + kNN scorer
  -> optional label-isolated evaluator
  -> JSON-safe EngineResult payload

schema agent -> proposes EngineConfig only
engine       -> validates, executes, evaluates
gatekeeper   -> tests a development winner against a graph null
dashboard    -> renders saved payloads; it does not recompute science
```

## One-week build order

### Days 1-2: parameterized engine

- Extract the validated session, graph, scoring, Node2Vec, and relational
  GraphSAGE primitives from the notebook.
- Replace dataset column names with `SchemaConfig` mappings.
- Enforce feature/label isolation before execution.
- Produce a versioned JSON-safe result payload with metrics, graph/session
  manifests, scores, and PCA coordinates.

### Days 3-4: schema agent

- Generate a bounded dataframe profile. Never send full telemetry or raw
  secrets to an LLM by default.
- Ask for a strict configuration object, not Python.
- Validate it locally against the engine contract and dataframe columns.
- Permit 2-3 permutations only on a designated development dataset, and record
  the complete candidate family.

### Day 5: gatekeeper

- Apply a typed degree-preserving rewire to any graph-based development winner.
- Compare paired seeds and report effect sizes for AP and Recall@K.
- Use an explicit threshold and an uncertainty statement. A single raw metric
  difference is not “significance.”
- Emit `supported`, `shortcut_detected`, or `inconclusive`; do not silently turn
  an inconclusive result into a win.

### Days 6-7: analyst UI

- Upload/profile/configure view.
- Validated mapping and selected-feature view.
- Method comparison and null-gate view.
- PCA/UMAP view with the visualization seed disclosed.
- Export the exact configuration and result payload used to render the page.

## Definition of done

- A renamed telemetry schema produces the same canonical sessions and scores.
- `score_only` results do not change if an ignored label column is modified.
- Every stochastic result records its seed and configuration.
- The agent cannot submit executable code or unknown configuration fields.
- Failed methods are explicit in the payload; they are never silently omitted.
- Holdout/reporting paths are separate from development selection paths.
