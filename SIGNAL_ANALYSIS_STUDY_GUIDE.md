# AutoSignal Signal Analysis Study Guide

## What this guide is for

This guide contains the theory needed to design, implement, interpret, and
defend the **signal localization and amplification** part of AutoSignal.

The central research question is:

> After AutoSignal creates several label-free telemetry representations, where
> is malicious-behavior evidence organized, what graph-signal regime does it
> occupy, and can one matched graph operation improve analyst triage beyond a
> topology-preserving null?

The important words are:

- **label-free representation and score:** labels do not construct the graph,
  representation, or deployment score;
- **localization:** determine which representation, neighborhood regime, and
  interpretable inputs carry useful evidence;
- **matched operation:** choose an amplifier because the diagnosed signal
  regime supports it;
- **beyond a null:** show that the result depends on meaningful neighborhood
  arrangement rather than degree, hubs, or generic smoothing;
- **analyst triage:** evaluate review order, not only geometric separation.

This is not a general graph-signal-processing textbook. It deliberately
separates the concepts required for the current contribution from attractive
but unnecessary extensions.

---

## 1. The whole research argument in one page

AutoSignal already produces several session representations:

| Method | Representation being tested | Scientific question |
|---|---|---|
| Raw session kNN | aggregated telemetry features | Does unusual aggregate behavior carry the signal? |
| M1 structural statistics | named graph-role statistics | Does explicit local graph structure carry it? |
| M2 Node2Vec | short-walk topology embedding | Does higher-order walk proximity carry it? |
| M3 GraphSAGE | learned feature–relation embedding | Does learned feature/topology interaction carry it? |
| Random | random score | Is performance above a sanity floor? |

The signal-analysis stage adds four objects:

\[
X_m\in\mathbb{R}^{N\times F_m},\qquad
s_m\in\mathbb{R}^{N},\qquad
G_m=(V,W_m),\qquad
y\in\{0,1\}^{N}.
\]

Where:

- \(N\) is the number of frozen canonical sessions;
- \(X_m\) is method \(m\)'s original high-dimensional session representation;
- \(s_m\) is its label-free anomaly score;
- \(G_m\) is a declared graph over the same sessions;
- \(y\) is the evaluation-only malicious-session indicator.

The minimal experiment is:

```text
freeze canonical sessions
→ retain X_m, its session IDs, and dimension names
→ build a label-free session graph from X_m
→ compute the original, support, residual, and scale-difference channels
→ use labels only to evaluate the frozen channels
→ compare observed organization with label and graph nulls
→ perform source analysis appropriate to the winning representation
→ test one regime-matched amplifier on real and rewired graphs
→ freeze and evaluate once on holdout
```

The smallest useful graph-filter bank is:

\[
\begin{aligned}
\text{intrinsic}       &= s,\\
\text{neighbor support}&=Ps,\\
\text{local contrast}  &=s-Ps,\\
\text{scale difference}&=Ps-P^2s.
\end{aligned}
\]

These channels answer:

1. Is the session suspicious on its own?
2. Is its score supported by its immediate neighborhood?
3. Is it a local exception to its neighborhood?
4. Is evidence concentrated at roughly one hop rather than diffused more
   broadly?

That is the core of the signal contribution. Full spectral decompositions,
wavelets, Slepians, learned filter ensembles, and large parameter searches are
not required to establish it.

---

## 2. The five objects you must never mix up

### 2.1 Canonical review units

The evaluation unit is a **session**, even when the native telemetry graph
contains processes, files, users, hosts, or endpoints.

Every method must use the same ordered session IDs:

```python
assert session_table.session_id.is_unique
assert np.array_equal(method_session_ids, session_table.session_id.to_numpy())
assert len(scores) == len(session_table)
```

**Why:** Graph mathematics will still return plausible numbers when values are
silently assigned to the wrong nodes. Misalignment is therefore more dangerous
than an obvious exception. It also makes AP, Recall@K, and neighborhood
comparisons invalid if methods use different sessions.

### 2.2 A representation

A representation is a matrix:

\[
X\in\mathbb{R}^{N\times F}.
\]

Each row describes one session. Its columns may be:

- named behavioral features;
- named structural statistics;
- latent Node2Vec coordinates;
- latent GraphSAGE coordinates.

**Why:** The representation determines the geometry in which sessions can be
similar or unusual. The method comparison is already a first localization
experiment: it asks which type of geometry exposes useful evidence.

### 2.3 A graph signal

A scalar graph signal is:

\[
x=[x_1,\ldots,x_N]^\top\in\mathbb{R}^{N},
\]

with exactly one value on each graph node. A feature matrix is \(F\) graph
signals—one per column.

Examples:

- one method's anomaly score \(s\);
- one standardized named feature;
- the malicious indicator \(y\), for evaluation only;
- a residual magnitude;
- an analyst-selected anchor impulse, in a later steering experiment.

**Why:** “The graph has signal” is incomplete. A defensible sentence names the
signal, graph, operator, and null:

> The malicious-session indicator is more locally organized on the frozen M1
> session graph than under session-level label permutations.

### 2.4 An anomaly score

The current deployable score is a kNN-distance anomaly score:

\[
s_i=\text{distance-based unusualness of session }i.
\]

Higher means higher review priority.

**Why:** A good representation and a good anomaly ranking are different
outcomes. Malicious sessions may form a compact cluster, giving high
malicious-neighbor purity, while a point-anomaly score treats that cluster as
ordinary. This would be useful retrieval geometry but weak zero-shot discovery.

### 2.5 UMAP coordinates

UMAP coordinates are a two-dimensional visualization artifact:

\[
Z_{\text{UMAP}}\in\mathbb{R}^{N\times2}.
\]

Do not build the scientific graph, compute signal filters, or attribute
features using these coordinates.

**Why:** UMAP intentionally distorts high-dimensional geometry to create a
readable plot. It can change global distances, density, and apparent cluster
separation. The analysis must use the original \(X_m\).

---

## 3. Two different graphs, two different claims

### 3.1 The native telemetry relation graph

This graph contains semantic entities and observed typed relations:

```text
process --parent_of------> process
process --executes-------> executable
process --touches--------> file
process --runs_on--------> host
user    --authenticates--> host
endpoint --communicates--> endpoint
```

Its adjacency means an observed semantic relationship, not necessarily that
the endpoints should have similar anomaly scores.

It is currently used to build M1, Node2Vec, and GraphSAGE representations.

### 3.2 A session-similarity graph

This graph contains one node per frozen session. An edge means that two
sessions are neighbors in a declared label-free representation \(X_m\).

It is the cleanest first graph for graph signal processing because:

- its nodes already match the analyst review unit;
- nearby nodes explicitly mean representation similarity;
- a neighbor average therefore has an interpretable meaning;
- every filter output remains session aligned.

### 3.3 Why the distinction matters

On the relation graph:

> Process A touched file F.

On the similarity graph:

> Session A is close to session B under representation X.

Neither implies the other. A parent-child edge may connect behaviorally
different processes. Two disconnected sessions may be structurally
equivalent. A shared-file projection may connect sessions only because they
share a ubiquitous system file.

The first GSP study should use a session-similarity graph. Native telemetry
relations remain essential for building representations and for later
method-specific source analysis.

### 3.4 The coupling caveat

If both \(s_m\) and \(G_m\) come from the same \(X_m\), the graph and score share
geometry. This is valid for diagnosing whether scores are locally supported or
contrastive, but it limits the claim.

You may claim:

> This representation's anomaly score has a non-random neighborhood regime.

You may not automatically claim:

> Native telemetry topology amplified the signal.

That stronger claim requires an independently defined semantic graph or
relation-specific operator.

---

## 4. Building the controlled session graph

### 4.1 Basic construction

For one frozen representation \(X\):

1. use the exact declared scaling;
2. compute session-to-session distances without labels;
3. select \(k=15\) nearest neighbors as the frozen primary rule;
4. symmetrize explicitly;
5. choose binary or declared distance-based weights;
6. remove or declare self-loops;
7. record all choices in a graph manifest.

Possible symmetrization rules:

- **union kNN:** connect \(i,j\) if either selects the other;
- **mutual kNN:** connect them only if both select each other.

Union has better coverage. Mutual kNN gives stronger neighbor agreement but can
create isolates. Pick one as primary before evaluating labels; use the other
only as a bounded sensitivity check.

### 4.2 Core matrices

Let \(W\) be the symmetric nonnegative adjacency/weight matrix and:

\[
D_{ii}=\sum_jW_{ij}.
\]

Important operators are:

| Operator | Definition | Meaning |
|---|---|---|
| Adjacency | \(W\) | unnormalized neighbor sum |
| Random walk | \(P=D^{-1}W\) | neighbor average |
| Laplacian | \(L=D-W\) | degree-weighted disagreement |
| Random-walk Laplacian | \(I-P\) | value minus neighbor average |
| Symmetric normalized Laplacian | \(\mathcal L=I-D^{-1/2}WD^{-1/2}\) | symmetric normalized variation |

For the first filter bank, use \(P\). It prevents high-degree sessions from
receiving larger values solely because they have more incident edges.

### 4.3 Matrix convention

This guide treats signals as column vectors and \(P\) as row stochastic:

\[
(Ps)_i=\sum_jP_{ij}s_j.
\]

Therefore \(Ps\) is session \(i\)'s weighted neighbor mean.

Keep this convention consistent. Some PageRank texts use \(P^\top s\) because
they treat scores as mass flowing between states. Both can be correct under
different conventions; silently mixing them cannot.

### 4.4 Isolates

An isolate has \(D_{ii}=0\). Its row cannot be normalized normally.

A defensible policy must be explicit. One conservative choice is:

\[
P_{ii}=1
\]

for isolates. Then an isolate retains itself, receives no graph-derived change,
and has zero local residual.

**Why:** “No graph evidence” should not silently become “benign,” nor should
division by zero choose the method's semantics.

### 4.5 Required graph audit

Before interpreting a filter, record:

- session count and edge count;
- isolate fraction;
- component-size distribution;
- degree and weighted-degree quantiles;
- in-neighbor hubness;
- nearest- and \(k\)th-neighbor distance quantiles;
- union/mutual kNN coverage;
- one-, two-, and three-hop neighborhood sizes;
- neighbor-set stability under small perturbations;
- sensitivity to identity, absolute time, and session-size proxies.

**Why:** A two-hop filter is not “local” if two hops already reach most of the
graph. A graph can also be mathematically valid but semantically dominated by
host identity, degree, or high-dimensional hubness.

---

## 5. The signal regimes

You are not looking for one universal pattern. The purpose of the audit is to
identify which regime, if any, fits the data.

### 5.1 Smooth or homophilous signal

Connected/neighboring sessions tend to have similar signal values.

For a suspicious-score signal:

```text
high intrinsic score
+ high neighbor score
= neighborhood-supported evidence
```

Possible cyber interpretation:

- related attack sessions form a local pocket;
- repeated campaign behaviors occupy nearby geometry;
- weak evidence is distributed across several similar sessions.

Candidate amplifier: shallow low-pass or restart diffusion.

### 5.2 Contrastive or heterophilous signal

A session differs sharply from its neighbors:

\[
|s_i-(Ps)_i|\text{ is large}.
\]

Possible cyber interpretation:

- one process/session violates an otherwise ordinary local context;
- malicious behavior attaches to common benign infrastructure;
- attack evidence occurs at a boundary rather than inside a cluster.

Candidate response: retain the residual/high-pass channel. Smoothing could
destroy this evidence.

### 5.3 Intermediate-scale or piecewise signal

One-hop support differs from broader support:

\[
Ps-P^2s.
\]

Possible cyber interpretation:

- a compact campaign pocket exists inside a larger mixed region;
- local evidence is strong, but wider diffusion crosses a boundary;
- attack evidence is organized at a limited radius.

Candidate response: the fixed scale-difference channel; wavelets are a later
extension only if this basic result is genuinely important.

### 5.4 Structural equivalence

Sessions can have similar graph roles without being connected or close.

Possible cyber interpretation:

- the same process/file pattern appears on different hosts;
- separate attacks create comparable fan-out or brokerage roles;
- malicious sessions repeat a motif in disconnected components.

Candidate methods: M1 structural statistics, role features, or Node2Vec-like
walk context. Ordinary score diffusion may not help because direct adjacency
is not the source of similarity.

### 5.5 No graph organization

The label or score behaves no differently from matched nulls.

Correct response: do not amplify. Retain the strongest non-graph ranking or
report localization without amplification.

**Why:** A negative result completes the research question. It prevents the
project from turning graph methods into a foregone conclusion.

---

## 6. The fixed four-channel signal audit

Let \(s\) be a frozen label-free anomaly score.

### 6.1 Intrinsic evidence

\[
c_0=s.
\]

This is the no-graph control.

**Why:** Every graph-derived output must be compared with the evidence that
already existed. Otherwise a transformed score can look sophisticated while
performing worse than its input.

### 6.2 Neighbor support

\[
c_{\text{support}}=Ps.
\]

This asks:

> What score would this session receive from its immediate neighbors?

High \(Ps_i\) means the neighborhood contains strong evidence. It does not mean
the session itself is anomalous.

### 6.3 Signed local contrast

\[
c_{\text{residual}}=s-Ps.
\]

Interpretation:

- positive: the session is more suspicious than its neighbors;
- negative: the neighbors are more suspicious than the session;
- near zero: local agreement.

Also retain:

\[
|s-Ps|
\]

as unsigned local surprise. Signed and unsigned residuals answer different
questions and must not be silently interchanged.

### 6.4 Scale difference

\[
c_{\text{scale}}=Ps-P^2s.
\]

This asks:

> Is immediate-neighborhood support different from broader two-hop context?

It is a compact band-pass-like test, not proof of a true universal “middle
frequency.”

### 6.5 Do not combine the channels yet

Initially evaluate each channel separately. A learned weighted ensemble could
hide whether performance came from:

- the original score;
- degree;
- smoothing;
- residual magnitude;
- one favorable scale;
- label-based weight selection.

Combine only if complementary channels are established on development data and
the combination rule is frozen before holdout.

---

## 7. A small numerical example

Suppose four sessions form a chain:

```text
1 — 2 — 3 — 4
```

and their intrinsic scores are:

\[
s=[0.9,\;0.8,\;0.1,\;0.2]^\top.
\]

Using an unweighted neighbor average:

\[
Ps=[0.8,\;0.5,\;0.5,\;0.1]^\top.
\]

The residual is:

\[
s-Ps=[0.1,\;0.3,\;-0.4,\;0.1]^\top.
\]

Interpretation:

- Session 1 is highly suspicious and supported by Session 2.
- Session 2 is suspicious but noticeably above its mixed neighborhood.
- Session 3 has low intrinsic evidence but suspicious neighbors; its negative
  residual must not be mistaken for “unimportant.”
- Session 4 has low evidence and a low-score neighbor.

Next:

\[
P^2s=[0.5,\;0.65,\;0.3,\;0.5]^\top
\]

and:

\[
Ps-P^2s=[0.3,\;-0.15,\;0.2,\;-0.4]^\top.
\]

The signs show where immediate support differs from the wider context. The
example also demonstrates why one scalar “graph score” cannot describe every
regime.

---

## 8. Graph variation and frequency

### 8.1 Dirichlet energy

For an undirected graph:

\[
x^\top Lx
=
\sum_{\{i,j\}\in E}w_{ij}(x_i-x_j)^2,
\]

when each undirected edge is counted once.

It measures total weighted disagreement across edges.

- low energy: neighboring values tend to agree;
- high energy: the signal changes sharply across edges.

Some texts sum over ordered pairs and include a factor of \(1/2\). Record the
convention; the scientific interpretation is the same.

### 8.2 Degree-normalized energy

Raw energy rises with graph volume and hub placement. A useful normalized form
is:

\[
\frac{x^\top Lx}{x^\top Dx}.
\]

**Why:** A unit deviation on a high-degree node should not automatically be
called more interesting than the same normalized disagreement on a rare node.
If the conclusion changes between raw and normalized energy, report that the
result is degree dependent.

### 8.3 The malicious-label signal

Let:

\[
y_i=
\begin{cases}
1,&\text{session }i\text{ is malicious}\\
0,&\text{otherwise.}
\end{cases}
\]

Then \(y^\top Ly\) measures malicious/benign boundary weight.

This is an **evaluation-only diagnostic**. It can establish that the frozen
representation organizes known malicious sessions, but it is not a deployable
score.

With few malicious sessions, compare it with session-level label permutations
that preserve the positive count.

### 8.4 The score signal

For deployable score \(s\), inspect:

- \(s^\top Ls\);
- \(Ps\);
- \((I-P)s\);
- correlation between \(s\) and \(Ps\);
- stability under graph perturbations;
- evaluation-only alignment of each frozen channel with \(y\).

This separates:

- a graph that organizes labels;
- a score that follows that organization;
- a score that is locally contrastive;
- a graph that does not expose useful organization.

### 8.5 Graph frequency

For symmetric \(L=U\Lambda U^\top\):

\[
\tilde{x}=U^\top x.
\]

Low-eigenvalue modes change slowly across strong edges. High-eigenvalue modes
change sharply.

Graph frequency is therefore not an intrinsic property of malicious behavior.
It is always:

> variation relative to this graph, weighting, and operator.

“High frequency” means “disagrees with this graph's neighbor assumption,” not
“malicious.” “Low frequency” means locally coherent, not “a campaign.”

### 8.6 Why the project can postpone a spectral atlas

The four polynomial channels already test low-pass, high-pass, and limited
intermediate-scale behavior without:

- computing every eigenvector;
- selecting unstable spectral cutoffs;
- comparing graph-specific bases;
- introducing many tunable bands.

Spectral energy curves are valuable confirmation if the basic channels expose
a real multiscale result. They are not required for the first defensible
experiment.

---

## 9. Localization has three levels

### Level 1: representation-family localization

Compare Raw, M1, M2, M3, and controls with the same scorer and sessions.

Question:

> Does useful triage evidence appear in aggregate behavior, structural roles,
> walk proximity, learned typed interaction, or nowhere reliably?

This is the primary AutoSignal localization claim.

### Level 2: winner-specific source analysis

Different representations permit different explanations:

| Winning representation | Defensible source analysis |
|---|---|
| Raw | winning feature hypothesis; largest standardized feature deviations and local feature residuals |
| M1 structural | named structural statistics; responsible relations/entities; degree and component controls |
| M2 Node2Vec | neighbors, components, degree, walk coverage, and real-versus-rewired behavior—not latent coordinate names |
| M3 GraphSAGE | trained-versus-random control plus one grouped relation removal; optional feature-group occlusion |
| UMAP | visualization only; never a source analysis |

**Why:** Raw and M1 dimensions have meanings. Node2Vec coordinates are
rotation-dependent latent axes. GraphSAGE coordinates are learned mixtures.
Forcing all methods to name original “important features” would produce
scientifically inconsistent explanations.

### Level 3: neighborhood-regime localization

Use \(s\), \(Ps\), \(s-Ps\), and \(Ps-P^2s\) to describe the evidence as:

- intrinsic;
- neighborhood supported;
- locally contrastive;
- intermediate scale;
- or not organized beyond nulls.

This level selects whether any amplifier is scientifically justified.

---

## 10. Named-feature localization

For a named representation \(X\), compute:

\[
R_X=(I-P)X=X-PX.
\]

For session \(i\), rank features by:

\[
|R_{X,i,f}|.
\]

This yields statements such as:

> Relative to its representation neighbors, this session is most unusual in
> `tcp_send_size`, `reg_writes`, and `duration_seconds`.

Keep:

- the session's standardized feature value;
- its neighbor-predicted value;
- the signed residual;
- the absolute residual;
- the neighbors contributing to the prediction.

**Why:** A global feature value says what is large. A local residual says what
is surprising relative to behaviorally similar sessions. Those are different
analyst questions.

Do not call a large residual causal. It is a model-relative discrepancy.

---

## 11. Representation diagnostics versus triage metrics

### 11.1 Representation diagnostics

These ask whether known malicious sessions are organized in frozen geometry:

- malicious neighbor purity;
- enrichment over malicious base rate;
- fraction with at least one malicious peer;
- nearest malicious-peer rank;
- malicious fragmentation/components;
- label Dirichlet energy;
- label-permutation percentile.

They use labels after representation construction and are not deployment
scores.

### 11.2 Triage metrics

These ask whether a frozen label-free score gives a useful review order:

- average precision;
- recall at 100 as a primary operational budget;
- reviews to first malicious;
- found/recall/precision at 25, 50, 100, and 250;
- prevalence beside AP;
- per-seed results and paired differences.

Accuracy is unsuitable under extreme imbalance. ROC-AUC can also look
impressive while top-of-list triage remains poor.

### 11.3 Why both are required

| Geometry | Ranking | Meaning |
|---|---|---|
| strong | strong | representation and score both expose task evidence |
| strong | weak | useful clustering/retrieval geometry, wrong discovery score |
| weak | strong | isolated point anomalies rather than a coherent malicious region |
| weak | weak | no useful evidence under this construction |

This table is one of the most important interpretive tools in the project.

---

## 12. Null models: the heart of the research claim

A null destroys the hypothesized source of signal while preserving nuisance
structure that could fake it.

### 12.1 Random ranking

Question:

> Does the method beat a chance review order?

Necessary, but too weak for a graph claim.

### 12.2 Label permutation

Keep \(X\), \(s\), and \(G\) fixed. Shuffle \(y\) across canonical sessions
while preserving the malicious count.

Question:

> Is the observed malicious-label organization stronger than random placement
> on this frozen graph?

Permutation occurs at session level, not process-row level. Process rows within
a session are not independent labels.

If malicious sessions are concentrated by host, campaign, or time, a later
stratified permutation can check those confounds. It should not enlarge the
first minimal experiment unless the basic result requires it.

### 12.3 Degree-preserving graph rewire

Randomize adjacency while preserving node degrees as closely as possible. For
a typed directed relation, preserve source/target types and preferably source
out-degree and target in-degree.

Question:

> Does the real neighborhood arrangement matter beyond activity volume, hubs,
> and the degree sequence?

A fully random Erdős–Rényi graph is too easy. It destroys the very hub
structure most likely to imitate a graph result.

### 12.4 GraphSAGE random initialization

Compare trained GraphSAGE with its random-initialized encoder under the same
pooling and scorer.

Question:

> Did the unsupervised training objective add useful organization beyond random
> relational feature mixing?

If trained and random match, do not claim learned encoder value.

### 12.5 Degree, component, identity, and session-size controls

Check correlations and performance strata for:

- typed degree;
- component membership/size;
- host and user identity;
- absolute time;
- session row count;
- ubiquitous entities.

Question:

> Is the apparent result a shortcut rather than the intended behavioral or
> topological organization?

### 12.6 Multiple comparisons

If several feature hypotheses, representations, filters, and seeds are examined
on development labels:

- record how many were tested;
- predeclare the selection rule where possible;
- run the required null for every candidate eligible to win;
- freeze the final choice;
- evaluate holdout once.

Rewiring only the final winner does not undo arbitrary searching over many
label-visible candidates.

---

## 13. What amplification actually means

Amplification is not “making scores numerically larger.” It means:

> A frozen label-free graph transformation improves operational triage on the
> real graph more than the same transformation improves triage on an
> appropriate rewired graph.

For metric \(M\):

\[
\Delta M_{\text{real}}
=
M(H(P_{\text{real}})s)-M(s),
\]

\[
\Delta M_{\text{rewired}}
=
M(H(P_{\text{rewired}})s)-M(s),
\]

and:

\[
\text{topology-specific gain}
=
\Delta M_{\text{real}}-\Delta M_{\text{rewired}}.
\]

### 13.1 Match the operation to the regime

| Diagnosed regime | Candidate action | Why |
|---|---|---|
| smooth/shared | shallow support or restart diffusion | nearby evidence reinforces the seed |
| contrastive | residual/high-pass ranking | neighbor disagreement is the evidence |
| intermediate scale | \(Ps-P^2s\) | one-hop support differs from wider context |
| structural role | role-based retrieval/source analysis | direct propagation is not the right mechanism |
| no non-null organization | do not amplify | graph transformation lacks justification |

### 13.2 Conservative restart diffusion

Using the column-signal convention:

\[
s^{(t+1)}
=
\alpha s^{(0)}
+
(1-\alpha)Ps^{(t)}.
\]

Restart retains intrinsic evidence while allowing bounded neighborhood support.
Use a small frozen number of iterations or a declared convergence rule.

### 13.3 Over-smoothing

Repeated propagation can make scores or embeddings nearly identical.

Monitor:

- score variance;
- mean pairwise similarity;
- rank correlation with the original score;
- top-\(K\) churn;
- degree-score correlation;
- fraction of score mass on hubs;
- triage metrics;
- corresponding rewired-graph behavior.

If variance collapses without a topology-specific triage gain, the method
smoothed the score; it did not amplify useful signal.

### 13.4 A valid negative outcome

If no operation beats its rewire:

> The representation localized evidence, but no topology-specific amplification
> was demonstrated under the frozen operator.

That is a complete, defensible research result.

---

## 14. Traceable evidence and explanation

### 14.1 Hop contribution

For:

\[
H(P)s=\sum_{k=0}^{K}a_kP^ks,
\]

the contribution at hop \(k\) is:

\[
C_{i,k}=a_k(P^ks)_i.
\]

This explains which radius changed session \(i\)'s score.

### 14.2 Source-session contribution

\[
(P^ks)_i=\sum_j(P^k)_{ij}s_j.
\]

Therefore:

\[
C_{i\leftarrow j,k}=a_k(P^k)_{ij}s_j.
\]

Report top positive and negative contributors. Neighbors can suppress a score
as well as increase it.

### 14.3 Edge-energy contribution

\[
e_{ij}=w_{ij}(x_i-x_j)^2.
\]

These values identify the edges across which a signal changes most.

### 14.4 Removal faithfulness

For reported support:

1. remove or mask it;
2. recompute the end-to-end score;
3. measure score and rank change;
4. compare with a size-, relation-, and degree-matched random removal;
5. repeat across seeds or small perturbations.

**Why:** An attractive neighbor or path is not an explanation unless it
materially affects the final score.

### 14.5 Association is not causality

Use:

> These sessions or typed relations supported the model score.

Do not use:

> This is the attack path.

A matrix power counts weighted walks, potentially including repeated nodes and
hubs. A shared-file path is contextual association, not proof of transmission.
Temporal and directional validation are required before even describing a
candidate provenance path.

---

## 15. The exact research workflow

### Stage 0 — Retain representation artifacts

For every successful method retain internally:

```text
method_key
method family
hypothesis
seed
ordered session_ids
matrix X
dimension_names, if meaningful
representation_type
scaling/normalization
source feature columns
graph configuration
```

Do not put large matrices into the ordinary dashboard JSON by default. Use an
internal artifact bundle or a compact NPZ/Parquet artifact plus a manifest.

**Why:** Scores and UMAP coordinates are insufficient for signal analysis and
feature localization.

### Stage 1 — Choose one controlled starting representation

Start with one deterministic, named-feature representation—normally one raw
feature hypothesis or M1.

**Why:** Named dimensions make it possible to verify the math and understand
local residuals before handling latent embeddings.

### Stage 2 — Build and audit one frozen session graph

Use the original \(X\), \(k=15\), declared symmetrization, declared weights, and
explicit isolate policy. Record the graph manifest before reading filter
metrics.

### Stage 3 — Compute the four fixed channels

Compute:

```text
s
P @ s
s - P @ s
P @ s - P @ P @ s
```

Also compute \(X-PX\) for named feature explanations.

### Stage 4 — Evaluate organization and controls

Report:

- AP and Recall@100 for frozen deployable channels;
- representation diagnostics;
- score and label variation;
- label-permutation results;
- degree-preserving-rewire results;
- degree/session-size correlations;
- exact seed and candidate counts.

### Stage 5 — Run one source analysis

Use the method-specific rules from Section 9. Do not force latent dimensions
into semantic feature explanations.

### Stage 6 — Select one amplifier or decline

Choose based on the diagnosed regime, not because it wins an unrestricted
filter search. Apply the exact same transformation to real and rewired graphs.

### Stage 7 — Freeze and evaluate holdout

Freeze:

- session rules;
- representation and feature hypothesis;
- graph rule and \(k\);
- operator;
- filter;
- scorer;
- seeds;
- metrics;
- selection rule.

Evaluate holdout once. Do not revise the method after revealing holdout labels.

### Stage 8 — Add the analyst UI

Only after the research artifact is trustworthy, expose:

- intrinsic score;
- neighbor support;
- signed and absolute residual;
- scale difference;
- final amplified score, if supported;
- contributing neighbors;
- named feature residuals when meaningful;
- demo labels behind the existing toggle.

UMAP remains a visualization layer.

---

## 16. Minimal implementation sketch

```python
def normalized_transition(W):
    degree = np.asarray(W.sum(axis=1)).ravel()
    # Explicit isolate handling is required here.
    ...
    return P


def basic_signal_channels(P, score):
    p1 = P @ score
    p2 = P @ p1
    return {
        "intrinsic": score.copy(),
        "neighbor_support": p1,
        "local_contrast": score - p1,
        "local_contrast_magnitude": np.abs(score - p1),
        "scale_difference": p1 - p2,
    }


def named_feature_residuals(P, X):
    return X - P @ X
```

The functions are easy. The research contribution comes from:

- defining the graph and signal correctly;
- preserving alignment;
- freezing choices;
- selecting the correct controls;
- interpreting each output within its assumptions.

---

## 17. Claims you can and cannot make

| Tempting claim | Defensible wording |
|---|---|
| The graph contains malicious signal. | The frozen malicious-session indicator is organized non-randomly on this declared graph/operator relative to matched nulls. |
| We amplified maliciousness without labels. | A frozen graph filter improved a label-free score; labels were used only for development selection and evaluation. |
| High frequency means malicious. | High-frequency energy indicates disagreement with this graph's neighbor model. |
| Low frequency reveals a campaign. | The evaluated sessions form a locally coherent region under this graph/operator. |
| This is the attack path. | This typed support structure materially affected the model score under removal testing. |
| GraphSAGE learned the signal. | Trained GraphSAGE improved over its random-initialization control under the shared scorer. |
| The method is dataset agnostic. | The procedure ports through schema mapping and per-dataset label-free graph normalization. |
| UMAP shows the signal. | UMAP visualizes the frozen representation; quantitative analysis uses its original dimensions. |

---

## 18. What is essential now and what is deferred

### Essential now

- canonical session alignment;
- original \(X_m\), \(s_m\), and dimension metadata;
- a declared session kNN graph;
- \(P\), \(I-P\), and the four fixed channels;
- AP, Recall@100, reviews-to-first, and prevalence;
- representation diagnostics kept separate from triage;
- label permutation;
- degree-preserving graph rewire;
- GraphSAGE trained-versus-random control;
- degree, component, session-size, and coverage checks;
- one method-appropriate source analysis;
- one matched amplifier or a recorded decline;
- development/holdout freeze.

### Learn conceptually, implement only if needed

- Laplacian eigendecomposition;
- normalized spectral energy bands;
- conductance;
- personalized PageRank/restart equilibrium;
- relation-specific operators and short typed meta-paths;
- deletion faithfulness.

### Explicitly defer

- spectral graph wavelets;
- Slepians;
- Chebyshev approximations;
- diffusion wavelets;
- learned graph construction;
- learned filter ensembles;
- exhaustive metapath or relation searches;
- SHAP over latent embeddings;
- causal attack-path reconstruction;
- large families of nulls and spectral tests.

Knowing why these exist is useful. Implementing them before the basic signal
audit succeeds would enlarge scope without strengthening the minimal claim.

---

## 19. Oral-defense questions

### What is the graph signal in AutoSignal?

Usually one method's label-free session anomaly score \(s\). Individual named
feature columns are also graph signals. The malicious indicator \(y\) is only
an evaluation signal.

### Why is an embedding not the same thing as a graph signal?

An embedding is a multichannel representation. Each coordinate can be treated
mathematically as a graph signal, but latent coordinates usually lack stable
individual semantics.

### Why use a session graph first?

Sessions are the fixed review unit, and representation-neighbor edges have a
clear similarity interpretation. This avoids mixing process/file signal
domains during the first GSP experiment.

### Why use \(P=D^{-1}W\) rather than \(W\)?

\(P\) computes a neighbor average and reduces raw degree bias. \(W\) computes a
sum, so hubs can receive or emit larger support simply because they have more
edges.

### What does \(s-Ps\) mean?

It is signed disagreement between intrinsic evidence and the neighborhood's
prediction. Positive values are more suspicious than their neighbors;
negative values have more suspicious neighbors than their own score suggests.

### Why retain absolute residual too?

The signed residual preserves direction; the absolute residual measures local
surprise regardless of direction. They answer different questions.

### What does \(Ps-P^2s\) test?

Whether immediate-neighborhood support differs from broader two-hop context.
It is a small, fixed intermediate-scale probe.

### Why not smooth every score?

Smoothing assumes useful evidence is locally shared. If malicious behavior is
contrastive or role based, smoothing can erase it.

### Why is label smoothness not a detector?

It describes organization of known labels after the graph is frozen. It does
not provide a label-free score for unseen telemetry.

### Why can good malicious-neighbor purity coexist with poor AP?

Malicious sessions can form a compact group that a point-anomaly scorer does
not regard as isolated. The geometry supports retrieval, but the scoring
direction does not support discovery.

### What does a label shuffle test?

Whether observed label organization exceeds random session-level placement on
the fixed graph.

### What does a degree-preserving rewire test?

Whether specific adjacency matters beyond degrees, activity volume, and hub
structure.

### What is topology-specific gain?

The score improvement on the real graph minus the improvement from the same
operation on a degree-preserving rewired graph.

### Why compare trained and random GraphSAGE?

To determine whether training added useful organization beyond random
relation-aware feature mixing.

### Why not analyze UMAP?

UMAP is a lossy visualization projection. Scientific distances and filters
must use the original representation.

### What counts as a faithful explanation?

Reported support should materially change the final score or rank when
removed, more than matched random support removal.

### What if no amplifier succeeds?

Report localization without amplification. That is a valid answer to the
research question.

---

## 20. Study order

### Pass 1 — Be able to explain the experiment

Learn:

1. \(X_m\), \(s_m\), \(G_m\), and \(y\);
2. native relation graph versus session-similarity graph;
3. \(W\), \(D\), \(P\), and \(L\);
4. the four fixed channels;
5. representation diagnostics versus triage metrics;
6. label shuffle versus degree-preserving rewire;
7. topology-specific gain.

Stop when you can explain the full experiment without equations.

### Pass 2 — Be able to derive and implement it

Learn:

1. row-normalized neighbor averaging;
2. residual and scale-difference calculations;
3. Dirichlet and normalized energy;
4. isolate handling;
5. named-feature residuals;
6. contribution decomposition;
7. strict alignment assertions.

Stop when you can compute the four-node example by hand and implement the
minimal functions.

### Pass 3 — Be able to defend the claims

Learn:

1. smooth, contrastive, intermediate-scale, and role-based regimes;
2. graph/score coupling;
3. hub and identity shortcuts;
4. multiple comparisons and development/holdout separation;
5. over-smoothing;
6. explanation faithfulness;
7. association-versus-causality wording.

Stop when you can explain what every possible positive or negative result
would mean.

### Pass 4 — Optional depth

Only then study spectral bands, conductance, restart equilibrium,
relation-specific operators, wavelets, or active analyst steering.

---

## 21. Compact glossary

| Term | AutoSignal meaning |
|---|---|
| Canonical session | fixed analyst review unit shared by every method |
| Representation | one high-dimensional vector per session |
| Graph signal | one scalar per aligned graph node |
| Operator | matrix defining how neighbor information is compared or propagated |
| Smoothness | neighboring signal values tend to agree |
| Homophily | connected units tend to share an attribute/label |
| Heterophily | useful edges often connect different values or labels |
| Structural equivalence | similar graph roles without direct proximity |
| Local residual | value minus its neighbor prediction |
| Dirichlet energy | total weighted disagreement across graph edges |
| Low graph frequency | slowly varying under a declared graph/operator |
| High graph frequency | sharply varying under that graph/operator |
| Filter | declared transformation built from graph operators |
| Diffusion | propagation of signal over multiple graph steps |
| Restart | repeated retention of original evidence during diffusion |
| Over-smoothing | propagation collapses distinctions without useful gain |
| Null model | randomized object preserving nuisance structure |
| Rewire | graph randomization that destroys specific adjacency |
| Source analysis | method-appropriate account of where evidence originates |
| Faithfulness | reported support changes the end-to-end output when removed |
| Amplification | controlled improvement of triage utility, not score magnitude |
| Topology-specific gain | real-graph gain minus matched-null gain |

---

## 22. Source map

Read these project notes in this order:

1. [MASTER_PLAN.md](MASTER_PLAN.md), Sections 1 and 3–7  
   The bounded thesis, label boundary, representation comparison, localization
   levels, one-amplifier rule, metrics, and controls.

2. [Ortega GSP Project Study Notes](Books/Ortega_GSP_Project_Study_Notes.md),
   Sections 1–4, 11–14, 16–20, and 22  
   Graph signals, operators, filters, graph frequency, signal regimes,
   amplification decisions, contributions, nulls, and implementation.

3. [Graph Representation Learning Project Study Notes](Books/GRL_Book_Project_Study_Notes.md),
   Sections 1.6, 2, 7–8, and 10–13  
   Homophily/heterophily/role distinctions, degree confounding, message
   passing, nulls, representation diagnostics, and method-specific controls.

4. [Networks, Crowds, and Markets Project Study Notes](Books/Networks_Crowds_Markets_Project_Study_Notes.md),
   Sections 1–4, 7, and 13–18  
   Graph semantics, coverage, affiliation projections, hubs, shortcut gates,
   structural nulls, operational metrics, and cautious tracing.

5. [Constrained Research Contract](CONSTRAINED_RESEARCH_CONTRACT.md)  
   Why valid advanced ideas remain deferred unless they replace current work.

---

## Final takeaway

You should be able to defend this sentence:

> AutoSignal first freezes label-free representations and anomaly scores on a
> common session population. It then constructs a declared session graph,
> diagnoses whether score evidence is intrinsic, neighborhood-supported,
> contrastive, or intermediate-scale, and compares that organization with
> session-label permutations and degree-preserving graph rewires. A single
> regime-matched graph operation is retained only when its triage gain exceeds
> the corresponding null behavior. Explanations are representation-specific,
> and labels remain outside graph construction and scoring.

If you understand every clause in that paragraph—and why it is there—you
understand the essential signal-analysis contribution.
