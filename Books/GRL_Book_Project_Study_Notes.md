# Graph Representation Learning: Project-Focused Study Notes

Source: William L. Hamilton, *Graph Representation Learning* (2020), pre-publication draft in [`GRL_Book.pdf`](./GRL_Book.pdf).

These notes extract what is useful for the cyber graph-triage project. They are not a chapter-by-chapter paraphrase of the whole book. The emphasis is on graph construction, unsupervised representation learning, graph signal localization, signal amplification, evaluation, interpretability, and cross-dataset claims.

## Citation convention

The PDF has eight pages of front matter. Printed book page 1 is PDF page 9. References below therefore use both forms, for example:

> (book p. 49; PDF p. 57)

When an equation is central, its equation number from the book is also included.

## Executive conclusions

The book supports the project's direction, but it sharpens the claim considerably.

1. **The graph is a hypothesis, not a neutral container.** Node types, edge types, direction, weights, temporal rules, and graph boundaries determine which relationships a method can use. A graph method can only find signal that the chosen graph makes expressible.

2. **An embedding preserves its training objective, not "maliciousness" in general.** An adjacency-reconstruction embedding preserves adjacency; node2vec preserves short-walk co-occurrence; a relational decoder preserves typed relations; a GNN trained with a corruption objective preserves whatever distinguishes the real graph from its corruption. Whether any of these geometries contain malicious signal is an empirical diagnostic question (book pp. 30-34; PDF pp. 38-42).

3. **There are at least three distinct graph-signal regimes.** The book distinguishes homophily, structural equivalence, and heterophily (book p. 5; PDF p. 13). Malicious sessions might be directly connected, occupy similar roles without sharing neighbors, or connect mainly to benign infrastructure. A single low-pass message-passing method does not test all three.

4. **The best three-method comparison is a comparison of hypotheses, not three similar GNN architectures.** A defensible core set is:

   - typed structural statistics;
   - short-walk proximity with node2vec;
   - relational message passing with GraphSAGE/RGCN-style aggregation.

5. **The current link-prediction GraphSAGE is a useful baseline, not a guaranteed winner.** Hamilton reports that neighborhood-reconstruction pretraining sometimes provides little advantage for GNNs because message passing already encodes neighborhood information. Corruption/mutual-information objectives such as DGI had more positive evidence in the cited work (book pp. 71-72; PDF pp. 79-80). This motivates an objective ablation rather than an assumption.

6. **Direction and relation semantics matter in this graph.** A symmetric dot-product decoder cannot faithfully model directional relations such as parent-to-child. Negative samples should respect node types, avoid known positives, and corrupt both heads and tails when direction matters (book pp. 40-45; PDF pp. 48-53).

7. **Graph signal processing gives a precise meaning to "signal amplification."** Multiplication by adjacency propagates a node signal; multiplication by the Laplacian measures neighbor differences; repeated normalized message passing behaves like low-pass filtering. This is useful when the relevant signal is smooth, but it can erase local or heterophilous signal through over-smoothing (book pp. 78-87; PDF pp. 86-95).

8. **Deeper is not automatically better.** A K-layer message-passing GNN uses K-hop information, but repeated aggregation can converge toward stationary/random-walk structure. Skip connections, gated updates, Jumping Knowledge, or personalized propagation preserve local information better than blindly adding layers (book pp. 58-62; PDF pp. 66-70).

9. **Attention can identify learned influence weights, but it is not automatically an explanation.** The book defines attention as neighbor weighting during aggregation (book pp. 56-58; PDF pp. 64-66). Treating those weights as causal attack-path evidence would be a project claim requiring separate validation.

10. **Degree is a pervasive confounder.** Hubs generate large overlap, path, centrality, and propagation values even under benign structure. The book repeatedly motivates degree normalization and configuration-model comparisons. Signal claims should survive degree-only baselines and degree-preserving rewires (book pp. 17-20; PDF pp. 25-28).

11. **"Dataset agnostic" must be decomposed into testable meanings.** Shallow embeddings are transductive and cannot embed unseen nodes without retraining (book p. 37; PDF p. 45). An inductive GNN can embed unseen nodes when features and relation schema remain compatible, but this does not prove zero-shot cross-dataset parameter transfer. The current defensible target is a label-free procedure that can be refit across datasets with frozen rules.

12. **Null models are part of signal localization, not optional decoration.** Erdős-Rényi, stochastic block, preferential-attachment, and configuration-style controls ask whether observed structure is more surprising than density, community structure, or degree alone would predict (book pp. 103-107; PDF pp. 111-115).

The thesis-level idea that emerges is:

> Given a heterogeneous telemetry graph, identify whether task-relevant signal is expressed as local structure, proximity, typed relations, graph-smooth communities, or repeated structural roles; localize the relations and bounded paths responsible; then apply the amplification mechanism appropriate to that signal regime and return both a triage ranking and its supporting subgraph.

The book gives the representation-learning foundation for that contribution. It does not itself provide the cyber-specific anomaly score, path explanation system, agentic layer, or proof of cross-dataset generalization.

## Reading map and relevance

| Section | Printed pages | PDF pages | Relevance to this project |
|---|---:|---:|---|
| Preface and Chapter 1 | vi, 1-8 | 6, 9-16 | Graph definitions, heterogeneous relations, task levels, homophily/heterophily |
| Chapter 2 | 9-27 | 17-35 | Essential classical baselines, degree controls, paths, PPR, Laplacians, spectral clustering |
| Chapter 3 | 29-37 | 37-45 | Essential encoder-decoder lens, node2vec, spectral connection, transductive limitation |
| Chapter 4 | 38-45 | 46-53 | Essential for relation-aware decoders, direction, negative sampling, composition |
| Chapter 5 | 47-67 | 55-75 | Highest priority: message passing, normalization, attention, skips, relational GNNs, pooling |
| Chapter 6 | 68-74 | 76-82 | Highest priority: objectives, inductive/transductive distinction, DGI, sampling, regularization |
| Chapter 7.1 | 75-88 | 83-96 | Highest priority: graph signals, filters, Laplacian frequency, over-smoothing |
| Chapter 7.2 | 88-92 | 96-100 | Useful conceptual view of GNNs as learned dependency inference |
| Chapter 7.3 | 92-101 | 100-109 | Essential limits: WL expressivity, motif/cycle blindness, higher-order cost |
| Chapter 8 | 103-107 | 111-115 | Selective but valuable: synthetic controls and graph null models |
| Chapter 9 | 108-122 | 116-130 | Mostly out of scope; evaluation-by-graph-statistics is useful |
| Conclusion | 123-124 | 131-132 | Important: latent graph inference and message-passing bottlenecks |

If reading time is limited, prioritize PDF pp. 9-16, 17-35, 37-53, 55-82, 83-96, 100-105, 111-115, and 131-132.

## The research pipeline implied by the book

```text
telemetry
   |
   +--> one frozen session table ------------------------+
   |                                                     |
   +--> heterogeneous graph schema                       |
          |                                              |
          +--> structural statistics                     |
          +--> random-walk representation                |
          +--> relational message-passing representation |
                    |                                    |
                    +--> fixed session pooling <---------+
                              |
                              +--> one common triage scorer
                              +--> label-aware diagnostics
                              +--> relation/path/null ablations
                                           |
                                           +--> signal regime
                                                   |
                                                   +--> amplification
                                                   +--> supporting subgraph
                                                   +--> analyst ranking
```

The central scientific separation is:

```python
graph, features = build_representation(telemetry, frozen_config)
embeddings = graph_method(graph, features)       # no malicious labels
scores = triage_score(embeddings)                # no malicious labels
metrics = evaluate(scores, hidden_labels)        # labels enter here
diagnostics = diagnose(embeddings, graph, hidden_labels)
```

The label-aware diagnostics can tell us where known malicious activity lies in a fixed representation. They do not become deployable unsupervised scores merely because they return numbers.

---

# 1. Chapter 1: deciding what problem the graph solves

## 1.1 Graphs prioritize relations

Hamilton's core motivation is that graphs model relationships rather than treating datapoints as independent objects (book pp. 1-2; PDF pp. 9-10). For this project, the graph must add information that the raw session statistics do not already encode.

That leads to a useful decomposition:

| View | Question it tests |
|---|---|
| Raw session features | Is malicious behavior unusual in aggregate telemetry? |
| Graph node features with shuffled topology | Can a graph model repackage attributes successfully without real relations? |
| Topology only | Does relational structure contain signal without the raw attributes? |
| Topology plus features | Do relations contextualize otherwise ambiguous attributes? |
| Typed topology | Do particular cyber relation semantics matter? |

Without this decomposition, a "graph win" could actually be a feature win, a degree/volume shortcut, or an identity shortcut.

## 1.2 Heterogeneous and multi-relational are the right abstractions

A multi-relational graph has edge tuples \((u, \tau, v)\), conceptually with one adjacency matrix per relation. A heterogeneous graph also has typed node sets and constraints on valid source and destination types (book p. 3; PDF p. 11).

The current process/file graph is therefore both heterogeneous and multi-relational:

| Relation | Source type | Target type | Key property |
|---|---|---|---|
| `parent_child` | process | process | directed, generally asymmetric |
| `touches` | process | file | directed and type constrained |
| `touched_by` | file | process | explicit inverse of `touches` |

Collapsing this graph with `to_homogeneous()` is reasonable for a node2vec baseline, but it intentionally discards relation identity unless relation information is reintroduced. It should be described as a lossy proximity control, not the final relational method.

## 1.3 Node and edge features are still part of graph learning

Hamilton represents node attributes with a feature matrix \(X\) and notes that heterogeneous node types normally have distinct feature spaces (book p. 3; PDF p. 11). The useful ablation is therefore not "features or graph" as a single binary choice. It is:

- node-feature-only;
- topology-only;
- topology plus features;
- typed topology versus collapsed topology.

This is the cleanest way to find whether the signal comes from attributes, structure, or their interaction.

## 1.4 Task level must match the evaluation unit

The book distinguishes node classification, relation prediction, community detection, and graph-level prediction (book pp. 4-8; PDF pp. 12-16).

The project's evaluation unit is a fixed session. That creates two valid formulations:

- If sessions are explicit nodes, triage is session-node representation and ranking.
- If sessions are bounded sets/subgraphs of process nodes, triage is subgraph pooling followed by ranking.

The current design follows the second form: learn process embeddings and pool them into the same frozen sessions used by the raw baseline. This is defensible and preserves a fair review unit.

Relation prediction is only the self-supervised training task. Good link reconstruction is not itself evidence of good session triage. Community detection similarly finds dense structural groups, not malicious groups by definition.

## 1.5 Graph observations are not i.i.d.

Graph nodes are dependent because edges explicitly connect them. Hamilton emphasizes that standard i.i.d. assumptions break in node-classification settings (book pp. 5-6; PDF pp. 13-14).

Cyber-specific implications include:

- random session splits can leak shared hosts, users, binaries, and infrastructure;
- a transductive GNN can use test-node topology without using test labels;
- future edges can leak information into earlier predictions if the graph is not time-bounded;
- highly correlated malicious sessions must not be treated as independent samples for significance claims.

The book establishes the non-i.i.d. issue; host-disjoint and chronological controls are the project-specific response.

## 1.6 Three different signal regimes

Hamilton explicitly identifies (book p. 5; PDF p. 13):

- **Homophily:** connected nodes share attributes or labels.
- **Structural equivalence:** nodes with similar local structures share attributes even if they are not directly connected.
- **Heterophily:** connected nodes preferentially differ.

This distinction should govern method selection.

| Observed regime | What it might mean here | Suitable methods |
|---|---|---|
| Homophily | malicious sessions share artifacts or occur in connected pockets | spectral methods, PPR, low-pass message passing |
| Structural equivalence | attacks repeat process/file patterns on separate hosts | graph statistics, role embeddings, motif/WL features |
| Heterophily | malicious processes attach mostly to benign/common infrastructure | relation-specific models, residual/high-pass views, boundary features |

A failed low-pass GNN does not prove the graph lacks signal; it can mean that the signal is role-based or heterophilous.

---

# 2. Chapter 2: traditional graph methods we actually need

## 2.1 Degree is both a feature and a confounder

Degree is one of the most basic and often most informative graph statistics. Directed and weighted graphs permit separate in-degree, out-degree, and weighted-degree definitions (book p. 11; PDF p. 19).

At minimum, an interpretable graph-statistics baseline should compute, per node and then aggregate per session:

- total degree;
- in-degree and out-degree;
- degree by relation;
- unique neighbors by node type;
- count and proportion of low-degree/rare neighbors;
- component size and local ego-graph size.

Degree also has to be a negative control. Many supposedly sophisticated scores rise simply because a process touches many files or because a file is ubiquitous.

## 2.2 Centrality means structural importance, not maliciousness

Hamilton covers eigenvector centrality and briefly notes betweenness and closeness (book pp. 11-12; PDF pp. 19-20).

- Eigenvector/PageRank-like centrality highlights nodes connected to other important nodes.
- Betweenness highlights bridges or chokepoints on shortest paths.
- Closeness highlights nodes with short paths to much of the graph.

These can support analyst-facing descriptions such as "this process bridges otherwise separated activity," but no centrality definition says "malicious." High values frequently identify common infrastructure.

## 2.3 Clustering, ego graphs, motifs, and graphlets

The local clustering coefficient measures closed triangles in a node's ego graph. Hamilton generalizes this idea to counting arbitrary motifs and graphlets (book p. 13; PDF p. 21).

Typed cyber motifs are a natural extension:

- one process touching many rare files;
- a parent-child chain followed by file access;
- multiple processes converging on the same low-degree file;
- repeated process-file-process wedges;
- a bounded sequence of typed relations repeated across hosts.

Motif counts are valuable because they are inherently traceable. Their limitation is combinatorial cost and the risk of encoding activity volume instead of meaningful structure.

## 2.4 Bag-of-nodes and WL features

A simple graph-level representation can aggregate node statistics into histograms or summaries, but this loses global structure (book p. 14; PDF p. 22). This is nevertheless an excellent first graph baseline because it is transparent and cheap.

The Weisfeiler-Lehman procedure iteratively aggregates the multiset of neighbor labels so that a node's label summarizes its K-hop neighborhood; histograms of these labels form graph representations (book pp. 14-15; PDF pp. 22-23).

For session subgraphs, valid initial labels include node type, relation-aware degree bucket, and non-label telemetry categories. Malicious ground truth must not be used as an initial WL label in an unsupervised method.

## 2.5 Rare shared neighbors are more informative than hubs

Common-neighbor, Jaccard, Sorensen, and Salton scores quantify local overlap. Resource Allocation and Adamic-Adar upweight low-degree shared neighbors because a rare shared neighbor carries more information than a ubiquitous one (book pp. 16-18; PDF pp. 24-26).

This directly supports the project's rare-file idea. Sharing a ubiquitous system binary should contribute less than sharing a rare file. Useful session-to-session similarities include:

- relation-specific Jaccard overlap;
- Resource Allocation overlap;
- Adamic-Adar overlap;
- rare-neighbor counts after explicit degree filtering.

The rare-neighbor threshold remains a dataset-fit statistic and belongs in the manifest. Rare does not mean malicious.

## 2.6 Path-based similarity and seeded propagation

Katz similarity sums paths of all lengths while geometrically downweighting longer paths (book pp. 18-19; PDF pp. 26-27):

\[
S_{Katz}[u,v] = \sum_{i=1}^{\infty}\beta^i A^i[u,v].
\]

Katz is degree biased. Hamilton's discussion of the Leicht-Holme-Newman similarity normalizes path counts by their expectation under a random graph with the same degree sequence (book pp. 19-20; PDF pp. 27-28). That gives a direct methodological lesson:

> A path concentration is interesting only if it exceeds what degree alone would make likely.

Personalized PageRank repeatedly restarts at an anchor and measures anchor-specific reachability (book p. 21; PDF p. 29). It is especially well aligned with the later amplification phase:

1. begin with one or more analyst-confirmed anchors;
2. propagate through the graph with restart;
3. rank candidates by reachability;
4. expose the high-contribution local subgraph and typed paths.

Because the anchor is supervision, PPR belongs in few-shot/steering evaluation, not the strictly unsupervised v0 baseline.

## 2.7 Laplacian energy is a direct signal-localization diagnostic

For the unnormalized Laplacian \(L=D-A\), Hamilton gives (book p. 22; PDF p. 30, Eq. 2.27-2.28):

\[
x^T L x = \sum_{(u,v)\in E}(x_u-x_v)^2.
\]

This measures how much a signal changes across edges. Applied after graph construction:

- set \(x\) to a feature column to see whether that feature is graph smooth;
- set \(x\) to a learned score to see whether the method imposed smoothness;
- set \(x\) to the malicious indicator only as an evaluation diagnostic.

Low malicious-label energy relative to shuffled labels suggests homophily. High energy suggests boundary-like or heterophilous signal. Compute it per relation type and compare with degree/host-aware permutations before interpreting it.

For the heterogeneous graph, direct label energy is easiest on a session projection or on process nodes carrying inherited session labels. File nodes are unlabeled, so a process-file-process metapath view may be more meaningful than assigning them artificial labels.

## 2.8 Spectral clustering tests a specific hypothesis

The second-smallest Laplacian eigenvector relaxes a balanced graph-cut problem; multiple low-frequency eigenvectors followed by k-means generalize this to multiple clusters (book pp. 24-27; PDF pp. 32-35).

Spectral clustering therefore asks:

> Does malicious signal align with smooth, community-scale, low-frequency structure?

It does not test structural equivalence across disconnected areas, typed relation composition, or high-frequency boundary signal. A malicious-enriched cluster is evidence; an unenriched spectral partition is not proof that the graph has no useful signal.

Normalized Laplacians should be the primary variant in a degree-skewed telemetry graph, with the unnormalized form retained as a sensitivity analysis.

---

# 3. Chapter 3: what an embedding really learns

## 3.1 Encoder, decoder, similarity, and loss

Hamilton's encoder-decoder lens is the most important conceptual tool in Part I (book pp. 30-32; PDF pp. 38-40):

\[
\operatorname{dec}(z_u,z_v) \approx S[u,v].
\]

Every embedding experiment should document four items:

| Item | Question |
|---|---|
| Encoder | What information can produce an embedding? Node ID, features, topology, or all three? |
| Decoder | How are two embeddings compared? Distance, dot product, or relation-specific function? |
| Similarity target | What graph relationship should geometry preserve? Adjacency, paths, walks, or typed edges? |
| Loss | How is disagreement optimized, and how are negatives selected? |

This prevents the common error of treating all graph embeddings as interchangeable.

## 3.2 Matrix factorization and spectral embeddings

Laplacian Eigenmaps preserve graph similarity using embedding distance. Graph Factorization reconstructs adjacency. GraRep uses powers of adjacency, and HOPE can preserve a selected overlap matrix. These can be viewed as low-rank approximations to a chosen node similarity matrix (book pp. 33-34; PDF pp. 41-42).

For this project, deterministic path/proximity matrices can be useful when interpretability matters more than end-to-end learning: the exact similarity being preserved is visible before the embedding step.

## 3.3 DeepWalk and node2vec preserve walk co-occurrence

DeepWalk and node2vec make nodes similar when they co-occur on short random walks. node2vec adds parameters that interpolate between breadth-first-like local exploration and depth-first-like outward exploration (book pp. 34-35; PDF pp. 42-43).

Consequences for the notebook:

- walk length and context window define the path scale being tested;
- the return/in-out biases define a proximity-versus-exploration hypothesis;
- a homogeneous walk ignores relation semantics unless the walk policy is typed;
- multiple seeds are required;
- hyperparameters must be frozen without optimizing on the final labels.

Node2vec is a good basic graph method because it asks a clear question: do short graph walks place malicious sessions near one another?

## 3.4 Proximity and structural role are different

Hamilton notes random-walk variants that encode structural roles instead of neighborhood proximity (book p. 36; PDF p. 44).

- Proximity embedding: "these nodes occur near one another."
- Role embedding: "these nodes have similar local structures."

Cross-host attack repetitions may be role-equivalent without sharing any entity. A later role baseline could therefore be more informative than comparing several nearly identical proximity embeddings.

## 3.5 Random-walk and spectral methods are related

DeepWalk approximately factorizes a function of powers of the random-walk transition matrix, and that matrix can be decomposed through the normalized Laplacian eigensystem (book p. 36; PDF p. 44).

Spectral and random-walk methods are still worth comparing, but the honest interpretation is that they weight related graph structure differently. Agreement between them is not evidence from two completely independent mechanisms.

## 3.6 Shallow embeddings are transductive

Shallow embeddings learn one parameter vector per node, do not share encoder parameters, ignore node features in the encoder, and cannot embed unseen nodes without further optimization (book p. 37; PDF p. 45).

Node2vec can support:

> The same unsupervised procedure can be refit on another dataset.

It cannot by itself support:

> One trained model directly embeds and generalizes to unseen telemetry graphs.

That stronger claim requires an inductive encoder and a compatible feature/relation schema.

---

# 4. Chapter 4: preserving direction and relation meaning

## 4.1 Multi-relational reconstruction

A multi-relational decoder scores \(\operatorname{dec}(z_u,\tau,z_v)\), interpreted as compatibility of a typed edge \((u,\tau,v)\) (book pp. 38-39; PDF pp. 46-47). This matters because the current graph's edge types are not interchangeable.

Most methods in this chapter reconstruct immediate typed relations. They do not automatically learn long attack chains. Typed multi-hop reasoning requires explicit paths, typed walks, relation composition, or a relational message-passing encoder.

## 4.2 Negative sampling is part of the method

Hamilton emphasizes that negative sampling materially affects embedding quality (book pp. 40-41; PDF pp. 48-49). A cyber implementation should:

- corrupt only with schema-valid node types;
- filter triples that are known positives;
- corrupt both source and target when direction matters;
- report the negative distribution and negative-to-positive ratio;
- avoid using temporally impossible negatives as if they were difficult examples;
- keep negative sampling identical when comparing decoders.

Uniformly replacing a file target with any node in a heterogeneous graph creates trivial negatives and teaches node type rather than relation structure.

## 4.3 Decoder capabilities must match the schema

| Decoder | Book-supported property | Project implication |
|---|---|---|
| RESCAL | relation-specific full matrix; expressive but \(O(d^2)\) parameters per relation | feasible with few relations, but statistically heavier |
| TransE | relation as translation; strong simple baseline | useful typed baseline, direction-capable |
| DistMult | tri-linear dot product; symmetric | mismatched as sole decoder for `parent_child` |
| ComplEx | complex embeddings support asymmetric relations | plausible direction-aware decoder |
| RotatE | relations as rotations; supports several relational patterns | plausible typed baseline, more machinery |

See book pp. 42-45; PDF pp. 50-53.

A plain dot product is symmetric. If the link loss uses the same dot product for both \((parent, child)\) and \((child, parent)\), the decoder cannot represent their directional difference even if the encoder saw directed edges.

## 4.4 Inverse and compositional relations

Hamilton compares whether decoders can express symmetry, anti-symmetry, inverse relations, and relation composition (book pp. 44-45; PDF pp. 52-53).

The current schema includes an explicit inverse pair:

```text
process --touches--> file
file --touched_by--> process
```

These are two directions of the same observed event, not two independent pieces of evidence. Model and reporting code should avoid claiming that their coexistence independently confirms a path.

Parent-child chains and process-file-process paths are compositional structures. If they become central to the contribution, evaluate them explicitly rather than assuming one-hop relation reconstruction preserves them.

---

# 5. Chapter 5: message passing as a controlled evidence radius

## 5.1 The generic model

Hamilton defines message passing as (book pp. 48-50; PDF pp. 56-58):

\[
m_{\mathcal N(u)}^{(k)} =
\operatorname{AGGREGATE}^{(k)}
\left(\{h_v^{(k)}:v\in\mathcal N(u)\}\right)
\]

\[
h_u^{(k+1)} =
\operatorname{UPDATE}^{(k)}
\left(h_u^{(k)},m_{\mathcal N(u)}^{(k)}\right),
\qquad h_u^{(0)}=x_u.
\]

After K layers, a node can depend on its K-hop neighborhood. Depth is therefore a hypothesis about evidence radius:

| Representation | Information available in the current graph |
|---|---|
| \(h^{(0)}\) | process/file's own features |
| \(h^{(1)}\) | direct files, parents, and children |
| \(h^{(2)}\) | shared-file process context, grandparents, grandchildren |
| \(h^{(3+)}\) | broader context increasingly exposed to mixing and hubs |

Evaluate every layer rather than only the final one. If malicious neighbor purity improves at one hop and falls at two, that is a useful localization result: the graph contains local signal that deeper propagation washes out.

The K-hop receptive field says where information *could* come from. It does not prove which path determined the output.

## 5.2 Preserve a separate self/root channel

The basic GNN uses separate transformations for the node itself and its neighbors (book p. 51; PDF p. 59):

\[
h_u^{(k)}=\sigma\left(
W_{self}^{(k)}h_u^{(k-1)}+
W_{neigh}^{(k)}\sum_{v\in\mathcal N(u)}h_v^{(k-1)}+b^{(k)}
\right).
\]

Replacing this with self-loops and a single shared aggregation is simpler, but it makes own-node evidence indistinguishable from neighbor evidence and reduces expressivity (book p. 52; PDF p. 60).

For this project, an explicit self channel answers a central localization question:

> Did the representation improve because of the process/session itself, or because graph context was introduced?

That decomposition is worth keeping even if self-loops are also used for stability.

## 5.3 Normalization can erase the signal

Sum aggregation preserves multiplicity but is degree sensitive. Mean and symmetric normalization improve scale stability, especially around hubs, but can make different-size neighborhoods indistinguishable (book pp. 53-54; PDF pp. 61-62).

Telemetry properties that a pure mean can erase include:

- number of files touched;
- repeated accesses;
- number of child processes;
- fan-out and convergence;
- twenty identical-type neighbors versus two.

A good first compromise is:

```text
relation-wise normalized aggregation
+ explicit relation-wise degree/count features
+ a separate root channel
```

Later compare this with relation-wise sums or a concatenated mean-plus-sum aggregator. If repeated telemetry events are collapsed into one graph edge, preserve event count as an edge feature in a later version rather than pretending multiplicity still exists.

## 5.4 Attention is a weighting mechanism, not a causal explanation

Graph attention learns neighbor weights \(\alpha_{u,v}\) and aggregates a weighted sum (book pp. 56-58; PDF pp. 64-66):

\[
m_{\mathcal N(u)}=\sum_{v\in\mathcal N(u)}\alpha_{u,v}h_v.
\]

Attention can help discount ubiquitous, uninformative neighbors and can generate candidate influential edges. It does not by itself justify:

- "this edge caused the alert";
- "this is the attack path";
- "attention weight is the probability of maliciousness";
- comparison of raw weights across differently sized neighborhoods.

The final method scores distances between pooled session embeddings. An attention explanation must therefore survive an end-to-end perturbation: mask the candidate edge or relation, recompute the embedding and kNN score, and report score/rank change.

## 5.5 Over-smoothing is a concrete risk

Hamilton relates normalized message-passing influence to K-step random-walk probabilities. As K grows, influence approaches the walk's stationary distribution and local information disappears (book pp. 58-59; PDF pp. 66-67). Shared files and other hubs can accelerate this mixing.

Useful defenses in the book include:

- concatenation or residual/skip updates (book pp. 59-61; PDF pp. 67-69);
- GRU/LSTM-style gated updates for genuinely long reasoning (book p. 61; PDF p. 69);
- Jumping Knowledge, which combines representations from multiple depths (book pp. 61-62; PDF pp. 69-70).

For the first learned model, a transparent Jumping Knowledge concatenation is preferable to a deep network:

\[
z_u=h_u^{(0)}\oplus h_u^{(1)}\oplus h_u^{(2)}.
\]

This retains local evidence and exposes the scale at which signal appears.

## 5.6 Relation-specific transformations are the textbook fit

RGCN-style aggregation uses a separate transformation \(W_\tau\) per relation, optionally with parameter sharing when the relation vocabulary is large (book pp. 62-63; PDF pp. 70-71).

The current graph has few relations, so separate transforms are straightforward:

- `parent_child`;
- `touches`;
- `touched_by`;
- a separately named reverse-parent relation if one is added.

Forward and reverse relations should not be collapsed merely because they connect the same entities. The useful propagation direction differs.

Continuous edge features can later enter through concatenation or attention (book p. 63; PDF p. 71). Candidate features include event count, access type, relative time, rarity, and temporal span. They should be introduced only after relation-level ablations show a reason to add them.

## 5.7 Session pooling is a possible bottleneck

Hamilton covers mean/sum pooling, attention pooling, and graph coarsening (book pp. 64-66; PDF pp. 72-74). Mean pooling is a reasonable v0 choice, but its meaning is specific:

- mean represents an average process state;
- it discards process count;
- sessions with the same embedding distribution but different sizes can become identical.

Sum retains size but can turn activity volume into the dominant signal. Keep mean as the primary structure-only comparison, report session size separately, and later test `mean + sum + count` only if pooling appears to erase useful structure.

Graph coarsening is unnecessary for v0 and adds training instability. Explicit fixed sessions already provide a meaningful pooling boundary.

## 5.8 Generalized edge-state message passing is future work

The book also describes message passing with hidden states for nodes, edges, and the whole graph (book pp. 66-67; PDF pp. 74-75). Edge states would make path and relation attribution more direct, but they materially expand scope. Treat them as a later traceability architecture, not a prerequisite for the first graph baseline.

---

# 6. Chapter 6: training objectives and practical controls

## 6.1 The loss defines the representation's job

The book organizes common GNN losses around node classification, graph classification, and relation prediction (book pp. 68-71; PDF pp. 76-79). This project's unsupervised GNN uses relation/link prediction as a *pretext task* and then applies a separate session anomaly score.

Keep those outcomes separate:

```text
edge reconstruction quality
    != session triage quality
    != maliciousness probability
```

A link objective may learn common relation patterns and degree shortcuts while giving little weight to rare anomalous edges. Its value must be established by downstream triage metrics and representation diagnostics.

## 6.2 Neighborhood reconstruction can be redundant for a GNN

Hamilton reports early evidence that neighborhood-reconstruction pretraining sometimes failed to outperform random initialization, with the proposed explanation that message passing already injects neighborhood information (book p. 71; PDF p. 79).

This does not establish that link-prediction pretraining never works. It establishes a required control:

- trained GraphSAGE versus randomly initialized GraphSAGE;
- real topology versus degree/relation-preserving shuffled topology;
- graph encoder versus feature-only MLP.

If a random encoder performs similarly, the gain may come from architecture-induced smoothing or random projection rather than learned graph structure.

## 6.3 DGI is the book-grounded alternative objective

Deep Graph Infomax contrasts node/graph embeddings from the real graph against embeddings from a corrupted graph and seeks high mutual information between local and global representations (book pp. 71-72; PDF pp. 79-80).

This is a suitable later objective ablation:

```text
same relational encoder
same node features
same sessions and scorer

objective A: typed link reconstruction
objective B: DGI-style real-versus-corrupted graph discrimination
```

The corruption must be difficult and semantically meaningful. An impossible corruption can teach a trivial schema artifact. Relation-preserving edge shuffles and feature shuffles should be documented separately.

## 6.4 Transductive and inductive are not interchangeable

Hamilton distinguishes (book pp. 69-70; PDF pp. 77-78):

- training nodes used in message passing and loss;
- transductive test nodes present in message passing but not the loss;
- inductive test nodes and edges entirely unseen in training.

Under the current per-dataset unsupervised refit policy:

- the code and hyperparameters can be portable;
- the model uses the full unlabeled graph for that dataset;
- parameters are refit for each dataset;
- this is not frozen-encoder transfer.

Identity one-hot features make a GNN transductive and unable to represent unseen nodes (book p. 50; PDF p. 58). Stable node types and behavioral attributes are more compatible with the cross-dataset ambition than `pid_hash`, host IDs, file IDs, or arbitrary node indices.

## 6.5 Sampling can remove the evidence being explained

Full-graph sparse operations are exact but memory intensive. Neighbor sampling enables mini-batches but modifies the observed computation graph and can disconnect relevant evidence (book pp. 72-73; PDF pp. 80-81).

For signal tracing:

- prefer full-batch execution while the graph fits;
- if sampling becomes necessary, seed it and record sampled neighborhoods;
- sample per relation so common edges do not crowd out rare relation types;
- report explanation stability under resampling;
- do not claim a path is absent when it may simply have been unsampled.

## 6.6 Edge dropout doubles as a robustness test

The book covers standard regularization and edge dropout (book pp. 73-74; PDF pp. 81-82). In telemetry, small random edge removal also simulates missing observations. Report whether triage ranks, nearest neighbors, and supporting paths remain stable under modest edge dropout. Extreme instability is an important negative result.

---

# 7. Chapter 7: the mathematical core of signal localization and amplification

## 7.1 A graph filter is a mixture of hop lengths

Hamilton expresses a polynomial graph filter as (book pp. 79-80; PDF pp. 87-88):

\[
Q_h=\alpha_0I+\alpha_1A+\alpha_2A^2+\cdots+\alpha_KA^K.
\]

Applied to node features:

\[
Q_hX=\alpha_0X+\alpha_1AX+\alpha_2A^2X+\cdots+\alpha_KA^KX.
\]

This is a precise model of amplification:

- \(\alpha_0\): keep local evidence;
- \(\alpha_1\): incorporate direct relations;
- \(\alpha_2\): incorporate shared-neighbor/metapath context;
- higher terms: incorporate broader walks.

Entries of \(A^k\) aggregate walks, including backtracking and cycles. They do not identify a unique simple path. A large \(A^k\) contribution should be described as multi-walk structural support unless a specific path is separately extracted.

For typed graphs, a project-specific extension decomposes by relation sequence:

\[
A_{r_k}\cdots A_{r_2}A_{r_1}X.
\]

This exposes hypotheses such as process -> file -> process or parent -> child -> file.

## 7.2 Adjacency propagates; the Laplacian measures difference

Hamilton's graph-signal analogy shows that adjacency multiplication propagates a signal and Laplacian multiplication computes differences between a node and its neighbors (book pp. 78-82; PDF pp. 86-90).

There is no universally correct choice of adjacency, unnormalized Laplacian, or normalized operator. The choice encodes a bias:

| Operator | Main behavior |
|---|---|
| \(A\) | degree-amplified aggregation |
| \(D^{-1}A\) | random-walk/mean propagation |
| \(D^{-1/2}AD^{-1/2}\) | symmetric degree-balanced propagation |
| \(L=D-A\) | neighbor-difference/high-frequency measurement |

Use normalized propagation for numerical stability, but preserve degree explicitly if multiplicity may matter.

## 7.3 Low and high frequencies describe the signal regime

Low-eigenvalue Laplacian modes vary slowly across edges and capture smooth community-scale structure. High-frequency modes vary rapidly across connected nodes (book pp. 82-84; PDF pp. 90-92).

The project's diagnostic question becomes:

```text
Is malicious activity graph-smooth, graph-contrastive, relation-specific,
or role-similar without direct connectivity?
```

- Low-frequency malicious signal favors diffusion, spectral clustering, PPR, and shallow low-pass GNNs.
- High-frequency malicious signal can be erased by smoothing and motivates residual/difference channels such as \(X-\tilde AX\).
- Relation-dependent frequency behavior motivates separate relation operators.
- Role similarity motivates graph-statistics or role embeddings rather than propagation.

The residual/high-pass recommendation is a project inference from the book's signal framework, not a method explicitly supplied by Hamilton.

## 7.4 Over-smoothing is low-pass collapse

Repeated normalized message passing emphasizes low-frequency components and can converge to constant representations within connected components (book pp. 86-87; PDF pp. 94-95). More layers can therefore yield a simpler, less discriminative filter.

This is why depth must be reported as a signal-scale experiment rather than tuned silently.

## 7.5 Deterministic propagation is a serious learned-model control

Hamilton discusses simplified approaches that place a deterministic graph filter between feature transformations, including powers of normalized adjacency and personalized PageRank-style propagation (book pp. 87-88; PDF pp. 95-96):

\[
Z=\operatorname{MLP}_\theta(f(A)\operatorname{MLP}_\phi(X)).
\]

This yields a highly useful control:

```text
fixed propagation operator -> session pooling -> same kNN score
```

It tests whether topology-based smoothing itself creates useful geometry without interleaving several learned message-passing layers. It is also easier to decompose by hop and relation.

## 7.6 The probabilistic view is conceptual, not calibrated uncertainty

The book connects GNN updates to approximate inference in graphical models: node states are updated using own features and neighboring latent-state summaries (book pp. 88-92; PDF pp. 96-100).

This is a helpful interpretation for heterogeneous telemetry: each relation learns how neighboring evidence changes a latent state. It does not make a GNN embedding a posterior maliciousness probability, confidence interval, or calibrated belief. Those require an explicitly defined probabilistic model and calibration.

## 7.7 Standard message passing has WL-level blind spots

Hamilton relates ordinary message-passing GNNs to the 1-dimensional Weisfeiler-Lehman test (book pp. 93-98; PDF pp. 101-106). Under the theorem's assumptions:

- message-passing GNNs are at most as discriminative as 1-WL;
- injective aggregation/update is needed to reach that bound;
- mean and weighted-average aggregation are not injective because they can lose multiset cardinality;
- some cycles and shared-neighbor structures cannot be distinguished.

Potentially lost cyber structure includes:

- repeated same-type neighbors;
- exact fan-out;
- two versus twenty identical events;
- whether two neighbors share another neighbor;
- closed process-file-parent motifs;
- globally different structures with identical local multisets.

GIN-style sum/MLP aggregation reaches the 1-WL bound more closely (book pp. 96-97; PDF pp. 104-105), but greater expressivity does not guarantee better anomaly ranking, robustness, or explanation.

Higher-order k-WL/k-GNN approaches can model node tuples but become combinatorially expensive (book pp. 99-101; PDF pp. 107-109). Explicit typed motifs and metapath counts are likely a better interpretable probe before introducing a higher-order GNN.

## 7.8 Unique IDs are the wrong escape hatch

Unique node IDs can break some structural symmetries, but they also inject identity dependence and undermine permutation/generalization properties. The relational-pooling construction restores invariance by marginalizing permutations, but exact computation is factorial (book pp. 97-99; PDF pp. 105-107).

Do not use unique identifiers to rescue graph performance if the research claim is structural and cross-dataset. If identity is later studied, make it an explicit labeled ablation.

---

# 8. Chapters 8-9 and the conclusion: null models, not graph generation scope

## 8.1 Simple generative models define increasingly strict nulls

Hamilton presents three traditional graph generators (book pp. 103-106; PDF pp. 111-114):

| Null model | Preserves/explains | What a deviation means |
|---|---|---|
| Erdős-Rényi | graph size and expected density | structure exceeds density alone |
| Stochastic block model | coarse community structure | structure exceeds simple block/community organization |
| Preferential attachment | hub-heavy growth and heavy-tailed degree | structure exceeds a generic rich-get-richer hub process |

Chapter 2's configuration-model reasoning adds a more immediately useful control: preserve degree sequence while randomizing connections (book pp. 19-20; PDF pp. 27-28).

For a heterogeneous telemetry graph, the project-specific version should preserve as much nuisance structure as possible:

- source and destination node types;
- relation type;
- direction;
- per-relation source and destination degree when feasible;
- number of nodes and edges;
- session boundaries when the null is meant to test within-session paths.

A fully random graph is too easy a control. A typed degree-preserving rewire asks whether path and neighborhood signal exceeds what hubs and activity volume already explain.

## 8.2 Null models have two roles

Hamilton explicitly identifies synthetic benchmarking and null-model comparison as uses of traditional generators (book p. 107; PDF p. 115).

Here that becomes:

1. **Benchmarking:** construct controlled graphs where signal is known to be homophilous, role-based, or heterophilous and verify that the localization diagnostics identify the correct regime.
2. **Real-data controls:** compare observed purity, path counts, Laplacian energy, and method performance with randomized graphs.

Synthetic tests are especially useful before claiming that a new localization metric measures what its name implies.

## 8.3 Deep graph generation is not needed now

VAEs, GANs, and autoregressive graph generators in Chapter 9 are outside the current contribution. The useful takeaway is its evaluation principle: compare distributions of graph statistics such as degree, graphlets, and spectral features rather than trusting visual similarity (book pp. 120-121; PDF pp. 128-129).

Do not expand scope into learned graph generation unless a later study specifically asks whether synthetic cyber graphs preserve the signal atlas.

## 8.4 The conclusion reinforces two project cautions

First, most representation-learning techniques assume the input graph is already given. Hamilton calls inference of the graph itself a separate problem, latent graph inference (book pp. 123-124; PDF pp. 131-132). Therefore graph construction is part of the method, and cross-dataset portability is conditional on a compatible schema or a documented schema-mapping step.

Second, Hamilton highlights message-passing bottlenecks: WL-bounded expressivity, simple filtering behavior, over-smoothing, tree-shaped computation, difficulty with cycles, and long-range dependencies (book p. 124; PDF p. 132). This supports keeping explicit path/motif diagnostics alongside learned embeddings.

The book is a 2020 snapshot. It provides a strong conceptual foundation, but it should not be treated as a complete survey of methods developed after 2020.

---

# 9. Recommended three-method graph study

The exact headline suite should test three different structural hypotheses.

| Method | Hypothesis | Representation family |
|---|---|---|
| `graph_structural_stats_knn` | malicious sessions have unusual explicit graph roles, counts, or typed motifs | transparent handcrafted topology |
| `node2vec_session_knn` | malicious sessions occupy distinctive short-walk proximity geometry | shallow transductive walk embedding |
| `relational_graphsage_session_knn` | learned typed feature/topology interactions create a better session geometry | inductive-capable relational message passing |

Keep `raw_session_stats_knn` and `random_score` as the graph-free controls. Treat deterministic PPR/filter propagation as an amplification/control method rather than replacing one of the three headline representations.

Why not count spectral embedding, DeepWalk, and node2vec as three independent methods? The book shows that random-walk embeddings and Laplacian spectral methods are mathematically related (book p. 36; PDF p. 44). Why not count GCN, GraphSAGE, and GAT? They are nearby variations within the same message-passing family and test less distinct scientific questions.

## 9.1 Method 1: `graph_structural_stats_knn`

### Hypothesis

Malicious sessions differ in explicit topology: branching, low-degree shared artifacts, component structure, boundary edges, or short typed motifs.

### Fixed evaluation unit

Use the canonical session membership from the raw sessionizer. Build graph features for those sessions; do not create evaluation sessions from graph connected components.

### Candidate features

Session-level counts:

- number of process nodes;
- number of unique retained file nodes touched;
- parent-child edge count;
- process-file edge count;
- process/file ratio;
- number of connected components in the session-induced subgraph;
- largest component fraction;
- internal versus boundary edge counts.

Aggregated node statistics:

- per-relation in/out degree mean, standard deviation, median, maximum, and selected quantiles;
- parent branching factor and chain-depth summaries;
- file-degree summaries;
- sum and mean inverse file degree;
- count of files in predeclared degree bins;
- number of files also touched outside the session;
- approximate betweenness or PPR summaries if computationally feasible.

Typed motifs/metapaths:

- process -> file <- process;
- parent -> child -> file;
- process -> file <- process -> file;
- parent -> child -> file <- process.

Do not use ordinary triangle clustering on the bipartite process-file portion; bipartite graphs have no triangles. Use type-valid wedges, 4-cycles, and metapaths.

### Score

```text
typed structural vector
-> StandardScaler
-> mean Euclidean distance to k=15 nearest sessions
```

This deliberately reuses the raw baseline's scorer so the comparison isolates representation rather than scoring logic.

### Interpretation

- A win means explicit structure is sufficient; a learned encoder may not be necessary.
- A loss to node2vec suggests selected summaries miss higher-order proximity.
- A loss to relational GraphSAGE suggests learned feature/topology interaction matters, provided the GNN also beats its random and shuffled controls.

### Explanation

This method provides the strongest first explanation: feature value, benign reference distribution, standardized deviation, and the graph entities/motifs that generated the feature.

## 9.2 Method 2: `node2vec_session_knn`

### Hypothesis

Short random-walk context places malicious processes/sessions in distinctive graph neighborhoods even when explicit statistics are insufficient.

### Graph treatment

Use a deliberately simple homogeneous graph as a topology-only control:

- process and file nodes both participate;
- process-file connectivity must be traversable in both directions;
- decide explicitly whether parent-child walks are directed or receive a separate reverse edge;
- preserve node offsets/types so only process embeddings are pooled to sessions.

Calling `to_homogeneous()` should be an implementation step after these semantics are decided, not the decision itself.

### Primary configuration

Use one predeclared unbiased configuration as the headline result:

```text
p = 1
q = 1
```

Optionally run one local/BFS-like and one outward/DFS-like sensitivity. Do not search a large grid and report the label-best setting as confirmatory.

### Session representation and score

```text
process node2vec embeddings
-> mean within canonical session
-> kNN distance anomaly score
```

Mean is primary. Sum is a pooling sensitivity because it reintroduces session size.

### Required reporting

- seeds 42, 43, and 44 individually and mean +/- standard deviation;
- rank and nearest-neighbor stability across seeds;
- degree-preserving rewired-graph control;
- collapsed-versus-typed limitation statement;
- no cross-dataset frozen-encoder claim.

## 9.3 Method 3: `relational_graphsage_session_knn`

### Hypothesis

A learned relation-aware encoder can combine process/file features and typed local structure to produce session geometry that contains more triage signal than fixed structural or walk representations.

### Primary architecture

- two message-passing layers;
- separate transformations for every directed relation;
- explicit self/root transform;
- normalized aggregation plus explicit per-relation degree features;
- transparent Jumping Knowledge concatenation \(h^{(0)}\oplus h^{(1)}\oplus h^{(2)}\);
- mean process-to-session pooling;
- three seeds.

If an inverse parent relation is added, name it separately. The explicit `touches`/`touched_by` pair remains one observed relation in two traversal directions.

### Node features

Do not use node IDs, hashes, host/user identity encodings, detector outputs, labels, or absolute timestamps in the primary structural claim.

Useful safe starting features include:

Process nodes:

- constant/type feature;
- relation-specific degree/count statistics;
- a small declared set of non-label behavioral fields in a separate feature-plus-topology experiment.

File nodes:

- constant/type feature;
- global retained-graph degree and inverse degree;
- stable coarse file type if available and defensible.

Run explicit variants:

```text
topology_only_relational_graphsage
feature_only_zero_layer
feature_and_topology_relational_graphsage
```

### Objective

Begin with relation-specific edge reconstruction using type-constrained, filtered negatives and a direction-capable decoder. Evaluate held-out edge reconstruction separately from triage.

### Mandatory controls

- same encoder randomly initialized and untrained;
- zero-layer feature representation;
- real versus feature-shuffled input;
- real versus relation-preserving shuffled graph;
- typed degree-preserving rewired graph;
- one-relation-at-a-time ablations;
- depth 1/2/3;
- mean versus count-preserving aggregation sensitivity;
- layerwise embedding variance and mean cosine similarity.

Do not claim learned graph value unless the trained encoder improves over the identical random encoder. If link reconstruction fails that control, test DGI-style corruption before adding an architecture zoo.

## 9.4 Optional methods, in priority order

1. Deterministic PPR/normalized graph filter as an amplification baseline.
2. Structural-role embedding when repeated cross-host roles appear more plausible than proximity.
3. Relation-aware GIN/sum aggregation when count/multiset loss appears to be the bottleneck.
4. Spectral embedding as a direct low-frequency/community diagnostic.
5. Attention only after relation/hop localization establishes heterogeneous neighbor importance.
6. Higher-order GNNs only after explicit motif probes show information missed by 1-WL-style message passing.

---

# 10. Shared metric and diagnostic suite

## 10.1 Deployable triage metrics

Labels enter only after every score is fixed.

```text
method
seed
average_precision
reviews_to_first_malicious
random_expected_reviews_to_first
found_at_25 / recall_at_25 / precision_at_25
found_at_50 / recall_at_50 / precision_at_50
found_at_100 / recall_at_100 / precision_at_100
found_at_250 / recall_at_250 / precision_at_250
```

Useful derived columns:

\[
AP\ lift = \frac{AP}{malicious\ session\ rate}
\]

\[
first\ hit\ lift =
\frac{(N+1)/(M+1)}{observed\ first\ malicious\ rank}.
\]

Report deterministic methods once. Report stochastic/learned methods per seed and as mean +/- standard deviation. Do not hide seed failures inside a mean.

## 10.2 Representation diagnostics

These use labels after the representation is fixed. They are not deployable anomaly scores.

### `malicious_neighbor_purity_at_15`

Already implemented. Retain:

- mean purity;
- median purity;
- fraction of malicious sessions with any malicious neighbor;
- malicious base rate excluding self;
- enrichment over base rate.

### `malicious_mean_peer_rank`

For each malicious anchor:

1. rank every other session by representation distance;
2. record ranks of all other malicious sessions;
3. normalize ranks by number of candidates;
4. average within anchor and then across anchors.

Lower is better. Also report nearest-malicious-peer rank because the full mean can reveal fragmentation while being influenced by faraway groups.

### `malicious_fragmentation_at_15`

Build a mutual-kNN graph over sessions, restrict it to malicious nodes, then report:

- number of malicious connected components;
- largest component coverage;
- isolate fraction;
- median malicious component size.

This provides a reproducible definition of fragmentation without choosing a clustering algorithm after seeing labels.

### Null comparison

For every diagnostic, report the observed value alongside empirical null distributions from:

- label permutations;
- typed degree-preserving rewires;
- relation-preserving endpoint shuffles.

## 10.3 Representation-objective diagnostics

Keep pretext-task success separate:

- held-out edge AP/AUROC per relation;
- positive/negative decoder score distributions;
- false-negative rate in negative sampling;
- loss curves and seed variance;
- trained-versus-random embedding comparison.

These show whether the chosen objective was learned. They do not establish useful session triage.

## 10.4 Steering/amplification metrics

This is a different supervision regime. For each malicious anchor:

1. exclude the anchor from evaluation;
2. use only that anchor as the seed/restart signal;
3. rank the remaining sessions;
4. report AP, reviews to next malicious, reciprocal rank, and recall@K;
5. separately report retrieval on different hosts/identities.

Macro-average across anchors, then summarize seed variability.

## 10.5 Suggested paper tables

### Table 1: Triage performance

```text
method | AP | AP lift | reviews_to_first | random_expected |
recall@25 | recall@50 | recall@100 | recall@250
```

### Table 2: Representation diagnostics

```text
representation | purity@15 | enrichment | nearest_peer_rank |
mean_peer_rank | malicious_components | isolate_fraction
```

### Table 3: Signal localization

```text
method | relation_config | depth | pooling | delta_AP |
delta_purity | label_energy | rewired_null_delta | seed_stability
```

### Table 4: Amplification

```text
source_signal | propagation | anchor_protocol | AP_remaining |
reviews_to_next | recall@100 | cross_host_recall@100
```

---

# 11. Ablations and negative controls

## 11.1 Representation controls

- `random_score`;
- `raw_session_stats_knn`;
- graph structural statistics;
- real node2vec versus degree-preserving rewired node2vec;
- trained relational GNN versus random relational GNN;
- zero-layer feature encoder;
- topology-only versus feature-only versus combined;
- mean versus count-preserving aggregation;
- mean versus sum/session-count-aware pooling.

## 11.2 Graph controls

### Typed degree-preserving rewiring

Rewire endpoints within each relation while preserving valid source/target types and degree sequences as closely as possible.

Question:

> Does meaningful topology matter beyond activity volume and hub structure?

### Relation-preserving endpoint shuffle

Shuffle destinations within valid node-type pairs without necessarily preserving degree.

Question:

> Does any observed connectivity matter?

### Relation-label shuffle

Keep endpoints fixed but permute relation labels only where type constraints permit.

Question:

> Do relation semantics matter beyond connectivity?

### Feature shuffle within node type

Shuffle process features only among processes and file features only among files.

Question:

> Does feature/topology alignment matter?

## 11.3 Relation ablations

Run at least:

- parent only;
- file only;
- parent plus file;
- remove parent;
- remove file;
- forward versus forward-plus-reverse;
- all real relations versus shuffled equivalents.

Removing a relation changes degree and connectivity. Compare with removing an equal number of degree-matched random edges before attributing the full performance delta to relation semantics.

## 11.4 Artifact and identity controls

- Keep same-user, same-host, and temporal edges absent from the primary v0 graph.
- If added later, report them as explicit new experiments or identity/time upper bounds.
- Freeze rare-file thresholds before holdout.
- Report host/user concentration of malicious and benign sessions.
- For anchored retrieval, report cross-host results.
- Do not call a graph path chronological unless timestamps are checked separately.

## 11.5 Robustness controls

- multiple seeds;
- small edge-dropout perturbations;
- score-rank Spearman stability;
- kNN-neighbor-set Jaccard stability;
- explanation/path stability;
- full-batch versus sampled-neighborhood consistency if sampling is added.

---

# 12. A signal-localization protocol

## Stage 1: locate the representation and regime

For raw features, structural statistics, node2vec, every GNN layer, and the final pooled view, compute:

- triage metrics;
- malicious neighbor purity;
- malicious peer ranks;
- fragmentation;
- label-shuffle null;
- graph-rewire null.

Interpretation examples:

- high purity but weak anomaly AP: useful retrieval geometry without an unsupervised discovery score;
- good AP but low malicious purity: isolated anomalies rather than a coherent campaign cluster;
- low Laplacian energy and improving diffusion: homophilous/low-frequency signal;
- high energy and worse diffusion: contrastive/heterophilous signal;
- role features succeed while proximity fails: repeated structure across disconnected regions.

Do not amplify until at least one graph representation shows signal beyond appropriate nulls.

## Stage 2: locate the relation

For each method, remove or shuffle one relation at a time and record paired changes:

```text
relation
delta_average_precision
delta_reviews_to_first
delta_neighbor_purity
delta_peer_rank
delta_fragmentation
matched_random_edge_removal_delta
seed_stability
```

A relation is a candidate signal carrier only if the loss is stable and larger than matched random removal.

## Stage 3: locate hop scale and metapath

Compare \(h^{(0)}\), \(h^{(1)}\), \(h^{(2)}\), and optionally \(h^{(3)}\). For deterministic filters, decompose by \(A^k\). For typed graphs, enumerate short relation sequences.

For every metapath family report:

- frequency near malicious sessions;
- frequency near degree/host-matched benign sessions;
- inverse-degree-weighted frequency;
- lift over typed degree-preserving rewires;
- host/identity diversity;
- holdout stability.

## Stage 4: generate session-specific evidence

For a candidate session, produce a structured evidence record:

```text
session_id
method
score
rank
path_rank
typed_walk_or_path
intermediate_nodes
edge_types
path_weight
degree_adjustment
null_lift
score_drop_if_removed
rank_drop_if_removed
seed_stability
```

Possible weights include finite random-walk probability, inverse-degree products, PPR contribution, and learned message contribution.

## Stage 5: test faithfulness end to end

For every claimed supporting edge, relation, or path:

1. mask it;
2. recompute node embeddings;
3. recompute session pooling;
4. recompute the kNN score and neighbor set;
5. compare score/rank change with equal-size random and degree-matched removals;
6. repeat across seeds.

Explaining an encoder is not the same as explaining the final kNN score. Neighbor sets can change discontinuously under small embedding perturbations.

Good wording:

> Including the rare-file process-file-process context moved this session from rank 74 to rank 19; removing that context reversed most of the change across all three seeds.

Unsupported wording:

> The rare file caused the malicious activity.

## Stage 6: optional agentic explanation

Only after structured evidence is stable:

- give an agent the explicit path/evidence table;
- require every natural-language statement to point to recorded nodes, edges, attributes, and perturbation results;
- let it translate evidence into analyst language;
- forbid invention of missing causal or temporal links.

The agent communicates model-grounded evidence; it does not create the evidence.

---

# 13. A signal-amplification protocol

## 13.1 Label-free score propagation

Start from a fixed label-free score \(s_0\), such as raw or graph anomaly distance, then use restart diffusion:

\[
s^*=\alpha s_0+(1-\alpha)P^Ts^*.
\]

This preserves some original evidence while propagating the rest. Compare:

- original versus propagated score;
- real graph versus degree-preserving rewire;
- per-relation propagation;
- a small predeclared set of restart values;
- over-smoothing diagnostics.

Improvement on real but not rewired topology supports graph-local amplification. Similar improvement on rewired graphs suggests generic smoothing/degree effects. Degradation means the assumed smoothness does not fit the signal.

## 13.2 One-anchor analyst steering

Place restart mass on processes in one confirmed malicious session, exclude that anchor from evaluation, diffuse, pool relevance to other sessions, and evaluate remaining malicious sessions.

This answers:

> Given one analyst-confirmed example, can the graph retrieve additional malicious sessions?

It is few-shot steering, not unsupervised discovery.

## 13.3 Relation-weighted propagation

Only after relation ablations identify stable carriers, combine relation-specific operators:

\[
P=\sum_r w_rP_r.
\]

Start with fixed or dev-frozen weights. A learned attention mechanism is a later option, but explanation must still rely on perturbation and path evidence.

## 13.4 Choose amplification by signal regime

| Diagnosed signal | Amplification strategy | Guardrail |
|---|---|---|
| low-frequency/homophilous | shallow diffusion, PPR, normalized low-pass filter | compare rewires and monitor over-smoothing |
| local rare-artifact proximity | short walks, inverse-degree weighting, high restart | control for rare benign artifacts |
| high-frequency/heterophilous | retain self channel, residual/difference features, relation separation | do not force label smoothing |
| mixed hop scales | Jumping Knowledge or explicit multi-hop filter | report each depth separately |
| repeated structural role | role/motif retrieval | do not require direct connectivity |
| typed composition | relational encoder or explicit metapaths | preserve direction and inverse semantics |
| no signal beyond null | do not amplify | revise graph hypothesis as a new experiment |

## 13.5 Over-smoothing guardrail

At every propagation depth/restart setting record:

- embedding per-dimension variance;
- mean pairwise cosine similarity;
- original-score retention;
- neighbor purity;
- triage metrics;
- component-wise collapse.

Stop calling the operation amplification when it merely homogenizes the graph.

---

# 14. Cross-dataset and "dataset-agnostic" claims

## 14.1 Five distinct levels

| Level | Evidence required | Current likely status |
|---|---|---|
| Algorithm portability | same code runs after schema mapping | plausible target |
| Protocol portability | same sessions, metrics, controls, and frozen hyperparameters | testable next |
| Unsupervised per-dataset refit | no red-team labels used to fit each dataset | current design target |
| Inductive unseen-node generalization | frozen feature-based encoder embeds unseen nodes/edges | requires explicit experiment |
| Cross-dataset parameter transfer | train once, apply frozen model to another dataset | not established |

Node2vec supports only per-graph refitting. A feature-based relational GNN can support an inductive experiment if relation schema and feature meanings align. Neither fact proves performance transfer.

## 14.2 Defensible interim wording

> The method is dataset-portable conditional on a compatible telemetry schema: it uses no fixed attack signature, refits its unsupervised representation per dataset under frozen rules, and outputs graph structures associated with task-relevant signal.

## 14.3 Strong wording that requires more evidence

> The method is dataset agnostic and generalizes across cyber telemetry datasets.

This requires at least a second dataset, frozen protocol/hyperparameters, and clear separation between per-dataset refitting and frozen-model transfer.

## 14.4 Graph construction remains dataset-specific

Filename normalization, process identity, node typing, missing-value behavior, event coverage, temporal granularity, and relation availability all affect the graph. A general method can expose these as schema adapters and frozen configuration, but it cannot pretend they do not exist.

---

# 15. Claims: supported, conditional, and unsupported

| Claim | Status |
|---|---|
| Graphs provide a general relational abstraction. | Supported by the book. |
| Typed relations should remain distinguishable. | Supported by the book. |
| Different objectives preserve different graph similarities. | Supported by the book. |
| Basic message passing is predominantly smoothing/low-pass. | Supported by the book. |
| Shallow embeddings are transductive. | Supported by the book. |
| A graph representation contains malicious signal. | Must be demonstrated against nulls. |
| A relation carries useful triage signal. | Requires relation ablation and matched removal. |
| A path is associated with the model score. | Requires end-to-end perturbation. |
| A path is the causal attack path. | Not established by this workflow. |
| High attention explains the decision. | Not established; attention is a candidate weighting. |
| Good link prediction implies good triage. | Unsupported. |
| More GNN layers capture more useful context. | Often false due to over-smoothing. |
| Rare files are malicious. | Unsupported; rarity is only structural information. |
| The graph learned signal. | Requires trained encoder to beat random encoder. |
| The procedure is dataset agnostic. | Conditional on cross-dataset evidence and claim definition. |

---

# 16. Concrete notebook roadmap

## Stage 0: freeze one session mapping

Before comparing graph methods, produce one canonical `process_index -> session_id` mapping and reuse it everywhere.

The current notebook still has two session identities:

- the raw sessionizer groups by user with host fallback;
- the graph builder groups by host plus user.

The graph builder already creates bounded sessions, not connected-component sessions, so the manifest comment saying the graph defines sessions from connected components is stale. The graph section's prose also mentions temporal relations, while the current builder only emits parent-child and process-file relations.

These are notebook consistency issues, not conclusions from the book.

Required gate:

```text
identical session IDs
identical session ordering
identical label vector
identical review unit
for every representation
```

## Stage 1: finish the raw baseline artifact

Return:

- slice manifest;
- canonical process-session map;
- raw session table;
- random and raw scores;
- metric summary;
- representation diagnostics;
- top-ranked sessions.

Explicitly exclude `bad_user` and absolute timestamp features for future safety, even though the current numeric-only selector does not include the current categorical `bad_user` column.

## Stage 2: implement structural graph statistics

Deliver:

- `graph_structural_stats` table;
- `graph_structural_stats_knn` score;
- feature dictionary with graph provenance;
- per-session explanation table;
- shared metrics;
- label-shuffle and typed-rewire controls.

This is the fastest, clearest graph method.

## Stage 3: complete node2vec

The current notebook's Node2Vec section stops at:

```python
homogenous_graph_data = graph_data.to_homogeneous()
```

Still required:

- deliberate directed/undirected semantics;
- node type/offset bookkeeping;
- training loop and negative sampling;
- seeds 42/43/44;
- process embedding extraction;
- canonical session mean pooling;
- kNN scoring and diagnostics;
- degree-preserving rewired control.

Use the unbiased walk as primary and BFS/DFS biases only as declared sensitivities.

## Stage 4: implement relation-aware GraphSAGE

The current graph builder has an empty process `FEATURE_COLS` list and constant-one file features. Before message passing, define an explicit topology-only feature design and a separate feature-plus-topology design.

Deliver:

- safe process and file feature schemas;
- separately named inverse parent edge if used;
- relation-specific convolutions;
- two-layer encoder with root/self preservation;
- direction-capable relation decoder;
- type-correct negative sampler;
- held-out edge evaluation;
- canonical session pooling;
- triage score;
- random-init and zero-layer controls;
- feature/topology/relation ablations.

## Stage 5: run the frozen comparison

```text
random_score
raw_session_stats_knn
graph_structural_stats_knn
node2vec_session_knn
relational_graphsage_session_knn
```

Freeze method definitions and hyperparameters after the dev slice, then apply the same protocol to the untouched viable holdout.

## Stage 6: build the signal atlas

Produce:

- per-representation diagnostics;
- relation ablations;
- layer/hop ablations;
- typed path enrichment;
- degree-controlled nulls;
- path-removal faithfulness;
- seed and perturbation stability.

This stage turns "where does signal come from?" into a reproducible artifact.

## Stage 7: add amplification

Keep two distinct protocols:

- label-free anomaly-score propagation;
- one-anchor malicious retrieval.

Do not merge their metrics or claims.

## Stage 8: confirm and generalize

1. Frozen development slice.
2. Untouched holdout viability and confirmation.
3. Full-set runtime/stability.
4. Second dataset with frozen schema mapping and hyperparameters.
5. Optional true frozen-encoder cross-dataset transfer.

---

# 17. Suggested implementation interface

Keep representation, pooling, scoring, and diagnostics modular:

```python
process_session_map = build_canonical_sessions(df, session_config)
graph = build_graph(df, graph_config)

process_embeddings = method.fit_transform(
    graph=graph,
    node_features=node_features,
    seed=seed,
)

session_embeddings = pool_process_embeddings(
    process_embeddings,
    process_session_map,
    pooling="mean",
)

scores = knn_distance_anomaly_scores(session_embeddings, k=15)
triage_metrics = evaluate_ranking(scores, hidden_session_labels)
representation_diagnostics = diagnose_representation(
    session_embeddings,
    hidden_session_labels,
)
```

Each method should return enough provenance to trace its output:

```python
{
    "method_config": ...,
    "process_embeddings": ...,
    "session_embeddings": ...,
    "scores": ...,
    "training_diagnostics": ...,
    "layer_outputs": ...,
    "relation_messages": ...,
}
```

Labels must never be passed into `fit_transform`, pooling, or score construction for the unsupervised study.

---

# 18. Predeclared hypotheses

These hypotheses align the existing raw result with the graph study.

### H1: Raw local structure without anomaly separation

The raw feature representation will retain malicious neighbor enrichment even when raw kNN anomaly ranking remains weak.

### H2: Explicit graph structure

Typed structural statistics will improve at least one representation diagnostic beyond raw features and a typed degree-preserving graph null.

### H3: Higher-order proximity

Node2vec will outperform explicit structural statistics if malicious signal depends on short-walk context not captured by the selected summaries.

### H4: Relation-aware learning

Relational GraphSAGE will outperform homogeneous node2vec only if relation semantics and/or feature-topology interactions add useful information.

### H5: Learned objective value

Trained relational GraphSAGE must outperform its randomly initialized encoder for a claim that self-supervised graph learning adds value.

### H6: Signal localization

At least one relation or short typed metapath will show stable diagnostic/performance loss under removal beyond matched random-edge removal.

### H7: Conditional amplification

Graph propagation will improve ranking only when the diagnosed signal is sufficiently smooth in the relevant relation-specific operator.

### H8: Portability

The direction of the best method/control comparison and the identified signal carrier will replicate under a frozen protocol on a second dataset or confirmatory split.

Negative outcomes remain scientifically useful. For example, if graph representations improve neighbor purity but not anomaly ranking, that directly motivates few-shot retrieval rather than unsupervised discovery.

---

# 19. Compact glossary

| Term | Project meaning |
|---|---|
| Homophily | connected evaluation units tend to share labels |
| Heterophily | useful relations often connect different labels/types |
| Structural equivalence | disconnected nodes/sessions occupy similar graph roles |
| Encoder | maps nodes and graph context to representations |
| Decoder | reconstructs a chosen pairwise/relational property from embeddings |
| Pretext task | label-free training objective used to obtain a representation |
| Transductive | test nodes/graph are present during fitting, though labels may be hidden |
| Inductive | nodes and incident edges are unseen during training |
| Graph smoothness | signal changes little across edges; low Laplacian energy |
| High-frequency signal | signal changes sharply across connected nodes |
| Over-smoothing | repeated propagation makes node embeddings too similar |
| Pooling | combines process embeddings into a session representation |
| Null model | randomized graph preserving selected nuisance properties |
| Faithfulness | claimed evidence predictably changes the end-to-end score when removed |
| 1-WL limit | ordinary message passing cannot distinguish some structures/motifs |

---

# 20. Final project takeaway

The book does not say that a GNN will find attacks. It gives a more useful foundation:

- graph construction states a relational hypothesis;
- the encoder and objective decide which part of that hypothesis becomes geometry;
- diagnostics determine whether known malicious signal is present and in what regime;
- ablations and nulls localize whether the signal comes from degree, relations, hops, roles, or motifs;
- propagation can amplify smooth local signal but can erase contrastive signal;
- perturbation-tested paths can support an analyst explanation without being mislabeled as causal proof.

The resulting contribution is focused and defensible:

> A graph signal localization and amplification framework for cyber triage, evaluated across complementary structural hypotheses and grounded in typed relations, null controls, fixed analyst review units, and faithful supporting-subgraph evidence.
