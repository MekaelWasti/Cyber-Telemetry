# MASTER PLAN — Graph Signal Localization & Amplification for Telemetry Triage

**Version 1 — 2026-07-13.**
Consolidates the three book study notes (`Books/GRL_Book_Project_Study_Notes.md`, `Books/Ortega_GSP_Project_Study_Notes.md`, `Books/Networks_Crowds_Markets_Project_Study_Notes.md`), the prior plans (`SIMPLIFIED_PLAN.md`, `NEXT_PHASE_PLAN.md`, `RESEARCH_SUMMARY.md`, `Scratch Notes.md`), and the current state of `Notebooks/Graph Triage Baseline v0.ipynb`.

**This document is now the single source of truth.** Where it conflicts with `NEXT_PHASE_PLAN.md` or `SIMPLIFIED_PLAN.md`, this document wins, and the conflict is noted inline. Citations like (GRL §9.1) point to sections of the study notes, which carry the underlying book page numbers.

**How to use it:** work top-to-bottom through the phases in §5. No phase starts until the previous phase's **gate** passes. Gates are label-free unless marked. Everything else in this document (metrics, nulls, decision rules, wording) exists so that each phase's output is defensible the day it is produced.

---

## 1. Thesis (refined)

Your draft thesis survives contact with all three books, with sharpened wording. The defensible version, converging across GRL §20, Ortega §25, and NCM §21:

> **Given a heterogeneous telemetry graph, determine whether task-relevant signal is expressed as local structure, walk proximity, typed relations, graph-smooth communities, or repeated structural roles — relative to matched null models; localize the relations, hops, and scales responsible; apply the amplification mechanism matched to that diagnosed regime with parameters frozen before evaluation; and return both a triage ranking and its perturbation-tested supporting subgraph.**

Three sharpenings versus your draft:

1. **"relative to matched null models"** — a signal claim is only meaningful against degree-, relation-, and label-count-matched nulls (GRL §11, Ortega §14, NCM §16). This is what makes the result publishable rather than anecdotal.
2. **"matched to that diagnosed regime"** — amplification is *conditional*. If the diagnosed regime is heterophilous/contrastive, low-pass diffusion *erases* the signal; if no regime beats the nulls, the correct action is *do not amplify* (Ortega §16, GRL §13.4).
3. **"perturbation-tested"** — a supporting subgraph is only evidence if deleting it moves the score more than matched random deletion (GRL §12 Stage 5, Ortega §17.5, NCM §18.3). It is *support*, never a "causal attack path."

### What the contribution is / is not

| The contribution IS | The contribution IS NOT |
|---|---|
| An auditable graph-signal **localization + conditional amplification framework** for triage, evaluated across three distinct structural hypotheses | A new GNN architecture, or proof that "GNNs detect attacks" |
| A **dataset-portable procedure**: frozen audit, methods, nulls, metrics; per-dataset unsupervised refit (GRL §14, Ortega §18, NCM §21) | A "dataset-agnostic" frozen model that transfers zero-shot |
| A ranking plus **faithful supporting structure** an analyst can inspect | Causal attack-path reconstruction |

### The "dataset agnostic" correction (important)

Your scratch note said *"we are dataset AGNOSTIC, we don't CARE about dataset analysis."* All three books push back on the letter of this while supporting its spirit: **graph construction is part of the method** (GRL §8.4, Ortega §8, NCM §1), so you cannot skip dataset structure — but you can make it a *standardized, audited input*. The portable thing is the **procedure**: schema contract → topology audit → representations → signal atlas → conditional amplification → faithfulness tests. Graph statistics, operators, and model parameters are refit per dataset without labels; the rules are frozen. That IS the dataset-agnostic claim, at the level you can actually defend (claim ladder in §9).

---

## 2. Where you are right now (state audit)

### Done and solid
- Frozen dev slice (`tail(100_000)` of train parquet), holdout loaded.
- Raw strawman: sessionizer (user w/ host fallback, 5 min inactivity / 30 min cap) → session stats → StandardScaler → kNN(k=15) distance score.
- Metric harness: AP, reviews-to-first (+ random expectation), found/recall/precision @ {25,50,100,250}; `random_score` control wired into the pipeline entry point.
- Label hygiene fixed: enrichment "score" correctly demoted to `malicious_neighbor_purity_diagnostic` (label-aware, evaluation-only).
- The key empirical fact so far: **purity@15 ≈ 0.207, enrichment ≈ 16.7× over base rate, 84% of malicious sessions have a malicious top-15 neighbor — while raw anomaly AP ≈ 0.016 (prevalence ≈ 0.013) and first hit at rank ~128 (random expectation ~73).**

### The correct reading of that fact
Malicious sessions form a **compact local cluster that the point-anomaly scorer treats as ordinary** (NCM §19.6, GRL §12 Stage 1, Ortega §9.5). This is not a failed baseline; it is a localized signal regime diagnosis. It predicts: (a) point-outlier kNN distance is the wrong score family for this data; (b) cluster-geometry scores (density peak / compact-isolated-cluster, already in your Scratch Notes) and anchor steering (already demonstrated in RESEARCH_SUMMARY) are the mechanisms matched to the regime. The whole plan below is built to establish that chain *defensibly* instead of anecdotally.

### Three blocking defects (all three books independently flag these)

**B1 — Two session definitions.** Raw sessionizer → 1,457 sessions; graph builder's `_extract_bounded_sessions` (host+user key) → 3,131. No cross-method comparison is valid until one canonical session table exists (GRL §16 Stage 0, Ortega §9.3, NCM §19.1).

**B2 — The v0 telemetry graph is nearly empty.** Saved build: 100,000 process nodes, **14 file nodes, 66 touches, 2,318 parent-child edges** → **≥95% of process nodes are provably isolated** (Ortega §9.1, NCM §2.3/§19.2). Training node2vec or GraphSAGE on this graph produces an uninterpretable result: a loss would not distinguish "graph methods fail" from "almost no node has any relational context." **Do not run the Node2Vec cell or the SAGE comparison until Phase 1's coverage gate passes.** This supersedes `NEXT_PHASE_PLAN.md` steps 4–5.

> Note on the pre-declared "don't rescue the graph" rule in SIMPLIFIED_PLAN: that rule forbids *label-driven* edge additions to rescue a losing score. It does not forbid a *label-free coverage repair* chosen on connectivity/semantic-validity criteria before any graph score exists. Record the v0 graph as "insufficient coverage — stop condition hit," and declare graph **v1** as a new experiment version (NCM §15.2, Ortega §8.3).

**B3 — Node features are effectively absent.** `FEATURE_COLS = []`, file features constant 1. Fine for node2vec (topology-only is its job); undefined for a GraphSAGE claim (NCM §19.3, GRL §16 Stage 4). Also stale bookkeeping: the manifest comment about connected-component sessions, the graph-section markdown mentioning "temporal relations," `git_commit: "N/A"`.

---

## 3. The scientific spine (non-negotiables)

These are the rules every phase obeys. They are the answer to "will I read something later and realize this was invalid."

**3.1 The label boundary.** (GRL "research pipeline" preamble, Ortega §11.2)

```python
graph = build_graph(telemetry, frozen_graph_config)        # no labels
X     = build_representation(telemetry, graph)             # no labels
s0    = label_free_score(X)                                # no labels
# ---- everything above is frozen before the line below ----
metrics      = evaluate_ranking(s0, hidden_labels)         # labels enter here
diagnostics  = diagnose_representation(X, hidden_labels)   # label-aware, marked as diagnostic
```

Litmus test (already in your Scratch Notes): *if shuffling `red_team` changes the score values, the score is label-aware; if it only changes the metrics, the method is clean.*

**3.2 One canonical evaluation contract.** One `process_index → session_id` map, one ordered session table, one label vector, one review unit — consumed identically by every method. Assert it in code (Ortega §20.6):

```python
assert session_table.session_id.is_unique
assert np.array_equal(method_session_ids, session_table.session_id.to_numpy())
assert scores.shape[0] == len(session_table)
```

**3.3 Diagnostics ≠ scores.** Label-aware quantities (purity, peer rank, fragmentation, label energy) are *representation diagnostics*; they never appear in the triage-score table, and they never select hyperparameters on the split they are reported on (NCM §16.2). If dev labels ever select a config (e.g., filter family), record it as *development-supervised selection*, then confirm frozen on holdout (Ortega §4.7).

**3.4 Two supervision regimes, never merged.** (GRL §10.4, NCM §14.5)
- **Unseeded discovery:** label-free score over all sessions.
- **Anchor steering:** one confirmed malicious session as seed; leave-one-anchor-out; anchor excluded from evaluation; report cross-host retrieval to kill identity shortcuts.

**3.5 Every claim ships with its control.** The minimum ladder (NCM §16.1): random ranking → prevalence → raw features → degree/activity-only features → real graph method → typed degree-preserving rewire → relation/feature ablations. "Beats random" is not a finding; "exploits more than degree, volume, component size, and identity" is.

**3.6 Frozen configs + manifest.** Every run records: slice rule, sessionizer params, graph config, feature list, k, scaler, seeds, filter params, git hash. Frozen values for this project: sessionization = user-identity w/ host fallback, 5 min inactivity, 30 min cap; k = 15; seeds = 42/43/44; review budgets = 25/50/100/250; refit policy = per-slice unsupervised refit (from SIMPLIFIED_PLAN — all still correct).

---

## 4. The method roster (what "3 methods" means now)

Both GRL §9 and NCM §14 land on the same headline triad — three *different structural hypotheses*, not three GNN variants. Ortega adds the level-0 method you called "the most basic graph method": it is **not a GNN**, it is a fixed filter bank on a session-similarity graph (Ortega §12.3).

| # | Method | Hypothesis tested | Graph used |
|---|---|---|---|
| C1 | `random_score` | sanity floor | — |
| C2 | `raw_session_stats_knn` | aggregate telemetry alone suffices | — |
| M0 | **GSP filter bank**: `s0`, `P·s0`, `(I−P)·s0`, `P·s0−P²·s0`, restart diffusion | the raw geometry's *local structure* carries signal a point score misses | session-similarity kNN graph (k=15, from raw features) |
| M1 | `typed_structural_stats_knn` | malicious sessions have unusual explicit roles/motifs/counts | telemetry graph v1 |
| M2 | `node2vec_session_knn` (p=q=1 primary) | short-walk proximity carries signal beyond explicit stats | telemetry graph v1, declared homogeneous projection |
| M3 | `relational_graphsage_session_knn` | learned typed feature×topology interaction adds value | telemetry graph v1, typed |

Mandatory companions (not headline methods): trained-vs-**random-init** encoder for M3 (GRL §6.2 — the single most load-bearing GNN control), degree-preserving rewired graph for M0–M3, zero-layer/feature-only encoder, shuffled-feature control. Personalized PageRank = transparent steering control, not a fourth headline (NCM §14). Deterministic PPR/filter propagation = amplification control (GRL §9.4).

All methods: pool process→session by **mean** over the canonical sessions (report session size separately; sum only as declared sensitivity — GRL §5.7), then the **same** kNN scorer, same metrics.

---

## 5. Phase roadmap with gates

Estimated effort assumes notebook-scale work. Phases 0–2 are days, not weeks, and Phase 2 can start while Phase 1's repair decisions settle.

### Phase 0 — Canonical evaluation contract *(supersedes nothing; NEXT_PHASE_PLAN step 1, unchanged)*
1. Keep the raw sessionizer rule as canonical (it is the one frozen in SIMPLIFIED_PLAN).
2. Delete `_extract_bounded_sessions`; the builder consumes the canonical map (`builder.sessions = sessions`).
3. Save `canonical_sessions` artifact: `process_index, pid_hash, session_id`; session table with labels computed once.
4. Fix bookkeeping: manifest gains n_sessions, n_malicious_sessions, file-node count, sessionizer params, git hash, config dump; delete stale markdown ("temporal relations", connected-component comment); holdout viability check recorded (malicious sessions present? counts by user/host).
5. Alignment + determinism + label-isolation tests from SIMPLIFIED_PLAN's test plan.

**Gate:** every method returns exactly one score per canonical session; `len(sessions)` identical everywhere; sessions partition all rows; two identical-seed runs reproduce the manifest and metrics.

### Phase 1 — Telemetry graph audit, then repair (label-free)
*This is the phase that saves you from the "oh no" moment. It comes BEFORE any graph training.*

**1a. Audit the v0 graph exactly** (Ortega §9.4, NCM §15.1): exact isolate counts by node type; component-size distribution; fraction of canonical sessions with ≥1 incident edge (parent evidence / file evidence separately); relation-specific degree quantiles; 1/2/3-hop coverage; walkable fraction under the declared direction semantics. Save as `graph_manifest` (schema in Ortega §21.1).

**1b. Repair coverage with label-free, declared criteria** (candidate levers, NCM §19.2):
- parent resolution against broader history (parents outside the tail slice currently vanish — a child whose parent fell outside the slice loses its lineage edge; context nodes may come from history without becoming evaluation sessions);
- file identity key: `filename` vs path vs hash vs documented composite (currently filename-only → 14 rare files);
- replace/augment the hard file-degree cap `[2,15]` with **inverse-degree weighting** of common files (keep ubiquitous context, downweight it — NCM §16.5, Ortega §8.5) and run the predeclared sensitivity set (include singletons; raise max degree; no filter on a sample — Ortega §8.3);
- name direction semantics explicitly: forward parent edges + separately-named reverse relation if walks need it; `touches`/`touched_by` = one observed event in two traversal directions, never double-counted as evidence (GRL §4.4).

Choose the v1 graph on **coverage, stability, and semantic validity — never on label metrics** (NCM Stage 1 gate). Record every variant's edge-survival delta.

**Gate (declare the threshold before looking):** a declared minimum share of canonical sessions has usable graph evidence (pick and write down, e.g., ≥60% sessions with ≥1 edge; there is no universal number — NCM §15.2); enough multi-node components exist for relational comparison; relation semantics documented. If the gate can't be met, the graph-methods claim is scoped to the connected minority — stated, not hidden (never headline connected-only results — NCM §17.3).

### Phase 2 — M0: the basic GSP baseline *(new; can start immediately after Phase 0)*
The cheapest, most theory-grounded next result, and it reuses your strongest finding (Ortega §9.5, §12.3):

1. Build the label-free session-similarity kNN graph (k=15) from the tight raw features; record reliability diagnostics (hubness, distance concentration, mutual-vs-union components, isolates — Ortega §8.6).
2. Operators: row-normalized `P = D⁻¹A` primary; combinatorial `L` as sensitivity (Ortega §1.2 — normalization is essential in a degree-skewed graph).
3. Compute the four channels of `s0` (= raw kNN score): identity, neighbor mean `P·s0`, residual `(I−P)·s0`, scale difference `P·s0 − P²·s0`, plus truncated restart diffusion (α ∈ small predeclared set, K ≤ 3). Evaluate each channel separately — no ensembles yet (Ortega §12.4).
4. **Signal audits** (this is the start of the signal atlas):
   - score audit (label-free): Dirichlet energy of `s0`, residual distribution, spectral energy profile;
   - label audit (evaluation-only, after everything is frozen): normalized label energy `zᵀLz/(zᵀDz)`, conductance, low/mid/high band mass, vs label-shuffle + degree-binned shuffle + host-blocked shuffle + degree-preserving rewire nulls (Ortega §3.2).
5. Report edge contributions `w_ij(x_i−x_j)²` for top sessions — the first traceability artifact (Ortega §17.4).

**Gate:** audit runs end-to-end with zero label-free/label-aware category errors; every channel scored on canonical sessions; null comparisons attached.

*Pre-registered expectation: given purity 16.7× with weak AP, the label audit should show low-frequency/localized structure that `s0` itself does not align with (Ortega §3.3 row 2/4). That exact table row is what licenses Phase 8's amplification choice.*

### Phase 3 — M1: typed structural statistics
First telemetry-graph method: cheap, auditable, and it doubles as the GraphSAGE feature table (NCM §14.2 has the full feature list — typed degrees, component/SCC roles, embeddedness/bridges, bipartite affiliation incl. inverse-file-degree co-affiliation and 4-cycles, PageRank/HITS as covariates).
- Pool with fixed summaries [mean, median, Q90, max, log(1+|S|)] (NCM §14.2).
- `log1p` skewed counts → robust-standardize → same kNN scorer.
- Ablations: lineage-only / affiliation-only / closure-brokerage-only / full; typed degree-preserving null (double-edge swaps within relation — NCM §16.3); label-shuffle null.
- Explanation artifact: per-session top standardized feature deviations + the nodes/edges instantiating them (GRL §9.1 — strongest first explanation in the whole project).

**Gate:** stable effects beyond degree/activity features and shuffled topology.

### Phase 4 — M2: node2vec
- Decide walk semantics *before* `to_homogeneous()` (directed vs association walks; typed graph stays canonical — NCM §19.4, GRL §9.2).
- p=q=1 primary; one BFS-ish and one DFS-ish setting as declared sensitivities only.
- Seeds 42/43/44; report walk coverage and isolate handling explicitly (isolates get no learned context — report them separately, never silently pooled).
- Controls: degree-preserving rewired graph; check embeddings aren't just encoding component membership or degree bands.

**Gate:** walk context adds something beyond M1 on ≥1 frozen metric/diagnostic, not explained by hubs.

### Phase 5 — M3: relational GraphSAGE
- Features: run the declared trio — topology-only (constant/type + relation-degree features), feature-only (zero-layer), feature+topology (GRL §9.3). `X_struct` from Phase 3 is the controlled feature input (NCM §14.4). No IDs, hashes, identity encodings, absolute timestamps in the primary claim.
- Architecture: 2 layers, relation-specific transforms, explicit self/root channel, normalized aggregation + explicit per-relation degree features, Jumping-Knowledge concat h⁰⊕h¹⊕h² (GRL §5).
- Objective: typed link prediction with type-valid, filtered negatives and a direction-capable decoder (dot product is symmetric — wrong for `parent_child` alone; GRL §4.2–4.3). Report held-out edge metrics separately from triage (GRL §10.3).
- **Mandatory controls:** trained vs random-init encoder (no random-init win → no "learned graph value" claim, test DGI corruption objective before any architecture zoo — GRL §6.2–6.3); shuffled features; relation-preserving shuffled graph; depth 1/2/3 with over-smoothing measures (embedding variance, mean cosine).

**Gate:** trained encoder beats identical random encoder AND same model on null topology, reproducibly across seeds.

### Phase 6 — Frozen comparison + scoring-direction experiment
1. One table: C1, C2, M0 (best declared channel), M1, M2, M3 — mean ± std across seeds, all metrics from §6, on the dev slice. Freeze method definitions after this table.
2. **Scoring-direction experiment** (separate, pre-declared — NCM §19.6): with the representation fixed, compare point-kNN-distance vs `density_peak_score` vs `compact_isolated_cluster_score` (your Scratch Notes suite). This tests whether the compact-cluster regime explains the weak AP — a headline-quality finding either way.
3. Anchor-steering evaluation of every representation (leave-one-anchor-out, cross-host reported) as the second evaluation mode (NCM §14.5) — this connects back to the RESEARCH_SUMMARY steering result under the new, clean protocol.

### Phase 7 — Signal atlas (localization)
For each representation/layer/relation view (GRL §12 Stages 1–3, Ortega §11.3):
- triage metrics + diagnostics (purity, `malicious_mean_peer_rank`, `malicious_fragmentation_at_15` — definitions in GRL §10.2) + label energy + band mass + null lifts + seed stability;
- relation ablations with **matched random-edge-removal** comparison (GRL §11.3);
- hop/layer curves (h⁰/h¹/h²); typed metapath enrichment (process→file←process, parent→child→file, …) vs typed rewires;
- classify the regime: smooth / contrastive / multiscale / relation-specific / role-based / **absent** (Ortega §15 Stage 5 gate).

**Deliverable:** `signal_atlas` + `filter_comparison` artifacts (schemas: Ortega §21).

### Phase 8 — Conditional amplification + faithful tracing
Choose the amplifier from the diagnosed regime — this table IS the decision rule (Ortega §16, GRL §13.4):

| Diagnosed regime | Amplifier | Guardrail |
|---|---|---|
| low-frequency / homophilous | restart diffusion, PPR, low-pass | must beat same filter on rewired graph; watch variance collapse |
| local rare-artifact proximity | short walks, inverse-degree weighting, high restart | control for rare-benign artifacts |
| high-frequency / contrastive | residual channels, self-channel retention | do not force smoothing |
| multiscale | SGWT band energy (Chebyshev, frozen bands) | approximation error reported |
| relation-specific | typed operator bank, combine only after ablation | direction preserved |
| repeated role | role/motif retrieval | no connectivity requirement |
| **absent** | **do not amplify** | revise graph hypothesis as new version |

Amplification success = ΔAP / Δrecall@budget on real graph **minus** the same filter's gain on rewired graph, stable under perturbation, without variance collapse (Ortega §13.4: "amplification" never means "numbers got bigger"). Faithful tracing per GRL §12 Stages 4–5 / Ortega §17: hop contributions `a_k(Pᵏs0)_i`, signed source contributions, relation/metapath contributions from a small predeclared bank, then **deletion faithfulness** vs matched random removal, across seeds. Paths are time-respecting, direction-respecting, relation-respecting or they are not called paths (NCM §11.5, §18.1).

### Phase 9 — Holdout confirmation
Viability check first (already required by SIMPLIFIED_PLAN); refit only what the frozen refit policy allows; **zero** graph/filter/threshold selection on holdout labels; confirmation standard = direction of dev result replicates on both co-primary metrics (unchanged from SIMPLIFIED_PLAN). Also report regime stability (does the signal atlas classification replicate?).

### Phase 10 — Second dataset (portability)
Schema adapter → same audit → per-dataset unsupervised refit under frozen rules → report which relations exist/don't → procedural transfer first, frozen-hyperparameter transfer second, frozen-model transfer only as an explicit extra experiment (GRL §14, Ortega §18, NCM §21). Recomputing degrees/spectra/normalizations per dataset is not a portability failure; hiding the refit would be (Ortega §18.2).

### Deferred (scope guard — revisit only with cause)
Slepians & diffusion wavelets (after SGWT shows multiscale signal), graph learning from signals (circularity risk, needs stable nodes + repeated windows — Ortega §8.7–8.8), active-learning/sampling review batches (Ortega §5), higher-order GNNs/GIN (only if motif probes show 1-WL blindness matters — GRL §7.7), attention (only after relation/hop localization — GRL §9.4), edge-state message passing, agentic explanation layer (presentation over the computed evidence record only — NCM §21.1; it never creates evidence).

---

## 6. Metric suite (final)

Locks in your Scratch Notes picks; identical scorer and metrics for every method.

**Triage (label-free scores, labels only at evaluation):** AP (+ AP lift = AP/prevalence), reviews_to_first (+ random expectation N+1/(M+1) + first-hit lift), found/recall/precision @ {25,50,100,250}. Deterministic methods once; stochastic per-seed and mean±std — never hide a seed failure in a mean (GRL §10.1). With 19 positives, reviews-to-first is volatile: never interpret alone (Ortega §13.1).

**Representation diagnostics (label-aware, marked):** `malicious_neighbor_purity_at_15` (+ enrichment, any-neighbor fraction), `malicious_mean_peer_rank` (+ nearest-peer rank), `malicious_fragmentation_at_15` (mutual-kNN components over malicious nodes) — each with label-shuffle, degree-binned shuffle, and rewire nulls (GRL §10.2).

**Signal-regime metrics:** Dirichlet & degree-normalized energy, conductance, band masses, local residual, node spread, null percentile (Ortega §13.3).

**Graph reliability:** isolate fraction, session coverage, component shares, degree concentration, hubness, K-hop coverage, perturbation stability (Ortega §13.6) — prerequisites to interpreting anything else.

**Uncertainty:** session bootstrap + host/campaign-grouped bootstrap + leave-one-host-out sensitivity; 19 correlated positives ≠ 19 independent samples (NCM §17.6 — this also retro-applies to the old Wilcoxon p-values in RESEARCH_SUMMARY).

---

## 7. Null & control ladder (applies to every result)

1. Label permutation (session-level; stratified by host/campaign when concentrated — NCM §16.2).
2. Degree-binned and host/time-blocked label shuffles (Ortega §3.2).
3. Typed degree-preserving rewire (double-edge swaps per relation; bipartite-degree-preserving for process-file — NCM §16.3).
4. Relation-preserving endpoint shuffle; relation-label shuffle (GRL §11.2).
5. Matched random edge removal (for every relation-ablation claim — GRL §11.3).
6. Feature shuffle within node type; trained-vs-random encoder; zero-layer encoder (GRL §11.1).
7. Temporal nulls when any temporal claim is made (NCM §16.4).
8. Shortcut checklist on every win: same-host? same-user? session size? time proximity? degree? one ubiquitous file? component membership? synthetic reverse edges? (NCM §15.4).

---

## 8. Pre-declared hypotheses & outcome handling

From GRL §18, aligned with the current evidence — write these down as-is before running Phase 3+:

- **H1** Raw features keep malicious neighbor enrichment even while raw anomaly ranking stays weak. *(already supported)*
- **H2** Typed structural stats beat raw features + typed rewire null on ≥1 diagnostic.
- **H3** node2vec beats structural stats only if short-walk context carries extra signal.
- **H4** Relational SAGE beats node2vec only if relation semantics / feature×topology interactions matter.
- **H5** Trained SAGE must beat random-init SAGE for any "learned" claim.
- **H6** ≥1 relation or short metapath shows stable loss under removal beyond matched random removal.
- **H7** Propagation improves ranking only where the diagnosed regime is smooth under the chosen operator.
- **H8** The best method/control direction and the identified signal carrier replicate on holdout.

**Every negative outcome has a pre-declared meaning** (this is what makes the project robust to "it didn't work"): graph loses → honest v0 finding, pivot to steering framing (already pre-declared in SIMPLIFIED_PLAN); purity high but AP weak → retrieval/steering representation, not a detector (GRL §18); trained ≈ random encoder → smoothing/projection effect, test DGI; gain survives on rewired graph → degree/volume artifact, claim dies; regime = absent → do not amplify, revise graph hypothesis as a new version.

---

## 9. Claims & wording discipline (for notes and the paper)

| Tempting | Defensible |
|---|---|
| "The graph contains malicious signal" | "The evaluation-only malicious indicator is organized non-randomly on this declared graph/operator relative to matched nulls" |
| "We amplified signal without labels" | "A frozen graph filter improved a label-free score; labels used only for evaluation" |
| "This is the attack path" | "This typed path materially supported the score and passed deletion-faithfulness" |
| "Dataset agnostic" | "Label-free at fit time; portable via schema adapters + per-dataset unsupervised refit under frozen rules" |
| "The GNN learned the structure" | Only if trained beats random-init on identical architecture |
| "Malicious sessions cluster because attacks spread" | Homophily ≠ propagation: selection, influence, shared context, or construction artifact all produce it (NCM §4.3) |

Dataset-agnostic claim ladder (NCM §21 / GRL §14): workflow portability (target now) → hyperparameter portability (test next) → model portability (not established) → mechanism portability (needs domain evidence).

---

## 10. Immediate next actions (this week, in order)

1. **Phase 0 in the notebook:** delete `_extract_bounded_sessions`, wire the canonical session map through the builder, fix the manifest (+ git hash, config dump, session counts), delete stale markdown, add the three assertions, run the determinism check. *(~half a day; NEXT_PHASE_PLAN steps 1–3 & 6–7 are absorbed here and remain valid.)*
2. **Phase 1a audit cell:** exact isolates, components, session coverage, hop coverage on the v0 graph. Expect it to fail the gate — that failure is itself a recorded, book-grounded result.
3. **Phase 2 (parallel):** session-similarity kNN graph + the 4-channel filter bank + score/label audits with shuffle/rewire nulls. This produces the project's first genuinely novel table and directly operationalizes "find where the signal lives."
4. **Phase 1b repair:** parent resolution against history, file identity key comparison, inverse-degree weighting vs hard caps; pick graph v1 on coverage/stability/semantics only.
5. Then Phases 3 → 4 → 5 in order. Do not touch the Node2Vec cell until the Phase 1 gate passes.

---

## 11. Source map (where to look things up)

| Topic | Primary source |
|---|---|
| Method design, encoders/decoders, message passing, objectives, controls | GRL notes §3–§7, §9, §11 |
| Signal/operator/frequency discipline, filter bank, audits, amplification math | Ortega notes §1–§4, §12–§17 |
| Graph semantics, coverage, homophily caution, nulls, temporal validity, tracing | NCM notes §2–§4, §15–§18 |
| Roadmaps that this plan merges | GRL §16, Ortega §15, NCM §20 |
| Prior empirical evidence (steering works; identity is the discriminator; temporal features hurt) | RESEARCH_SUMMARY.md |
| Frozen protocol details (slice, sessionizer, seeds, refit, budgets) | SIMPLIFIED_PLAN.md |
