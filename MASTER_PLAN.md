# MASTER PLAN — Constrained Graph Signal Localization and Amplification

**Version 2 — 2026-07-14**

**Status:** Active three-week execution plan

**Governance:** [`CONSTRAINED_RESEARCH_CONTRACT.md`](CONSTRAINED_RESEARCH_CONTRACT.md)

This replaces the expansive Version 1 roadmap. Version 1 remains in git history as future-work material, not as an active task list. Theory guides decisions inside this plan; it does not continuously enlarge it.

## 1. Thesis

> **Given a telemetry dataset, use a fixed label-free workflow to test where evidence associated with malicious behavior is expressed—in aggregate session features, raw-feature neighborhood geometry, explicit graph structure, short-walk proximity, or learned typed relations—and then apply one amplification mechanism matched to the strongest observed signal regime. Return a session-level triage ranking and a concise account of which representation, relations, or behaviors supported it.**

The project asks:

1. **Localization:** Where, if anywhere, does useful malicious-behavior signal appear?
2. **Amplification:** Can one simple graph mechanism make that signal more useful for triage?

Graph methods are not assumed to win. Finding no usable graph signal is a valid result.

### Portability claim

“Dataset agnostic” means **procedure-portable**, not that one trained model or feature set works unchanged everywhere:

```text
schema adapter
→ canonical review units
→ label-free graph and representations
→ common scoring
→ signal localization
→ conditional amplification
→ frozen evaluation
```

Each dataset may expose different useful features, behaviors, and graph regimes. The reusable contribution is the bounded procedure that finds them. Zero-shot transfer and second-dataset validation are future work.

## 2. The fixed box

- Target: **three weeks**.
- Hard maximum: **six weeks**, reserved for contingency and writing.
- One canonical session/evaluation contract.
- Random and raw-feature controls.
- Existing session-similarity filter-bank baseline.
- One heterogeneous telemetry graph and basic audit.
- Three graph representations: typed structural statistics, Node2Vec, and relational GraphSAGE.
- One common scorer and metric suite.
- One bounded localization analysis.
- At most one final amplification experiment.
- Essential controls, one frozen holdout evaluation, and the report.

Anything else is deferred unless the project owner explicitly substitutes it for an active item.

## 3. Fixed scientific design

### Label boundary

Graph construction, representations, and scores are label-free. Labels enter only for evaluation and clearly marked diagnostics:

```python
graph = build_graph(telemetry, frozen_config)
representation = build_representation(telemetry, graph)
scores = label_free_score(representation)

metrics = evaluate(scores, labels)
diagnostics = diagnose(representation, labels)
```

Development labels may select the single final amplifier. That choice is recorded as development-informed, frozen, and evaluated once on holdout.

### Evaluation contract

Every method uses the same ordered canonical sessions and returns one representation or score per session:

```python
assert session_table.session_id.is_unique
assert np.array_equal(method_session_ids, session_table.session_id.to_numpy())
assert len(scores) == len(session_table)
```

Frozen settings:

- review unit: strawman sessions;
- identity: user with host fallback;
- inactivity threshold: 5 minutes;
- maximum duration: 30 minutes;
- kNN scorer: `k=15`;
- review budgets: 25, 50, 100, and 250;
- stochastic seeds: 42, 43, and 44 where applicable;
- per-dataset unsupervised refit under the same procedure.

Every representation follows:

```text
session representation → declared scaling → kNN distance score → common metrics
```

No method-specific scoring rescue is added during the main comparison.

## 4. Fixed methods

| ID | Method | Signal location tested |
|---|---|---|
| C0 | Random ranking | Sanity floor |
| C1 | Raw session statistics + kNN | Aggregate session behavior |
| M0 | Session-similarity filter bank | Raw-feature neighborhood organization |
| M1 | Typed structural statistics + kNN | Explicit graph roles and relation patterns |
| M2 | Node2Vec session representation + kNN | Short-walk proximity and context |
| M3 | Relational GraphSAGE session representation + kNN | Learned typed feature–topology interaction |

Limits:

- M0 uses the filters already implemented; no new filter search.
- M1 uses one compact, interpretable feature table; no motif catalogue.
- M2 uses `p=q=1` as primary; no walk-parameter search.
- M3 uses one fixed two-layer configuration; no architecture search.
- Process representations pool to sessions by mean, with session size explicit.
- A weak method is still a completed method.

## 5. Bounded localization

“Where the signal lives” is answered at only the depth required by the thesis.

### Level 1: representation family

The common comparison determines whether the strongest evidence appears in raw aggregates, raw similarity geometry, structural features, walk proximity, learned typed topology, or nowhere reliably. This is the primary localization claim.

### Level 2: one compact source analysis

Run this only for the strongest telemetry-graph representation:

- M1 wins: report its largest standardized structural-feature deviations.
- M2 wins: check whether degree or component membership explains retrieval, using the rewire control and basic covariates.
- M3 wins: use trained-versus-random initialization and one grouped relation-removal comparison.

Relation groups are limited to the graph’s main semantic families, such as lineage and process–file affiliation. No combinatorial metapath or ablation search.

### Level 3: neighborhood regime

Use the existing filter channels and neighbor-purity diagnostic to describe the evidence as shared/smooth, locally contrastive, intermediate-scale, or not relationally organized. A full spectral atlas is not required.

## 6. One conditional amplification experiment

After the main comparison:

1. Select the strongest supported representation.
2. Choose one matching action:
   - shared neighborhood evidence → neighbor support or restart diffusion;
   - local contrast → residual channel;
   - intermediate scale → one-hop-versus-two-hop channel;
   - no reliable relational signal → do not amplify.
3. Compare the representation before and after amplification.
4. Apply the same operation to the degree-preserving rewired control.
5. Freeze and evaluate once on holdout.

Amplification means a triage improvement on the real graph beyond corresponding behavior on the rewire. If that is not demonstrated, localization without amplification is the completed outcome.

## 7. Metrics and controls

Primary metrics:

- average precision;
- recall at 100.

Supporting metrics:

- reviews to first malicious session, with random expectation;
- found/recall/precision at 25, 50, and 250;
- malicious-neighbor purity at 15 as an evaluation-only diagnostic.

Essential controls:

1. Random ranking.
2. Raw-session-feature baseline.
3. One appropriate degree-preserving topology rewire for graph claims.
4. Trained-versus-random initialization for GraphSAGE.
5. Basic degree, component, session-size, and coverage checks for obvious shortcuts.

With 19 malicious development sessions, no conclusion rests on one volatile metric. Additional null families, bootstraps, spectral tests, and exhaustive ablations are limitations or future work, not active prerequisites.

## 8. Telemetry graph boundary

The sparse v0 telemetry graph is recorded as an unsuccessful construction. Build one v1 graph using label-free semantic rules:

- process nodes for evaluation events;
- context nodes only where needed for declared relations;
- parent–child lineage when resolvable;
- process–file affiliation using one documented file identity rule;
- explicit direction and reverse-traversal semantics;
- no edges added because they improve malicious-label metrics.

Record node/edge counts by type, isolates, components, session coverage, degree quantiles, and basic hop/walk coverage.

Allow one implementation pass and one bounded repair pass for a concrete semantic or coverage defect. If coverage remains limited, report it, handle isolates explicitly, and continue. Do not begin an open-ended graph-rescue cycle.

## 9. Three-week execution plan

### Week 1: shared foundation

**Stage 0 — Close M0 and canonicalize**

- Remove the stray `sparse.cs` cell.
- Record the existing M0 result and existing null results.
- Add basic kNN-graph statistics and alignment assertions.
- Establish the canonical process-to-session map and ordered session table.
- Update the run manifest.

Done when the raw baseline and M0 return aligned scores on canonical sessions. Further filter diagnostics are deferred.

**Stage 1 — Build and audit telemetry graph v1**

- Implement the single declared schema.
- Record the basic audit.
- Use at most one bounded repair if a concrete defect is found.

Done when the graph can feed all three representations with documented coverage and isolate handling.

### Week 2: move horizontally through methods

**Stage 2 — M1:** build the typed feature table, pool, score, and record top deviations.

**Stage 3 — M2:** run primary Node2Vec with declared seeds, pool with explicit isolate handling, and score.

**Stage 4 — M3:** run the fixed relational GraphSAGE and random-init control, pool, and score.

Done when each method produces one aligned representation and comparable metric row, regardless of performance.

### Week 3: localize, amplify once, freeze, and write

**Stage 5 — Compare and localize**

- Produce the C0/C1/M0/M1/M2/M3 table.
- Identify the strongest supported representation family.
- Run the one compact source analysis allowed in Section 5.

**Stage 6 — Amplify once**

- Apply one matching amplifier or record “do not amplify.”
- Compare with the rewired control.

**Stage 7 — Holdout and report**

- Freeze graph, representation, scorer, amplifier, and seeds.
- Refit only label-free components under the declared policy.
- Evaluate holdout once without further selection.
- Write methods, results, limitations, and future work.

## 10. Result stop rules

| Result | Response |
|---|---|
| A method performs poorly | Record it and continue |
| A method performs well | Run its declared control; do not launch a search |
| Graph coverage is weak | Use the one bounded repair, then report the limit |
| Trained GraphSAGE matches random init | Report no learned-encoder value |
| Gain survives on rewired topology | Do not attribute it to semantic graph structure |
| No graph representation beats raw features | Report no added graph value under this construction |
| Amplification fails its control | Report localization without amplification |
| A new idea appears | Preserve it in future work; do not interrupt execution |

No result creates a new model family, null suite, graph redesign, or scoring family without an explicit scope substitution under the contract.

## 11. Required artifacts and completion

Required artifacts:

1. `canonical_sessions`.
2. `graph_manifest`.
3. `representation_manifest` for each method.
4. `method_comparison`.
5. `localization_summary`.
6. `amplification_comparison`, including a valid “do not amplify” outcome.
7. `holdout_result`.

The project is complete when all methods run through the common pipeline, the strongest observed signal family or its absence is recorded, one matched amplifier is tested or declined, essential controls are reported, holdout is evaluated once, and conclusions and limitations are written.

Completion does not require positive results, exhaustive explanation, or proof across multiple datasets.

## 12. Explicitly deferred

- Full spectral-energy and conductance atlas.
- Additional host/time/degree-binned null families.
- Extensive bootstrap and leave-one-host-out analysis.
- Density-peak and compact-cluster score families.
- Anchor steering across every method.
- Exhaustive relation, hop, layer, metapath, or architecture ablations.
- SGWT, wavelets, attention, deletion-faithfulness, and path reconstruction.
- Second-dataset and zero-shot-transfer experiments.

These may extend the completed modular pipeline. They cannot delay it.

## 13. Theory source map

| Decision | Source |
|---|---|
| Representation design and GraphSAGE controls | `Books/GRL_Book_Project_Study_Notes.md` |
| Session-graph filters and conditional amplification | `Books/Ortega_GSP_Project_Study_Notes.md` |
| Graph semantics, coverage, and cautious interpretation | `Books/Networks_Crowds_Markets_Project_Study_Notes.md` |
| Frozen session/scoring details | `SIMPLIFIED_PLAN.md` |
| Prior empirical findings | `RESEARCH_SUMMARY.md` |

Use these resources to choose among the bounded alternatives above. A theoretically valid new option is not automatically an active task.

> **Standing rule:** Build the shared interface, test each declared signal location once, apply one matched amplifier, freeze, and finish. Preserve new ideas without obeying them during the active run.
