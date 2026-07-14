# Introduction to Graph Signal Processing: Project-Focused Study Notes

Source: Antonio Ortega, *Introduction to Graph Signal Processing* (Cambridge University Press, 2022), in the local [source PDF](<./Antonio Ortega - Introduction to Graph Signal Processing (2022, Cambridge University Press) - libgen.li.pdf>).

These notes extract the material that matters for the cyber graph-triage project. They are not a substitute for the book or a chapter-by-chapter paraphrase. The focus is the proposed research sequence:

> detect whether a graph contains useful task signal, locate where and at what scale it occurs, apply a matching graph filter to amplify it, and return both a triage ranking and traceable supporting structure.

This book is the signal-processing companion to the [Hamilton study notes](./GRL_Book_Project_Study_Notes.md). Hamilton explains how graph representations and GNNs encode structure. Ortega explains what a graph signal is, how the graph and operator define frequency, how to test signal assumptions, and how to build explicit local, low-pass, high-pass, band-pass, and multiscale transformations.

## Citation convention

The PDF has 18 pages of front matter before printed page 1. References use both printed and PDF page numbers:

> (printed p. 51; PDF p. 69)

Thus, for Chapters 1–7, the PDF page is the printed page plus 18. The book's notation is adapted slightly where that makes the project mapping clearer.

## Executive conclusions

1. **The basic research unit is not just a graph; it is a graph–signal–operator triple.** A graph signal is a scalar value at every node. The graph says which nodes are related, while the operator—adjacency, random-walk matrix, combinatorial Laplacian, normalized Laplacian, or another choice—determines what propagation, variation, and frequency mean. Results cannot be interpreted without naming all three (printed pp. 2–10, 41–55, 75–103; PDF pp. 20–28, 59–73, 93–121).

2. **A telemetry relation is not automatically a similarity relation.** Much of classical GSP assumes a large nonnegative edge weight means the incident nodes should have similar signal values. That is natural for a similarity graph, but it is not automatically true of `parent_child` or `process -> file` relations. A parent and child can have different roles; a malicious process can touch a benign common file. The project therefore needs either a deliberately constructed similarity graph, a justified relation-specific operator, or both (printed pp. 181–194; PDF pp. 199–212).

3. **Graph choice is part of the model, not preprocessing.** The book repeatedly emphasizes that locality, smoothness, the graph Fourier basis, filters, and sampling sets all change when the graph changes. There is no context-free “right graph.” A graph is useful when its assumptions fit the signal and the downstream task (printed pp. 181–182, 204–205, 233; PDF pp. 199–200, 222–223, 251).

4. **“Signal amplification” can be made mathematically precise.** If \(Z\) is a one-hop operator, a polynomial graph filter

   \[
   H(Z)=\sum_{k=0}^{K} a_k Z^k
   \]

   combines information from bounded \(K\)-hop neighborhoods. Its frequency response is \(h(\lambda)=\sum_k a_k\lambda^k\). Low-pass filters strengthen graph-smooth components, high-pass filters expose local disagreement, and band-pass or wavelet filters isolate intermediate scales (printed pp. 51–55, 89–95, 165–169; PDF pp. 69–73, 107–113, 183–187).

5. **Polynomial filters are especially well aligned with traceability.** The contribution of \(Z^k x\) is explicitly tied to \(k\)-hop walks, and the coefficient \(a_k\) says how much that scale contributes. With typed operators, products such as \(P_{\text{session-process}}P_{\text{process-file}}P_{\text{file-process}}P_{\text{process-session}}\) identify semantic meta-paths. These are inspectable influence paths, although they are not automatically causal attack paths (printed pp. 53–55, 94–95; PDF pp. 71–73, 112–113).

6. **Low frequency is not synonymous with useful, and high frequency is not synonymous with noise.** Frequency is graph-relative. A malicious cluster on a good similarity graph may be low or piecewise-low frequency; isolated malicious events, boundary behavior, or heterophilous relations may be high frequency. The appropriate filter follows from a diagnosed signal regime, not from a default preference for smoothing (printed pp. 79–89, 120–130; PDF pp. 97–107, 138–148).

7. **The book provides an exact first diagnostic: graph variation.** For an undirected nonnegative graph with combinatorial Laplacian \(L=D-A\),

   \[
   x^\top Lx=\sum_{i\sim j} w_{ij}(x_i-x_j)^2.
   \]

   This measures how much a signal changes across weighted edges. Applied to an evaluation-only malicious indicator, it tests whether the chosen graph puts malicious and benign sessions on opposite sides of many strong edges. Applied to a label-free anomaly score, it tests whether the score is locally coherent. Both should be compared against suitable permutations rather than read in isolation (printed pp. 79–85; PDF pp. 97–103).

8. **Degree normalization is essential for this telemetry graph.** Combinatorial and normalized operators treat hubs and isolated nodes differently. In an irregular graph, an impulse has combinatorial variation equal to its degree, while a degree-weighted normalized formulation can give every impulse equal variation. Without this distinction, common files, high-volume processes, and dense sessions can dominate a purported signal result (printed pp. 49–53, 99–103, 145–147; PDF pp. 67–71, 117–121, 163–165).

9. **The project should diagnose a signal model before choosing an amplifier.** Ortega develops bandlimited, approximately bandlimited, piecewise-smooth, statistical, and stationary graph-signal models. These imply different reconstruction and filtering strategies. For rare cyber activity, approximate or piecewise smoothness is more plausible than exact bandlimitedness; localized high-frequency components may be the useful signal rather than model error (printed pp. 120–130; PDF pp. 138–148).

10. **The raw neighbor-purity result supports localization, but not yet unsupervised amplification.** The current raw representation places malicious sessions near malicious sessions at roughly 16.7 times the random rate, while its anomaly score has weak AP. That says the hidden label signal is locally concentrated in that representation. It does not supply a deployable seed signal: malicious-neighbor purity uses labels. A label-free amplifier still needs an input such as the raw anomaly score, a rule score, a reconstruction residual, or analyst-provided anchors.

11. **Sampling is relevant to analyst review, but the analogy must be used carefully.** Graph sampling chooses observed nodes so an assumed signal can be reconstructed elsewhere. Triage ranks nodes to find rare positives. Those are different objectives. Sampling theory becomes directly useful when the project asks which sessions to label so that a smooth score or label field can be reconstructed, which makes it a strong later-stage active-learning component rather than the first anomaly-ranking method (printed pp. 120, 131–148, 229–230; PDF pp. 138, 149–166, 247–248).

12. **Graph Slepians and graph wavelets are the book's strongest tools for localization.** Slepians find low-frequency vectors concentrated in a chosen subgraph. Spectral graph wavelets apply a bank of filters at multiple scales, making it possible to identify whether unusual energy is node-localized, frequency-localized, or both. These are excellent second-stage tools after a basic filter-bank baseline is working (printed pp. 149–169; PDF pp. 167–187).

13. **Graph learning can help, but it is a major circularity risk.** Learning a graph by making observed signals smooth can guarantee that those same signals look low-frequency on the result. If labels or evaluation outcomes influence the learned edges, the signal claim leaks. Graphs learned from data must use label-free training signals, be fit only on the allowed training portion, and be evaluated against simpler fixed graphs and null graphs (printed pp. 194–201; PDF pp. 212–219).

14. **Local normalized filters are more portable than graph-specific eigenvectors.** A polynomial in a normalized one-hop operator has the same procedural meaning on different graphs: aggregate one hop, two hops, and so on. A coefficient at “the 47th eigenvector” has no stable semantic alignment across datasets. This makes local polynomial or rational filters the best foundation for the project's realistic dataset-agnostic claim (printed pp. 53–55, 89–94, 167–169, 230–233; PDF pp. 71–73, 107–112, 185–187, 248–251).

15. **Portability has a stability–selectivity trade-off.** Sharply frequency-selective filters can change substantially when graph topology changes; flatter filters are more stable but less selective. A cross-dataset claim should therefore report graph perturbation stability and should not assume that a filter tuned to one exact spectrum transfers unchanged (printed pp. 230–233; PDF pp. 248–251).

16. **The book supports a bounded thesis contribution.** A coherent scope is: define graph-signal diagnostics, compare a small fixed filter bank, localize successful signal by relation/hop/scale, and return supporting subgraphs. Graph learning, active sampling, and agentic explanation can be framed as extensions rather than requirements for the first contribution.

The research statement that survives these qualifications is:

> Given a telemetry-derived graph and a label-free node signal, diagnose how that signal and an evaluation-only task signal are organized across graph relations and scales; select or learn a bounded, interpretable graph filter without using evaluation labels; then produce a triage ranking together with the relation-, hop-, and node-level contributions that generated it.

---

## How Ortega complements Hamilton

| Research question | Hamilton: representation-learning view | Ortega: signal-processing view |
|---|---|---|
| What is learned? | Node/session representations that preserve a training objective | A transformation of explicit scalar or multichannel signals on a chosen graph |
| Central object | Encoder, decoder, neighborhood aggregator, embedding | Graph \(G\), operator \(Z\), signal \(x\), filter \(H(Z)\) |
| Main inductive bias | Homophily, structural role, typed message passing, objective design | Smoothness, frequency content, locality, stationarity, signal model |
| Meaning of depth/order | Number of message-passing layers | Polynomial degree and therefore bounded hop range |
| Basic diagnostic | Downstream geometry, link objective, structural controls | Dirichlet variation, spectral energy, local residual, filter response |
| Explicit amplification | Learned message passing or personalized propagation | Low-, high-, band-pass, rational, wavelet, or diffusion filtering |
| Localization | Attention, saliency, paths, subgraphs | Node-frequency spread, localized kernels, Slepians, wavelets |
| Graph construction | Schema and relation design | Approximate, sparsify, construct from attributes, or learn from signals |
| Portability warning | Feature/schema compatibility and inductive versus transductive learning | Frequency/operator dependence and topology perturbation stability |

The two books imply a useful division of labor:

```text
Hamilton methods                         Ortega methods
----------------                         --------------
construct graph representations          test explicit graph-signal hypotheses
learn typed structural encoders          measure smoothness and spectral location
pool process nodes into sessions          filter a score or feature signal
compare structural hypotheses             localize successful filter response
```

The current three representation candidates from the Hamilton notes remain sensible:

1. `graph_structural_stats_knn`
2. `node2vec_session_knn`
3. `relational_graphsage_session_knn`

Ortega does not require replacing them with three more embedding models. It adds a second layer of experiments:

1. diagnose the graph-signal regime of each representation or score;
2. run a small fixed amplification filter bank;
3. identify which relation, hop, and frequency scale provides the gain.

## Reading map and priority

| Section | Printed pages | PDF pages | Project relevance |
|---|---:|---:|---|
| Chapter 1 | 1–28 | 19–46 | Essential definitions; graph signal, frequency, filter, sampling, and why graph choice is task-dependent |
| Chapter 2.2–2.4 | 33–55 | 51–73 | Highest priority: locality, graph operators, normalized residuals, polynomial \(K\)-hop filters |
| Chapter 2.5 | 56–74 | 74–92 | Selective: invariant subspaces, multiplicities, and practical filter limits |
| Chapter 3.1–3.4 | 75–103 | 93–121 | Highest priority: GFT, Dirichlet variation, frequency response, normalization and irregular graphs |
| Chapter 3.5 | 104–119 | 122–137 | Useful spectral intuition, especially multiplicities and bipartite structure |
| Chapter 4.1 | 120–130 | 138–148 | Highest priority: choose a signal model before choosing a method |
| Chapter 4.2–4.5 | 131–148 | 149–166 | Later-stage active review/label selection; useful normalized-versus-unnormalized comparison |
| Chapter 5.1–5.2 | 149–158 | 167–176 | Highest priority for node-frequency localization and Slepians |
| Chapter 5.3–5.7 | 158–180 | 176–198 | Filterbanks, wavelets, Chebyshev implementation, multiscale analysis |
| Chapter 6 | 181–201 | 199–219 | Highest overall priority: graph approximation, similarity graphs, and graph learning assumptions |
| Chapter 7.1 | 202–205 | 220–223 | Practical application checklist that should become the experiment checklist |
| Chapter 7.2.2 | 206 | 224 | Direct anomaly-detection example: attacks introduce higher graph-frequency content |
| Chapter 7.5 | 224–233 | 242–251 | Label-signal smoothness, active learning, GCN/filter connection, stability |

If reading time is limited, prioritize PDF pp. 69–73, 97–121, 138–148, 167–187, 199–223, and 242–251.

---

# 1. The graph–signal–operator discipline

## 1.1 A graph signal is not an embedding

For \(N\) nodes, a graph signal is a vector

\[
x=[x(1),\ldots,x(N)]^\top\in\mathbb{R}^N,
\]

where \(x(i)\) is one scalar measured at node \(i\). A node-feature matrix \(X\in\mathbb{R}^{N\times F}\) is therefore \(F\) graph signals, one per feature column. An embedding is also multichannel, but its coordinates are learned and may not have an individual semantic interpretation (printed pp. 2–3, 29–31; PDF pp. 20–21, 47–49).

For this project, plausible graph signals include:

| Signal | Node domain | Label-free? | Proper use |
|---|---|---:|---|
| Raw kNN anomaly score \(s_0\) | session | Yes | Main first amplification input |
| Per-feature standardized value | session or process | Yes | Diagnose which telemetry measurements have graph structure |
| Local feature reconstruction error | session or process | Yes | High-pass/anomaly input |
| Rule or detector score | session or process | Usually | Fuse weak existing signals through graph context |
| Anchor impulse \(\delta_a\) | session | Yes after analyst selection | Steering/retrieval propagation |
| Learned embedding coordinate | session or process | Yes if encoder is unsupervised | Spectral audit, with coordinate-rotation caveat |
| Malicious indicator \(y\in\{0,1\}^N\) | session | **No** | Evaluation-only signal diagnostic |
| Method error \(y-\hat y\) | session | No | Post hoc error localization only |

This prevents a common category error. “The graph has signal” is incomplete. The proper statement is:

> The malicious session indicator has unusually low/high/localized variation on graph \(G\) under operator \(Z\), relative to a declared null distribution.

Likewise, “the method amplifies signal” should identify the input signal and transformation:

> The filter \(H(Z)\) improves the ranking induced by the label-free score \(s_0\), with parameters frozen before evaluation.

## 1.2 The graph and operator have different jobs

Let \(A\) be a weighted adjacency matrix and \(D\) its diagonal degree matrix. Common choices include:

| Operator | Formula | Node-domain interpretation | Important bias |
|---|---|---|---|
| Adjacency | \(A\) | weighted neighbor sum | favors high-degree/high-weight neighborhoods |
| Random walk | \(P=D^{-1}A\) | weighted neighbor average | row-normalized propagation |
| Combinatorial Laplacian | \(L=D-A\) | degree-weighted local prediction error | impulse variation grows with degree |
| Random-walk Laplacian | \(T=I-P\) | value minus neighbor average | normalized local residual |
| Symmetric normalized adjacency | \(D^{-1/2}AD^{-1/2}\) | symmetric normalized propagation | orthogonal spectrum for undirected graph |
| Symmetric normalized Laplacian | \(\mathcal{L}=I-D^{-1/2}AD^{-1/2}\) | normalized variation | lowest mode is degree weighted |

The choice is substantive. For a session score \(s\):

- \(Ps\) asks what score the neighborhood predicts for each session;
- \((I-P)s\) asks how much each session disagrees with that prediction;
- \(Ls\) weights that disagreement by degree;
- a polynomial in \(P\) mixes predictions across several hop ranges.

In the current telemetry graph, degree varies radically because some files are ubiquitous, some processes touch many artifacts, and session sizes differ. The first GSP baseline should therefore use a normalized operator, with the combinatorial version retained as a sensitivity analysis rather than the only definition (printed pp. 46–53, 99–103; PDF pp. 64–71, 117–121).

## 1.3 The telemetry relation graph and the GSP similarity graph are distinct hypotheses

The book often assumes that a larger \(w_{ij}\) means greater expected similarity between \(x_i\) and \(x_j\). Under this assumption, the quadratic variation penalizes differences most strongly across high-weight edges (printed pp. 2–3, 79–81, 192–194; PDF pp. 20–21, 97–99, 210–212).

The minimal telemetry graph instead says:

```text
process --parent_child--> process
process ------touches----> file
file --------touched_by--> process
```

Those edges encode event semantics, not necessarily signal similarity. Three defensible GSP constructions follow:

### A. Session similarity graph

Each node is a frozen session. Edges are built from a label-free session representation such as raw statistics, structural statistics, node2vec, or GraphSAGE embeddings. This is the cleanest setting for classical Laplacian GSP and makes the output directly align with the triage unit.

Limitation: if both the graph and initial score come from exactly the same kNN distances, a gain can be a geometric restatement of the raw representation. Compare feature-derived and telemetry-derived graphs.

### B. Process graph, followed by fixed session pooling

Define process-level feature, residual, or detector signals, filter them over a process relation graph, and pool filtered values into the already frozen sessions. This uses the native telemetry relations but requires a clear process-level input signal.

Limitation: file nodes and process nodes carry different kinds of measurements. A scalar signal should not be placed on both types by arbitrary padding without explaining its meaning.

### C. Typed block or relation-specific operators

Use one normalized operator per valid relation and compose them into semantic paths. For example, a session-to-session process/file meta-path can be written schematically as

\[
P_{SP}P_{PF}P_{FP}P_{PS}.
\]

This propagates session information through contained processes and shared files back to sessions. Relation-specific filters are closer to the heterogeneous graph's meaning and offer strong path explanations.

Limitation: this is no longer the book's simplest single symmetric Laplacian setting. Direction, type domains, normalization, and the meaning of each composition must be stated explicitly.

The practical recommendation is to keep two graph families separate in names and tables:

- `telemetry_relation_graph`: event semantics, used for structural/GNN representations and typed path analysis;
- `session_similarity_graph`: expected score/label similarity, used for first-order GSP diagnostics and filters.

## 1.4 Direction and symmetrization are modeling choices

The book permits directed graphs, but undirected symmetric operators have real eigenvalues, orthogonal eigenvectors, and a clean Laplacian variation interpretation. Symmetrizing a parent-child graph removes causal direction and changes the model. Keeping it directed may produce a non-normal or even defective operator, complicating the GFT (printed pp. 76–79, 96–103; PDF pp. 94–97, 114–121).

For a first study:

1. use an undirected nonnegative session similarity graph for the primary GSP experiment;
2. keep edge direction in the native telemetry representation methods;
3. later test separate forward and reverse typed propagation operators rather than silently symmetrizing them;
4. label all symmetrized variants explicitly.

## 1.5 A required experiment manifest

Every GSP result should record:

```yaml
evaluation_unit: session
node_set: frozen session IDs
input_signal: raw_session_stats_knn_score
input_signal_label_free: true
graph_family: session_similarity_graph
graph_source_features: tight_raw_session_stats
edge_rule: mutual_knn
k_graph: 15
edge_weight: local_scale_gaussian
operator: random_walk
self_loops: false
filter_family: truncated_restart_diffusion
filter_order: 3
filter_parameters: frozen_on_dev
normalization: row
sessionizer_version: ...
label_usage: evaluation_and_posthoc_diagnostics_only
```

Without this, two methods called “graph diffusion” can embody different graphs, signals, and assumptions.

---

# 2. Chapters 1–2: locality and explicit graph filters

## 2.1 Locality is the main interpretability advantage

The book defines local graph processing by graph distance rather than Euclidean distance. If \(Z\) is one-hop localized, \(Z^k\) is \(k\)-hop localized. Therefore a degree-\(K\) polynomial filter depends only on nodes within \(K\) hops, unless the graph diameter is so small that \(K\) hops already covers most of the graph (printed pp. 33–37, 53–55; PDF pp. 51–55, 71–73).

That leads to a more precise version of “trace the signal”:

\[
z_i=a_0x_i+a_1(Zx)_i+a_2(Z^2x)_i+\cdots+a_K(Z^Kx)_i.
\]

For session \(i\), report:

- the original contribution \(a_0x_i\);
- total contribution by hop \(a_k(Z^kx)_i\);
- top source nodes \(j\) contributing to each term;
- top relation sequences when \(Z^k\) is replaced by typed operator products;
- positive and negative contributions separately.

This is an algebraic provenance record for the score. It explains which walks carried influence. It does **not** establish that those walks are the actual causal attack chain.

## 2.2 One-hop smooth and residual views

With \(P=D^{-1}A\), the one-hop neighbor average is

\[
m=Px.
\]

The random-walk Laplacian residual is

\[
r=(I-P)x=x-Px.
\]

The book interprets this as a local prediction error: a value close to its neighborhood average has small residual, while a locally discordant value has a large residual (printed pp. 51–53; PDF pp. 69–71).

For cyber triage, retain at least four channels rather than collapsing immediately:

| Channel | Meaning |
|---|---|
| \(x_i\) | original evidence at session \(i\) |
| \((Px)_i\) | neighborhood-supported evidence |
| \(x_i-(Px)_i\) | signed local disagreement |
| \(|x_i-\(Px\)_i|\) or residual energy | magnitude of local surprise |

A suspicious session with suspicious neighbors can have high \(x_i\), high \(Px_i\), and low residual. An isolated suspicious session can have high \(x_i\), low \(Px_i\), and high residual. Both can matter, so a single “smoothed score” discards useful regime information.

## 2.3 Degree is part of the residual interpretation

The book contrasts the random-walk residual with the combinatorial Laplacian:

\[
Lx=D(I-P)x.
\]

Thus two nodes can have the same deviation from their neighborhood average but receive different combinatorial residuals because one has much higher degree (printed pp. 52–53; PDF pp. 70–71). That can be interpreted either as greater confidence from many neighbors or as an unwanted popularity bias.

For this project:

- a high-degree file or process should not automatically be more anomalous;
- a residual supported by many independent, rare relationships may deserve more weight;
- “many neighbors” and “many redundant neighbors” are not the same;
- report raw degree, weighted degree, and effective number of neighbors next to residual scores;
- compare \(I-P\), \(L\), and \(\mathcal{L}\) rather than hiding the choice.

## 2.4 Polynomial filters are the first amplification family to implement

For a one-hop operator \(Z\), the book defines a graph filter as

\[
H(Z)=a_0I+a_1Z+\cdots+a_KZ^K.
\]

The polynomial restriction provides three useful properties (printed pp. 53–55, 89–94; PDF pp. 71–73, 107–112):

1. **Locality:** degree \(K\) bounds the hop range.
2. **Shared rule:** the same coefficients apply everywhere, adapted through local topology.
3. **Spectral interpretation:** if \(Z=U\Lambda U^{-1}\), then the response at graph frequency \(\lambda\) is \(h(\lambda)\).

The smallest useful fixed bank is:

```text
identity:      H0(P) = I
one-hop mean:  HLP(P) = P
residual:      HHP(P) = I - P
two-hop band:  HBP(P) = P - P^2
restart:       HR(P)  = (1-alpha) * sum_{k=0}^K alpha^k P^k
```

These are not claimed to be universally optimal. They test distinct hypotheses:

- identity: no graph benefit;
- neighbor mean: local homophilous support;
- residual: local heterophily or isolated anomaly;
- difference of scales: intermediate-radius structure;
- restart diffusion: multi-hop support while retaining the seed.

Use fixed \(K\in\{1,2,3\}\) and a small predeclared set of \(\alpha\) values on development data. A large hyperparameter search would turn the metric suite into a filter-fitting mechanism.

## 2.5 Locality must be judged relative to graph diameter and mixing

A “three-hop” filter can be nearly global on a dense small-world graph. Ortega explicitly warns that polynomial degree alone does not guarantee meaningful locality; it is relative to radius, diameter, and the operator's minimal polynomial (printed pp. 54, 69–74, 94–95; PDF pp. 72, 87–92, 112–113).

For every graph/filter pair, report:

- median and 90th-percentile \(K\)-hop neighborhood size;
- fraction of nodes reachable within \(K\) hops;
- graph diameter or an approximate effective diameter;
- diffusion concentration or entropy after each hop;
- degree distribution and largest connected component size.

If \(P^3\delta_i\) covers most sessions, the three-hop explanation is not local even though the polynomial order is small.

---

# 3. Chapter 3: frequency, variation, and the signal audit

## 3.1 Graph frequency means variation under a chosen operator

On a regular time axis, sinusoids provide a universal frequency basis. On an arbitrary graph, the basis comes from a graph operator. For an undirected Laplacian \(L=U\Lambda U^\top\), the eigenvectors \(u_k\) are ordered by increasing eigenvalue. Low-eigenvalue vectors vary little across strong edges; high-eigenvalue vectors vary more (printed pp. 75–89; PDF pp. 93–107).

For any signal \(x=U\tilde{x}\),

\[
x^\top Lx=\sum_k \lambda_k\tilde{x}_k^2.
\]

This identity connects three views:

```text
node view:       differences across weighted edges
operator view:   quadratic form x^T L x
frequency view:  energy weighted by graph frequency
```

The word “frequency” is therefore always shorthand for “frequency with respect to this graph and this operator.” A malicious indicator can be low-frequency on one graph and high-frequency on another.

## 3.2 The label-signal audit

Let \(y_i=1\) if session \(i\) is malicious and 0 otherwise. This signal is evaluation-only. For every candidate session graph \(G_m\), compute:

\[
E_m(y)=y^\top L_my.
\]

For binary \(y\), this is the total weight of edges crossing the malicious/benign boundary. Low energy means positives form relatively coherent graph regions; high energy means they are isolated or connected mainly to benign nodes.

Because only 19 of the current 1,457 sessions are malicious, the raw energy is not comparable across graphs with different density or degree. Use several normalized quantities:

\[
R_L(y)=\frac{y^\top Ly}{y^\top y},
\qquad
R_{L,D}(y)=\frac{y^\top Ly}{y^\top Dy},
\]

along with:

- cut weight per malicious node;
- cut weight divided by malicious incident volume;
- within-malicious edge weight divided by its degree-matched expectation;
- spectral energy fractions in predeclared low/mid/high bands;
- a permutation \(z\)-score or empirical \(p\)-value.

Useful nulls include:

1. shuffle the 19 positive labels over all sessions;
2. shuffle within degree bins to control hub placement;
3. shuffle within host or time blocks to control dataset concentration;
4. degree-preserving graph rewire while keeping \(y\) fixed;
5. relation-specific edge shuffles.

The first null asks whether the observed localization exceeds chance. The later nulls ask whether degree, identity, chronology, or relation counts explain it.

## 3.3 The score-signal audit

The deployable signal is not \(y\); it is a label-free score \(s_0\). Measure:

- \(s_0^\top Ls_0\): overall graph variation;
- local residual \(r=(I-P)s_0\);
- low/mid/high spectral energy of \(s_0\);
- correlation between \(s_0\) and \(Ps_0\);
- stability of those measurements across graph perturbations;
- evaluation-only alignment of each component with \(y\).

This separates several possibilities:

| Observation | Interpretation | Candidate response |
|---|---|---|
| \(y\) smooth, \(s_0\) smooth and aligned | graph supports the existing score | modest low-pass/restart diffusion |
| \(y\) smooth, \(s_0\) not aligned | representation has task structure but current score misses it | learn a label-free seed or use anchors; smoothing alone will not create task evidence |
| \(y\) high-frequency, \(s_0\) high-frequency and aligned | positives are local exceptions/boundaries | residual or wavelet energy |
| \(y\) piecewise smooth at several scales | attack pockets with boundaries | multiscale band-pass/wavelet bank |
| \(y\) has no non-null structure | graph does not expose task signal | do not amplify; revisit graph or use non-graph baseline |

The current result—strong malicious-neighbor enrichment but weak anomaly AP—most directly supports the second or fourth row. It says the representation contains local task structure, but it does not show that the raw anomaly score is the right graph signal to diffuse.

## 3.4 Spectral energy profiles

For a symmetric operator with GFT \(U\), compute \(\tilde{x}=U^\top x\). Define frequency bands by normalized eigenvalue intervals rather than eigenvector counts when comparing different graph sizes:

\[
\rho_b(x)=\frac{\sum_{k:\lambda_k\in B_b}\tilde{x}_k^2}{\sum_k\tilde{x}_k^2}.
\]

A practical first partition for \(\mathcal{L}\), whose eigenvalues lie in \([0,2]\), is:

```text
low:   [0.0, 0.5)
mid:   [0.5, 1.2)
high:  [1.2, 2.0]
```

The exact boundaries are hypotheses, not constants of nature. Report a cumulative energy curve as well so conclusions do not depend on one partition.

For cross-dataset work, normalized eigenvalue bands are more meaningful than “first 100 eigenvectors,” but even these bands are graph-dependent. Polynomial response curves and their achieved energy transfer should be reported alongside them.

## 3.5 Irregular graphs require an explicit inner product

Ortega shows that variation and orthogonality can be separated through a generalized eigenproblem

\[
Mu_i=\lambda_iQu_i,
\]

where \(M\) defines variation and \(Q\) defines the inner product or node-volume weighting (printed pp. 101–103; PDF pp. 119–121). With \(M=L\) and \(Q=D\), the fundamental operator is the random-walk Laplacian \(D^{-1}L\), eigenvectors are \(D\)-orthogonal, and every node impulse has normalized variation 1. With \(Q=I\), combinatorial impulse variation equals degree.

This is not a mathematical footnote for telemetry. It answers whether a unit anomaly at a hub should count as intrinsically higher frequency than a unit anomaly at a rare node. The first report should include both:

- `combinatorial_dirichlet_energy`, sensitive to edge volume;
- `degree_normalized_dirichlet_energy`, reducing hub dominance.

If the conclusion changes sign, the apparent signal is degree-dependent and should be described that way.

## 3.6 Multiplicity and basis instability

Repeated or very close eigenvalues imply that individual eigenvectors may be non-unique or unstable even when their invariant subspace is stable. A graph perturbation can rotate basis vectors inside a repeated eigenspace or swap the order of nearby frequencies (printed pp. 58–74, 91–92, 183–187; PDF pp. 76–92, 109–110, 201–205).

Consequences for the project:

- do not explain an outcome by a single eigenvector when its eigenvalue is repeated or tightly clustered;
- aggregate energy over frequency bands or invariant subspaces;
- align subspaces, not columns, across graph perturbations;
- prefer polynomial filters when cross-graph comparison is the goal;
- report eigengaps around any selected spectral cutoff.

## 3.7 Powers of an operator explain walk propagation, not causality

For unweighted adjacency, \((A^k)_{ij}\) counts length-\(k\) walks between \(i\) and \(j\); weighted operators accumulate products of edge weights along such walks (printed pp. 94–95; PDF pp. 112–113). Thus a filtered score can be decomposed into walk contributions.

However:

- a walk can revisit nodes and is not necessarily a simple path;
- a large contribution can arise from many redundant walks through a hub;
- symmetrization destroys original direction;
- shared-file connectivity is associative evidence, not proof of execution flow;
- normalization changes each path's weight.

The correct output label is therefore `supporting influence paths` or `high-contribution meta-paths`, not `causal attack path`, unless a separate temporal/provenance validation establishes causality.

---

# 4. Chapter 4: select a signal model before a filter

## 4.1 Signal models are falsifiable assumptions

Ortega begins the sampling chapter by making the modeling dependency explicit: one cannot reconstruct an arbitrary \(N\)-dimensional graph signal from fewer than \(N\) samples. Recovery is possible only after restricting the expected class of signals. The graph, graph operator, frequency definition, and signal model jointly determine the method and its guarantees (printed pp. 120–121; PDF pp. 138–139).

The same principle applies to amplification. A filter can only increase a chosen component; it cannot determine on its own whether that component is malicious. The project should test the following regimes:

| Signal regime | Mathematical symptom | Cyber interpretation | First matching tool |
|---|---|---|---|
| Low-frequency/bandlimited | energy concentrated in low \(\lambda\) | connected sessions share task state | low-pass/restart diffusion |
| Approximately low-frequency | low-frequency majority plus residual | campaign coherence with exceptions | low-pass plus residual channels |
| Piecewise constant/smooth | small boundary relative to internal volume | one or more campaign pockets | graph total variation, wavelets, Slepians |
| Local high-frequency | large local residual in small region | isolated event or sharp behavior change | \(I-P\), high-pass wavelet energy |
| Multiscale | energy in several localized bands | attack spans process, session, and campaign scales | spectral graph wavelet bank |
| Stationary background plus departures | stable local response distribution with outliers | repeated normal behavior and anomalous deviations | standardized multiscale residual |
| No non-null graph organization | diagnostics resemble shuffles/rewires | chosen graph does not express task signal | do not amplify this graph |

The regime may vary by relation. A score can be smooth along shared rare-file edges but high-frequency along parent-child edges. Aggregate-only analysis can cancel that information.

## 4.2 Exact bandlimitedness is a useful idealization, not a default cyber claim

For GFT basis \(U\), an \(R\)-bandlimited signal is

\[
x=U_Ra,
\]

where \(U_R\) contains a known set of \(R\) frequency vectors, usually the first \(R\) low-frequency vectors (printed pp. 121–122; PDF pp. 139–140). If the support is known, high-pass, band-pass, or nonconsecutive \(R\)-sparse spectral models can be handled similarly.

For a task indicator \(y\), cumulative low-frequency mass is

\[
C_y(R)=\frac{\sum_{k=1}^{R}(u_k^\top y)^2}{\|y\|_2^2}.
\]

This is a useful evaluation diagnostic. But the malicious indicator is binary, rare, and unlikely to be exactly bandlimited. Exact recovery language should not be used unless the high-frequency coefficients are actually zero within numerical tolerance and the cutoff was not chosen using holdout labels.

Better language is:

> The centered malicious indicator has more energy in the low normalized-Laplacian bands than label-count- and degree-matched permutations.

That is a measured relative statement, not a universal smoothness claim.

## 4.3 Approximate bandlimitedness fits campaign structure better

The book allows

\[
x=U_Ra+n
\]

and softer priors such as small \(x^\top Lx\), where high frequencies are penalized but not forced to zero (printed pp. 122–123; PDF pp. 140–141). A general reconstruction can penalize \(\|W x\|\), where \(W\) is a chosen high-pass graph filter.

This gives a practical decomposition:

\[
x=x_{\mathrm{low}}+x_{\mathrm{resid}}.
\]

Both outputs should be evaluated. If malicious sessions form a coherent pocket with unusual boundary processes, the low component can expose the pocket while the residual exposes its boundary. Declaring one of them “noise” in advance would impose the answer.

## 4.4 Piecewise smoothness is probably the most plausible first task model

With signed incidence matrix \(B\), the vector \(B^\top x\) contains signal differences across edges. A piecewise constant signal has relatively few nonzero edge differences:

\[
\|B^\top x\|_0\ \text{is small relative to the graph's edge volume}.
\]

Ortega emphasizes that the meaningful condition is not merely a set of equal-valued nodes. The set must have substantially more internal connectivity than boundary connectivity (printed pp. 123–125; PDF pp. 141–143).

For a binary malicious indicator:

- internal malicious edges contribute zero variation;
- malicious-to-benign boundary edges contribute their weight;
- disconnected malicious pockets can still be piecewise constant;
- a high-degree malicious node can have a large raw boundary even if it has meaningful internal support.

Report:

\[
\frac{\|B^\top y\|_0}{|E|},
\qquad
\|B^\top y\|_1,
\qquad
y^\top Ly,
\]

plus conductance and null comparisons. For continuous score \(s_0\), use edge-difference distributions and relation-specific total variation.

## 4.5 Statistical smoothness models can yield a label-free residual

The book connects a Gaussian graph model with likelihood proportional to a decreasing function of \(x^\top Lx\): smoother signals are assigned higher likelihood (printed pp. 125–127; PDF pp. 143–145). This suggests a label-free strategy:

1. fit an expected graph-context model using allowed development or historical data;
2. predict each node signal from its graph neighborhood;
3. standardize residuals by node/relation/degree context;
4. rank large residuals while retaining their supporting edges.

The one-hop form is simply \(r=(I-P)x\). A more complete model can use several feature signals and estimate a residual covariance.

Cyber caveats are substantial:

- count data are often heavy-tailed and zero-inflated;
- roles and host classes create legitimate multimodality;
- attacks can contaminate the background fit;
- low likelihood means model mismatch, not maliciousness;
- a singular Laplacian needs constraints or regularization in a probabilistic model.

This makes the statistical model a useful anomaly baseline, not a semantic maliciousness detector.

## 4.6 Stationarity offers a later normal-background model

Graph stationarity is more complicated than temporal stationarity because applying \(Z\) mixes neighboring values rather than translating a signal to another observation location. The book surveys definitions based on covariance alignment with the graph basis and on local filter measurements that remain similar across nodes (printed pp. 127–131; PDF pp. 145–149).

The localized multiscale view is particularly useful. Let

\[
q(i,s)=\langle x,p_{i,s}\rangle
\]

be the response of a filter kernel centered at node \(i\) and scale \(s\). A label-free anomaly score can compare the response profile \(q(i,:)\) with a reference distribution:

\[
a_i=\left\|\Sigma_q^{-1/2}(q(i,:)-\mu_q)\right\|_2.
\]

This asks whether a node's behavior across graph scales is unusual, rather than assuming the malicious signal itself is globally smooth.

It requires repeated observations—time windows, feature channels, or multiple comparable graphs—to estimate \(\mu_q\) and \(\Sigma_q\) reliably. The current single dev slice should not be used to make strong stationarity claims without such an ensemble.

## 4.7 A signal-model selection protocol

Use development data only, and separate label-free fit from label-aware diagnosis:

```text
1. Build graph/operator without labels.
2. Build input score/features without labels.
3. Measure score smoothness, residuals, and spectral profile.
4. After representation is frozen, inspect label-signal profile.
5. Compare both profiles to shuffles and graph nulls.
6. Choose a small filter family on development data.
7. Freeze graph rules, bands, order, and parameters.
8. Evaluate once on holdout.
```

If development labels choose the regime or filter, the resulting procedure is development-supervised even when the filter itself never consumes labels at inference. That can be scientifically valid, but it should not be called fully unsupervised per dataset.

---

# 5. Chapter 4: sampling is not the same as triage

## 5.1 The objective distinction

Graph sampling observes values at a subset of nodes and estimates unobserved values elsewhere. Anomaly triage ranks nodes to find rare positives early. The optimal sets differ:

```text
sampling objective:  cover the assumed signal space for reconstruction
triage objective:    maximize discoveries under a review budget
```

A low-degree isolated node may be essential for reconstructing a low-frequency signal because no neighbor predicts it. That does not mean it is likely malicious. Conversely, ten similar high-risk sessions may be redundant for reconstruction but all valuable discoveries.

Sampling belongs in this project primarily when:

- choosing sessions for an analyst to label;
- constructing a diverse review batch from high-scoring candidates;
- reconstructing a smooth risk/label signal from a few confirmed examples;
- selecting representative nodes for an expensive explanation procedure.

## 5.2 Reconstruction assumptions and active labels

For a model subspace \(\mathcal{V}\), a sampling set is valid only if no nonzero signal in \(\mathcal{V}\) is invisible on the sampled nodes. For an \(R\)-bandlimited model, the restricted GFT matrix must have full column rank and at least \(R\) samples are needed (printed pp. 132–136; PDF pp. 150–154).

Translated to analyst steering:

1. construct a label-free similarity graph;
2. select a review set \(S\) under a declared signal model;
3. obtain real analyst labels on \(S\);
4. interpolate or propagate those observed labels;
5. evaluate only on unreviewed nodes.

This is an active/semi-supervised method. The seed or reviewed labels must be excluded from retrieval metrics.

## 5.3 Robust sampling criteria select coverage, not suspiciousness

The book presents A-, E-, and D-optimal criteria based on the restricted basis matrix (printed pp. 139–140; PDF pp. 157–158):

- A-optimality reduces average reconstruction variance;
- E-optimality improves the worst observed direction;
- D-optimality maximizes information volume.

For triage, a useful hybrid is:

\[
\text{selection utility}(i)
=
\beta\,\text{suspiciousness}(i)
+
(1-\beta)\,\text{marginal coverage}(i\mid S).
\]

Keep the two terms in the output table. Otherwise a method can appear to rank threats when it is really selecting topological coverage.

## 5.4 Localized kernels give a principled diversity measure

If \(d_i=g(L)\delta_i\) is a localized interpolation kernel around node \(i\), useful sample nodes have substantial kernel norm and low overlap with already selected kernels (printed pp. 143–145; PDF pp. 161–163).

A practical review wrapper is:

```text
candidate pool = top M by frozen anomaly score
repeat until budget B:
    choose candidate with high score
    penalize overlap between its localized kernel and selected kernels
```

Evaluate:

- discoveries at budget;
- unique campaigns/hosts represented;
- mean review cost;
- reconstruction error, if reconstruction is actually a goal;
- comparison with pure score ranking and random diversified selection.

## 5.5 Operator choice changes the selected nodes

Ortega shows that combinatorial-Laplacian sampling tends to prioritize low-degree nodes and sparse clusters, whereas normalized-Laplacian sampling spreads choices more evenly across density regimes (printed pp. 145–147; PDF pp. 163–165).

For cyber review, this means a graph sampling method can masquerade as a rarity detector. Always compare:

- combinatorial versus normalized operator;
- degree-only selection;
- random selection;
- selection after degree-preserving rewire;
- review recall and reconstruction error separately.

---

# 6. Chapter 5: node-frequency localization

## 6.1 “Where is the signal?” has two coordinates

The book distinguishes node-domain localization—energy concentrated near a subset of connected nodes—from frequency localization—energy concentrated in part of the graph spectrum (printed pp. 149–153; PDF pp. 167–171).

For reference node \(a\), node spread can be measured as

\[
\Delta^2_{G,a}(x)
=
\sum_i d(a,i)^2\frac{x_i^2}{\|x\|_2^2}.
\]

For a Laplacian and zero-frequency reference, frequency spread is the normalized Dirichlet energy:

\[
\Delta_S^2(x)=\frac{x^\top Lx}{\|x\|_2^2}.
\]

Together they give a useful empirical taxonomy:

| Node spread | Frequency spread | Likely interpretation |
|---|---|---|
| Small | Small | localized, internally coherent pocket |
| Small | Large | isolated spike or sharp local boundary |
| Large | Small | broad coherent mode, common behavior, or campaign spanning the graph |
| Large | Large | fragmented, noisy, or genuinely multiscale activity |

For multiple attack pockets, a single center is inappropriate. Compute spread per detected region or use a mixture of centers.

## 6.2 Graph localization can violate ordinary Fourier intuition

Graph signals can sometimes have compact support in both a node subset and a frequency subset. Graph eigenvectors themselves can be spatially localized (printed pp. 154–155; PDF pp. 172–173). Therefore:

- a localized campaign is not necessarily spectrally broad;
- a low-frequency component is not necessarily global;
- an unusual localized eigenmode can arise from graph topology alone;
- node and frequency localization should both be reported.

This is why a two-dimensional `node_region × graph_scale` atlas is more informative than a single embedding plot.

## 6.3 Graph Slepians test whether a candidate region contains smooth signal

Given node subset \(S\) and low-frequency basis \(U_F\), define the concentration matrix

\[
C_S=U_F^\top I_SU_F.
\]

Its eigenvectors generate bandlimited graph signals ordered by concentration in \(S\). Concentration eigenvalues near one indicate that a low-frequency signal can live mostly inside that region (printed p. 155; PDF p. 173).

Project workflow:

1. propose \(S\) without holdout labels—from a top-score ego graph, community, or typed path bundle;
2. freeze the frequency range from development rules;
3. compute top Slepian concentration values;
4. project the label-free input score into the localized basis;
5. report concentration, projection energy, and dominant nodes;
6. mask the claimed relations/nodes and recompute.

Slepians are a strong second-stage localizer, not a first detector. They require a candidate region, and scanning many regions creates selection and multiple-testing problems.

## 6.4 Structured dictionaries provide explanation atoms

A graph dictionary \(V\in\mathbb{R}^{N\times M}\) represents \(x=Vc\). An overcomplete dictionary can include atoms centered at many nodes and scales; a sparse coefficient vector can summarize a signal with a few atoms (printed pp. 155–158; PDF pp. 173–176).

This yields a natural explanation format:

> The unusual part of this score is represented mainly by a two-hop mid-band atom centered on session 417 and a one-hop high-pass atom centered on session 982.

But sparse atoms can be correlated and the coefficient solution can be non-unique. Explanation stability under small graph perturbations and alternative dictionaries is required.

---

# 7. Chapter 5: wavelets and multiscale signal localization

## 7.1 The simplest low/high two-channel representation

The book's one-hop construction combines a neighborhood-agreement channel and a prediction-residual channel using a normalized one-hop operator (printed pp. 158–160; PDF pp. 176–178). For project notation, let \(P=D^{-1}A\):

\[
x_{\mathrm{agree}}=(I+P)x,
\qquad
x_{\mathrm{resid}}=(I-P)x.
\]

The scaling of \(I+P\) can be normalized if needed. The important experimental idea is to retain both agreement and disagreement instead of assuming homophily.

For feature matrix \(X\), compute row summaries:

- \(\|(I+P)X\|_{2,\mathrm{row}}\);
- \(\|(I-P)X\|_{2,\mathrm{row}}\);
- low/high energy ratio;
- maximum feature residual;
- relation-specific residual norms;
- session-pooled quantiles and maxima.

This is the highest-value first GSP representation to implement because it is cheap, transparent, and tests two regimes simultaneously.

## 7.2 Node-domain hop-ring wavelets

Node-domain graph wavelets assign weights to exact hop rings around a center and choose coefficients whose weighted sum annihilates the constant signal (printed pp. 160–162; PDF pp. 178–180). They provide intuitive profiles such as:

```text
center value
one-hop mean difference
two-hop ring difference
three-hop ring difference
```

They are low complexity but are developed for unweighted graphs and lack a clean polynomial/spectral interpretation. In the typed telemetry graph, untyped hop rings also mix incompatible relations. Typed meta-path rings would be a project extension.

## 7.3 Spectral graph wavelets are the strongest general localization tool in the book

Spectral graph wavelet transforms use a low-pass scaling function \(h(\lambda)\) and scaled band-pass filters \(g(t_j\lambda)\). Applying every filter produces a node-by-scale coefficient map (printed pp. 165–167; PDF pp. 183–185):

\[
c_{i,j}=\left[g(t_jL)x\right]_i.
\]

This directly addresses the project's desired output:

- which nodes carry unusual energy;
- at what graph scale;
- in which frequency band;
- under which relation/operator view;
- with which source features or seed signals.

A possible label-free score is a standardized maximum or aggregate band response:

\[
a_i=\max_j\frac{|c_{i,j}|-\mu_{i,j}}{\sigma_{i,j}+\epsilon},
\]

where the reference statistics are fit without evaluation labels. Simpler first experiments can use band-energy row norms and compare their rankings directly.

Frame bounds matter: the combined filter responses should cover the spectrum without common zeros. A tight or near-tight frame makes coefficient-energy attribution more stable (printed pp. 166–167; PDF pp. 184–185).

## 7.4 Chebyshev polynomials make spectral filters local and scalable

Filters designed as functions of \(\lambda\) can be approximated by Chebyshev polynomials and evaluated recursively without computing all eigenvectors (printed pp. 167–169; PDF pp. 185–187). A degree-\(K\) approximation:

- uses sparse matrix-vector multiplication;
- is \(K\)-hop localized;
- provides a clear explanation support bound;
- transfers procedurally across graph sizes;
- introduces approximation error that must be measured.

Increasing \(K\) improves frequency-response approximation but reduces locality. This is an explicit selectivity–explanation trade-off, not merely a performance hyperparameter.

Graph eigenvalues are discrete and uneven. A continuous band may contain few or no actual eigenvalues. Inspect spectral density on development graphs or use spectrum-adaptive bands, then freeze the design rule rather than tuning bands on test labels.

## 7.5 Diffusion wavelets provide an adaptive hierarchy

Diffusion wavelets form nested approximation spaces from successive powers of a diffusion operator. Nonprincipal modes decay, so increasingly coarse spaces can represent the remaining signal with lower numerical rank; detail spaces capture what is lost at each scale (printed pp. 178–180; PDF pp. 196–198).

They are useful when the goal is a graph-adaptive global multiscale basis:

- fine details: highly local deviations;
- intermediate details: campaign or infrastructure neighborhoods;
- coarse modes: broad graph behavior.

Limitations include slow mixing, disconnected components, bipartite \(-1\) modes, hub smearing, topology-specific bases, and limited direct support for directed heterogeneous relations. Use them after a fixed SGWT/filter-bank baseline shows that multiscale structure is useful.

## 7.6 Techniques to defer

The book also covers lifting, subgraph filterbanks, critically sampled bipartite filterbanks, and pyramid transforms. They are important for exact reconstruction, compression, or multiresolution processing, but they add graph partitioning, bipartite approximation, downsampling, reconnection, and sometimes synthetic edges (printed pp. 162–178; PDF pp. 180–196).

For the present project, defer them unless the research question becomes graph compression or active sampling. Overcomplete wavelet coefficients are acceptable because interpretation matters more than minimizing coefficient count.

---

# 8. Chapter 6: how to choose a graph

## 8.1 This is the highest-priority chapter for the project

Ortega divides graph selection into three cases (printed pp. 181–182; PDF pp. 199–200):

1. **Graph approximation:** a graph exists, but it is sparsified, simplified, reduced, or forced into a desired topology.
2. **Graph construction from node attributes:** nodes have features or positions, and similarity determines edges.
3. **Graph learning from signal examples:** repeated signals over a fixed node set are used to infer a graph that matches their behavior.

These cases correspond to different evidence and should be separate experiment families:

| Graph family | Evidence used | Project example | What it can support |
|---|---|---|---|
| Observed relation graph | telemetry records | parent-child, process-file | claims about recorded relational structure |
| Approximated relation graph | observed graph plus declared simplification | rare-file filtering, symmetrization | claims conditional on retained topology |
| Attribute similarity graph | label-free node/session representation | raw-stat session kNN | claims about representation geometry |
| Learned signal graph | repeated node-aligned observations | stable entities across time windows | statistical dependency/smoothness model |

A session similarity graph built from raw features is not independent graph evidence that the provenance graph contains signal. It is a graph form of the raw geometry. Likewise, a kNN graph built from GraphSAGE embeddings diagnoses the learned representation; it does not by itself prove which original relation caused the geometry.

## 8.2 There is no uniquely “right” graph

The chapter explicitly frames graph selection as a modeling problem. Desired spectral spacing, sparsity, topology, computational cost, data fit, and interpretability can conflict. The book's premise is that there may be no single correct underlying graph to recover (printed pp. 181–182, 200–201; PDF pp. 199–200, 218–219).

This suggests comparing graph hypotheses rather than searching for one graph that wins after repeated label inspection:

```text
G_parent       parent-child evidence only
G_file         inverse-degree shared-file evidence only
G_combined     predeclared weighted combination
G_raw_knn      raw session-feature similarity
G_struct_knn   structural-stat similarity
G_embed_knn    learned representation similarity
G_null         relation/degree-matched controls
```

For every result, name the graph view and operator. “The graph signal is smooth” is not meaningful without both.

## 8.3 Sparsification changes signal and locality

Sparsification reduces edges while attempting to preserve selected graph properties. It lowers the cost of multiplying by \(Z\), increases geodesic distances, and makes a fixed polynomial order more local. But it also changes the spectrum and can destroy bridges or components (printed pp. 183–187; PDF pp. 201–205).

The project's rare-file filter is therefore a graph hypothesis, not neutral cleaning. A threshold can:

- remove ubiquitous artifacts that create hubs;
- remove singleton artifacts that may be highly informative;
- disconnect most process nodes;
- change the graph diameter and frequency basis;
- select which attack paths can exist at all.

Required `graph_sparsification_audit` fields:

| Field | Why it matters |
|---|---|
| nodes/edges before and after | magnitude of alteration |
| retained fraction per relation | relation-specific loss |
| exact isolate count | representation coverage |
| component count and largest fraction | whether filtering is fragmented |
| degree and weighted-degree quantiles | hub/leaf behavior |
| removed incident weight by node quantiles | concentrated damage |
| approximate \(\lambda_2\) and low eigenspace | connectivity and low-frequency change |
| \(K\)-hop coverage | true filter locality |

Run a small predeclared sensitivity set:

- current file-degree interval `[2, 15]`;
- include singleton files;
- increase the maximum file degree;
- no file filter on a manageable sample;
- matched random edge removal;
- 5% and 10% relation-preserving edge dropout.

Evaluate representation and explanation stability as well as triage metrics. Choosing thresholds by malicious-neighbor purity and then calling them unsupervised would be label-based model selection.

## 8.4 Edge removal should preserve more than weight rank

Removing the smallest weights is intuitive, but a weak bridge with no alternate route can be structurally crucial. The book describes spectral sparsification using edge weight times effective resistance, which favors indispensable connections and downweights edges with strong alternative paths (printed pp. 185–187; PDF pp. 203–205).

This is a useful later control for projected similarity graphs. It is probably unnecessary for the first sparse native telemetry graph, where the immediate question is whether enough connectivity exists at all.

The book also shows why individual eigenvectors can be unstable after small perturbations when eigengaps are small. Compare low-frequency subspaces using principal angles and compare filter outputs, rather than matching eigenvector columns by index.

## 8.5 Projection and reduction can manufacture connectivity

Kron reduction removes nodes and reconnects their neighbors; removing one intermediate node can connect all of its former neighbors, and repeated reduction tends to densify the graph (printed pp. 190–192; PDF pp. 208–210). A process-file-process or session projection has a related clique-forming effect: every process/session sharing a common artifact becomes connected.

For a session-file incidence matrix \(B_{SF}\), a simple weighted projection is

\[
W_{\mathrm{file}}=B_{SF}D_F^{-1}B_{SF}^\top,
\]

with the diagonal removed and optional session-size normalization. The inverse file degree prevents ubiquitous files from contributing quadratically many full-strength session edges.

Report:

- which intermediate node types were projected away;
- how projected weights are normalized;
- how many cliques/hubs the projection creates;
- whether the projection is subsequently sparsified;
- whether top explanations can be mapped back to original process/file evidence.

Session mean pooling is a readout over process embeddings; it is not a topology-preserving reduction of the process graph.

## 8.6 Constructing a session similarity graph

Given node attributes \(v_i\), the book presents Gaussian weights

\[
w_{ij}=\exp\left(-\frac{\|v_i-v_j\|^2}{2\sigma^2}\right)
\]

and cosine similarity. These normally create dense graphs, so kNN or another sparsification is needed (printed pp. 192–194; PDF pp. 210–212).

A suitable first constructor is:

```python
build_session_similarity_graph(
    X,
    k=15,
    symmetrization="union",       # compare mutual as sensitivity
    weighting="unweighted",      # Gaussian as sensitivity
    sigma_rule="median_knn_distance",
)
```

Reliability diagnostics:

- nearest- and kth-neighbor distance quantiles;
- distance concentration ratio;
- in-neighbor hubness—how often a session appears in other lists;
- union versus mutual kNN component structure;
- neighbor-set Jaccard under feature bootstrap or small noise;
- graph stability for \(k\in\{10,15,30\}\), with 15 primary;
- isolate and component counts;
- sensitivity to removing absolute time and identity proxies.

High-dimensional distances can become nearly indistinguishable. A graph built in such a space may encode hubness and noise more than meaningful similarity, even if the kNN routine returns neighbors for every point.

## 8.7 Learning a graph from signals requires repeated, node-aligned observations

The graph-learning section assumes a fixed set of \(N\) nodes and \(M\) repeated graph signals over those same nodes (printed pp. 194–201; PDF pp. 212–219). Methods include covariance/precision estimation, local regression, optimization for signal smoothness, and frequency-domain methods based on a stationarity assumption.

Current ephemeral process or session nodes do not naturally satisfy this setup. Treating feature columns as \(M\) repeated signals over 1,457 sessions yields very few observations relative to the potential edge parameters and an awkward interpretation.

A more faithful later design is:

```text
stable nodes:       process names, file tokens, hosts, or another schema-stable entity
signal observation: count/rate/score vector for one time window
M observations:     many comparable windows
learned edge:       conditional association or smoothness relation across windows
```

Before attempting it, produce:

| Candidate | \(N\) nodes | \(M\) observations | \(M/N\) | Stationarity evidence | Meaning of learned edge |
|---|---:|---:|---:|---|---|

## 8.8 Graph-learning circularity and leakage

Smoothness-based graph learning explicitly selects \(L\) so observed signals have small \(x^\top Lx\). Showing that those training signals are smooth on the result is not independent validation. Similarly, a precision graph encodes conditional dependence under its statistical model, not causality (printed pp. 195–201; PDF pp. 213–219).

Rules for this project:

- never use evaluation labels as graph-learning signals;
- fit the graph only on the allowed development/training period;
- freeze graph-learning objectives and regularization before holdout;
- evaluate learned graphs against attribute graphs, provenance graphs, and null graphs;
- test contamination sensitivity if attacks may appear in graph-fitting data;
- do not interpret a learned edge as an attack path;
- do not validate a learned graph solely with the same smoothness objective it optimized.

Graph learning is a later contribution. It should not precede a clear result on fixed, interpretable graph hypotheses.

---

# 9. The current notebook through Ortega's lens

The saved state of `Notebooks/Graph Triage Baseline v0.ipynb` makes graph construction the immediate gate before representation learning.

## 9.1 Saved topology summary

The notebook currently reports:

| Quantity | Saved value |
|---|---:|
| Process nodes | 100,000 |
| Retained file nodes | 14 |
| Parent-child edges | 2,318 |
| Process-file `touches` edges | 66 |
| Reverse `touched_by` edges | 66 |
| Homogeneous edge entries | 2,450 |
| Homogeneous total nodes | 100,014 |
| Graph-builder sessions | 3,131 |
| Raw-baseline sessions | 1,457 |

There are 2,384 distinct semantic edges before counting the explicit reverse of `touches`. Even under the most generous assumption that all endpoints are distinct, at most \(2(2318)+66+14=4,716\) nodes can be incident to an edge. Therefore **at least 95,298 of the 100,014 nodes must be isolated under the saved edge counts**; the exact isolate count may be larger because endpoints overlap. The notebook should compute it directly.

This means a node2vec or GraphSAGE loss on the saved graph would be ambiguous. It could show that the method fails, or simply that nearly all evaluation processes have no usable relational context.

## 9.2 Current graph choices that need explicit treatment

| Current choice | Ortega interpretation | Required action |
|---|---|---|
| `RARE_FILE_MIN_DEGREE=2`, `MAX=15` | severe topology/sparsification hypothesis | audit connectivity and run frozen sensitivities |
| Forward parent edges only | directed flow view | decide whether walkers need explicit reverse-parent relation |
| File edges in both directions | traversable bipartite relation | distinguish semantic reverse from duplicate evidence |
| `to_homogeneous()` | relation/type collapse | use only as declared topology-only control |
| Empty process `FEATURE_COLS` | no process attribute signal | acceptable for node2vec; not a complete GraphSAGE feature design |
| File feature of constant one | type/constant indicator after padding | state what homogeneous feature matrix actually encodes |
| 3,131 graph sessions vs 1,457 raw sessions | evaluation-unit mismatch | freeze one canonical session mapping first |
| Manifest comment about connected-component sessions | stale description | update when notebook implementation work resumes |

The full graph is not bipartite because it includes process-process parent edges. Only the process-file subgraph is bipartite.

## 9.3 Canonical sessions are the first repair

The raw sessionizer groups by user, falling back to host when the user is missing. The graph builder groups by `(host, user-or-host-activity)`. That changes the review unit, label prevalence, and pooling operation. No representation comparison is valid until every method maps to the same frozen session IDs.

The graph should be allowed to use relations crossing sessions if that is part of its hypothesis, but its final embedding/score must be pooled and evaluated on the identical canonical session table.

## 9.4 Add a graph/operator audit before node2vec

Minimum new outputs before graph training:

```text
exact isolated process/file counts
component count and size distribution
fraction of canonical sessions with any incident graph edge
fraction with parent evidence
fraction with file evidence
relation-specific degree quantiles
1/2/3-hop coverage
walkable fraction under the chosen directed semantics
projected session-graph density and hubness
```

Gate:

> Do not interpret a learned-method result until graph coverage of the canonical session evaluation set is known.

## 9.5 The raw result is already a strong GSP diagnostic opportunity

The raw session representation has:

- 1,457 sessions;
- 19 malicious sessions;
- top-15 malicious-neighbor purity about 0.207;
- approximately 16.75× enrichment over the random class rate;
- 84.2% of malicious sessions with at least one malicious top-15 neighbor;
- weak raw anomaly ranking.

This is almost tailor-made for the first session-level GSP audit:

1. build the explicit \(k=15\) session similarity graph without labels;
2. compute topology reliability and hubness;
3. treat the malicious indicator as an evaluation-only graph signal;
4. compute normalized Dirichlet energy, conductance, and spectral energy;
5. compare label shuffle and degree-matched nulls;
6. treat the raw anomaly score as the deployable signal;
7. compare \(s_0\), \(Ps_0\), \((I-P)s_0\), and restart diffusion;
8. freeze any chosen filter before holdout.

This does not change the existing raw baseline. It explains precisely what kind of graph organization its representation contains and whether the deployable score shares that organization.

---

# 10. Chapter 7: the application checklist and machine-learning bridge

## 10.1 Ortega's application checklist should become a required method card

The book recommends knowing the graph, examining whether observed signals occupy expected frequencies, relating polynomial degree to graph size/diameter, inspecting intermediate operations, and selecting interpretable graph-learning solutions rather than judging only end-to-end performance (printed pp. 204–205; PDF pp. 222–223).

Every project method should answer:

```text
What are the nodes and the evaluation unit?
What does each edge and weight mean?
Is the edge observed, projected, similarity-derived, or learned?
Is direction preserved?
What was sparsified or symmetrized?
Which operator and inner product are used?
What scalar or multichannel graph signal is processed?
Why should that signal agree, disagree, or diffuse across these edges?
What is the filter order and effective coverage?
Which quantities were fit without labels?
Where do labels first enter?
Which null graph or signal should reproduce a spurious result?
How is a reported support path tested for faithfulness?
```

This checklist is the best route to dataset portability: standardize the questions and procedure without pretending the graph semantics are universal.

## 10.2 The book includes a direct anomaly example—but it is conditional

In an electric-grid example, normal voltage measurements are smooth on a physically meaningful network and malicious measurement injection raises high-frequency energy (printed p. 206; PDF p. 224). This supports high-pass anomaly detection when:

- the graph is physically grounded;
- the normal signal is known to be smooth;
- the attack disrupts that smoothness;
- the measurement scale is common across nodes.

It does not prove that cyber process/file labels are high frequency. The correct transfer is the procedure:

1. justify a normal signal model;
2. measure frequency content;
3. test whether attacks depart from it;
4. use high-pass energy only if the evidence supports it.

## 10.3 Label-signal smoothness measures representation difficulty

For a similarity graph and class indicator \(y_c\), the book shows

\[
y_c^\top Ly_c
=
\sum_{i\sim j}w_{ij}(y_{c,i}-y_{c,j})^2.
\]

This is the total weight connecting class \(c\) to other classes. Small variation and high low-frequency mass indicate a representation in which the class is easier to separate using graph-local information (printed pp. 224–227; PDF pp. 242–245).

For the rare malicious class, use the centered signal \(z=y-\bar y\) and normalize:

\[
E_{\mathrm{norm}}(y)=\frac{z^\top Lz}{z^\top Dz}.
\]

Report label-count shuffle and degree-preserving graph-rewire distributions. This remains a label-aware representation diagnostic, not an unsupervised score.

## 10.4 Layerwise smoothness can operationalize “amplification” in a GNN

Build a session similarity graph from each frozen representation stage:

```text
h0: input features
h1: first message-passing layer
h2: second message-passing layer
pooled: canonical session embedding
```

At each stage report:

- normalized label energy;
- cumulative low-frequency label mass;
- malicious-neighbor purity;
- peer rank and fragmentation;
- anomaly-ranking metrics;
- embedding variance and mean cosine similarity;
- neighbor-set stability.

Interpretation:

- falling label energy with improved retrieval suggests useful task organization;
- falling label energy with collapsed embedding variance suggests over-smoothing;
- improved neighbor purity without anomaly AP suggests a steering/retrieval representation rather than a standalone outlier score;
- no change beyond rewired controls suggests generic smoothing or degree effects.

## 10.5 Active learning is the proper home for sampling

The book maps sampling to active semi-supervised learning: select nodes, obtain labels, and propagate/interpolate labels over a similarity graph (printed pp. 229–230; PDF pp. 247–248). This provides a principled future phase for the current strong neighbor-purity result:

```text
confirmed anchor(s)
-> graph sampling/diverse review selection
-> observed labels
-> label propagation
-> evaluate on unreviewed malicious sessions
```

Keep this separate from fully label-free discovery. An analyst-confirmed anchor changes the supervision regime and should be presented as steering or few-shot retrieval.

## 10.6 Graph convolutions are learned polynomial filters

The GCN discussion links graph convolutions to local polynomial filters. A degree-\(K\) polynomial is a \(K\)-hop template whose coefficients are shared across nodes, and Chebyshev filters avoid computing the full GFT (printed pp. 230–232; PDF pp. 248–250).

This connects directly to Hamilton:

- GNN depth is a hop-scale experiment;
- fixed \(P\), \(P^2\), and \(I-P\) are essential deterministic controls;
- retaining intermediate layers supports a scale curve;
- relation-specific message passing corresponds to multiple operators;
- canonical session pooling is a readout, not evidence of topology preservation.

## 10.7 Stability trades off against frequency selectivity

Ortega closes with a central transfer warning: small topology changes move graph frequencies. A sharp filter response can therefore change substantially between related graphs, while a flatter response is more stable but less selective (printed pp. 232–233; PDF pp. 250–251).

For each amplifier, report both performance and stability under:

- relation-preserving edge dropout;
- file-threshold perturbation;
- kNN graph perturbation;
- time-slice changes;
- bootstrap resampling;
- the second dataset.

This is more informative than claiming dataset agnosticism from a single formula.

---

# 11. The research architecture implied by both books

## 11.1 Keep representation, diagnosis, and amplification separate

```text
telemetry
   |
   +--> canonical sessions and label-free raw features
   |
   +--> explicit graph hypotheses
          |-- native typed telemetry graph
          |-- parent-only and file-only operators
          |-- session similarity graphs
          |-- matched null graphs
                    |
                    +--> representation methods
                    |      |-- structural statistics
                    |      |-- node2vec
                    |      `-- relational GraphSAGE
                    |
                    +--> graph-signal audit
                           |-- score/feature variation
                           |-- evaluation-only label variation
                           |-- spectral energy and localization
                           |-- relation/hop/null comparisons
                                      |
                                      +--> fixed filter bank
                                      |      |-- neighbor agreement
                                      |      |-- residual/high-pass
                                      |      |-- restart/multihop
                                      |      `-- wavelet bands
                                      |
                                      +--> ranking + supporting subgraph
                                             |-- node contributions
                                             |-- relation contributions
                                             |-- hop/scale contributions
                                             `-- deletion-faithfulness tests
```

This separation answers four different questions:

1. **Presence:** is task-relevant organization stronger than matched nulls?
2. **Location:** which nodes, relations, hops, and scales contain it?
3. **Amplification:** can a frozen label-free transformation improve a deployable score?
4. **Explanation:** which inputs materially supported the output when removed?

An improvement on one does not imply all four. For example, label smoothness can establish presence in a frozen representation without yielding a deployable anomaly score.

## 11.2 The clean scientific boundary for labels

```python
graph = build_graph(telemetry, frozen_graph_config)       # no labels
X = build_signals_or_representation(telemetry, graph)    # no labels
s0 = label_free_score(X)                                 # no labels
diagnostics_x = audit_signal(graph, X, s0)                # no labels

# labels enter after all objects above are frozen
diagnostics_y = audit_task_signal(graph, hidden_labels)
metrics = evaluate_ranking(s0, hidden_labels)
```

If development labels select the graph, filter, or scale, record that separately:

```python
chosen_config = select_on_development(dev_diagnostics_y, candidate_configs)
frozen_result = evaluate_once(holdout, chosen_config)
```

That is a legitimate supervised development protocol, not a fully unsupervised per-dataset procedure.

## 11.3 Two atlases, not one score table

The project needs:

### Representation atlas

Asks what structure each method preserves.

```text
method × relation × layer
-> neighbor purity
-> peer rank/fragmentation
-> label energy
-> low-frequency mass
-> null lift
-> stability
```

### Triage atlas

Asks whether a label-free score helps an analyst.

```text
input score × graph × filter
-> AP
-> reviews to first malicious
-> recall/precision at review budgets
-> score stability
-> relation/hop/scale contribution
-> removal faithfulness
```

This prevents a good representation diagnostic from being reported as a good anomaly detector.

---

# 12. Which “three methods” to compare

## 12.1 Keep the Hamilton representation triad as the headline comparison

The most informative three representation methods remain:

1. **Typed structural statistics** — explicit local structure and role hypothesis.
2. **Node2vec session representation** — short-walk proximity hypothesis.
3. **Relational GraphSAGE session representation** — typed learned message-passing hypothesis.

They are meaningfully different. Replacing them with three small variations of spectral filtering would weaken the representation comparison.

Apply the same Ortega audit to all three. That is where the two books join.

## 12.2 If three GSP methods are needed, use these

### GSP-A: normalized local residual

Input: standardized feature matrix \(X\) or fixed raw score \(s_0\).

\[
R=(I-P)X,
\qquad
a_i=\|R_{i,:}\|_2
\]

or \(a_i=|(I-P)s_0|_i\).

Hypothesis: relevant activity is locally contrastive.

Outputs:

- residual score;
- neighbor prediction;
- top feature residuals;
- top contributing edges by relation;
- combinatorial-versus-normalized comparison.

### GSP-B: truncated restart diffusion

Input: fixed label-free seed score \(s_0\).

\[
s_K=(1-\alpha)\sum_{k=0}^{K}\alpha^kP^ks_0.
\]

Hypothesis: weak evidence receives support from nearby graph-coherent evidence, while restart retains the original seed.

Outputs:

- filtered score;
- contribution by hop;
- top source sessions;
- relation/meta-path support;
- score change under edge/path deletion.

### GSP-C: spectral graph wavelet energy

Input: \(s_0\), selected raw feature signals, or representation coordinates.

\[
c_j=g_j(\mathcal{L})x,
\qquad
a_i=\operatorname{aggregate}_j |c_j(i)|^2.
\]

Hypothesis: task signal is localized at one or more graph scales rather than purely smooth or purely residual.

Outputs:

- node-by-band energy map;
- dominant scale;
- bandwise session scores;
- Chebyshev approximation error;
- topology-perturbation stability.

## 12.3 The first basic graph method

The smallest defensible implementation is not a learned GNN. It is:

```text
canonical session representation
-> k=15 label-free session similarity graph
-> row-normalized P
-> compute [s0, P s0, (I-P)s0, P s0 - P^2 s0]
-> evaluate each frozen channel
-> report exact neighbor/edge contributions
```

This tests graph agreement, local surprise, and intermediate scale with almost no optimization. It also validates the graph/operator infrastructure needed for later wavelets and GNN diagnostics.

## 12.4 Do not learn an ensemble before understanding the channels

Initially report each filter output separately. A learned or rank-summed ensemble can hide whether improvement came from:

- the raw score;
- degree;
- smoothing;
- residual magnitude;
- one high-performing frequency band;
- label-driven weight selection.

Only build an ensemble after development results identify complementary channels, and freeze its rule before holdout.

---

# 13. The graph-signal metric suite

## 13.1 Triage metrics

Retain the current score metrics for every deployable output:

- average precision;
- reviews to first malicious;
- random expected reviews to first malicious;
- found, recall, and precision at 25, 50, 100, and 250 reviews;
- full ranked score table;
- score distribution and tie count.

With 19 positives, reviews-to-first is volatile. Always pair it with AP, budget curves, and uncertainty across seeds/slices. Do not run many filter variants and headline only the best first-hit rank.

## 13.2 Representation metrics

For every frozen session representation:

- malicious-neighbor purity at \(k\);
- enrichment over base rate;
- fraction of malicious sessions with any malicious peer;
- median rank of nearest malicious peer;
- number/size of malicious fragments;
- host-disjoint and time-disjoint peer metrics;
- topology-shuffle and feature-shuffle controls.

These are label-aware diagnostics and should be marked as such.

## 13.3 Signal-regime metrics

| Metric | Formula/definition | Label use | Main question |
|---|---|---|---|
| Dirichlet energy | \(x^\top Lx\) | Either | how much weighted edge disagreement? |
| Normalized energy | \(x^\top Lx/(x^\top Dx)\) | Either | disagreement after degree-volume normalization? |
| Conductance | boundary weight / smaller volume | Usually label-aware for \(y\) | is the positive set a coherent region? |
| Low-band mass | spectral energy in low band | Either | is the signal graph-smooth? |
| Mid/high-band mass | spectral energy by band | Either | boundary or multiscale content? |
| Local residual | \((I-P)x\) | No for deployable \(x\) | where does the signal violate neighbors? |
| Node spread | distance-weighted signal energy | Either | how geographically localized on graph? |
| Wavelet sparsity | concentration of coefficient energy | Either | does a small node-scale set explain the signal? |
| Null percentile | position versus shuffles/rewires | Labels only if \(x=y\) | is organization non-random? |

For multichannel \(X\), report per-channel metrics and a robust aggregate. Summing raw energies across differently scaled features is not meaningful without standardization.

## 13.4 Amplification metrics

“Amplification” should not mean that numbers became larger. Measure:

- change in AP and budget recall;
- rank correlation with the input score;
- change in score variance and entropy;
- malicious-versus-benign score contrast on evaluation data;
- retained original evidence fraction;
- contribution concentration by hop/relation/scale;
- improvement over the same filter on rewired graphs;
- stability under graph perturbations;
- fraction of nodes collapsed to near-identical scores.

If variance collapses and cosine similarity rises without improved triage, the method smoothed the signal but did not amplify useful contrast.

## 13.5 Localization and explanation metrics

- top-\(q\) contribution mass: how much of the score is explained by the top nodes/edges;
- relation attribution mass;
- hop/scale attribution mass;
- supporting-subgraph size;
- deletion delta: score change after removing reported support;
- matched-random deletion delta;
- explanation Jaccard across seeds/perturbations;
- path validity in the original typed temporal graph;
- temporal-order consistency when a path is presented as provenance.

An explanation is stronger when its removal changes the score substantially more than matched random removal.

## 13.6 Graph reliability metrics

- isolate fraction;
- component-size distribution;
- canonical-session coverage;
- relation coverage;
- degree/weighted-degree quantiles;
- neighbor hubness;
- kNN distance concentration;
- bootstrap neighbor Jaccard;
- \(K\)-hop coverage;
- spectral gaps and repeated eigenvalues;
- low-eigenspace principal-angle stability;
- filter-output correlation under topology perturbation.

These are prerequisites to interpreting a signal result, not optional exploratory plots.

## 13.7 A compact result schema

```text
representation
graph_view
operator
input_signal
filter
filter_order
seed
label_free_fit

average_precision
reviews_to_first_malicious
recall_at_25/50/100/250

normalized_score_energy
normalized_label_energy
label_energy_null_percentile
low/mid/high_energy_fraction
neighbor_purity

isolate_fraction
session_coverage
score_rank_stability
deletion_faithfulness_delta
```

Keep raw per-seed/per-slice rows. Summaries should not erase variability.

---

# 14. Controls that the GSP claim requires

## 14.1 Signal nulls

- uniform random score;
- shuffle the score over nodes;
- shuffle labels, preserving class count;
- shuffle within node type;
- shuffle within degree bins;
- shuffle within host/time blocks;
- random feature rotations where relevant.

These ask whether the apparent signal comes from value placement rather than graph structure.

## 14.2 Graph nulls

- degree-preserving rewire;
- degree-and-relation-type-preserving rewire;
- time-shifted edges;
- relation-specific edge shuffle;
- matched random edge deletion;
- feature-derived kNN graph with topology shuffled but weights retained;
- identity/time-only graph as an explicit proxy control.

These ask which graph property is necessary.

## 14.3 Operator controls

- \(A\) versus \(D^{-1}A\);
- \(L\) versus \(I-D^{-1}A\) versus \(\mathcal{L}\);
- with versus without self-loops;
- directed transition versus explicit symmetrization;
- lazy walk versus ordinary walk on bipartite views;
- binary versus weighted edges.

These separate degree, normalization, direction, and periodicity effects.

## 14.4 Representation controls

- raw features with real topology;
- raw features with shuffled topology;
- topology only;
- topology plus features;
- typed versus homogeneous topology;
- degree/structural statistics only;
- real GraphSAGE versus deterministic \(P/P^2\) filters;
- real graph versus relation-matched corruption objective.

## 14.5 Leakage controls

- assert labels are not in graph construction or score features;
- inspect absolute time and identity proxies;
- fit scaling and graph rules only in the declared evaluation protocol;
- exclude reviewed anchors from retrieval metrics;
- prevent future edges in chronological evaluation;
- build graph-learning signals from allowed history only;
- log exactly where label-aware configuration selection occurs.

---

# 15. A staged execution roadmap

## Stage 0: finish the raw baseline artifact

- complete the primary ranking metrics and random control;
- preserve the strong neighbor-purity diagnostic as label-aware;
- keep the tight time-column sensitivity result;
- record the full feature list and session manifest;
- confirm deterministic reruns.

Gate: one frozen raw score table over canonical sessions.

## Stage 1: freeze canonical sessions

- choose one identity/fallback/time rule;
- assign every process a canonical `session_id` once;
- reuse it for raw, structural, node2vec, GNN, and GSP views;
- compute malicious labels only after session construction.

Gate: all methods return exactly the same ordered session IDs.

## Stage 2: audit the native telemetry graph

- exact isolates/components/coverage;
- parent/file relation summaries;
- rare-file threshold sensitivity;
- directed-walk semantics;
- one-, two-, and three-hop effective coverage;
- canonical-session relation coverage.

Gate: enough usable graph support exists to interpret a graph method, or the sparsification/schema is revised as a declared new version.

## Stage 3: implement the most basic GSP method

- build the label-free \(k=15\) raw-session similarity graph;
- compute \(s_0\), \(Ps_0\), \((I-P)s_0\), and \(Ps_0-P^2s_0\);
- add score and label-signal audits;
- compare shuffle and rewire controls;
- output edge contributions.

Gate: the audit runs end to end and makes no label-free/label-aware category errors.

## Stage 4: complete the three representation hypotheses

1. typed structural statistics;
2. node2vec with declared direction/reverse-edge semantics;
3. relational GraphSAGE with real process features and proper relation controls.

Pool every method to canonical sessions and use one common scorer.

Gate: seed-complete results plus feature/topology/null controls.

## Stage 5: build the graph signal atlas

For each representation, relation view, and GNN layer:

- label energy and conductance;
- low/mid/high spectral mass;
- neighbor purity and peer rank;
- score variation and residual;
- topology/signal null lift;
- perturbation stability.

Gate: classify the observed regime as smooth, contrastive, multiscale, relation-specific, or absent.

## Stage 6: conditional amplification

- smooth regime: restart/low-pass diffusion;
- contrastive regime: local residual/high-pass;
- multiscale regime: SGWT band energy;
- relation-specific regime: typed operator bank;
- absent regime: no amplification claim.

Use a small development-only configuration set and freeze it.

Gate: improvement over identity, raw score, and rewired-filter controls.

## Stage 7: trace and validate support

- node, edge, relation, hop, and scale contributions;
- supporting typed subgraph;
- removal and recomputation;
- matched random removal;
- stability across seeds and perturbations;
- optional agent-generated narrative grounded only in the computed support record.

Gate: explanations are materially faithful, not just plausible-looking.

## Stage 8: untouched holdout

- confirm malicious-session viability first;
- refit only quantities allowed by the frozen protocol;
- no filter or graph selection on holdout labels;
- report direction of result on both co-primary metrics;
- report graph/signal regime stability.

## Stage 9: second dataset

- implement a schema adapter;
- preserve signal-construction and graph semantics where possible;
- recompute graph-dependent bases and normalization;
- test procedural transfer first;
- test frozen hyperparameter or parameter transfer separately.

## Stage 10: optional extensions

- Slepian region localization;
- analyst-budget sampling/active learning;
- graph learning over stable nodes and repeated windows;
- agentic explanation interface;
- diffusion wavelets.

These are not required to establish the initial graph signal localization/amplification contribution.

---

# 16. Decision rules for amplification

```text
Does the evaluation-only task signal exceed graph/null diagnostics?
   |
   +-- no --> do not amplify; revise graph hypothesis or retain raw method
   |
   `-- yes
        |
        +-- mostly low-frequency / low conductance?
        |      `--> test low-pass or restart propagation
        |
        +-- localized high-frequency / large residual?
        |      `--> test high-pass residual or wavelet detail
        |
        +-- piecewise smooth / several bands?
        |      `--> test SGWT or region-conditioned Slepian representation
        |
        `-- relation-specific?
               `--> filter relations separately; combine only after ablation

For the chosen filter:
   |
   +-- improves only on real graph, survives holdout, stable under perturbation
   |      `--> support for graph-based amplification
   |
   +-- improves equally on rewired graph
   |      `--> generic degree/smoothing effect, not semantic graph signal
   |
   +-- improves retrieval but not anomaly ranking
   |      `--> steering representation, not discovery detector
   |
   `-- collapses variance without metric gain
          `--> over-smoothing, not amplification
```

---

# 17. Traceable amplification in detail

## 17.1 Hop-wise contribution

For

\[
s=\sum_{k=0}^{K}a_kP^ks_0,
\]

store the matrix of per-hop outputs:

\[
C_{i,k}=a_k(P^ks_0)_i.
\]

This answers which scale moved session \(i\)'s score. It does not yet identify source nodes.

## 17.2 Source-node contribution

Because

\[
(P^ks_0)_i=\sum_j(P^k)_{ij}s_{0,j},
\]

the contribution from source \(j\) at hop \(k\) is

\[
C_{i\leftarrow j,k}=a_k(P^k)_{ij}s_{0,j}.
\]

Return the top positive and negative contributors, not only absolute values. A source can suppress a score as well as increase it.

For large sparse graphs, compute contributions only for the top-ranked targets and bounded \(K\), rather than materializing dense \(P^k\).

## 17.3 Relation/meta-path contribution

For relation operators \(P_r\), use a short predeclared meta-path bank:

\[
P_{r_1}P_{r_2}\cdots P_{r_k}s_0.
\]

Examples:

- session → process → parent/child process → session;
- session → process → file → process → session;
- forward-parent versus reverse-parent flow.

Each product has a semantic label and its own contribution. Avoid unconstrained enumeration; it creates a combinatorial search and an easy path to label tuning.

## 17.4 Edge-energy explanations

For residual or smoothness results, return

\[
e_{ij}=w_{ij}(x_i-x_j)^2.
\]

These contributions exactly sum to Dirichlet energy under the stated convention. They explain where graph agreement fails, which can be a campaign boundary rather than the suspicious interior.

## 17.5 Removal faithfulness

For every reported top relation/path/subgraph:

1. remove or mask it;
2. recompute the exact score;
3. measure target rank/score change;
4. compare with matched random removal of the same size, degree, and relation type;
5. repeat across seeds or small topology perturbations.

Report:

```text
support_id
target_session
support_type
nodes/edges/relations
original_contribution
score_delta_after_removal
rank_delta_after_removal
matched_random_delta_mean/std
stability_jaccard
```

Only after this should an agent turn the record into prose. The agent can summarize computed evidence; it cannot upgrade association into causality.

---

# 18. What “dataset agnostic” can mean

The phrase should be decomposed into levels:

| Level | Meaning | Current realistic target? |
|---|---|---:|
| Procedural portability | same graph-signal audit and metric protocol | Yes |
| Schema portability | adapter maps equivalent entities/relations/features | Yes, to test |
| Per-dataset unsupervised refit | scaling, graph, bases, and score refit without labels | Yes |
| Frozen hyperparameters | same \(k\), filter order, bands, and restart values | Later test |
| Frozen learned parameters | model weights transfer without retraining | Not yet |
| Zero-shot universal graph semantics | no dataset/schema adaptation | Not credible |

A strong near-term claim is:

> The procedure is label-free at fit time and portable across datasets through explicit schema adapters and per-dataset graph normalization; graph-dependent bases are recomputed, while signal definitions, relation semantics, filter-design rules, controls, and metrics remain frozen.

This is still dataset-agnostic methodology in a meaningful sense. It does not require identical eigenvectors or graphs.

## 18.1 Why polynomial filters are the best portability foundation

- coefficients have local hop meaning;
- normalized operators place spectra in comparable ranges;
- sparse computation scales with edges;
- no eigenvector alignment is required;
- contribution paths remain inspectable;
- the same procedure adapts to graph size.

## 18.2 What must be recomputed

Even under procedural portability, recompute:

- degree and normalization matrices;
- connected components;
- graph distances and effective locality;
- spectrum bounds or spectral density estimates;
- Chebyshev scaling;
- wavelet/Slepian/diffusion bases;
- reference distributions of filter responses;
- graph reliability diagnostics.

Refitting these graph-adapted quantities is not a failure of portability. Hiding that refit would be.

---

# 19. Claims and wording discipline

| Tempting claim | Defensible replacement |
|---|---|
| “The graph contains malicious signal.” | “The evaluation-only malicious indicator is organized non-randomly on this declared graph/operator relative to matched nulls.” |
| “We amplified malicious signal without labels.” | “A frozen graph filter improved a label-free score; labels were used only for evaluation.” |
| “High frequency means malicious.” | “High-frequency energy marks disagreement with this graph's similarity assumption.” |
| “Low frequency means a campaign.” | “The candidate region is internally coherent under this operator; cyber semantics require separate validation.” |
| “This is the attack path.” | “This typed path materially supported the model score and passed a deletion-faithfulness test.” |
| “The method is dataset agnostic.” | “The frozen procedure ports through schema mapping and per-dataset unsupervised graph adaptation.” |
| “Graph learning recovered the true network.” | “The learned graph is an interpretable statistical model optimized under stated priors.” |
| “Sampling selects the most suspicious sessions.” | “Sampling selects informative/covering sessions under a reconstruction model; suspiciousness is a separate term.” |
| “The GNN amplified signal because embeddings became smoother.” | “Layerwise label organization improved without representation collapse and exceeded deterministic/rewired controls.” |

---

# 20. Minimal implementation blueprint

## 20.1 Core interfaces

```python
GraphView = {
    "name": str,
    "node_ids": np.ndarray,
    "W": sparse.csr_matrix,
    "operator_name": str,
    "operator": sparse.csr_matrix,
    "metadata": dict,
}

SignalView = {
    "name": str,
    "values": np.ndarray,       # [N] or [N, F]
    "label_free": bool,
    "fit_scope": str,
    "metadata": dict,
}

FilterResult = {
    "scores": pd.DataFrame,
    "hop_outputs": dict,
    "band_outputs": dict,
    "contributions": pd.DataFrame,
    "diagnostics": pd.DataFrame,
}
```

## 20.2 Graph construction

```python
def build_session_knn_graph(X, k=15, mutual=False, weighted=False):
    # X is label-free and aligned to canonical session IDs.
    # Return symmetric W and graph reliability diagnostics.
    ...

def normalized_operators(W):
    # Handle isolates explicitly.
    # Return P, T=I-P, and symmetric normalized L.
    ...
```

Isolate policy must be explicit. Common choices are a zero propagation row, identity self-retention, or per-component processing. Do not allow division by zero to determine the semantics accidentally.

## 20.3 Signal audit

```python
def signal_audit(W, P, Lsym, x, bands, nulls):
    return {
        "dirichlet_energy": ...,
        "normalized_energy": ...,
        "local_residual": ...,
        "spectral_energy": ...,
        "node_spread": ...,
        "null_summary": ...,
    }
```

Use exact eigendecomposition only on the 1,457-session graph or manageable components. For the 100k-node process graph, prefer sparse extremal eigenpairs or polynomial filters.

## 20.4 Fixed filter bank

```python
def basic_filter_bank(P, s0, alpha=0.5, order=3):
    outputs = {"identity": s0.copy()}
    p1 = P @ s0
    p2 = P @ p1
    outputs["neighbor_mean"] = p1
    outputs["local_residual"] = s0 - p1
    outputs["scale_difference"] = p1 - p2

    restart = (1 - alpha) * s0.copy()
    current = s0.copy()
    for k in range(1, order + 1):
        current = P @ current
        restart += (1 - alpha) * (alpha ** k) * current
    outputs["restart_diffusion"] = restart
    return outputs
```

The exact restart normalization can be chosen differently, but it must be declared and applied consistently.

## 20.5 Contribution extraction

```python
def top_filter_contributions(P, s0, targets, coeffs, top_n=20):
    # Sparse bounded-hop propagation that retains source-node identity.
    # Returns signed source contribution by target and hop.
    ...
```

For relation-aware paths, retain sparse intermediates keyed by relation sequence.

## 20.6 Strict alignment assertions

```python
assert session_table.session_id.is_unique
assert np.array_equal(graph_session_ids, session_table.session_id.to_numpy())
assert scores.shape[0] == len(session_table)
assert not any(label_column in graph_feature_columns for label_column in LABEL_COLUMNS)
assert graph_config_was_frozen_before_evaluation
```

Alignment errors are especially dangerous because GSP formulas will still return plausible numbers when signals are permuted onto the wrong nodes.

---

# 21. Proposed output artifacts

## 21.1 `graph_manifest`

```text
graph_view
node_definition
edge_definition
direction
weight_rule
sparsification
node_count
edge_count
isolate_fraction
component_count
largest_component_fraction
degree_quantiles
canonical_session_coverage
```

## 21.2 `signal_atlas`

```text
representation
layer
graph_view
operator
signal
label_free
dirichlet_energy
normalized_energy
low/mid/high_mass
node_spread
null_percentile
```

## 21.3 `filter_comparison`

```text
input_signal
graph_view
filter
order
alpha
seed
triage_metrics...
rank_correlation_to_input
score_variance_ratio
rewire_delta
perturbation_stability
```

## 21.4 `supporting_subgraphs`

```text
target_session
rank
source_session_or_entity
relation_sequence
hop
scale
signed_contribution
supporting_edges
deletion_score_delta
random_deletion_percentile
```

## 21.5 `review_selection`

```text
review_rank
session_id
suspiciousness
marginal_graph_coverage
overlap_penalty
estimated_review_cost
observed_label_after_review
```

Keep this artifact exclusive to active/steering experiments.

---

# 22. Equation and concept cheat sheet

| Concept | Expression | Project meaning |
|---|---|---|
| Graph signal | \(x\in\mathbb{R}^N\) | one scalar value per aligned node |
| Neighbor sum | \(Ax\) | unnormalized incoming support |
| Neighbor mean | \(Px=D^{-1}Ax\) | local graph prediction |
| Local residual | \((I-P)x\) | normalized disagreement with neighbors |
| Laplacian residual | \(Lx=D(I-P)x\) | degree-weighted disagreement |
| Dirichlet energy | \(x^\top Lx=\sum w_{ij}(x_i-x_j)^2\) | total weighted boundary/disagreement |
| Normalized energy | \(x^\top Lx/(x^\top Dx)\) | degree-volume-normalized variation |
| GFT | \(\tilde x=U^\top x\) for symmetric \(Z\) | signal coefficients in graph modes |
| Spectral energy | \(\tilde x_k^2\) | energy at graph mode \(k\) |
| Polynomial filter | \(H(Z)=\sum a_kZ^k\) | shared bounded-hop transformation |
| Filter response | \(h(\lambda)=\sum a_k\lambda^k\) | gain at graph frequency \(\lambda\) |
| Restart diffusion | \((1-\alpha)\sum \alpha^kP^kx\) | multihop support with seed retention |
| Piecewise constant | sparse \(B^\top x\) | few graph boundaries relative to internal structure |
| Node spread | \(\sum d(a,i)^2x_i^2/\|x\|^2\) | graph-local concentration around \(a\) |
| Slepian concentration | eigenproblem of \(U_F^\top I_SU_F\) | low-frequency energy localized in region \(S\) |
| SGWT coefficient | \([g_j(L)x]_i\) | signal at node \(i\), graph scale \(j\) |
| Chebyshev approximation | polynomial approximation to (\(g(L)\)x) | scalable local spectral filtering |
| Sampling | observe \(x_S\) to recover \(x\) under a model | analyst-label coverage, not automatically ranking |

---

# 23. What to read closely versus skim

## Read closely now

1. **Node-domain filters, printed pp. 51–55 / PDF pp. 69–73.** This is the direct mathematical basis for the first low/high filter bank and hop tracing.
2. **Variation and GFT, printed pp. 79–103 / PDF pp. 97–121.** This defines the signal atlas, degree normalization, and label-energy diagnostic.
3. **Signal models, printed pp. 120–130 / PDF pp. 138–148.** This prevents choosing smoothing before diagnosing the regime.
4. **Localization and SGWT, printed pp. 149–169 / PDF pp. 167–187.** This is the basis for node-scale localization.
5. **How to Choose a Graph, printed pp. 181–201 / PDF pp. 199–219.** This is the most important chapter for graph construction, sparsification, and circularity.
6. **Application checklist and machine learning, printed pp. 204–205 and 224–233 / PDF pp. 222–223 and 242–251.** This ties the diagnostics to label smoothness, active review, GCNs, and stability.

## Skim until needed

- invariant-subspace proofs and minimal-polynomial details beyond their locality implications;
- exact sampling-set optimization algorithms;
- critically sampled bipartite filterbank derivations;
- image/video-specific applications;
- full diffusion-wavelet construction;
- MATLAB/GraSP appendix details, unless using the reference implementations.

---

# 24. Concrete next actions

In priority order:

1. **Freeze one canonical session map.** This is required before any fair graph comparison.
2. **Add exact graph coverage diagnostics.** The current graph is extremely sparse relative to 100k processes.
3. **Build the \(k=15\) raw-session similarity graph.** It reuses the already successful representation diagnostic.
4. **Implement \(s_0\), \(Ps_0\), \((I-P)s_0\), and \(Ps_0-P^2s_0\).** This is the basic Ortega filter experiment.
5. **Add normalized label energy and spectral mass as evaluation-only diagnostics.** Compare label shuffles and degree-aware nulls.
6. **Finish structural-statistics, node2vec, and relational GraphSAGE representations.** Apply the same GSP audit to each.
7. **Implement SGWT only if the basic audit shows multiscale signal.** Use Chebyshev filters and a small frozen band set.
8. **Add path/relation contributions and deletion tests.** Do this before an agentic explanation layer.
9. **Freeze on development and evaluate untouched holdout.** No graph/filter selection on holdout labels.
10. **Port the procedure to a second dataset.** Test procedural refit before attempting frozen-parameter transfer.

---

# 25. Final synthesis

Ortega turns the project's intuitive phrase “find and amplify graph signal” into a disciplined research program:

1. define the node-aligned signal;
2. state what every graph relation and weight means;
3. choose an operator whose propagation and variation match that meaning;
4. test smooth, contrastive, piecewise, and multiscale regimes against nulls;
5. apply only the filter family supported by the diagnosed regime;
6. decompose its output by relation, hop, scale, and source node;
7. validate explanations by removal and recomputation;
8. evaluate triage separately from representation quality and sampling coverage;
9. freeze the procedure before holdout;
10. claim portability at the level actually demonstrated.

The strongest bounded contribution is not a universal graph model and not an agent that declares where maliciousness lives. It is:

> an auditable graph-signal triage framework that determines whether a chosen telemetry graph expresses task-relevant organization, identifies the relations and scales responsible, applies a frozen label-free filter to the available evidence, and returns both a ranked review list and perturbation-tested supporting structure.

Hamilton provides the representation hypotheses. Ortega provides the missing signal model, operator audit, localization machinery, filter vocabulary, and claim discipline. Together they support the intended scope: graph signal localization and amplification first; generalization beyond graph-structured telemetry as future work.
