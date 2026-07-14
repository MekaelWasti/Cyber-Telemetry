# Networks, Crowds, and Markets: Project-Focused Study Notes

Source studied: David Easley and Jon Kleinberg, *Networks, Crowds, and Markets: Reasoning about a Highly Connected World*, Cambridge University Press, 2010, draft dated June 10, 2010, in the local [source PDF](./networks-book.pdf).

These notes extract the parts of the book that materially strengthen the graph-triage project. They are not a chapter-by-chapter substitute for the book. The focus is network construction, topology audits, local and global structural features, directed reachability, link analysis, heavy-tailed degree, diffusion, temporal paths, explanation faithfulness, and the limits of a dataset-agnostic claim.

They complement the existing [Hamilton representation-learning notes](./GRL_Book_Project_Study_Notes.md) and [Ortega graph-signal-processing notes](./Ortega_GSP_Project_Study_Notes.md).

## Citation convention

The PDF has 14 pages of front matter before printed page 1. Therefore:

> printed page $p$ = PDF page $p+14$.

References below use `printed page / PDF page`. For example, `pp. 48-49 / PDF pp. 62-63` refers to printed pages 48-49 and PDF pages 62-63.

## How to read these notes

Three labels are used throughout:

- **Book concept** states what Easley and Kleinberg define, derive, or illustrate.
- **Project translation** adapts that concept to cyber telemetry and graph triage.
- **Guardrail** marks an assumption or interpretation that the book does not justify automatically.

The book is often written through social-network examples. A person, friendship, or adoption process should not be transferred literally to a process-file-parent graph. The mathematical structure can transfer; the social mechanism usually does not unless the telemetry relation supports it.

## Executive conclusions

1. **The network is a model of a relation, not a neutral container for rows.** A path only has meaning after node, edge, direction, time, and weight semantics have been stated. The book's opening graph definitions make this explicit (`pp. 23-29 / PDF pp. 37-43`).

2. **Connectivity is an experimental prerequisite.** A graph method cannot discover relational signal for isolated nodes. The current saved graph has 100,014 nodes but only 2,318 parent-child edges and 66 process-file touches. Even under the most optimistic assumption that every base edge touches two previously unseen nodes, at least about 95% of nodes must be isolated. Representation learning should not begin before this coverage failure is measured and repaired.

3. **Dense regions and boundary-spanning edges carry different information.** Clustering, embeddedness, and neighborhood overlap describe local redundancy; bridges, local bridges, betweenness, and ego-boundary measures describe brokerage or access across regions (`pp. 48-82 / PDF pp. 62-96`). Both should be explicit features in the basic structural method.

4. **A rare bridge can matter more than a frequent hub, but only under a stated task.** In the book, weak ties can provide novel information across social groups. In telemetry, a low-overlap process-file or parent-child relation may reveal a rare structural transition. It may also be an extraction error, an incomplete observation, or ordinary one-off behavior. Rarity is evidence to test, not maliciousness.

5. **Homophily is a diagnostic, not an explanation.** Similar labels or behaviors among neighbors can arise because the relation selected similar entities, because influence propagated, because both share an external context, or because graph construction encoded identity (`pp. 86-92 / PDF pp. 100-106`). A static malicious-neighbor-purity result does not show propagation.

6. **Affiliation networks are the closest textbook analogue to process-file telemetry.** A bipartite person-focus graph captures how shared contexts induce same-type proximity (`pp. 93-97 / PDF pp. 107-111`). The corresponding cyber question is whether two processes are related because they touch the same file, and whether file degree makes that connection specific or ubiquitous.

7. **Direction must be preserved when it encodes reachability.** Strongly connected components, upstream and downstream regions, and the Web's bow-tie decomposition show what symmetrization erases (`pp. 384-392 / PDF pp. 398-406`). A parent launches child edge and a child launched by parent edge answer different questions.

8. **Centrality is role or traffic, not threat.** HITS and PageRank infer importance from endorsement and random-walk equilibrium (`pp. 399-428 / PDF pp. 413-442`). In telemetry, high PageRank may identify a shared service, common binary, or sink. It should be a feature and a confounder control, never a synonym for anomaly.

9. **Heavy-tailed degree can arise without task signal.** Preferential attachment and copying can generate extreme popularity (`pp. 543-550 / PDF pp. 557-564`). A hub can be structurally expected. Any gain attributed to graph learning must survive degree-only baselines and degree-preserving nulls.

10. **Diffusion models are conditional stories.** Threshold cascades require a state that becomes more attractive as more neighbors adopt it; epidemic models require a contact capable of transmission (`pp. 563-587 and 645-665 / PDF pp. 577-601 and 659-679`). Arbitrary telemetry adjacency does not establish either condition.

11. **Shortest paths are not automatically discoverable, probable, or causal.** The small-world chapters separate the existence of short paths from the ability to find them with local information (`pp. 611-630 / PDF pp. 625-644`). The project should output supporting subgraphs and path scores under explicit criteria, not present one shortest path as the attack story.

12. **Temporal order is non-negotiable for propagation claims.** The same aggregate graph can permit or forbid a route depending on edge timing (`pp. 662-665 / PDF pp. 676-679`). A valid trace must be time-respecting, direction-respecting, and relation-respecting.

13. **The book strengthens the existing three-method comparison rather than replacing it.** Keep structural statistics, node2vec, and relational GraphSAGE as the headline representation hypotheses. Use the network concepts here to construct the structural feature set, audit the graph, design nulls, and interpret failures.

14. **The strongest portable contribution is a procedure.** Across datasets, freeze the schema contract, audit, normalized feature definitions, method families, null-generation rules, evaluation budgets, and explanation tests. Refit graph statistics and models without evaluation labels. Do not claim that one topology or threshold is universally correct.

## How this book complements the other two project texts

| Text | Primary question | Main contribution to this project |
|---|---|---|
| Hamilton, *Graph Representation Learning* | How can a graph be encoded or learned? | Structural features, node2vec, message passing, relational learning, objectives, and representation controls |
| Ortega, *Introduction to Graph Signal Processing* | How should values on a graph be analyzed and filtered? | Graph-signal-operator discipline, smoothness, spectral regimes, localized filters, multiscale representations, and amplification |
| Easley and Kleinberg, *Networks, Crowds, and Markets* | Why does a network have its observed structure, and what can flow through it? | Closure, bridges, homophily, affiliation, directed reachability, centrality, heavy tails, cascades, search, temporal contacts, and mechanism cautions |

The synthesis is:

```text
telemetry rows
    -> explicit node/edge/time schema
    -> topology and mechanism audit
    -> three representation hypotheses
         1. typed structural statistics
         2. walk-based proximity
         3. relation-aware message passing
    -> graph-signal atlas
    -> conditional filtering/amplification
    -> time-respecting supporting subgraphs
    -> frozen triage and faithfulness evaluation
```

Easley and Kleinberg are most useful before and after model fitting:

- **before**, to decide whether the graph has the structure and mechanism a method assumes;
- **after**, to interpret what the representation preserved and whether a reported path or diffusion story is defensible.

## Reading map

| Priority | Chapters or sections | Why they matter |
|---|---|---|
| Read closely now | Ch. 2, Sections 2.1-2.4 | Graph semantics, components, distance, BFS, and network-data limitations |
| Read closely now | Ch. 3, especially Sections 3.1-3.3 and 3.5-3.6 | Closure, overlap, bridges, embeddedness, betweenness, and partitioning |
| Read closely now | Ch. 4, Sections 4.1-4.4 | Homophily, selection versus influence, affiliation graphs, and longitudinal link formation |
| Read selectively | Ch. 5 | Signed relations and structural balance; useful only if positive and negative edge semantics are real |
| Skim for one caution | Ch. 12, Sections 12.1-12.3 | Network position is role-dependent; simple centrality can misstate power |
| Read closely now | Ch. 13, Sections 13.3-13.4 | Directed paths, strongly connected components, and bow-tie structure |
| Read closely now | Ch. 14, Sections 14.2-14.6 | HITS, PageRank, random walks, sinks, teleportation, and spectral link analysis |
| Read for controls | Ch. 18, Sections 18.1-18.4 and 18.6 | Heavy tails, copying, preferential attachment, and feedback |
| Read conditionally | Ch. 16 | Information cascades and the risk of correlated analyst or agent judgments |
| Skim for response stability | Ch. 17 | Tipping points, path dependence, and amplification response curves |
| Read closely before propagation claims | Ch. 19, Sections 19.1-19.5 | Threshold diffusion, blocking clusters, weak ties, and heterogeneous thresholds |
| Read closely for tracing | Ch. 20, Sections 20.1-20.6 | Short paths, navigability, scale, and core-periphery bias |
| Read closely for temporal tracing | Ch. 21, Sections 21.1-21.6 | Contact semantics, random contagion, SIR/SIS, percolation, time expansion, and transient edges |
| Defer | Chs. 6-11, 15, 22-24 | Game theory, auctions, most market machinery, voting, and property rights are not needed for the current core contribution |

# 1. A graph is a scientific claim about relations

## 1.1 Nodes and edges do not explain themselves

**Book concept.** A graph specifies a set of nodes and a set of edges between them. An undirected edge represents a symmetric relation; a directed edge represents an asymmetric one (`pp. 23-24 / PDF pp. 37-38`). The drawing layout is irrelevant to topology unless spatial position is itself part of the model.

**Project translation.** Every graph artifact should carry a schema contract:

| Field | Required question |
|---|---|
| Node type | What real entity or event does one node represent? |
| Node identity | When are two rows the same entity, and can IDs collide or be reused? |
| Edge type | What observed fact creates the edge? |
| Direction | Which endpoint can affect, precede, create, or refer to the other? |
| Time | Is the edge instantaneous, interval-valued, persistent, or aggregated over a window? |
| Weight | Does a larger value mean count, confidence, similarity, rarity, capacity, or something else? |
| Scope | Which nodes and edges could have been observed but were missing from the slice? |
| Evaluation mapping | How are node outputs pooled to the fixed review unit? |

For the current v0 graph, the intended base schema is approximately:

- process nodes;
- rare-file nodes;
- directed `process -> process` parent-child edges;
- directed `process -> file` touches edges plus an explicit reverse relation for message passing;
- a separately defined fixed session ID for evaluation.

The graph currently does not contain meaningful process features in the graph builder because `FEATURE_COLS` is empty. Node2vec can still operate from topology, but a GNN cannot be interpreted as learning telemetry content until features are added deliberately.

**Guardrail.** Adding reverse edges for computation does not make the underlying fact symmetric. The reverse relation should be named separately, as the notebook already does with `touches` and `touched_by`, so explanations retain direction.

## 1.2 A relation graph and a similarity graph answer different questions

The book uses graphs for communication, social interaction, information linkage, dependencies, and physical structure (`pp. 24-27 / PDF pp. 38-41`). This variety is a reminder that adjacency does not always mean similarity.

For this project:

- a parent-child edge represents lineage;
- a process-file edge represents participation in a shared context;
- a session kNN edge represents feature similarity;
- a temporal edge represents precedence;
- a same-host edge represents shared environment.

These relations should not be collapsed and then interpreted as one generic form of closeness. Ortega's graph-signal analysis needs an operator whose neighbor agreement is meaningful. Hamilton's relational GNN needs transformations that distinguish relation types. Easley and Kleinberg add the mechanism question: *why would this edge make information, state, or risk transferable?*

## 1.3 Network data is an observation, not the network itself

**Book concept.** Large network datasets are often proxies assembled from collaboration records, communication traces, transactions, or links (`pp. 40-43 / PDF pp. 54-57`). A co-authorship edge, for example, captures one formal kind of collaboration while missing informal interaction (`pp. 28-29 / PDF pp. 42-43`). The book also warns that findings from one online setting do not automatically extrapolate to another (`p. 98 / PDF p. 112`).

**Project translation.** A graph audit must separate:

1. **true absence:** no relationship occurred;
2. **unobserved relation:** it occurred outside the selected telemetry or time slice;
3. **filtered relation:** graph construction intentionally removed it;
4. **failed resolution:** the relevant identifier was missing or did not join;
5. **censored boundary:** an endpoint lies outside the 100,000-row slice.

The distinction is critical for bridges and isolates. An observed local bridge may disappear when missing edges are restored. An isolate may mean "no graph evidence was captured," not "the behavior was structurally independent."

## 1.4 Freeze the review unit before comparing graphs

The graph can contain processes, files, and relations across time, but the triage comparison must use one canonical session mapping. The current notebook produces 1,457 raw sessions but 3,131 graph sessions because the two builders group identities differently. Until this is fixed, AP, recall at budget, and reviews-to-first are not comparable.

The clean design is:

1. sessionize once from the raw rows using frozen identity and time rules;
2. attach `session_id` to every process node;
3. allow graph edges to cross sessions when their semantics justify it;
4. produce node representations or scores;
5. pool them back to the same 1,457 review units;
6. evaluate every method against the same 19 malicious session labels.

# 2. Connectivity, reachability, and the graph-coverage gate

## 2.1 Paths, walks, and cycles

**Book concept.** A path is a sequence of adjacent nodes; under the book's introductory definition it may repeat nodes, while a *simple path* does not (`p. 26 / PDF p. 40`). A cycle returns to its starting node and provides alternate routing (`pp. 26-28 / PDF pp. 40-42`).

In matrix-based graph learning, powers of adjacency aggregate over **walks**, including repeated nodes and edges. This matters for explanation:

- a large $A^k$ contribution need not correspond to one simple path;
- a hub can participate in many repetitive walks;
- cycles can cause repeated reinforcement;
- a polynomial filter's support is a bounded neighborhood, not a unique route.

Use the precise term required by the calculation. "The score receives support from these length-$k$ walks" is stronger and more accurate than "the model found the attack path."

## 2.2 Connected components are independent evidence regions

**Book concept.** In an undirected graph, a connected component is a maximal set in which every pair of nodes is joined by a path (`pp. 28-31 / PDF pp. 42-45`). Large networks often contain one giant component plus many smaller components, but this is an empirical pattern, not a requirement.

**Project translation.** Report:

- number and size distribution of components;
- isolate count and isolate fraction;
- giant-component fraction by node type;
- fraction of canonical sessions with zero, one, or several connected process nodes;
- malicious-session coverage, used only after topology is frozen;
- component purity only as an evaluation diagnostic;
- score calibration by component size.

No propagation or neighborhood method can help an isolate. A session containing only isolates should either:

- fall back to raw/session features;
- receive an explicit "no graph evidence" flag;
- or be excluded from a graph-only analysis with coverage reported.

It must not silently receive a zero that is interpreted as benign.

## 2.3 The current graph fails an optimistic coverage bound

The saved notebook reports:

| Quantity | Saved value |
|---|---:|
| Process nodes | 100,000 |
| File nodes | 14 |
| Parent-child base edges | 2,318 |
| Process-file base touches | 66 |
| Directed entries after reverse touch edges | 2,450 |
| Graph-created sessions | 3,131 |

The parent relations can cover at most $2(2,318)=4,636$ distinct process nodes, and the touch relations can add at most 66 more distinct processes. Therefore at most 4,702 of the 100,000 process nodes can be incident to any native edge. At least 95,298 processes - 95.3% - must be isolated under this optimistic bound. Since there are only 14 file nodes, including all files does not loosen the total-node bound. Reused endpoints can only increase the actual isolate count.

This is a hard gate:

> Do not interpret node2vec or message-passing results until exact incident-node coverage is computed and the canonical session coverage is acceptable.

The likely repair is not to add arbitrary density. It is to examine why parent IDs resolve so rarely, why only 14 file nodes survive, whether `filename` is the correct stable file identity, whether the row slice cuts parent histories, and whether additional high-confidence relation types are available.

## 2.4 Breadth-first search gives a reach profile, not just a distance

**Book concept.** BFS discovers nodes in layers of increasing shortest-path distance (`pp. 32-35 / PDF pp. 46-49`).

For each relevant node type and relation view, record:

$$
g_i(k)=\left|\{j:d(i,j)\leq k\}\right|
$$

and summarize $g_i(1)$, $g_i(2)$, and $g_i(3)$ across nodes and sessions.

This answers:

- whether "two-hop local" is actually local;
- whether hubs make nearly the entire graph reachable in two steps;
- whether malicious sessions occupy compact or fragmented regions;
- whether a filter depth or GNN depth has a defensible evidence radius.

Use both raw counts and fractions of the reachable component. A 50-node two-hop neighborhood means something different in a 60-node component and a 50,000-node component.

## 2.5 Directed paths and strongly connected components

**Book concept.** In a directed graph, a path must follow edge direction. A strongly connected component (SCC) is a maximal set in which every node can reach every other (`pp. 384-388 / PDF pp. 398-402`).

**Project translation.** On a directed parent-child graph:

- descendants are reachable by forward paths;
- ancestors are reachable only on the reversed view;
- mutual reachability should be rare unless multiple relation types or explicit reverse edges create cycles;
- symmetrization erases the ancestor/descendant distinction.

Report:

- weakly connected components;
- SCC sizes;
- reciprocity by relation type;
- source SCCs and sink SCCs;
- forward and reverse reachability curves;
- whether computational reverse edges are included in the diagnostic.

## 2.6 Bow-tie position is a useful directed role

**Book concept.** Relative to a giant SCC, a directed network can be divided into:

- **IN:** can reach the SCC but cannot be reached from it;
- **SCC/core:** mutually reachable;
- **OUT:** reachable from the SCC but cannot return;
- **tendrils/tubes:** lie around IN and OUT without passing through the core;
- **disconnected:** not even weakly attached to the core

(`pp. 389-392 / PDF pp. 403-406`).

**Project translation.** This decomposition can become a structural feature on a relation-specific directed view. Examples:

- parent-only graph: sources, lineage interiors, and terminal descendants;
- process-file-process projection: contributors to shared contexts and sinks;
- temporal communication graph: upstream initiators and downstream receivers.

**Guardrail.** Do not call the largest SCC a "malicious core." Bow-tie position is a reachability role. Its triage value must be established post hoc and compared with degree and component-size controls.

# 3. Closure, overlap, bridges, and structural roles

## 3.1 Clustering coefficient

**Book concept.** The local clustering coefficient of node $i$ is the fraction of pairs of its neighbors that are themselves connected (`p. 49 / PDF p. 63`):

$$
C_i=
\frac{\text{number of edges among neighbors of }i}
{\binom{d_i}{2}}
$$

for $d_i\geq2$.

In social networks, high clustering can reflect triadic closure. In telemetry it may reflect:

- repeated membership in a shared context;
- dense process families;
- projection through common files or hosts;
- duplicate or near-duplicate event construction;
- or actual multi-step coordination.

Compute clustering only on a clearly named homogeneous view. A raw heterogeneous triangle can mix incomparable edge meanings. On a pure process-file bipartite graph, ordinary triangles cannot exist at all; four-cycles or same-type projections are the relevant structures.

## 3.2 Common neighbors and closure are interpretable baselines

**Book concept.** Triadic closure says that two nodes with a common neighbor are more likely to form a future link; the book measures an empirical $T(k)$, the rate of future link formation among pairs with $k$ common neighbors (`pp. 97-104 / PDF pp. 111-118`).

**Project translation.** Common-neighbor counts can test whether the graph contains repeated relational context:

$$
\operatorname{CN}(u,v)=|N(u)\cap N(v)|.
$$

For link prediction, use time-separated snapshots:

1. build the graph using only edges available before cutoff $t$;
2. compute common-neighbor or typed-metapath features;
3. test which edges appear after $t$;
4. compare with matched non-edges.

For triage, common neighbors are not themselves suspicious. They are a low-cost structural feature and a way to ask whether local closure patterns differ from matched benign structure.

## 3.3 Edge embeddedness and neighborhood overlap

**Book concept.**

- Edge embeddedness is the number of common neighbors of its endpoints (`pp. 65-66 / PDF pp. 79-80`).
- Neighborhood overlap softens the local-bridge definition (`pp. 57-59 / PDF pp. 71-73`):

$$
O(u,v)=
\frac{|N(u)\cap N(v)|}
{|(N(u)\cup N(v))\setminus\{u,v\}|}.
$$

An overlap of zero means the edge is a local bridge.

**Project translation.** For every relation view, aggregate:

- median and minimum incident-edge embeddedness;
- fraction of incident edges with zero overlap;
- inverse-degree-weighted shared-neighbor counts;
- distribution of overlap by edge type;
- overlap percentiles relative to same-type, same-degree controls.

At session level, useful features include:

- minimum process-edge overlap;
- fraction of process nodes participating in low-overlap edges;
- total edge weight carried by low-overlap edges;
- number of distinct components connected by the session's processes;
- rare-file overlap after controlling for file degree.

These are prime candidates for `graph_structural_stats_knn`.

**Bipartite degeneracy.** In a pure process-file graph, a process has only file neighbors and a file has only process neighbors, so the endpoints of every process-file edge have no ordinary common neighbor. Every such edge therefore has zero triangle embeddedness and satisfies the ordinary local-bridge definition, even if it belongs to many four-cycles. Do not use those raw values as informative features. Use same-type projections with degree correction, square/four-cycle participation, or typed alternate-path length while retaining the original bipartite graph for explanation and null modeling.

## 3.4 Bridges and local bridges

**Book concept.**

- A bridge is an edge whose deletion separates its endpoints into different components (`pp. 50-51 / PDF pp. 64-65`).
- A local bridge is an edge whose endpoints have no common neighbor; its span is the distance between its endpoints after the edge is removed (`pp. 51-53 / PDF pp. 65-67`).

The distinction matters because true bridges can be rare in large networks while low-overlap local bridges remain common and informative.

**Project translation.** A bridge-like telemetry relation can mean:

- a unique transition between otherwise separate process families;
- a process joining two file contexts;
- a one-off parent-child lineage that connects sessions or hosts;
- the only observed route from a raw anomaly pocket to a broader campaign pocket.

**Guardrails.**

- Bridge status is brittle under missing edges.
- A bridge in an extremely sparse graph is often trivial.
- Span should be computed after deletion on the same directed/undirected view used by the claim.
- A bridge indicates structural dependence, not causal transmission.

Use a matched deletion test: remove the candidate edge, recompute the final session score or localized coefficient, and compare the drop against removal of edges matched on relation type, degree, weight, and time.

## 3.5 Structural holes and brokerage

**Book concept.** Nodes at interfaces between groups can access nonredundant information and regulate its flow; the book describes this as spanning structural holes (`pp. 64-69 / PDF pp. 78-83`).

**Project translation.** A process or session with neighbors in several low-overlap regions may be a broker. Quantify with:

- ego-network density;
- number of neighbor communities;
- participation coefficient across communities or relation types;
- fraction of neighbor pairs disconnected without the node;
- node and edge betweenness;
- component increase after node removal;
- boundary edges divided by internal edges.

Do not call brokerage malicious. System services, package managers, shared infrastructure, and management agents are legitimate brokers. Brokerage becomes triage evidence only when it is unusual for the node type, host role, time, and degree stratum.

## 3.6 Betweenness and divisive partitioning

**Book concept.** Edge betweenness is the total shortest-path flow through an edge when one unit is sent between every connected pair and divided evenly among tied shortest paths (`pp. 73-76 / PDF pp. 87-90`). Girvan-Newman repeatedly removes the highest-betweenness edges, recomputing after each removal, to reveal nested regions (`pp. 76-82 / PDF pp. 90-96`).

For edge $e$:

$$
B(e)=
\sum_{\{s,t\}:\sigma_{st}>0}
\frac{\sigma_{st}(e)}{\sigma_{st}},
$$

where the sum is over connected unordered node pairs, $\sigma_{st}$ is the number of shortest paths from $s$ to $t$, and $\sigma_{st}(e)$ is the number using $e$.

**Project translation.**

- Betweenness is a diagnostic for structural bottlenecks.
- Partition stability under edge deletion can identify candidate campaign boundaries.
- The nested deletion sequence can reveal whether a suspicious region is a robust module or an artifact of one link.

**Guardrails.**

- Exact repeated betweenness is expensive; the book notes the method is practical mainly for moderate networks (`p. 82 / PDF p. 96`).
- Shortest-path traffic is hypothetical, not measured telemetry flow.
- High betweenness is inflated by component shape and bridge sparsity.
- Community assignments can be unstable under small graph changes.

Use approximate betweenness or sampled sources for the audit. Do not make Girvan-Newman the headline triage method.

# 4. Homophily, context, and the selection-influence problem

## 4.1 A random-mixing baseline

**Book concept.** If a binary node attribute has population proportions $p$ and $q=1-p$, random assignment produces a cross-type edge with expected probability $2pq$. A substantially smaller observed cross-type fraction is evidence of homophily (`pp. 88-90 / PDF pp. 102-104`).

For multiple categories with proportions $\pi_c$, the expected same-type fraction under independent random mixing is:

$$
\sum_c \pi_c^2,
$$

and the expected heterogeneous fraction is:

$$
1-\sum_c\pi_c^2.
$$

**Project translation.** Apply this idea to:

- node or session labels, evaluation only;
- host roles;
- users;
- process families;
- time blocks;
- predicted clusters;
- raw anomaly-score quantiles.

But independent random mixing is usually too weak as the only null. Degree, relation type, time, and opportunity constrain which endpoints could connect. Prefer permutation or rewiring within:

- node type;
- relation type;
- degree bin;
- host or environment stratum;
- time block;
- and, when relevant, connected component.

## 4.2 Malicious-neighbor purity measures representation, not causation

The current raw feature space has:

- 1,457 sessions;
- 19 malicious sessions;
- mean malicious neighbor purity at $k=15$ of about 0.207;
- median purity about 0.267;
- 84.2% of malicious sessions with at least one malicious neighbor;
- about 16.75 times enrichment over the random base rate.

This is a strong descriptive indication that malicious sessions occupy related regions in that frozen representation, subject to the small label count and identity/context confounds. It does not establish:

- that maliciousness flowed between them;
- that their closeness is graph-derived;
- that the deployment-time score can find them without labels;
- or that the representation transfers.

The correct use is to motivate a graph/signal study: the anomaly ranking is weak, while label structure is locally concentrated. The research problem is to find a label-free signal or topology that exposes that concentration.

## 4.3 Selection, influence, and confounding

**Book concept.** Similarity between neighbors can arise because:

- **selection:** similar nodes preferentially connect;
- **influence:** connected nodes become more similar;
- **shared context/confounding:** another factor creates both the connection and the behavior.

A static snapshot generally cannot separate these mechanisms. Longitudinal data helps establish whether attributes changed after ties or ties formed after attributes (`pp. 90-92 and 105-106 / PDF pp. 104-106 and 119-120`).

**Project translation.**

- Same-host processes may look similar because the host generated both, not because either influenced the other.
- Processes touching the same file may share a software context, not an attack.
- Parent and child behavior may be correlated because of lineage, a shared user command, or common policy.
- Sessions close in absolute time may share environment drift.

Therefore, any "signal propagation" result should compare at least:

1. native relation graph;
2. relation-preserving endpoint shuffle;
3. time-block shuffle;
4. identity/context ablation;
5. direction reversal or symmetrization control;
6. degree-matched graph.

## 4.4 Affiliation graphs are the right starting abstraction for process-file relations

**Book concept.** An affiliation network is bipartite: one node set represents people, the other foci or contexts, and edges encode participation (`pp. 93-95 / PDF pp. 107-109`). Shared foci can induce same-type connections; the book distinguishes:

- triadic closure among people;
- focal closure between people sharing a focus;
- membership closure when a person joins a friend's focus

(`pp. 95-97 / PDF pp. 109-111`).

**Project translation.** Map cautiously:

| Book abstraction | Telemetry analogue |
|---|---|
| person | process or canonical session |
| focus | file, host, user, destination, registry key, or another context |
| affiliation edge | touched, executed, authenticated, connected, or modified |
| shared-focus projection | process-process or session-session metapath |

For a process-context incidence matrix $B$, the off-diagonal entries of the projection

$$
P=BB^\top
$$

counts shared contexts. A degree-adjusted projection should downweight ubiquitous context $f$, for example:

$$
P_{ij}^{\text{rare}}
=
\sum_f
\frac{B_{if}B_{jf}}
\max(d_f-1,1)}.
$$

This weighting is a project design, not a formula from the book. It follows the book's central insight that shared context creates opportunity while recognizing that common contexts are less specific.

## 4.5 Projection can manufacture density

A file touched by $d_f$ processes creates up to $\binom{d_f}{2}$ process-process pairs in a one-mode projection. A small number of ubiquitous files can therefore create:

- artificial clustering;
- short paths;
- high malicious-neighbor purity driven by context;
- rapid diffusion dominated by hubs;
- and apparently strong community structure.

Always compare:

- the original bipartite graph;
- a binary projection;
- a degree-adjusted projection;
- a file-degree-capped graph;
- and a bipartite degree-preserving rewire.

The representation should preserve the bipartite view whenever explanation needs to say *which file* supported a process-process relationship.

# 5. Directed importance: HITS, PageRank, and what they do not mean

Chapters 13-14 move from undirected social structure to directed Web links. The useful transfer is not that a telemetry edge is an endorsement. It is that direction creates distinct source, target, upstream, downstream, hub, authority, and stationary-flow roles.

## 5.1 HITS separates hub and authority roles

**Book concept.** HITS assigns every node two recursively defined scores:

$$
a_p \leftarrow \sum_{q:q\rightarrow p} h_q,
\qquad
h_p \leftarrow \sum_{q:p\rightarrow q} a_q.
$$

An authority is pointed to by good hubs; a hub points to good authorities. The iterations are normalized after each round (pp. 399-406 / PDF pp. 413-420).

For adjacency matrix $M$, where $M_{ij}=1$ when $i\rightarrow j$,

$$
h \leftarrow Ma,
\qquad
a \leftarrow M^\top h.
$$

Consequently,

$$
h^{(k)}=(MM^\top)^k h^{(0)},
\qquad
a^{(k)}=(M^\top M)^{k-1}M^\top h^{(0)}.
$$

The limiting hub and authority roles are therefore associated with the dominant eigenvectors of $MM^\top$ and $M^\top M$ respectively (pp. 417-424 / PDF pp. 431-438).

**Project translation.** Run HITS only on a relation whose direction has a coherent interpretation. Examples include:

- process $\rightarrow$ file: a high-hub process touches recursively authoritative files, while a high-authority file is touched by recursively high-hub processes;
- parent process $\rightarrow$ child process: a hub launches recursively authoritative descendants;
- session $\rightarrow$ artifact: session and artifact roles remain distinct;
- account $\rightarrow$ resource: activity source and frequently targeted resource remain distinct.

These can be useful *role features*. They are not anomaly scores. A ubiquitous system file may be an excellent HITS authority and completely benign.

A local HITS calculation is often more useful than a global one: take an anchor, construct a bounded, semantically compatible base set, and compute hub/authority roles inside it. This asks which nodes organize this candidate region rather than which nodes dominate the whole enterprise.

**Guardrails.**

- Synthetic reverse edges erase the intended source/target distinction.
- A disconnected component with slightly stronger spectral mass may capture the leading vector.
- Common files and high-volume processes can dominate.
- A repeated or nearly repeated top eigenvalue makes rankings initialization-sensitive or perturbation-sensitive (p. 424 / PDF p. 438).
- The book explicitly warns that even a Web link is only an implicit vote in aggregate; individual links can express criticism or manipulation (p. 399 / PDF p. 413). A process-file edge is even less endorsement-like.

Report HITS alongside plain in-degree/out-degree, its correlation with degree, the leading spectral gap, and results on bipartite degree-preserving rewires.

## 5.2 PageRank is equilibrium flow on a directed graph

**Book concept.** Basic PageRank sends each node's current mass uniformly over its outgoing links, with dangling nodes retaining their mass under the book's convention. If $N$ is row-stochastic,

$$
r^{(t+1)}=N^\top r^{(t)}.
$$

Basic PageRank can leak into closed downstream regions. In the Web bow tie, rank can drain from the giant strongly connected core into OUT (pp. 406-410 / PDF pp. 420-424).

Scaled PageRank follows a link with probability $s$ and teleports uniformly with probability $1-s$:

$$
r^{(t+1)}
=
sN^\top r^{(t)}
+
(1-s)\frac{\mathbf 1}{n}.
$$

Equivalently,

$$
\widetilde N_{ij}
=
sN_{ij}+\frac{1-s}{n}.
$$

The added positive teleport probability produces a unique equilibrium and convergence on any graph. The book describes $s$ values around $0.8$-$0.9$ in the Web setting; those values are not automatically appropriate for telemetry (pp. 410-412, 424-428 / PDF pp. 424-426, 438-442).

The equivalent thought experiment is a random surfer who either follows a uniformly selected outgoing edge or jumps. The book stresses that this defines the score; it is not necessarily an accurate behavioral model (pp. 411-412 / PDF pp. 425-426).

## 5.3 Personalized PageRank is a transparent localization baseline

Replace uniform teleportation by an anchor distribution $q$:

$$
r^{(t+1)}
=
sP^\top r^{(t)}
+
(1-s)q.
$$

At equilibrium,

$$
r^*
=
(1-s)\sum_{k=0}^{\infty}s^k(P^\top)^kq.
$$

This path expansion is a direct mathematical consequence of the PageRank recurrence. It makes personalized PageRank especially useful for this project: score is accumulated across walks starting from the anchor, with geometric attenuation by length.

Useful variants are:

- forward PPR for plausible descendants or effects;
- reverse-graph PPR for plausible precursors;
- relation-weighted $P=\sum_r \alpha_rP_r$;
- a finite number of steps for stronger localization;
- a temporal transition matrix that excludes invalid moves;
- multi-anchor $q$ after analyst feedback.

For every returned candidate, preserve contribution by seed, hop, relation type, and predecessor. Teleportation is a mathematical restart and must never appear as a physical explanation edge.

**Guardrail.** Personalized PageRank is an association or support score unless every transition has a defensible transmission meaning. With `touches` and synthetic `touched_by` edges, it describes proximity in an association graph, not a causal attack path.

## 5.4 Centrality is a covariate and confounder, not a verdict

Chapter 12 supplies a useful general warning: network power depends on alternatives and the surrounding configuration, so a seemingly central node can have little bargaining power while a less visually central node has leverage (pp. 339-346 / PDF pp. 353-360). HITS and PageRank similarly measure precise structural roles, not generic importance.

For triage, use global link-analysis scores in three ways:

1. as interpretable structural features;
2. as nuisance variables to control, because benign hubs attract score;
3. as baselines to beat.

Do not write:

> High PageRank indicates a maliciously influential process.

Write:

> The process occupies a high stationary-flow role under relation set $R$; malicious relevance was assessed separately against degree-, type-, and activity-matched controls.

# 6. Signed relations and structural balance: relevant only with real signs

Chapter 5 is mathematically clean but lower priority for the current graph.

## 6.1 Exact and weak balance

**Book concept.** In a complete, undirected signed graph, every pair has a positive or negative edge. A triangle is balanced when it has one or three positive edges. With $s_{ij}\in\{-1,+1\}$,

$$
s_{ij}s_{jk}s_{ki}=+1
$$

for a balanced triangle (pp. 119-122 / PDF pp. 133-136).

The Balance Theorem says a complete balanced graph is either:

- entirely positive; or
- split into two internally positive groups with negative edges between them.

(pp. 123-126 / PDF pp. 137-140)

Weak balance allows all-negative triangles and therefore permits more than two internally positive, mutually antagonistic groups (pp. 129-132 / PDF pp. 143-146).

For sparse signed graphs, missing is a third state, not a negative edge. A sparse signed graph is balanced exactly when no cycle contains an odd number of negative edges (pp. 133-143 / PDF pp. 147-157).

## 6.2 Why this is not yet a core project method

The current relations - parent-child and process-file touch - do not carry positive and negative semantics. The following shortcuts would be invalid:

- malicious = negative and benign = positive, because this leaks labels;
- absent edge = negative edge;
- edge direction = sign;
- rare edge = negative edge;
- failed or denied action = automatically antagonistic.

The book already notes that directed trust/distrust does not inherit the clean friend/enemy interpretation (pp. 128-129 / PDF pp. 142-143). Heterogeneous cyber relations are even less likely to do so.

If a future dataset provides defensible supportive/contradictory or allow/deny relations, possible diagnostics include:

$$
U
=
\frac{\#\text{ unbalanced fully observed signed triangles}}
{\#\text{ fully observed signed triangles}},
$$

node-local participation in unbalanced cycles, and shortest odd-negative-cycle certificates. Compare all of them with sign-permuted nulls preserving node type, relation type, and positive/negative degrees.

Recommendation: keep structural balance in the “conditional extension” box, not in the first three-method comparison.

# 7. Heavy tails, hubs, and algorithmic rich-get-richer effects

## 7.1 A straight log-log line is not enough

**Book concept.** A power-law frequency distribution has

$$
f(k)=\frac{a}{k^c},
$$

so

$$
\log f(k)=\log a-c\log k.
$$

The book uses log-log plots as a quick empirical diagnostic and discusses the Web's historically heavy-tailed in-degree distribution (pp. 543-546 / PDF pp. 557-560).

**Guardrail.** A roughly straight plot does not establish a power law. A serious empirical claim would require a fitted tail cutoff, uncertainty on the exponent, and comparison with alternatives such as lognormal and truncated power-law models. The project does not need a power-law claim to justify degree normalization.

## 7.2 Copying and preferential attachment explain why popularity compounds

In the book's copying model, a new page either links uniformly to an existing page with probability $p$ or copies one of an existing page's links with probability $1-p$. The copying step chooses targets in proportion to their current in-degree (pp. 547-549 / PDF pp. 561-563).

Writing $q=1-p$ and $X_j(t)$ for page $j$'s degree,

$$
P(\text{new link targets }j)
=
\frac{p}{t}
+
\frac{qX_j(t)}{t}.
$$

The deterministic approximation

$$
\frac{dx_j}{dt}=\frac{p+qx_j}{t}
$$

leads to a heavy-tailed degree distribution (pp. 555-559 / PDF pp. 569-573). The broader lesson is that early random advantage plus proportional growth creates inequality and unstable rankings; other mechanisms can generate similar tails.

## 7.3 Cyber graphs contain legitimate hubs

Expected hubs include:

- system binaries and shared libraries;
- service accounts and orchestration processes;
- DNS resolvers and gateways;
- update servers;
- high-volume scanners;
- common temporary paths;
- high-activity hosts.

Therefore:

$$
\text{high degree}\not\Rightarrow\text{malicious}.
$$

An iterative amplifier can create its own rich-get-richer loop: hubs receive more support because they have more edges, their score then becomes a source of more support, and score concentration grows on every round.

Audit before and after propagation:

- top-1% score-mass share;
- Gini coefficient or Herfindahl-Hirschman index;
- Spearman correlation between score and typed degree;
- precision and recall within degree/activity strata;
- core versus periphery performance;
- fraction of mass attributable to the largest seed;
- fraction of explanatory paths passing through top-degree nodes.

Portable features should use within-type ranks, empirical tail probabilities, robust log-degree, or residuals from typed null expectations rather than one raw degree threshold shared across datasets.

# 8. “Spread” is not one mechanism

The book discusses several processes that can all produce increasing prevalence. They should not be blended into one metaphor.

| Mechanism | What changes | Governing idea | Safe project use |
|---|---|---|---|
| Information cascade | A decision-maker's belief/action | Earlier visible choices can override private evidence | Warning about dependent alerts and analyst/model feedback |
| Network effect | Payoff from adopting | Adoption becomes more valuable when others adopt | Response-curve analogy for iterative amplification |
| Threshold diffusion | State or behavior | Enough neighbor reinforcement triggers adoption | Nonlinear topology stress test |
| Epidemic process | Infection/state | Random transmission over eligible contacts | Temporal reachability or Monte Carlo support model |
| Graph propagation | A numerical score | An operator chosen by the researcher | The literal mechanism implemented in the pipeline |

Telemetry does not automatically instantiate the first four. Unless the corresponding causal assumptions are validated, call the output:

- graph-derived support;
- algorithmic reachability;
- anchor-conditioned association;
- propagated score;
- or time-respecting candidate route.

Do not call it infection probability, behavioral adoption, influence, or causal attack flow merely because the mathematics resembles those processes.

# 9. Threshold diffusion: reach is different from reinforcement

## 9.1 The coordination threshold

**Book concept.** Suppose a node receives payoff $a>0$ per neighbor matching choice $A$ and payoff $b>0$ per neighbor matching choice $B$. If fraction $p$ of its neighbors currently use $A$, then the node chooses $A$ when

$$
pda \ge (1-p)db,
$$

or equivalently

$$
p\ge q,
\qquad
q=\frac{b}{a+b}.
$$

The diffusion process starts with a seed set using $A$; all other nodes use $B$ and irreversibly switch once their active-neighbor fraction reaches $q$ (pp. 563-570 / PDF pp. 577-584).

Seed placement can matter as much as seed count. A seed next to an almost activated boundary can continue a cascade while an equally sized seed in a highly resistant region does nothing (pp. 570-573 / PDF pp. 584-587).

## 9.2 Blocking clusters give a structural explanation for failure

A set $S$ is a cluster of density $p$ when every node in $S$ has at least fraction $p$ of all its neighbors inside $S$.

For a common threshold $q$, the book proves:

- if the nodes outside the seed set contain a cluster of density greater than $1-q$, it blocks a complete cascade;
- if a cascade stops before reaching every node, its remaining inactive nodes form such a cluster.

Thus the cascade succeeds exactly when no blocking cluster of density greater than $1-q$ remains outside the initial seed set (pp. 573-577 / PDF pp. 587-591).

With node-specific thresholds $q_v$, every member $v$ of a blocking set must have more than fraction $1-q_v$ of its neighbors inside that set (pp. 580-583 / PDF pp. 594-597).

This is useful for explanation: an activation can name the neighbors whose previous-round support crossed its threshold, while a failed cascade can identify a resistant region. It is not evidence that telemetry entities literally make coordination decisions.

## 9.3 Weak ties can carry awareness without enough support

Chapter 3 emphasizes local bridges as routes into new regions. Chapter 19 adds an important qualification: a bridge can expose a region to a signal but may provide only one active neighbor, which is insufficient for high-threshold adoption. Dense local structure supplies reinforcement; weak ties supply access (pp. 578-580 / PDF pp. 592-594).

For this project:

> An edge may be excellent for tracing where support can reach and still be too weak to justify amplifying the destination's score.

That distinction suggests reporting two graphs:

1. a permissive *trace graph* encoding plausible association or transmission opportunities;
2. a conservative *support graph* or rule requiring independent, typed, or repeated evidence before amplification.

## 9.4 Weighted threshold support as a stress test

A project extension is:

$$
\frac{
\sum_{u\in N(v)}w_{uv}\mathbf 1[u\text{ active}]
}{
\sum_{u\in N(v)}w_{uv}
}
\ge q_v.
$$

Possible $w_{uv}$ factors include relation reliability, inverse artifact degree, temporal decay, and source-provenance independence.

This is not the book's unweighted theorem. Once the graph is directed, typed, weighted, signed, or temporal, the eligible predecessor set and denominator must be specified, and the exact blocking theorem may no longer apply.

Use threshold propagation as a nonlinear topology probe:

1. choose seeds without using evaluation labels;
2. sweep $q$ over a declared range;
3. record activation time and contributing predecessors;
4. compare seed sets matched on type, degree, and activity;
5. compare synchronous with asynchronous updates;
6. compare original topology with typed degree-preserving rewires;
7. report the whole response curve, not the best threshold selected after seeing labels.

# 10. Small worlds: short paths are not automatically traceable

## 10.1 Existence and discoverability are different questions

**Book concept.** The small-world problem separates:

1. whether a short path exists;
2. whether a participant with only local information can find one.

(pp. 611-612 / PDF pp. 625-626)

Breadth-first search can reveal a shortest path by exploring the graph globally. Decentralized routing must choose one next hop using local knowledge (pp. 616-619 / PDF pp. 630-633).

The Watts-Strogatz model shows that a few long-range edges can sharply reduce path length while retaining local clustering. But uniformly random shortcuts do not necessarily make decentralized search effective because they offer no consistent direction toward the target (pp. 612-619 / PDF pp. 626-633).

## 10.2 Kleinberg's result explains the need for a useful gradient

In a two-dimensional grid, suppose the probability of a long-range contact from $v$ to $w$ is proportional to

$$
d(v,w)^{-q}.
$$

Efficient decentralized search occurs at $q=2$, matching the dimension: links are distributed across distance scales in a way that repeatedly offers useful progress (pp. 619-621 / PDF pp. 633-635).

The rank-based generalization defines

$$
\operatorname{rank}_v(w)
=
\left|\{u:d(v,u)<d(v,w)\}\right|
$$

and uses probability proportional to $\operatorname{rank}_v(w)^{-1}$ (pp. 622-625 / PDF pp. 636-639).

Do not transfer the inverse-square law literally to telemetry. The transferable idea is that local search needs a feature that correlates with progress toward the target at multiple scales.

Possible cyber steering signals include:

- event time and temporal proximity;
- process ancestry;
- host, account, or session context;
- relation type;
- semantic feature similarity;
- rarity relative to a typed null;
- attack-stage compatibility where independently available.

## 10.3 Core-periphery structure biases trace success

Peripheral nodes often connect quickly into a dense core. Core targets are therefore easy to reach, while another peripheral target may remain hard to find even if a short path exists (pp. 629-630 / PDF pp. 643-644).

A method can look strong by repeatedly returning core infrastructure. Evaluate:

- recall stratified by typed degree and activity;
- performance in core versus periphery;
- fraction of paths passing through the top 1% of hubs;
- effective diameter before and after hub removal;
- malicious examples intentionally placed or held out in the periphery;
- path validity after removing generic infrastructure.

## 10.4 Evaluate three notions of a path

For each anchor-candidate pair, distinguish:

| Path object | Constraint | What it establishes |
|---|---|---|
| Unweighted shortest path | Fewest edges | Static graph proximity |
| Locally discoverable path | Each step chosen using declared local information | Operational traceability |
| Typed, directed, time-respecting path | Relation semantics, direction, and time all valid | A plausible support route |

None alone establishes causality. Report path length, relation sequence, elapsed/waiting time, hub exposure, and deletion sensitivity.

# 11. Epidemic models: useful mathematics with strict semantic conditions

## 11.1 The graph must match the transmission opportunity

**Book concept.** A contact graph should contain an edge when the relationship makes the modeled transmission possible. Different processes on the same population can require different contact graphs (pp. 645-647 / PDF pp. 659-661).

This is one of the book's most important graph-construction rules for the project. A parent-child edge, a file co-use edge, a network connection, and feature similarity are not interchangeable channels.

For each relation, document:

- what can move or be inferred across it;
- its direction;
- whether it is persistent or instantaneous;
- whether repeated occurrences are independent;
- whether it is causal, contextual, similarity-based, or synthetic;
- what null preserves its nuisance structure.

## 11.2 $R_0$ is a local branching summary, not a topology guarantee

In the simple branching model, each infected individual contacts $k$ new individuals and transmits independently with probability $p$:

$$
R_0=pk.
$$

If $R_0<1$, extinction occurs almost surely. If $R_0>1$, indefinite survival has positive probability, not certainty (pp. 647-650 / PDF pp. 661-664).

The book gives a layered network where $R_0=4/3$ but every layer has a fixed positive probability of completely blocking further transmission, so eventual extinction occurs almost surely (pp. 653-655 / PDF pp. 667-669). Average reproduction cannot replace topology.

A clearly labeled algorithm diagnostic could be:

$$
R_{\text{amp}}^{(t)}
=
\frac{\text{newly supported nodes or score mass at }t+1}
{\text{active nodes or score mass at }t}.
$$

This is not epidemiological $R_0$. It tests whether the chosen amplifier is subcritical, explosive, or near a sensitive boundary. Break it down by node type, edge type, degree band, seed family, and propagation depth. If $R_{\text{amp}}>1$ is driven by benign hubs, the method is amplifying topology rather than malicious evidence.

## 11.3 SIR and percolation offer a probabilistic reachability view

The SIR model has susceptible, infectious, and removed states. An infectious node attempts to infect susceptible neighbors and later becomes removed (pp. 650-655 / PDF pp. 664-669).

For a one-step infectious period, there is an equivalent static percolation construction:

1. mark each eligible edge open independently with probability $p$;
2. block it otherwise;
3. a node is eventually infected exactly when an open directed path connects it to a seed.

(pp. 654-655 / PDF pp. 668-669)

Project use could include Monte Carlo open-edge reachability with relation-specific support probabilities. But an arbitrary edge weight is not a calibrated probability. The output should remain “reach probability under the specified graph model” unless real transmission frequencies justify a stronger interpretation.

## 11.4 Cycles can recirculate the same support

The SIS model permits reinfection. The book represents a one-step SIS process as SIR on a time-expanded graph, with node copies at every time and edges

$$
(v,t)\rightarrow(w,t+1)
$$

when the original graph permits $v\rightarrow w$ (pp. 656-658 / PDF pp. 670-672).

For graph amplification, cycles can repeatedly recycle one original observation and make it look like multiple confirmations. Controls include:

- restart to the original score;
- damping;
- finite propagation depth;
- time expansion;
- prohibition on repeated edge or evidence-source use;
- provenance deduplication;
- explicit separation of intrinsic and propagated score.

## 11.5 Temporal order can reverse reachability

The transient-contact examples show that two graphs with identical aggregate edges can have different possible transmissions solely because the contact windows occur in a different order (pp. 662-665 / PDF pp. 676-679).

For instantaneous directed events, a valid temporal path

$$
(v_0,t_1,v_1),
(v_1,t_2,v_2),
\ldots,
(v_{m-1},t_m,v_m)
$$

requires

$$
t_1\le t_2\le\cdots\le t_m.
$$

For interval edges, each next edge must still be active when the process arrives. Concurrency - overlapping contact windows - can increase reachability even when aggregate degree, total contacts, and durations are held fixed (pp. 664-666 / PDF pp. 678-680).

Required temporal controls are:

- static versus time-respecting graph;
- original versus within-stratum timestamp shuffle;
- forward-only versus unconstrained paths;
- maximum waiting-time sensitivity;
- relation-specific transmission delay;
- explicit simultaneous-event policy;
- duration-preserving shifts for interval data;
- train/test splits that prevent future edges from explaining earlier decisions.

A time-respecting path establishes temporal plausibility, not causality.

# 12. Information cascades, base rates, and dependent evidence

## 12.1 Cascades can be rational, wrong, and fragile

**Book concept.** In an information cascade, people decide sequentially, observe earlier choices but not the private signals behind them, and may rationally ignore their own signal once previous decisions provide stronger apparent evidence (pp. 483-488 / PDF pp. 497-502).

Once later people merely copy, their actions add no independent information. A long cascade can rest on only a few early observations, can be wrong, and can break when genuinely new public evidence arrives (pp. 488-489, 503-504 / PDF pp. 502-503, 517-518).

## 12.2 Rare-event priors matter

Bayes' rule is

$$
P(A\mid B)=\frac{P(A)P(B\mid A)}{P(B)}.
$$

For state $G$, prior $P(G)=p$, and a symmetric private signal of accuracy $q$,

$$
P(G\mid H)
=
\frac{pq}{pq+(1-p)(1-q)}.
$$

(pp. 490-500 / PDF pp. 504-514)

In rare-event triage, even a seemingly accurate local clue can have a modest posterior because the malicious base rate is small. Graph support must not silently erase that prior.

## 12.3 A detection pipeline can manufacture a cascade

A plausible failure chain is:

1. one source event produces multiple derivative alerts;
2. the graph treats them as independent corroboration;
3. propagation spreads that duplicated support;
4. a downstream model or analyst sees the propagated ranking;
5. their response becomes new training or evaluation evidence.

The apparent consensus may trace back to one seed.

Maintain the decomposition

$$
s_v^{\text{final}}
=
s_v^{(0)}
+
\Delta_v^{\text{graph}},
$$

where $s_v^{(0)}$ is intrinsic/local evidence and $\Delta_v^{\text{graph}}$ is graph-derived support. For the second term, store provenance by original seed, detector family, source event, path, relation, and propagation round.

Key controls:

- collapse alerts sharing a source event;
- leave one detector family out;
- leave one host or data source out;
- remove the earliest or strongest seed and rerun;
- obtain independent judgments without showing prior model outputs;
- count unique evidence sources, not only paths;
- cap the contribution of any one seed.

## 12.4 Network-effect models motivate amplification response curves

Chapter 17 studies settings in which adoption itself increases value and produces tipping points, multiple equilibria, and path dependence (pp. 509-533 / PDF pp. 523-547). The social mechanism need not transfer, but the stability lesson does.

Treat the amplifier as a response system. For initial seed mass $z_0$ and parameter vector $\theta$, measure

$$
A(z_0,\theta)
=
\text{final supported fraction or propagated score mass}.
$$

Sweep:

- seed count and seed mass;
- restart/damping;
- threshold;
- edge-time window;
- graph sparsification;
- iteration count;
- relation weights.

Look for abrupt transitions, saturation, hysteresis, and large changes under small seed perturbations. A method that succeeds only because one dataset sits just above an accidental tipping point is not robustly portable.

# 13. Project architecture implied by the book

The project becomes clearer if it separates four planes rather than treating “the graph model” as one object.

## 13.1 Evidence plane

Store original, non-graph evidence as

$$
s_v^{(0)}=\text{local evidence for node }v.
$$

Requirements:

- label-free at deployment time;
- calibrated or at least rank-normalized within entity type;
- timestamped;
- provenance-preserving;
- deduplicated across derivative alerts where possible;
- kept available after propagation so graph gain is measurable.

## 13.2 Relation plane

Every edge should retain:

- source and destination;
- source and destination types;
- relation type;
- direction;
- event time or validity interval;
- multiplicity;
- confidence or extraction quality;
- whether reverse edges are observed or synthetic;
- whether the relation is causal, contextual, similarity-based, or merely computational.

A message-passing graph may add reverse edges for numerical convenience. A trace graph must distinguish those from observed reverse relations.

## 13.3 Operator plane

The operator says how support moves or how a representation is learned:

- structural feature map;
- random-walk/window co-occurrence;
- relation-specific message passing;
- restarted linear propagation;
- threshold reinforcement;
- time-respecting Monte Carlo reachability.

The operator is the literal mechanism implemented. Social influence or malware transmission is an interpretation that requires additional validation.

## 13.4 Explanation plane

Return more than a scalar. For each reviewed session, provide:

- intrinsic score;
- graph-derived increment;
- most influential seeds;
- relation and hop composition;
- supporting nodes and edges;
- valid time-respecting paths;
- score drop under removal of the claimed support;
- matched-null comparison;
- a statement of what the graph supports and what it cannot establish.

# 14. The three-method representation study

The book strengthens the planned three-method comparison:

| Method | Hypothesis tested | Primary output | Main failure mode |
|---|---|---|---|
| Typed structural statistics | Hand-designed local roles contain useful signal | Interpretable feature vector | Misses higher-order equivalence |
| node2vec | Walk co-occurrence captures useful higher-order proximity | Dense topology-only embedding | Hubs and mixed relations dominate walks |
| Relational GraphSAGE | Typed neighborhood aggregation adds value beyond local features | Learned inductive embedding | Empty/leaky features, over-smoothing, relation shortcuts |

Personalized PageRank should be a transparent anchor-steering control, not a fourth representation headline. Ortega-style graph filters belong in the later amplification stage after the representation and topology gates are passed.

## 14.1 Freeze the common experimental substrate

All three methods must share:

1. one canonical node table;
2. one canonical session definition and process-to-session mapping;
3. the same observed relation tables;
4. the same train/validation/test time boundaries;
5. the same review unit;
6. the same label-free fitting population;
7. the same session pooling and downstream scoring rule where possible;
8. the same evaluation budgets and bootstrap units.

If one method uses 3,131 graph sessions and another uses 1,457 raw sessions, their results do not answer the same question.

## 14.2 Method 1: typed structural statistics

This should be the first implementation because it is cheap, auditable, and directly tests whether the graph contains usable topology.

### Node-level features

Compute within compatible graph views:

**Typed activity**

- in-degree and out-degree per relation;
- unique-neighbor count;
- event multiplicity;
- robust log-degree;
- degree percentile within node type and time window;
- residual from a type- and activity-matched null.

**Connectivity and position**

- isolated indicator;
- weak component size and rank;
- SCC size;
- IN/core/OUT/tendril role where direction is meaningful;
- in- and out-reachable counts up to a small hop limit;
- BFS layer expansion $|L_1|,|L_2|,|L_3|$;
- k-core or core-periphery score as a project extension.

**Redundancy and boundary**

- clustering coefficient on same-type or otherwise triangle-valid views;
- shared-neighbor counts;
- Jaccard overlap;
- edge embeddedness summaries;
- fraction of incident bridge/local-bridge edges;
- local-bridge span summaries;
- ego density;
- number of distinct neighboring components joined after removing the ego node;
- approximate or local betweenness.

**Bipartite affiliation**

- process degree and file degree;
- inverse-file-degree weighted co-affiliation;
- rare-file count;
- four-cycle/square participation;
- typed alternate-path length;
- projection overlap under binary and degree-adjusted weights;
- number of parent/child neighbors sharing a file.

**Directed recursive roles**

- global and local HITS hub/authority;
- PageRank;
- forward and reverse PPR relative to an analyst anchor only in anchor-conditioned experiments;
- correlations or residuals relative to degree.

**Temporal structure**

- forward and backward reachable counts;
- first/last event span;
- edge-time burstiness;
- fraction of static paths that remain time-respecting;
- temporal waiting-time summaries;
- concurrency count where interval data exists.

### Session pooling

For node feature $x_v$, pool to session $S$ using several fixed summaries:

$$
\operatorname{pool}(S,x)
=
\left[
\operatorname{mean}_{v\in S}x_v,\,
\operatorname{median}_{v\in S}x_v,\,
Q_{0.90}(x_v),\,
\max_{v\in S}x_v,\,
\log(1+|S|)
\right].
$$

Do not use a sum without controlling session size. Include session size explicitly so the model can distinguish “one extreme process” from “many ordinary processes.”

### Scoring

A deliberately basic unsupervised implementation is:

1. transform skewed positive counts with `log1p`;
2. robust-standardize or rank-normalize each feature on training data only;
3. form the session feature matrix;
4. use cosine similarity for anchor retrieval;
5. use mean $k$-nearest-neighbor distance or local outlier factor as an unsupervised triage score;
6. freeze $k$ using label-free stability or a validation rule declared before test labels.

Call this baseline `typed_structural_stats_knn`.

Its explanation is direct: report the session's largest standardized feature deviations, the nodes responsible for each pooled extreme, and the graph edges that instantiate those features.

## 14.3 Method 2: node2vec

node2vec tests whether higher-order walk context contains signal that the explicit local statistics miss.

Keep the comparison honest:

- run on a graph whose relation mixing is declared;
- compare the combined graph with relation-specific graphs;
- treat synthetic reverse edges as association transitions, not causal moves;
- match embedding dimension and downstream scoring protocol;
- inspect visit frequency by node type and degree;
- compare with degree-preserving rewires;
- report whether embeddings merely reconstruct component or degree bands.

The walk parameters $p$ and $q$ control the balance between local/BFS-like and outward/DFS-like exploration. Select them without test labels. A small grid with fixed seeds and an unsupervised stability or held-out-edge rule is preferable to a large label-tuned search.

For a highly disconnected graph, node2vec cannot learn useful cross-node context for isolates. Any default vector assigned to isolated nodes should be reported separately, not silently pooled with learned embeddings.

## 14.4 Method 3: relational GraphSAGE

Relational GraphSAGE tests whether learned, typed aggregation improves on both explicit statistics and fixed random-walk context.

A strong comparison is:

- `X_basic`: non-graph attributes and type indicators available across datasets;
- `X_struct`: the label-free structural feature table from Method 1;
- `GraphSAGE(X_basic)`;
- `GraphSAGE(X_basic + X_struct)`;
- feature-only scoring on the identical input.

This reveals whether gain comes from features, graph aggregation, or both.

Required controls:

- real edges versus typed degree-preserving shuffled edges;
- each relation removed in turn;
- features shuffled within node type;
- zero/constant-feature run as a diagnostic, not the main result;
- depth sweep with over-smoothing measures;
- multi-seed mean, standard deviation, and paired differences;
- future-edge or self-supervised objective with realistic, type-valid negatives.

An empty `FEATURE_COLS` list makes a learned GNN difficult to interpret. A model driven by trainable node embeddings may be transductive memorization rather than a portable inductive method.

## 14.5 One downstream scorer, two evaluation modes

Each representation $z_S$ should be evaluated in:

**Unseeded triage**

- anomaly score from the same unsupervised scorer where feasible;
- ranking of all sessions under operational review budgets.

**Anchor-conditioned steering**

- remove one known anchor from evaluation;
- rank remaining sessions by representation similarity or anchor-conditioned method;
- enforce cross-host or other anti-shortcut restrictions when relevant;
- report retrieval of the other malicious sessions.

These are different tasks. Strong anchor retrieval does not imply strong cold-start anomaly detection.

# 15. Topology audit: the gate before representation learning

## 15.1 Audit each graph view separately

At minimum, create:

1. parent-child directed graph;
2. parent-child undirected association view;
3. process-file bipartite graph;
4. combined heterogeneous message-passing graph;
5. semantic directed trace graph;
6. session graph, if sessions are explicit nodes or aggregated relations.

For each view report:

- node and edge counts by type/relation;
- unique observed edges versus synthetic reverse edges;
- self-loops and duplicates;
- isolated fraction by node type;
- component-size distribution;
- giant weak-component share;
- SCC-size distribution and giant-SCC share;
- reciprocity;
- typed degree quantiles and concentration;
- clustering only where triangles are meaningful;
- four-cycle counts in bipartite views;
- bridge/local-bridge fraction;
- shortest-path and effective-diameter summaries on connected samples;
- hop-wise neighborhood growth;
- edge-time coverage and static-versus-temporal reachability.

## 15.2 The graph-coverage gate

Before fitting an embedding, require:

- a declared minimum non-isolated share for the review-unit population;
- enough multi-node components for relational comparison;
- nontrivial relation coverage beyond identity shortcuts;
- a documented policy for isolates;
- stable counts under reasonable parsing and time-window changes.

There is no universal pass percentage. The rule should be specified before reading label performance and justified operationally. A graph with 95% isolated nodes can still be studied, but its contribution is necessarily limited to the connected minority.

## 15.3 The semantic-direction gate

For every directed analysis answer:

- Is this direction observed or added for training?
- Does it mean cause-to-effect, actor-to-object, earlier-to-later, or only source-to-recorded-target?
- Can a path legally mix these relation types?
- Are all edges on the path simultaneously or sequentially valid?
- What would reversing the edge assert?

If those questions cannot be answered, use an undirected association interpretation and avoid attack-flow language.

## 15.4 The shortcut gate

Check whether performance can be explained by:

- same host;
- same user;
- same session size;
- time proximity;
- degree/activity;
- one ubiquitous file;
- component membership;
- synthetic reverse edges;
- future information;
- duplicated alerts.

Report ablations and matched controls for each shortcut that exists in the data.

# 16. Null models and controls

A null should destroy one hypothesized source of signal while preserving the nuisance structure most likely to fake it. One maximally random graph is not enough.

## 16.1 Minimum control ladder

Every graph result should be placed beside:

1. random ranking;
2. prevalence or majority reference where appropriate;
3. raw/evidence-only representation;
4. graph-only score;
5. typed degree and activity features;
6. the real graph with the same scorer;
7. matched structural nulls;
8. relation and feature ablations.

The question is not merely “does the graph method beat random?” It is “does it exploit more than prevalence, activity, component size, and degree?”

## 16.2 Fixed-topology attribute null

Permute evaluation labels or a diagnostic signal on the fixed graph only after every representation, score, and hyperparameter is frozen.

Because process rows inherit session labels, permutation must occur at the canonical session level. When malicious sessions cluster by host, campaign, or user group, add grouped or stratified permutations. IID process-level permutation would create thousands of false independent samples.

Use this null for:

- malicious-neighbor purity;
- label smoothness;
- component enrichment;
- post-hoc feature association;
- final AP significance.

Labels remain evaluation instruments, not seeds for the unsupervised method.

## 16.3 Typed degree-preserving topology null

For directed relation $r$, perform double-edge swaps that preserve source out-degree and target in-degree:

$$
(a\rightarrow b,\;c\rightarrow d)
\mapsto
(a\rightarrow d,\;c\rightarrow b),
$$

rejecting invalid type pairs, duplicates when prohibited, and temporal or host constraints required by the null.

This preserves popularity while destroying specific adjacency.

For the process-file bipartite graph, swap

$$
(p_1,f_1),\;(p_2,f_2)
\mapsto
(p_1,f_2),\;(p_2,f_1)
$$

while preserving process degrees and file degrees. This is essential: otherwise a null can appear easy simply because it removes ubiquitous-file structure.

## 16.4 Temporal nulls

Use several strengths:

- shuffle timestamps within relation, host, and coarse time block;
- preserve endpoint pairs but shuffle event order;
- shift intervals while preserving duration and activity rhythm;
- preserve timestamps but permute compatible endpoints;
- reverse time as a deliberately impossible control.

Compare static reach, forward temporal reach, and null temporal reach. A signal that survives endpoint rewiring but disappears under time shuffle is structurally different from one that survives time shuffle but disappears under degree-preserving rewiring.

## 16.5 Relation and direction controls

- delete one relation at a time;
- use one relation at a time;
- permute relation labels while keeping endpoints;
- symmetrize;
- reverse observed directions;
- remove synthetic reverse relations;
- cap or remove the highest-degree context nodes;
- retain common files but inverse-degree weight them;
- compare with hard file deletion.

These reveal whether performance comes from semantics, mere density, a particular hub, or a direction convention.

## 16.6 Feature and provenance controls

- shuffle features within node type and time band;
- zero one feature family at a time;
- remove duplicate alerts from the same source;
- leave one detector family out;
- leave one host, campaign, or data source out;
- use seed sets matched by type, degree, and activity;
- compare single-pass aggregation with iterative feedback.

For every null report the observed value, null median, interval, percentile or standardized effect, and variability across random seeds.

# 17. Metric suite

## 17.1 Operational triage metrics

With extreme imbalance, accuracy and ROC-AUC can look good while review order remains poor. Prioritize:

- average precision / PR-AUC;
- reviews to first malicious;
- recall at review budgets such as 25, 50, 100, and 250;
- precision at the same budgets;
- number found at each budget;
- normalized discounted cumulative gain if graded relevance exists;
- bootstrap intervals and multi-seed spread.

Report prevalence beside AP. Report every budget in absolute reviews as well as percentages.

## 17.2 Representation diagnostics

These ask whether a representation organizes relevant structure before asking whether an anomaly scorer points in the correct direction:

- malicious top-$k$ neighbor purity, evaluation-only;
- fraction of malicious sessions with at least one malicious neighbor;
- malicious peer mean/median rank;
- within-malicious versus malicious-to-benign distance;
- component and neighborhood label enrichment against stratified permutation;
- retrieval AP and Recall@$k$ under leave-one-anchor-out;
- cross-host retrieval to test identity shortcuts;
- real-edge versus shuffled-edge embedding separation;
- stability of nearest neighbors across seeds.

A representation can have high malicious-neighbor purity and poor anomaly AP if malicious sessions form a compact group that the point-anomaly scorer treats as normal. That is a scoring-direction issue, not proof that the representation failed.

## 17.3 Topology and coverage metrics

Always accompany learned results with:

- all-session graph coverage;
- process and session isolate rates;
- connected-only performance as a secondary diagnostic;
- component/SCC shares;
- typed degree concentration;
- walk coverage for node2vec;
- proportion of sessions with any usable message-passing edge;
- fraction of paths that are direction-valid and time-valid.

Never headline a connected-only score without the all-session result.

## 17.4 Trace metrics

For proposed support subgraphs:

- explanation coverage;
- number of nodes, edges, hops, and relation types;
- temporal validity rate;
- generic-hub exposure;
- provenance completeness;
- necessity: score/rank drop when explanation is removed;
- sufficiency: score retained when only explanation evidence remains;
- stability across seeds and graph variants;
- deletion effect relative to matched random removals;
- path precision when ground-truth chains actually exist.

## 17.5 Amplification metrics

Measure change from the frozen pre-amplification score:

$$
\Delta\mathrm{AP}
=
\mathrm{AP}_{\text{amplified}}
-
\mathrm{AP}_{\text{initial}},
$$

and similarly:

- change in recall at a fixed review budget;
- change in reviews to first malicious;
- false-positive amplification factor;
- malicious-to-benign score contrast;
- top-$K$ churn;
- degree-score correlation change;
- top-1% score-mass change;
- per-seed attribution concentration;
- $R_{\text{amp}}^{(t)}$ by propagation round;
- gain on the real graph minus gain on structural nulls.

Amplification has succeeded only if it improves operational ranking without merely increasing score magnitude or concentrating mass on hubs.

## 17.6 Uncertainty unit

Sessions from one host or campaign are not fully independent. With only 19 malicious sessions, report:

- session bootstrap as a descriptive interval;
- host- or campaign-grouped bootstrap where feasible;
- leave-one-host/group-out sensitivity;
- paired seed-level differences between methods;
- exact counts alongside percentages.

Do not let thousands of process nodes create artificial confidence for a session-level claim.

# 18. From localization to faithful tracing and controlled amplification

## 18.1 Trace a support bundle, not one cinematic path

For a high-ranked session:

1. identify the processes or pooled features driving the score;
2. enumerate short typed candidate paths, preferably no more than three observed edges at first;
3. enforce direction and time where the claimed interpretation needs them;
4. retain relation, endpoint, time, multiplicity, artifact degree, and seed provenance;
5. rank paths using a declared score;
6. test the top support by deletion and retention;
7. compare with matched random paths or edges.

Keep path types explicit:

- `process -> process -> process`: lineage;
- `process -> file <- process`: shared affiliation/context;
- `process -> host <- process`: shared host context, if added;
- `process -> network endpoint`: directional contact, if available.

A shared-file path is not a process-to-process transmission path.

## 18.2 A possible path-support score

One transparent project design is:

$$
\operatorname{support}(\pi)
=
\sum_{e\in\pi}
\left[
\log w_e
-
\lambda_d\log(1+d_e)
-
\lambda_t\,\Delta t_e
\right],
$$

where $w_e$ is relation confidence or null-relative specificity, $d_e$ is a nuisance degree such as artifact popularity, and $\Delta t_e$ is waiting time. Invalid directions or times receive no path score.

This formula is not from the book. Its value is auditability: every preference is exposed rather than hidden inside the phrase “most likely path.” If $w_e$ is not a calibrated probability, do not describe the resulting path as probabilistically most likely.

## 18.3 Necessity and sufficiency

Let $f(G,x)$ be the session score.

Deletion necessity:

$$
\Delta_{\text{del}}(E^*)
=
f(G,x)-f(G\setminus E^*,x).
$$

Retention sufficiency:

$$
\Delta_{\text{keep}}(E^*)
=
f(G[E^*],x)-f(G_{\text{empty}},x).
$$

Compare each with relation-, degree-, and size-matched random edge sets. An explanation that looks plausible but does not affect the score is not faithful to the model.

## 18.4 Conservative first amplifier

After a representation and initial evidence score are frozen, start with restarted, degree-normalized propagation:

$$
s^{(t+1)}
=
\alpha s^{(0)}
+
(1-\alpha)P^\top s^{(t)}.
$$

Restart preserves intrinsic evidence; row normalization limits raw degree capture. Use relation-specific transitions, temporal filtering, and seed/path attribution.

Compare:

- no propagation;
- one-pass aggregation;
- finite-step propagation;
- equilibrium propagation;
- real graph;
- typed degree-preserving rewires;
- hub-capped graph;
- timestamp-shuffled graph.

Then use Ortega's operator and frequency analysis to determine which localized components are being amplified. The Easley-Kleinberg contribution is to test whether the underlying paths, hubs, bridges, and temporal channels make that amplification structurally credible.

## 18.5 Stop conditions

Do not proceed to amplification if:

- most review units have no graph evidence;
- the initial score is undefined or label-seeded;
- representation gain vanishes on a degree/activity baseline;
- paths are mostly synthetic, temporally invalid, or dominated by ubiquitous hubs;
- topology-shuffled graphs perform equally well;
- small parameter changes cause uncontrolled score explosions;
- support cannot be traced back to independent original evidence.

# 19. What this says about the current notebook

This section connects the textbook to the saved state of `Notebooks/Graph Triage Baseline v0.ipynb` at the time these notes were prepared.

## 19.1 The review unit is inconsistent

The raw baseline has 1,457 sessions. The graph builder has 3,131. The difference comes from distinct identity/session rules, including whether host is part of a user session key.

This invalidates a direct AP or review-cost comparison. First create one canonical session table and require every method to consume it. A reasonable contract is an explicit tuple such as:

$$
\text{session key}
=
(\text{host},\text{user},\text{declared time/session boundary}),
$$

with a documented fallback when a field is missing. The precise choice is less important than making it single, saved, and shared.

## 19.2 The current graph has a coverage stop condition

Saved topology:

- 100,000 process nodes;
- 14 file nodes;
- 2,318 parent-child edges;
- 66 process-file touches;
- 66 synthetic reverse file-to-process entries;
- 2,450 directed homogeneous entries total.

As derived in Section 2.3, at least 95,298 process nodes - 95.3% - are isolated even under an endpoint-maximizing bound. Actual isolation can only be higher when endpoints repeat.

Likely contributors include:

- parent resolution restricted to processes inside the same deduplicated tail slice;
- no broader historical context for a child whose parent fell outside the scoring slice;
- file identity keyed only by `filename`;
- a hard file-degree cutoff that leaves only 14 files and 66 touches;
- deletion of common context instead of retaining it with inverse-degree weighting;
- absence of other typed context relations;
- an undocumented mixture of forward-only parent edges and bidirectional file association edges.

Repair should increase *semantically valid coverage*, not arbitrary density. Context nodes can come from a broader history without becoming evaluation sessions.

## 19.3 Features are effectively absent

`TelemetryGraphBuilder.FEATURE_COLS` is empty. Process nodes therefore have no substantive input attributes, while file nodes receive a constant one. A homogeneous conversion mostly distinguishes zero-padded processes from constant file nodes.

- node2vec can ignore attributes, but it still needs nontrivial walk structure;
- GraphSAGE needs meaningful type-specific features, structural features, or an explicitly justified learned initialization;
- trainable node IDs are a transductive fallback, not evidence of a portable inductive model.

Build the label-free structural table first. It becomes both Method 1 and a controlled GraphSAGE input/ablation.

## 19.4 The homogeneous walk graph has an implicit operator

Ordinary node2vec will not use the saved `edge_type` values. It will see:

- parent-child only in the recorded direction;
- file touches in both recorded and synthetic reverse directions;
- no explicit distinction among relation meanings during a walk.

That is an operator choice, even if it was not named. Declare and compare:

- directed combined walk;
- undirected association walk;
- relation-weighted walk;
- separate relation-specific walks;
- canonical typed graph plus an explicit projection only for node2vec.

Keep the typed graph canonical so later trace explanations are not forced to reverse-engineer a lossy homogeneous projection.

## 19.5 The graph branches are incomplete as a benchmark

The current saved graph-session branch does not yet populate a comparable session feature matrix and scorer, the node2vec cell prepares a homogeneous object without training an embedding, and the holdout is not yet the basis of a frozen final comparison.

This is not a criticism of an exploratory notebook. It means reported intermediate outputs should be treated as construction diagnostics, not as a finished method ranking.

## 19.6 The raw result suggests local collective signal

The raw baseline contains a useful tension:

- AP is about 0.01630 versus prevalence about $19/1457\approx0.01304$;
- the first malicious session appears at rank 128, worse than the random expected position around 72.9;
- no malicious session appears in the top 100;
- malicious top-15 neighbor purity is about 0.207;
- the corresponding local enrichment is about 16.75 times the base rate;
- 84.2% of malicious sessions have at least one malicious neighbor.

This does **not** establish a successful detector. It suggests that malicious sessions may be locally grouped while the current kNN-distance score treats that compact group as ordinary rather than anomalous.

Preserve two separate experiments:

1. **representation comparison:** one fixed scorer across raw, structural, node2vec, and GraphSAGE representations;
2. **scoring-direction comparison:** after the representation study is frozen, compare point-anomaly scoring with a predeclared collective or small-cluster score.

Neighbor purity uses labels and therefore remains evaluation-only. It cannot become the seed, threshold, or hyperparameter selector on the same split.

# 20. Staged roadmap with decision gates

## Stage 0: canonical evaluation contract

- freeze session identity;
- attach every scoring process to exactly one session;
- save the process-to-session table;
- freeze development and holdout boundaries;
- define the primary all-session population and review budgets.

**Gate:** every method returns exactly one vector and one score per canonical review unit.

## Stage 1: graph construction audit and repair

- load broader context for parent resolution;
- audit parent identifiers and temporal order;
- compare file keys such as filename, path, hash, or a documented composite;
- retain the bipartite graph;
- compare hard file caps with inverse-degree weighting;
- add host/user/time-window focus nodes only as typed ablations;
- name synthetic reverse relations explicitly;
- save edge-survival deltas for every graph variant.

Choose variants using coverage, stability, and semantic validity before looking at test AP.

**Gate:** enough sessions have graph evidence for the claimed scope; walk and message-passing coverage are nontrivial; relation meanings are documented.

## Stage 2: structural baseline

- compute `typed_structural_stats_knn`;
- pool to canonical sessions;
- run lineage-only, affiliation-only, closure/brokerage-only, component/core-only, and full-feature ablations;
- run typed degree-preserving nulls;
- save human-readable explanations.

**Gate:** the real graph produces stable, nontrivial effects beyond degree/activity and shuffled topology.

## Stage 3: node2vec

- freeze the walk projection;
- report walk coverage and isolate handling;
- train across fixed seeds;
- pool with the same session contract;
- compare with random embeddings and shuffled edges.

**Gate:** higher-order walk context improves at least one frozen representation or operational metric without being explained by hubs.

## Stage 4: relational GraphSAGE

- retain edge types;
- use a declared unsupervised objective;
- compare features only, real topology, shuffled topology, and random initialization;
- measure over-smoothing with depth;
- pool and score identically.

**Gate:** learned aggregation adds reproducible value beyond its input features and the same model on null topology.

## Stage 5: frozen three-method comparison

- evaluate structural statistics, node2vec, and relational GraphSAGE;
- include raw and random controls;
- report all-session AP, review budgets, reviews-to-first, uncertainty, and coverage;
- use neighbor purity only as a secondary representation diagnostic;
- select a representation by a predeclared rule.

## Stage 6: signal atlas and faithful tracing

- use Ortega's graph-signal analysis to localize relation, hop, scale, node, and component contributions;
- generate typed, time-valid support subgraphs;
- run deletion/retention tests;
- compare explanations with matched null evidence.

**Gate:** proposed support is stable, model-relevant, and not mostly generic hubs or invalid paths.

## Stage 7: controlled amplification

- preserve intrinsic evidence;
- start with restarted normalized propagation;
- sweep response curves;
- test relation, time, degree, and seed nulls;
- quantify gain and false-positive amplification.

**Gate:** operational ranking improves on the real graph more than on null graphs, with acceptable concentration and stability.

## Stage 8: holdout and another dataset

- execute the untouched holdout once;
- map the schema explicitly on another dataset;
- report missing relations;
- refit unsupervised graph statistics/operators under the frozen procedure;
- distinguish workflow, hyperparameter, and model transfer.

# 21. Dataset agnosticism: a defensible hierarchy

“Dataset agnostic” has several strengths:

| Level | Claim | Realistic now? |
|---|---|---|
| 1. Workflow portability | Same audit, formulas, null rules, metrics, and explanation tests; refit graph statistics per dataset | Yes, primary target |
| 2. Hyperparameter portability | Same graph-construction and scoring hyperparameters work on another dataset | Testable next |
| 3. Model portability | Frozen learned parameters transfer directly | Not yet established |
| 4. Mechanism portability | The same path pattern has the same cyber meaning everywhere | Requires separate domain evidence |

Portable components:

- schema *contract*, not identical schema;
- coverage and topology audit;
- within-type normalizations;
- method families;
- null-generation principles;
- metric and review-budget definitions;
- temporal/path faithfulness tests;
- contribution and provenance reporting.

Dataset-specific components that must be recomputed or mapped:

- entity keys;
- available relation types;
- edge semantics and direction;
- time resolution;
- graph degrees, components, spectra, and backgrounds;
- unsupervised model parameters;
- relation reliability;
- operational base rate and review capacity.

A precise thesis statement is:

> We develop a dataset-portable workflow for auditing typed telemetry graphs, locating candidate structural signal, comparing graph representations under a fixed scorer, tracing support through typed and time-respecting subgraphs, and testing controlled amplification against topology-aware nulls.

Avoid:

- “one universal telemetry graph”;
- “causal attack paths” without causal validation;
- “diffusion models the attack” without transmission semantics;
- “high centrality means threat”;
- “short path means related”;
- “several graph methods agree, so evidence is independent”;
- “the same trained model works everywhere” unless directly tested.

## 21.1 Agentic explanation is a presentation layer, not new evidence

An agent can assemble relation definitions, retrieve supporting events, compare alternative paths, and draft a readable rationale. It should not:

- convert association into causality;
- hide invalid edge times;
- count three correlated model outputs as three independent witnesses;
- invent missing edge semantics;
- replace deletion and null tests with a persuasive narrative.

If multiple agents are used, have them inspect evidence independently before sharing conclusions, record their source provenance, and measure agreement after removing duplicated evidence. Chapter 16's cascade lesson is directly relevant: later consensus may contain no new information.

# 22. Compact reference sheet

| Concept | Formula or test | Project role |
|---|---|---|
| Clustering | $C_v=m_v/\binom{d_v}{2}$ | Local redundancy on triangle-valid views |
| Edge overlap | $\lvert N(u)\cap N(v)\rvert/\lvert(N(u)\cup N(v))\setminus\{u,v\}\rvert$ | Embedded versus boundary edge |
| Random category mixing | cross-edge rate $2pq$ for two groups | Weak homophily null |
| HITS | $h\leftarrow Ma$, $a\leftarrow M^\top h$ | Source/target role features |
| PageRank | $r\leftarrow sP^\top r+(1-s)v$ | Global or personalized flow baseline |
| Threshold | $q=b/(a+b)$ | Nonlinear support stress test |
| Blocking cluster | internal density $>1-q$ | Why a threshold cascade stops |
| Branching summary | $R_0=pk$ | Local expected growth, not topology guarantee |
| Temporal path | $t_1\le\cdots\le t_m$ | Necessary chronological validity |
| Restarted amplifier | $s^{t+1}=\alpha s^0+(1-\alpha)P^\top s^t$ | Conservative graph-support baseline |

## Recommended reading order from this book

1. **Chapters 2-4:** graph semantics, components, BFS, closure, bridges, homophily, and affiliation.
2. **Chapters 13-14:** directed reachability, bow ties, HITS, PageRank, and random walks.
3. **Chapters 20-21:** discoverability, core-periphery bias, contact semantics, and temporal paths.
4. **Chapters 17-19:** response curves and tipping, heavy tails, feedback, thresholds, blocking clusters, and weak-tie limitations.
5. **Chapter 16:** dependent information and cascade fragility, especially before adding agents.
6. **Chapter 5:** only if defensible signed relations emerge.
7. **Chapter 12:** retain the centrality/power caution; defer the bargaining machinery.
8. **The remaining market, auction, voting, and property chapters:** defer for the current scope.

# Final synthesis

This book does not tell the project to build a more elaborate detector. It tells the project how to establish that a graph deserves to be learned from and how to avoid telling a stronger story than the edges support.

The immediate sequence is:

1. unify the review unit;
2. repair and audit typed graph coverage;
3. implement the structural-statistics baseline;
4. compare structural statistics, node2vec, and relational GraphSAGE fairly;
5. localize signal against matched structural nulls;
6. trace short, typed, time-respecting support subgraphs;
7. test explanations by deletion and retention;
8. amplify only when graph gain survives hub, time, provenance, and topology controls.

That sequence preserves the ambition in the original idea. The project can become dataset-portable not by ignoring dataset structure, but by turning structure into an explicit audited input and making every claimed gain survive the right counterfactual.
