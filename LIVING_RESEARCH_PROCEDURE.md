# AutoSignal Living Research Procedure

**Document role:** Current source of truth for what happens next, what is frozen,
what remains exploratory, and why each experiment exists.

**Last updated:** 2026-08-04

**Current phase:** Phase 7 - prepare evidence-backed final figures and report

**Immediate objective:** Present the completed Phase 4/5 evidence without
opening any sealed confirmation partition. No configuration reached Recommend,
so Phase 6 is not activated under the frozen rule.

> This is a living document. Update the status tables and current decisions in
> place. Preserve the decision log at the end. Do not append competing roadmaps.

## 1. Stable project thesis

AutoSignal is a method-agnostic, agent-guided scientific gateway that converts
telemetry feature and relation hypotheses into comparable session
representations and anomaly rankings. It evaluates where information is gained
or lost and returns one of three evidence-aware outcomes:

1. **Recommend:** a stable, practically useful ranking supported by controls.
2. **Explore:** a qualified finding, such as useful representation-level
   separation paired with a failed anomaly scorer.
3. **Abstain:** no tested result is sufficiently credible or actionable.

The project does **not** assume that the most complex graph method should win.

The central decomposition is:

\[
\text{schema/feature hypothesis}
\rightarrow X
\rightarrow s
\rightarrow \text{score organization}
\rightarrow \text{malicious retrieval}
\rightarrow \text{analyst utility}.
\]

These layers are not interchangeable:

\[
\text{representation quality}
\ne \text{anomaly-score quality}
\ne \text{graph-relative score organization}
\ne \text{analyst utility}.
\]

## 2. How to maintain this document

Use these rules whenever the project changes:

1. Update **Last updated**, **Current phase**, and **Immediate objective**.
2. Change the relevant status in the tracker; do not create a second checklist.
3. Record material scope or scientific decisions in the append-only decision
   log.
4. When an experiment finishes, link its immutable run manifest or result
   artifact from the tracker.
5. Mark superseded claims as superseded in the decision log, then replace them
   in the active sections. Do not leave contradictory active instructions.
6. Separate statuses rigorously:
   - `implemented`: present and tested in code;
   - `pilot`: used to validate correctness or feasibility;
   - `frozen`: predeclared for the final experiment;
   - `completed`: final run finished and artifact saved;
   - `deferred`: intentionally outside the active scope;
   - `blocked`: cannot proceed without a named dependency or decision.
7. Never promote a preliminary observation to a result without a frozen run.
8. Treat older planning documents as historical context when they conflict
   with this procedure.

## 3. Non-negotiable scientific rules

- One canonical, ordered session population is shared by every compared method.
- Labels are excluded from feature construction, graph construction,
  representation learning, anomaly scoring, and signal-regime selection.
- Development labels may evaluate representations and rankings, but this use
  must be named explicitly.
- UMAP is visualization only; it cannot establish separation in the original
  representation.
- Every stochastic method records its seed.
- Failed methods and negative results remain in the result table.
- Methods compared as a controlled experiment use the same sessions and split.
- Search/pilot results do not count as untouched confirmation.
- The exact final matrix is frozen only after implementation and pilot checks.
- Once frozen, the matrix is not revised because a result looks disappointing.
- Signal-regime significance is not called malicious relevance.
- A matched signal transform is rejected when it harms analyst utility.
- The system may abstain instead of selecting the least-bad method.

## 4. Current system inventory

| Component | Status | Current role |
|---|---|---|
| Validated agent configuration | Implemented | Declares schema, feature hypotheses, labels, sessions, and typed relations |
| Deterministic preprocessing | Implemented | Produces finite row features from declared inputs |
| Canonical sessionization | Implemented | Establishes the shared review units and ordering |
| Typed telemetry graph | Implemented | Supplies relation-aware representations |
| Raw session representation | Implemented | Tests aggregate behavioral evidence |
| Typed structural statistics (M1) | Implemented | Tests explicit graph roles |
| Node2Vec/DeepWalk-style representation (M2) | Implemented | Tests short-walk topology |
| Random GraphSAGE control | Implemented | Tests value beyond random graph propagation |
| Trained relational GraphSAGE (M3) | Implemented | Tests learned feature–relation interaction |
| Shared kNN anomaly scorer | Implemented | Current common pointwise scorer |
| Signal-regime diagnosis | Implemented | Label-blind description of score organization |
| Matched signal transform | Implemented | One diagnostic intervention, retained only if useful |
| Streamlit analyst interface | Implemented | Compares rankings, representations, and signal channels |
| Post-hoc representation evaluation | Implemented | Tests information in \(X\) independently from \(s\) |
| Cluster-level anomaly scorer | Implemented | HDBSCAN rarity/separation scorer with explicit abstention |
| Isolation Forest scorer | Implemented | Tests whether kNN is the wrong pointwise scorer |
| DOMINANT-style attributed graph method | Implemented | Tests anomaly-oriented joint attribute/structure reconstruction |
| CoLA-style contrastive graph method | Deferred; gate not activated | Would test node–neighborhood incompatibility if a future context-sampler gate passes |
| Exact final experiment matrix | Frozen | [`experiments/phase3/matrix_v1.json`](experiments/phase3/matrix_v1.json), SHA-256 `c56ca6f3cc5d…` |
| Untouched confirmation run | Not started | Runs once after all choices are frozen |

## 5. Method suite and the question each method answers

The goal is not to accumulate models. Each included method must isolate a
different possible source of success or failure.

### 5.1 Existing representation families

| Method | Input | Score | Scientific question |
|---|---|---|---|
| Random baseline | Session count | Random score | Is performance plausibly above chance? |
| Raw session features | Agent feature hypothesis | kNN distance | Does unusual aggregate behavior support triage? |
| M1 structural statistics | Typed relations | kNN distance | Do explicit graph roles carry useful evidence? |
| M2 Node2Vec | Graph topology | kNN distance | Does short-walk proximity carry useful evidence? |
| Random GraphSAGE | Attributes + typed relations | kNN distance | Does architecture/random propagation alone explain performance? |
| Trained GraphSAGE | Attributes + typed relations | kNN distance | Does link-reconstruction training add value beyond random initialization? |

### 5.2 Final scorer and evaluation additions

These are implemented and frozen in the Phase 3 matrix.

#### Post-hoc representation evaluation

Evaluate the original full-dimensional \(X\), using development labels only:

- malicious-neighbor purity with a permutation/prevalence reference;
- label-based silhouette, interpreted cautiously under imbalance;
- cross-validated linear-probe AP using an appropriate grouped or temporal split;
- seed and slice stability;
- optional centroid/distribution separation if specified before final review.

Purpose: distinguish **representation failure** from **scorer failure**.

#### One cluster-level anomaly scorer

Apply one predeclared cluster/population scoring rule to an existing \(X\) and
compare it directly with kNN on the identical representation and sessions.

Purpose: test the case where malicious sessions form an internally coherent,
globally distinct, relatively uncommon population and therefore are not
pointwise kNN outliers.

The implemented scorer uses HDBSCAN on standardized full-space `X`. For each
non-dominant coherent population, it assigns:

\[
-\log(n_c/N)
\times
\frac{\lVert \mu_c-\mu_{\mathrm{dominant}}\rVert_2}
{\mathrm{global\ RMS}}.
\]

Noise receives zero because isolated-point evidence is tested separately by
kNN and Isolation Forest. The scorer abstains when HDBSCAN finds fewer than two
coherent populations or when the largest cluster is less than 1.25 times the
second largest. Phase 3 freezes these defaults unchanged. Do not create a broad
cluster-algorithm search.

### 5.3 Most important additions from the earlier five-method shortlist

#### A. Isolation Forest — selected

Apply Isolation Forest to the same session representation \(X\).

It asks:

> Does the representation support anomaly retrieval when anomalous combinations
> are isolated by feature splits rather than nearest-neighbor distance?

Why it belongs:

- inexpensive relative to new neural graph methods;
- a strong, established non-distance baseline;
- directly tests whether kNN discarded useful information in \(X\);
- works across Raw and learned session representations;
- adds little architectural noise.

#### B. DOMINANT-style attributed graph anomaly detection — selected

Use an attributed graph autoencoder that produces node/session evidence from
attribute reconstruction error and structural reconstruction error.

It asks:

> Can an anomaly-oriented graph objective expose behavior that ordinary
> relation reconstruction in GraphSAGE misses?

Why it belongs:

- current GraphSAGE training often matches its random control;
- its anomaly objective is more aligned with the research target than generic
  link reconstruction;
- it tests attributes and structure jointly;
- its two error sources support analyst-facing localization;
- it is a substantively different graph method, not another encoder variant.

DOMINANT must still receive a random/untrained or appropriate shuffled control,
session-aligned outputs, and the same downstream evaluation contract.

#### C. CoLA-style contrastive graph anomaly detection — gated third choice

CoLA tests whether a node agrees with its sampled local subgraph context.

It should be added only if, after Isolation Forest, cluster scoring, and
DOMINANT pilots, the unresolved question is specifically contextual mismatch.
It should not be added merely to increase the method count.

#### Deferred from the five

- **Deep SVDD:** scientifically valid, but lower marginal value after Isolation
  Forest and cluster scoring already test alternative \(X\rightarrow s\)
  mappings. Reconsider if nonlinear one-class modeling becomes the identified
  missing comparison.
- **Temporal encoder/TGN:** potentially important, but it changes the data
  representation and requires reliable ordered event histories. Treat it as a
  future temporal study unless static aggregation is demonstrated to be the
  dominant unresolved failure.

The selected expansion is therefore:

```text
Required now:
  post-hoc representation evaluation
  + one cluster-level scorer
  + Isolation Forest
  + DOMINANT

Conditional:
  CoLA only through its decision gate

Deferred:
  Deep SVDD and temporal/TGN
```

## 6. Perpetual phase procedure

### Phase 0 — Preserve the baseline

**Status:** Completed/ongoing regression requirement

- Preserve the current methods and outputs.
- Confirm current tests pass before adding new scientific components.
- Record the active engine path and avoid parallel implementation drift.
- Do not reinterpret preliminary manual results as final results.

**Exit condition:** Existing behavior is reproducible and protected by tests.

### Phase 1 — Complete the evaluation and scorer layer

**Status:** Completed

Implement and test:

1. Post-hoc representation metrics.
2. One cluster-level scorer.
3. Isolation Forest as an alternative scorer on the same \(X\).
4. DOMINANT through the common artifact interface.
5. Method/scorer metadata sufficient to distinguish representation from score.

Every addition must emit or reference:

- ordered `session_id` values;
- representation key and dimension metadata when applicable;
- scorer key;
- aligned score vector;
- seed and configuration;
- runtime/failure diagnostics;
- evaluation metrics only when development labels are legitimately available.

**Exit condition:** Met. Each addition passes alignment, determinism where
applicable, label-isolation, and strict serialization tests on a smoke dataset;
the populated Streamlit result view also renders without exceptions.

### Phase 2 — Pilot for correctness and feasibility

**Status:** Completed for the locally available ACME development schema

Run a deliberately small pilot across representative datasets/configurations.
The pilot may answer only design questions:

- Are implementations correct and numerically stable?
- Are runtimes feasible?
- Does the cluster score behave sensibly for noise and tiny clusters?
- Can DOMINANT map node evidence back to canonical sessions without leakage?
- Are representation metrics meaningful with the available positive counts?
- Are any methods exact duplicates or consistently failing technically?
- Which dataset slices are scientifically meaningful and computationally viable?

Pilot results may remove an infeasible or invalid method. They may not be used
to cherry-pick only the best-looking method/dataset combinations.

#### CoLA decision gate

Add CoLA only when all are true:

- DOMINANT is functioning through the shared contract;
- the remaining scientific question concerns node–neighborhood contextual
  inconsistency;
- the required graph sampling can be implemented and tested within the project
  schedule;
- adding it will not displace the frozen evaluation, analysis, or presentation.

Otherwise record CoLA as deferred.

**Exit condition:** Met for the locally available ACME development schema. The
technical contract, reproducibility, two-seed stability path, runtime, and
memory budget passed. Cross-schema portability remains untested because the two
other catalog configurations have no matching local data.

### Phase 3 — Freeze the exact experiment matrix

**Status:** Completed

This is when the exact matrix—not merely its general shape—is frozen.

Record:

- dataset names, versions, and fingerprints;
- exact development, selection, and confirmation partitions;
- meaningful slice definitions;
- feature-catalog and agent-prompt versions;
- exact feature hypotheses and relation configurations;
- canonical sessionization parameters;
- representation methods;
- scorers applicable to each representation;
- seeds;
- method hyperparameters;
- evaluation metrics and analyst budgets;
- controls and nulls;
- decision thresholds;
- planned paired comparisons;
- multiple-comparison policy;
- artifact/output locations.

The matrix should be a set of valid combinations, not necessarily a blind
Cartesian product. For example, DOMINANT consumes an attributed graph, whereas
Isolation Forest can score any compatible session representation.

**Exit condition:** Met. The versioned specification is
[`experiments/phase3/matrix_v1.json`](experiments/phase3/matrix_v1.json), with
SHA-256 `c56ca6f3cc5d794fc6da3b09dd273b5a07c461ceba1165017608bb559f190b68`.
All confirmation partitions remain sealed.

### Phase 4 — Execute the frozen experiments

**Status:** Current

- Run all declared combinations.
- Cache representations and scores where scientifically safe.
- Preserve failures as result rows with diagnostics.
- Do not silently rerun with changed settings.
- Produce one tidy result table keyed by dataset, slice, feature hypothesis,
  relation configuration, representation, scorer, and seed.

Primary ranking measures:

- average precision;
- Recall and Precision at 25, 50, 100, and 250;
- malicious sessions found at each budget;
- reviews to first malicious;
- prevalence/random reference.

Representation measures:

- full-space neighbor purity;
- cross-validated linear-probe AP;
- label silhouette where valid;
- stability across seeds and slices.

Controls/comparisons:

- random score;
- kNN versus Isolation Forest versus cluster score on the same \(X\);
- trained versus random GraphSAGE;
- real versus shuffled/rewired relations where applicable;
- DOMINANT attribute versus structural error and its declared graph control;
- intrinsic versus the one regime-matched signal score.

**Exit condition:** The full frozen development/selection matrix is complete or
every missing row has a documented failure reason.

### Phase 5 — Statistical analysis and outcome assignment

**Status:** Pending

- Use paired comparisons because methods score the same sessions.
- Report uncertainty for AP and Recall@K differences.
- Report effect sizes and practical analyst-budget changes, not p-values alone.
- Measure rank correlation and top-K overlap across seeds.
- Correct confirmatory multiple comparisons according to the frozen policy.
- Assign each relevant configuration to Recommend, Explore, or Abstain.
- Select case studies by predeclared outcome categories, not visual appeal alone.

Required case-study targets:

1. Useful representation and useful ranking, if one exists.
2. Useful representation but failed scorer, if one exists.
3. Significant or attractive structure that is operationally harmful or
   unsupported.
4. Trained GraphSAGE approximately equal to random GraphSAGE, if reproduced.

**Exit condition:** Every headline claim is traceable to a frozen result and
uncertainty/control evidence.

### Phase 6 — Untouched confirmation

**Status:** Pending

- Freeze the selected configuration and decision rule.
- Run it once on the untouched confirmation partition.
- Do not revise the method after viewing confirmation labels.
- If it fails, report the failure and narrow the conclusion.

**Exit condition:** The final claim is confirmed, qualified, or rejected.

### Phase 7 — Presentation and paper artifacts

**Status:** Pending

Build the presentation around one causal story:

1. Telemetry schemas make feature and relation choices uncertain.
2. AutoSignal converts those choices into explicit hypotheses.
3. A shared interface compares distinct information sources.
4. Representation quality and scoring quality can diverge.
5. Random and structural controls expose spurious sophistication.
6. Signal organization can be real but irrelevant to malicious retrieval.
7. The system recommends, exposes partial success, or abstains.
8. A new method can be implemented once and inherit the full workflow.

Priority visuals:

- end-to-end architecture;
- experiment performance matrix;
- trained versus random GraphSAGE;
- representation quality versus ranking quality;
- kNN versus Isolation Forest versus cluster scoring on the same \(X\);
- DOMINANT attribute/structure evidence;
- a failed-amplification case;
- Recommend/Explore/Abstain outcome summary.

**Exit condition:** Every displayed number matches a saved result artifact, all
preliminary evidence is labelled, and limitations are explicit.

## 7. Current interpretation of preliminary evidence

These observations motivate experiments; they are not final claims:

- Trained GraphSAGE has often tied or only negligibly exceeded random
  GraphSAGE.
- Significant intermediate-scale organization was observed for one Node2Vec
  result, but its matched pocket score severely harmed malicious retrieval.
- Some UMAP views suggest coherent malicious populations, while kNN rankings
  remain weak.
- Signal transforms have frequently been useless or harmful in manual runs.

The correct hypotheses are therefore:

- a representation may contain recoverable information that kNN discards;
- an anomaly-oriented graph objective may outperform generic link
  reconstruction—or may also fail;
- graph-relative score organization may describe benign structure rather than
  malicious relevance;
- abstention may be the most defensible outcome for some slices.

## 8. Active tracker

| ID | Task | Status | Evidence/exit artifact |
|---|---|---|---|
| P0.1 | Preserve current engine behavior and tests | Implemented | 14-test engine regression suite passes on 2026-08-03 |
| P1.1 | Implement full-space neighbor-purity evaluation | Implemented | Deterministic permutation-reference unit test |
| P1.2 | Implement label silhouette with validity guards | Implemented | Full-space evaluator unit test; undefined values serialize as `null` |
| P1.3 | Implement cross-validated linear probe | Implemented | Stratified out-of-fold development probe; grouped/temporal probe remains a stated limitation |
| P1.4 | Implement representation stability metrics | Implemented | Rotation-invariant distance-rank and neighbor-overlap test; cross-seed engine aggregation |
| P1.5 | Select and implement one cluster-level scorer | Implemented | HDBSCAN rare/separated-population formula, abstention policy, and synthetic population test |
| P1.6 | Implement Isolation Forest scorer adapter | Implemented | Same-\(X\), deterministic score-direction unit test |
| P1.7 | Implement DOMINANT adapter and controls | Implemented | Sparse heterogeneous trained/untrained paths, aligned component rows, integration test |
| P2.1 | Run small correctness/feasibility pilot | Completed | [`experiments/phase2/results/pilot_v1/REPORT.md`](experiments/phase2/results/pilot_v1/REPORT.md); spec SHA-256 `5133edd044b3…` |
| P2.2 | Decide CoLA through the declared gate | Completed — deferred | Gate was not activated; no label-blind context sampler is frozen or tested |
| P3.1 | Write immutable final matrix specification | Completed | [`experiments/phase3/matrix_v1.json`](experiments/phase3/matrix_v1.json), SHA-256 `c56ca6f3cc5d…` |
| P4.1 | Execute and cache frozen matrix | Completed | 12/12 cases, 0 failures, 912 method rows, 390 representation rows |
| P5.1 | Run paired statistical analysis | Completed | [`experiments/phase5/results/analysis_v1/comparisons.csv`](experiments/phase5/results/analysis_v1/comparisons.csv) |
| P5.2 | Assign Recommend/Explore/Abstain outcomes | Completed | 0 Recommend, 104 Explore, 54 Abstain; [`outcomes.csv`](experiments/phase5/results/analysis_v1/outcomes.csv) |
| P5.3 | Select evidence-backed case studies | Completed | [`case_study_manifest.csv`](experiments/phase5/results/analysis_v1/case_study_manifest.csv) |
| P6.1 | Run untouched confirmation once | Not activated | No Recommend configuration; confirmation labels remain sealed |
| P7.1 | Generate final figures | Pending | Validated figure directory |
| P7.2 | Assemble and verify presentation | Pending | Final deck/export |

## 9. Run-manifest minimum fields

Every final run should record at least:

```text
run_id
timestamp
git_commit
working_tree_state
dataset_name
dataset_version_or_fingerprint
slice_id_and_definition
partition_role
feature_catalog_version
agent_prompt_version
agent_config_hash
sessionization_config
session_count
malicious_session_count
relation_manifest
representation_method
representation_hyperparameters
scorer
scorer_hyperparameters
seed
signal_config
software_environment
runtime
status
failure_reason
artifact_paths
```

## 10. Stop rules

| Observation | Required response |
|---|---|
| A method performs poorly | Record it; do not rescue it post hoc |
| Trained GraphSAGE matches random | Report no demonstrated training value |
| DOMINANT matches its controls | Report no demonstrated anomaly-objective value |
| Representation metrics are useful but all scorers fail | Return Explore: representation-only finding |
| UMAP looks separated but full-space tests fail | Reject the separation claim |
| Signal transform worsens retrieval | Retain intrinsic ranking and reject amplification |
| Results are unstable across seeds/slices | Qualify or abstain |
| Malicious count is inadequate | Mark insufficient evidence |
| Confirmation fails | Narrow/reject the development conclusion |
| A new model idea appears | Add it to future work unless it replaces scope by explicit decision |

## 11. Explicitly deferred unless a decision log entry activates them

- Deep SVDD;
- temporal sequence encoder or Temporal Graph Network;
- unrestricted AutoML or hyperparameter search;
- GCN/GAT/deeper GraphSAGE/HGT variants using the same unresolved objective;
- broad cluster-algorithm comparison;
- exhaustive relation or metapath search;
- repeated signal transforms after the matched transform fails;
- automated open-ended agent refinement;
- production deployment claims.

## 12. Decision log — append only

### 2026-08-03 — Living procedure established

- Replaced the idea of freezing the exact experiment matrix immediately with:
  freeze scope, implement final components, pilot for correctness/feasibility,
  then freeze the exact matrix.
- Retained existing representations without redesign.
- Confirmed post-hoc representation evaluation and one cluster-level scorer as
  immediate additions.
- Selected Isolation Forest and DOMINANT as the most important additions from
  the earlier five-method shortlist.
- Made CoLA conditional on a specific contextual-mismatch question and schedule
  capacity.
- Deferred Deep SVDD and temporal/TGN until evidence identifies their unique
  hypotheses as necessary.
- No implementation was performed as part of this documentation change.

### 2026-08-03 — Phase 1 method and evaluation layer implemented

- Added a stable `representation_key`/`scorer` separation so one original `X`
  can be evaluated once and scored several ways without conflating layers.
- Added full-space malicious-neighbor purity, label silhouette, an out-of-fold
  stratified linear probe, and rotation-invariant cross-seed stability.
- Selected HDBSCAN for the single cluster-level scorer and fixed its current
  rarity/separation formula, noise policy, and dominant-population abstention
  rule. Parameters remain pilot settings until the Phase 3 freeze.
- Added Isolation Forest to compatible session representations.
- Added a sparse heterogeneous DOMINANT-style method with primary-attribute and
  sampled typed-relation reconstruction, trained-versus-untrained controls,
  and exact attribute/structure component evidence at the session level.
- Tightened label isolation so the evaluation label cannot define timestamps,
  sessions, group identities, features, or graph endpoints.
- Updated the Streamlit and workbench payload paths. The workbench cache now
  includes result schema version `2.0`, preventing stale v1 payload reuse.
- CoLA remains gated until the Phase 2 pilot answers whether contextual
  node–neighborhood inconsistency is still an unresolved scientific question.

### 2026-08-03 — Phase 1 verification completed

- The full 14-test engine suite passed, including label isolation, deterministic
  scorer behavior, exact score/session alignment, trained/untrained DOMINANT
  component accounting, explicit graph-failure retention, and strict JSON
  serialization.
- Both the empty and populated Streamlit states rendered without exceptions;
  the populated smoke run exercised the new representation, scorer, stability,
  cluster, and DOMINANT diagnostics.
- Phase 1 is closed. The next action is the bounded Phase 2 pilot, not a final
  matrix freeze and not a broad model or hyperparameter search.

### 2026-08-03 — Phase 2 pilot v1 predeclared

- Froze `experiments/phase2/pilot_v1.json` before model execution.
- Limited real-data evidence to physical-head engineering slices from the ACME
  development parquet. These slices are explicitly non-temporal and cannot be
  used as confirmation evidence.
- Explicitly prohibited reading the sealed test parquet or the combined
  train/test parquet during the pilot.
- Selected one feature hypothesis, a same-seed repeat at 1,000 rows, and a
  two-seed 5,000-row scale/stability case. This tests correctness,
  reproducibility, runtime, memory, and applicability without broad search.
- Predeclared that AP, Recall@K, UMAP appearance, and other performance outcomes
  cannot determine pilot pass/fail or method inclusion.
- CoLA remains deferred unless its separate label-blind context and feasibility
  gates pass; poor DOMINANT retrieval alone cannot activate it.

### 2026-08-03 — Phase 2 pilot v1 passed

- Executed the frozen spec with SHA-256
  `5133edd044b3688a334d25fe8fb90f8516993fcec3d1b508e09c8b246f694436`.
- All three case contracts passed strict serialization, key cardinality,
  canonical-session alignment, finite output, DOMINANT component identity,
  usable relation-example, HDBSCAN policy, and runtime-diagnostic checks.
- The two independent 1,000-row seed-42 runs reproduced 17 completed score
  vectors, their exact rankings, and all cluster/DOMINANT score components.
- The 5,000-row two-seed case produced the five predeclared cross-seed stability
  rows. Across the pilot, 65 method outcomes completed, two HDBSCAN population
  scorers abstained under their fixed assumptions, and none failed.
- Total measured wall time was 261.26 seconds. Peak measured RSS was 1.54 GiB.
  On the 5,000-row case, coordinate projection was the largest instrumented
  cost (84.89 seconds); cache representations/coordinates in the final runner.
- Primary-node structural coverage passed the provisional CoLA data gate:
  non-isolated fraction was 1.0, degree-at-least-two fraction was at least
  0.606, and maximum incident-edge share was at most 0.0147. CoLA nevertheless
  remains deferred because no label-blind context sampler/control is frozen or
  tested, and adding it is not necessary to freeze the existing bounded suite.
- The sealed test parquet and combined train/test parquet were not used. Pilot
  retrieval metrics remain exploratory and were not interpreted for inclusion.
- Phase 2 is complete for ACME; Phase 3 now freezes the exact final matrix.

### 2026-08-03 — Phase 3 matrix v1 frozen

- Froze [`experiments/phase3/matrix_v1.json`](experiments/phase3/matrix_v1.json)
  with SHA-256
  `c56ca6f3cc5d794fc6da3b09dd273b5a07c461ceba1165017608bb559f190b68`.
  Any semantic change now requires a versioned successor rather than an edit.
- The core datasets are ACME, UNSW-NB15, and CIC-IDS2017. LANL remains an
  optional future extension and cannot block or change the core experiment.
- Froze non-overlapping development, selection, and confirmation partitions:
  a label-blind 70/30 time split of ACME train with ACME test sealed; UNSW raw
  files 1–2/3/4; and CIC Monday–Wednesday/Thursday/Friday.
- Capped each partition at 25,000 review units and 25,000 source rows using a
  deterministic, label-blind SHA-256 sampling rule. ACME retains whole
  canonical sessions under both caps; UNSW and CIC use flow rows. Confirmation
  samples are not materialized early.
- Froze all three agent-proposed feature hypotheses per dataset, stochastic
  seeds 42/137/314, the existing representation and scorer battery, one
  degree-sequence-preserving relation-target permutation null, and the single
  label-blind matched signal transform.
- The declared Phase 4 matrix has six development/selection partitions, 912
  method rows, and 390 representation rows. HDBSCAN and technically impossible
  graph-null cases retain explicit valid-abstention rows.
- Froze paired cluster-bootstrap inference, Holm-Bonferroni correction within
  dataset, practical Recall/Precision@K rules, and deterministic
  Recommend/Explore/Abstain plus confirmation-selection rules.
- Dataset configurations are frozen separately in
  [`experiments/phase3/dataset_configs_v1.json`](experiments/phase3/dataset_configs_v1.json).
  This corrects the UNSW raw header mapping and treats all declared CIC attack
  labels as malicious instead of limiting CIC evaluation to Bot.
- Phase 3 is complete. Phase 4 must execute this matrix without hyperparameter
  retries, result-driven scope changes, or confirmation-label access.

### 2026-08-03 — Phase 4 runner made intentionally narrow

- Implemented [`experiments/phase4/run_matrix.py`](experiments/phase4/run_matrix.py)
  as a resumable executor rather than a second experiment-definition layer.
  It reads all scientific choices from the frozen matrix and rejects sealed
  confirmation roles.
- The primary human-facing result is one compact matrix digest grouped by
  dataset, partition, feature hypothesis, representation, scorer, and graph
  variant. Full per-review-unit scores remain supporting Parquet artifacts.
- Disabled coordinate generation during matrix execution because Phase 2
  showed it was the largest avoidable runtime and visual appearance cannot
  select a result.
- Limited label-blind signal diagnosis to the substantive observed
  representations; random, untrained, and permuted controls remain controls
  rather than generating redundant signal-transform branches.
- Added a second 25,000-source-row cap. ACME therefore retains complete hashed
  sessions without constructing a graph from all 467,836 development rows;
  UNSW and CIC already use one flow row per review unit.
- A 500-flow CIC smoke execution completed the observed and graph-null paths,
  produced 58 method rows and 25 representation rows, and wrote the compact
  digest with zero failures.

### 2026-08-04 - Phase 4 matrix and Phase 5 analysis completed

- Executed all 12 frozen development/selection cases across ACME, UNSW-NB15,
  and CIC-IDS-2017. All cases completed with zero failures and produced the
  exact declared totals: 912 method rows and 390 representation rows.
- Ran 2,000-replicate paired cluster-bootstrap comparisons using hostname,
  source IP, or source file according to the frozen dataset policy, followed
  by Holm correction within dataset.
- Assigned 158 selection configurations: 0 Recommend, 104 Explore, and 54
  Abstain. No confirmation candidate was selected, so every Phase 6 partition
  remains sealed.
- Direction-only method-family results were informative but insufficient for
  confirmation: raw Isolation Forest exceeded raw kNN on two datasets;
  DOMINANT training exceeded its untrained control on three; GraphSAGE training
  exceeded random GraphSAGE on zero; and matched amplification improved on zero.
- Recorded a preregistration resolution limitation: with 2,000 bootstrap draws,
  a conservative two-sided finite-sample p-value, and 146-158 evaluable Holm
  comparisons per dataset, the adjusted p <= 0.05 gate is mathematically
  unattainable. This prevents Recommend under the frozen operationalization and
  must not be misreported as evidence that all methods are equivalent.
- The intrinsic outcome table is intentionally smaller than the complete
  outcome table because matched transforms are supporting configurations. The
  complete machine-readable result remains in Phase 5 `outcomes.csv`.
