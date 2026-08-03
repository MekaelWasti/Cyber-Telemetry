# Parameterize AutoSignal notebook (2)

> can you catch up on this please
>
> User context
>
> Attachments:
> - # Parameterize AutoSignal notebook > I'm making an Agentic Data Gateway/Agentic…: `/work/home/mwasti/.codex/attachments/22ce69e8-9efa-4635-8760-ef39b137f4dd/pasted-text.txt`

<details><summary>3 previous messages</summary>

> I’ll read the attached context and then orient myself in the repository so I can give you a concise state-of-play and pick up where the work left off.
>
> I’ve reached the latest handoff. The project has moved well beyond the original notebook-parameterization question: AutoSignal’s adapter, engine, and Streamlit shell are largely in place, and the next deliberate step is the research-grade graph-signal analysis—not more dashboard refactoring. I’m checking the live repo now to separate what actually exists here from what was only discussed in the prior thread.
>
> The live code matches the handoff: the dynamic stage plan, progress callback, arbitrary typed relations, full method battery, aligned session outputs, and resizable DataMapPlot are present. One important gap is also confirmed: method artifacts export scores and UMAP coordinates, but they do not retain the original high-dimensional representation matrices and dimension names needed for the proposed signal audit. I’m doing a quick test pass and checking whether any parallel/duplicate implementation has appeared outside the committed notebook path.
</details>

I’m caught up.

Current state:

- The committed AutoSignal path is [Notebooks/autosignal_engine.py](./Notebooks/autosignal_engine.py) plus [Notebooks/main.py](./Notebooks/main.py).
- Schema adaptation, sessionization, arbitrary typed relations, Raw/M1/Node2Vec/GraphSAGE, progress reporting, UMAP/DataMapPlot, and exports are implemented.
- The committed engine’s three tests pass.
- A separate untracked `autosignal/` package also exists and its six tests pass, but it is not the implementation wired into the current dashboard. We should avoid accidentally developing both versions.
- The working tree contains substantial pre-existing untracked data/artifacts and a deleted STAMP notebook; I changed nothing.

The next research step is exactly where the previous discussion ended:

```text
retain original representation X and dimension names
→ construct a frozen session kNN graph
→ compute s, Ps, s−Ps, and Ps−P²s
→ diagnose smooth / contrastive / intermediate-scale organization
→ run label-shuffle and degree-preserving-rewire controls
→ perform method-appropriate source analysis
→ test one matched amplifier—or conclude “do not amplify”
```

The immediate missing plumbing is that the engine currently retains anomaly scores and UMAP coordinates, but discards the original high-dimensional method representations. Signal analysis must use those original representations—not UMAP.

I also understand that you want to develop this portion hands-on because it is the core research contribution. I won’t simply build the entire signal-analysis layer. The sensible next session is to jointly specify the smallest representation-artifact contract and then work through the first four graph-signal channels mathematically on one controlled feature set before integrating anything into Streamlit.

> okay you are going to have to make a study guide for all the stuff I need to know and all the concepts for this signal part and WHY

<details><summary>4 previous messages</summary>

> Yes. I’ll turn the theory into a project-specific study guide—not a generic graph-signal-processing textbook summary. It will explain every concept needed to defend the signal-analysis stage, why it belongs, how it maps to AutoSignal, what can and cannot be claimed, and the exact order in which you should learn and apply it.
>
> The key simplification is now clear: you do not need to master all of spectral graph theory. You need a precise chain of ideas—aligned representations, graph signals, operators, signal regimes, null models, matched amplification, and claim boundaries. I’m structuring the guide around that chain and explicitly marking advanced topics such as wavelets and Slepians as deferred, so “rigorous” does not become “unfinishable.”
>
> <details><summary>Created a file</summary>
>
> - Wrote `./SIGNAL_ANALYSIS_STUDY_GUIDE.md` (+1478 -0)
>
> </details>
>
> The guide is now complete at about 6,100 words. It includes the minimum mathematical foundation, a hand-worked example, the scientific purpose of each null/control, method-specific interpretation rules, implementation order, claim wording, oral-defense questions, and a clear boundary between required and deferred theory. I’ve also checked it against the current engine: it correctly identifies the missing representation-artifact layer and does not treat UMAP as scientific input.
</details>

Created the complete project-specific study guide:

[Signal Analysis Study Guide](./SIGNAL_ANALYSIS_STUDY_GUIDE.md)

It covers:

- The complete research argument and why each step exists
- Representations, graph signals, scores, graphs, and operators
- \(W\), \(D\), \(P\), Laplacians, residuals, and graph frequency
- Smooth, contrastive, intermediate-scale, and role-based signal regimes
- The four essential channels: \(s\), \(Ps\), \(s-Ps\), and \(Ps-P^2s\)
- A numerical example worked by hand
- Representation diagnostics versus operational triage metrics
- Label permutations, degree-preserving rewires, and shortcut controls
- What “amplification” must mean scientifically
- Method-specific source analysis for Raw, M1, Node2Vec, and GraphSAGE
- Traceability, removal faithfulness, and causality boundaries
- The exact research and implementation workflow
- Required versus deferred theory
- Oral-defense questions, glossary, study order, and source map

The best starting route is Sections 1–7. Those establish the experiment and the essential math. Sections 8–17 explain how to defend and implement it, while Sections 18–22 are revision and reference material.

> okay before I study this, is this still valid for where my project is? like does it make sense the whoel flow, that we take proposed extracted feature sets and relations per dataset, and then run them across method (we can always change the method suite later after we do evaluations and find which ones actually change over different sets and relations and which are useless) and then do signal analyses on the best methods?

Yes—the overall flow is still valid and fits the current project. The important refinement is that signal analysis should help determine whether a “best” method is genuinely supported, not happen only after choosing a winner from one metric.

```text
unseen telemetry
→ dataset profile
→ agent proposes feature sets + typed relations
→ deterministic validation and preprocessing
→ one canonical session assignment
→ construct method-specific representations
→ apply one common anomaly scorer
→ light localization/control audit across methods
→ select strongest supported representation
→ deep signal-regime and source analysis
→ test one matching amplifier or decline
→ freeze configuration
→ evaluate holdout once
```

## How the proposed inputs feed the methods

Feature sets and graph relations affect different methods differently:

| Method | Feature-set dependent? | Relation dependent? | What it tests |
|---|---:|---:|---|
| Raw session kNN | Yes | No | Aggregate behavioral evidence |
| M1 structural statistics | Mostly no | Yes | Explicit graph roles and relation patterns |
| M2 Node2Vec | No | Yes | Walk-based topology |
| M3 GraphSAGE | Yes | Yes | Feature–relation interaction |

That is essentially what the current engine does:

- Each proposed feature set gets a Raw run.
- M1 runs on the configured graph.
- Node2Vec runs on the configured graph per seed.
- Each feature set gets a GraphSAGE run on that graph.

So you are not forcing the exact same feature matrix through incompatible methods. You are testing the same broader behavioral hypotheses through the representations each method can actually use.

## Relations should remain dataset-specific

Yes, the agent can propose whatever meaningful typed relations the dataset supports. For example:

- process lineage;
- process–file affiliation;
- user–host authentication;
- endpoint communication;
- process–module loading;
- account–resource access.

That is compatible with the portability claim:

> AutoSignal ports the procedure, not identical columns or identical graph semantics.

Each dataset can produce different feature sets and graph relations while still passing through the same validation, representation, scoring, localization, and control protocol.

## Avoid a feature × relation explosion initially

If the agent proposes three feature sets and three separate relation configurations, then GraphSAGE alone creates nine combinations per seed. That quickly becomes a label-visible search.

For the first complete version, I would retain:

- exactly three bounded feature hypotheses;
- one main graph containing all semantically justified relations;
- relation-specific statistics and diagnostics;
- only a small grouped relation ablation for the strongest graph method.

Later, if evaluation shows that relation selection itself is the contribution, relation configurations can become explicit hypotheses. At that point you record the candidate count and control the selection process.

## “Best method” needs two passes

The small correction to your wording is:

> Run a light signal and control audit across the eligible methods, then perform deep source analysis and amplification on the strongest supported method.

### Pass A: compare every representation

For all methods, inspect:

- AP and Recall@100;
- prevalence and random baseline;
- seed stability;
- malicious-neighbor organization;
- graph coverage;
- degree/session-size shortcuts;
- GraphSAGE trained versus random initialization;
- applicable graph-null behavior.

This determines whether the apparent winner is credible.

### Pass B: deeply analyze the selected method

Then perform only the appropriate source analysis:

- Raw: named feature deviations and local feature residuals;
- M1: structural feature deviations and responsible relations;
- Node2Vec: neighborhoods, components, degrees, and rewiring;
- GraphSAGE: trained-versus-random plus one grouped relation removal.

After that, diagnose whether its anomaly score is neighborhood-supported, contrastive, intermediate-scale, or unorganized. That diagnosis determines whether to test diffusion, a residual channel, a scale-difference channel, or no amplifier.

## You can revise the method suite later

That is entirely sensible during development. You may discover that:

- M1 never changes meaningfully across relation sets;
- Node2Vec mostly reproduces degree;
- trained GraphSAGE never beats random initialization;
- certain feature hypotheses are redundant;
- another bounded representation is better justified.

Those are valid reasons to revise the suite on development data. Once the final suite is chosen, freeze it before holdout. The sealed holdout cannot be used to decide which methods to remove or add.

One codebase detail to keep in mind: the dashboard currently runs through [Notebooks/autosignal_engine.py](./Notebooks/autosignal_engine.py), imported by [main.py](./Notebooks/main.py:23). The separate `autosignal/engine.py`, `models.py`, and `config.py` files open in your IDE are a parallel, currently untracked implementation. Before adding signal-analysis code, we should choose one canonical engine so the research layer does not get implemented twice.

So yes: the study guide and overall flow remain valid. The precise research formulation is:

> Agent-proposed, label-blind feature and relation hypotheses are converted into comparable representations. A shared engine evaluates where useful evidence appears. Lightweight controls establish which result is supported, after which one selected representation receives deeper signal-regime analysis, source localization, and at most one matched amplification test.

> okay that sounds good, and what does this part actually mean
>
> after which one selected representation receives deeper signal-regime analysis, source localization, and at most one matched amplification test.
>
> like what does that look like, why do we do it, what's teh expected outcome, and what are the go tos. In layman terms

In plain English, it means:

> Once one representation looks genuinely useful, we zoom in to discover what pattern it is exploiting, where its evidence comes from, and whether graph context can safely improve its ranking.

Suppose the selected representation is:

```text
Raw kNN using the “Network Activity” feature set
```

It gives every session an anomaly score. The method table tells us whether that ranking finds malicious sessions—but it does not yet tell us why it works or whether neighboring sessions can improve it.

## 1. Deeper signal-regime analysis

This asks:

> What does suspicious evidence look like around each session’s neighborhood?

Imagine every session surrounded by its 15 most similar sessions. We calculate four simple views:

| View | Layman meaning |
|---|---|
| Original score \(s\) | How suspicious is this session by itself? |
| Neighbor score \(Ps\) | How suspicious are sessions like this one? |
| Difference \(s-Ps\) | Is this session much stranger than its neighbors? |
| One-hop versus two-hop \(Ps-P^2s\) | Is the evidence concentrated in a small local pocket? |

This gives us a regime.

### Neighborhood-supported

```text
This session is suspicious
and its similar neighbors are suspicious.
```

This suggests a cluster or pocket of related behavior.

### Locally contrastive

```text
This session is suspicious,
but everything around it looks ordinary.
```

This suggests an isolated exception or boundary event.

### Intermediate-scale

```text
The immediate neighborhood is suspicious,
but the broader neighborhood is not.
```

This suggests a small localized pocket that would be diluted by broad smoothing.

### No useful organization

```text
Suspicious scores are scattered without a repeatable neighborhood pattern.
```

Then the graph is not providing useful support, and we should not amplify it.

### Why do this?

Because blindly spreading anomaly scores assumes suspicious sessions should have suspicious neighbors. That might be true—but it might also destroy the signal if attacks are isolated exceptions.

The regime analysis tells us which assumption the data actually supports.

---

## 2. Source localization

This does **not** mean finding the original attacker or reconstructing the attack path.

It means:

> Which parts of the selected representation caused a session to look unusual or well-supported?

What we inspect depends on which method won.

### If Raw features win

We can say:

> This session differs from its neighbors mainly in outbound bytes, registry writes, and duration.

We compare each named feature with its neighborhood average:

```text
session’s tcp_send_size       = unusually high
neighbor-average tcp_send_size = ordinary
difference                     = large
```

This is the most direct kind of explanation.

### If structural statistics win

We might say:

> The session is unusual because its processes have high file fan-out, touch unusually rare entities, and occupy small graph components.

Here the evidence comes from named graph statistics rather than telemetry measurements.

### If Node2Vec wins

Node2Vec dimensions do not have meanings like “network activity dimension.” Instead, we inspect:

- nearest sessions;
- shared entities and neighborhoods;
- component membership;
- degree and hub effects;
- whether performance disappears after graph rewiring.

A defensible explanation is:

> The session occupies an unusual short-walk neighborhood involving these entities.

### If GraphSAGE wins

We check:

- whether trained GraphSAGE actually beats random GraphSAGE;
- what happens when one relation family is removed;
- optionally what happens when a feature family is removed.

For example:

> Most of the useful improvement disappeared when process–file relations were removed, but not when lineage relations were removed.

### Why do this?

The score table tells us that something works. Source localization tells us what type of evidence produced that result and whether it matches a believable behavioral explanation.

It also exposes shortcuts such as:

- one host containing most attacks;
- session size driving scores;
- ubiquitous files acting as hubs;
- degree alone explaining a graph method;
- GraphSAGE training adding nothing beyond random initialization.

---

## 3. One matched amplification test

After identifying the regime, we test one operation designed for that regime.

| Diagnosed pattern | Go-to test |
|---|---|
| Suspicious sessions support one another | Shallow neighbor support or restart diffusion |
| Suspicious sessions are local exceptions | Residual/high-pass score |
| Evidence exists in a small pocket | One-hop-versus-two-hop score |
| Repeated structural role rather than proximity | Do not diffuse; retain role-based ranking |
| No organization beyond controls | Do not amplify |

### Example: neighborhood-supported evidence

Suppose a session has:

```text
Intrinsic score:         0.72
Neighbor support:        0.81
```

We might test a conservative combined score:

\[
s_{\text{new}}=0.5s+0.5Ps.
\]

In layman terms:

```text
50% how suspicious you are
+
50% how suspicious similar sessions are
```

That is the one amplification experiment.

### Why only one?

Because testing 20 filters and reporting whichever happens to perform best would overfit the small development label set.

We diagnose first, choose the matching operation, record the choice, and test it. This creates an actual scientific hypothesis:

> Because the evidence appeared neighborhood-supported, shallow propagation should improve triage.

---

## 4. The matched control

We apply the identical amplifier to two graphs:

1. the real session-neighborhood graph;
2. a rewired graph that retains the same degree pattern but changes who is connected to whom.

Think of it like this:

```text
Real graph:
the same number of roads exists,
and they connect the actual neighborhoods.

Rewired graph:
every location has the same number of roads,
but the roads lead to randomized destinations.
```

Suppose the results are hypothetically:

| Score | AP |
|---|---:|
| Original | 0.10 |
| Amplified on real graph | 0.16 |
| Amplified on rewired graph | 0.11 |

Then:

```text
real gain      = 0.16 − 0.10 = 0.06
rewired gain   = 0.11 − 0.10 = 0.01
specific gain  = 0.06 − 0.01 = 0.05
```

That supports the idea that the actual neighborhood arrangement mattered.

But if both graphs improve from `0.10` to `0.16`, then the improvement probably came from generic smoothing, score averaging, degree, or another nuisance—not meaningful topology.

---

## What the final output looks like

For the selected representation, we want one compact research result:

| Field | Example |
|---|---|
| Selected representation | Raw: Network Activity |
| Diagnosed regime | Neighborhood-supported |
| Strongest sources | outbound bytes, connection count, event rate |
| Initial AP | 0.10 |
| Amplified AP | 0.16 |
| Rewired amplified AP | 0.11 |
| Topology-specific gain | +0.05 |
| Decision | Amplification supported |

And for an individual analyst session:

```text
Session 418

Intrinsic score:        0.72
Neighbor support:       0.81
Final score:            0.765

Strongest local differences:
1. tcp_send_size
2. connection_count
3. event_rate

Strongest supporting neighbors:
Session 392
Session 421
Session 437
```

## The expected outcomes

There are four legitimate endings:

### 1. Localization and amplification

> We found where the evidence lives, identified its regime, and improved triage specifically on the real graph.

This is the strongest positive result.

### 2. Localization without amplification

> The representation contains useful evidence, but graph propagation does not improve it beyond the null.

Still a complete contribution.

### 3. Useful representation, wrong anomaly score

> Malicious sessions occupy meaningful neighborhoods, but the unsupervised anomaly score does not retrieve them effectively.

This suggests retrieval or analyst steering may be more appropriate than zero-shot discovery.

### 4. No supported graph signal

> Under the tested representations and graph constructions, graph organization did not exceed the controls.

Also valid. It means the raw behavioral method remains the defensible choice.

So the entire phrase boils down to three questions:

```text
What shape does the evidence take?
Where is that evidence coming from?
Can we improve it using the graph for the reason we think we can?
```

The signal-analysis section turns “Method X got the highest AP” into an actual research explanation of what worked, why it may have worked, and whether the graph genuinely contributed.

> what can the analyst do after that signal regieme? like is that useful to just give the results and vidualizations of the signal regime

Yes, the signal regime is useful—but a regime label and visualization alone are not enough. The purpose is to tell the analyst how to review and expand the evidence.

The analyst should receive:

```text
What kind of evidence is present?
→ Which ranking should I review?
→ Should I inspect a single exception or a group?
→ Which neighbors/features contributed?
→ How far should I expand the investigation?
```

## Actions by signal regime

| Regime | What it means | Analyst action |
|---|---|---|
| Neighborhood-supported | Suspicious sessions resemble other suspicious sessions | Review the group together and look for shared behavior/entities |
| Locally contrastive | One session is strange relative to otherwise ordinary neighbors | Investigate the individual exception and compare it with its local baseline |
| Intermediate-scale | Evidence occupies a small pocket but disappears at broader range | Review the immediate pocket without expanding indiscriminately |
| Structural-role | Similar graph behavior appears in disconnected places | Search for sessions playing the same role, even if they are not directly connected |
| No graph organization | Neighborhoods provide no reliable extra information | Use the intrinsic anomaly ranking and avoid graph-based expansion |

## What the dashboard should let them do

### 1. Switch between evidence views

The analyst can color and rank sessions by:

- **Intrinsic score:** suspicious by itself
- **Neighbor support:** surrounded by suspicious sessions
- **Positive residual:** more suspicious than its neighbors
- **Residual magnitude:** locally unusual in either direction
- **Scale difference:** concentrated in an immediate pocket
- **Final amplified score:** only when the matched amplifier passed its control

These are different investigation queues, not merely different color schemes.

### 2. Click a session and inspect its evidence

A selected session should show something like:

```text
Session 418
Regime: neighborhood-supported

Intrinsic score:       0.72
Neighbor support:      0.81
Graph increment:      +0.045
Final score:           0.765

Primary feature evidence:
- tcp_send_size
- connection_count
- event_rate

Strongest supporting sessions:
- Session 392
- Session 421
- Session 437
```

This tells the analyst whether the system ranked the session because of its own behavior, its neighborhood, or both.

### 3. Compare a session with its neighbors

For Raw or M1 representations, the analyst should see:

| Feature | Selected session | Neighbor average | Difference |
|---|---:|---:|---:|
| `tcp_send_size` | 4.1 | 0.7 | +3.4 |
| `reg_writes` | 2.9 | 0.3 | +2.6 |
| `duration_seconds` | −1.2 | 0.1 | −1.3 |

That makes “locally unusual” concrete.

For latent methods such as Node2Vec, show:

- closest sessions;
- shared graph entities;
- component and degree context;
- short typed connections;
- whether the relationship survives the rewire control.

Do not present latent coordinate 17 as though it were a meaningful telemetry feature.

### 4. Expand an investigation appropriately

For a neighborhood-supported result, the analyst could select:

> Show the sessions that contributed most to this score.

The interface can then display the supporting group, shared hosts/files/users, and strongest connections.

For a contrastive result, the useful action is different:

> Compare this session against its otherwise normal neighborhood.

The analyst is looking for the exact behavioral discrepancy, not a campaign cluster.

For an intermediate-scale result:

> Show the immediate support pocket and where that support breaks down.

This can help scope an investigation without pulling in an entire component.

## Analyst feedback can become steering

After the analyst confirms one session as relevant, AutoSignal can enter a separate **analyst-steering mode**:

```text
analyst confirms one session
→ use it as an explicit anchor
→ propagate/retrieve through the validated representation
→ rank additional related sessions
→ exclude the original anchor from evaluation
```

That answers:

> Given one confirmed example, what else looks related?

This is different from the original zero-shot anomaly ranking. It is few-shot retrieval, and the UI should label it clearly.

This can be one of the most operationally useful outcomes when the representation has strong malicious-neighbor organization but weak anomaly AP.

## The minimum useful analyst interface

I would make the signal page contain four areas:

1. **Regime summary**

   ```text
   Selected representation: Raw — Network Activity
   Regime: Neighborhood-supported
   Null result: Supported
   Recommended action: Review supporting session groups
   ```

2. **Ranking/map controls**

   Intrinsic, support, residual, scale difference, and validated final score.

3. **Session evidence panel**

   Feature differences, graph increment, supporting and contradicting neighbors, and shared entities.

4. **Investigation actions**

   Expand immediate support, compare with neighbors, mark reviewed, use as an analyst anchor, and export the evidence bundle.

## Why the visualization matters

The visualization is useful when it lets the analyst answer:

- Is this a single exception or part of a group?
- Which sessions support its ranking?
- Where does the suspicious pocket end?
- Which behavioral measurements differ?
- Is graph context helping or merely pulling everything toward a hub?

A colored scatter plot without those answers is mostly presentation.

So the research output is the validated regime and control result; the analyst value comes from turning that result into the correct investigation queue, comparison context, and expansion behavior.

> okay that sounds very good, and one LAST THING would I leave it there or would I allow one more agent prompt to do something to the embeddings or feature/relation set that the best method used. and use the signal results to enhance the embeddings for the analyst or something like that

Yes—you can add one more agent step, but I would not let it directly rewrite the winning embedding or silently change the experiment.

The clean architecture is:

```text
Frozen scientific result
→ deterministic signal-informed analyst views
→ agent explains evidence and proposes one optional follow-up
```

The distinction matters because changing feature weights or relations after seeing label performance creates a new method. It cannot be presented as an explanation of the original method.

## My recommended final agent

Use a **Signal Interpretation and Refinement Agent**.

Give it only structured results:

- selected method and feature hypothesis;
- diagnosed signal regime;
- null-control verdict;
- named feature residuals;
- important relations;
- supporting and contradicting neighbors;
- graph coverage and shortcut warnings;
- before/after amplification metrics.

The agent can then produce:

1. A plain-language explanation of the result.
2. Recommended analyst actions.
3. The most useful map/evidence view.
4. One optional, bounded follow-up hypothesis.
5. An honest statement of uncertainty and limitations.

It should not generate arbitrary Python or alter embeddings directly.

## For the analyst view, keep the embedding fixed

The safest and most useful design is to retain the original UMAP positions and change the overlays:

```text
same session positions
→ color by intrinsic score
→ color by neighbor support
→ color by local residual
→ color by scale difference
→ color by validated amplified score
→ display supporting-neighbor edges
```

Why keep positions fixed?

If points move every time the signal view changes, the analyst cannot tell whether the method changed the evidence or merely changed the visualization. Fixed positions let them compare the same sessions across evidence channels.

The agent can say:

> This representation is neighborhood-supported. Show the amplified ranking, immediate supporting neighbors, and shared network features.

Or:

> This representation is contrastive. Keep the intrinsic map and highlight sessions with large positive local residuals.

That is genuinely agentic while keeping the evidence deterministic.

## If you really want a signal-enhanced representation

There is a defensible deterministic construction:

\[
X_{\text{signal}}
=
[X,\;PX,\;X-PX].
\]

In plain language, each session receives:

- its original features;
- what its neighbors predict;
- how it differs from those neighbors.

For named Raw or M1 features, this could create a powerful analyst representation:

```text
original behavior
+ neighborhood context
+ local behavioral discrepancy
```

But this is a **new representation**, not merely a visualization. It must:

- receive its own method key;
- use declared scaling;
- be rescored from scratch;
- be compared with the original;
- be tested on the rewired graph;
- be selected only on development data;
- be frozen before holdout.

The resulting map should be labelled something like:

> Signal-Augmented Representation — Exploratory

I would not allow the LLM to invent the transformation. The agent can select from a tiny allowed vocabulary based on the diagnosed regime:

| Regime | Allowed proposal |
|---|---|
| Neighborhood-supported | Add \(PX\) or shallow score support |
| Contrastive | Add \(X-PX\) residual channels |
| Intermediate-scale | Add \(PX-P^2X\) scale channels |
| Structural-role | Create a relation-specific view |
| No supported signal | Propose no modification |

Deterministic code constructs and validates it.

## What about changing features or relations?

The agent may propose one development-only refinement, such as:

- remove a relation shown to be a shortcut;
- isolate a relation family that appears to carry signal;
- add local residuals for the strongest named features;
- remove a feature dominated by host identity;
- create a narrower behavioral hypothesis.

But the proposal must start a new versioned experiment:

```text
Original configuration
→ signal evidence
→ agent proposes one exact config diff
→ validator approves/rejects
→ engine reruns complete pipeline
→ compare with original and nulls
```

Never:

```text
agent edits winner
→ dashboard silently displays improved result
```

The latter would erase the boundary between analysis, optimization, and evaluation.

## The analyst can also provide an anchor

A particularly useful optional step is:

```text
analyst confirms one suspicious session
→ agent summarizes what made it relevant
→ deterministic anchored retrieval finds related sessions
```

This does not change the original zero-shot ranking. It creates a separately labelled:

> Analyst-Steered Investigation

That lets the analyst ask:

- “Find more sessions like this.”
- “Restrict expansion to different hosts.”
- “Show only support involving process–file relations.”
- “Explain why these sessions were retrieved.”
- “Show the immediate pocket without broader diffusion.”

This is likely more operationally valuable than repeatedly regenerating embeddings.

## Where I would stop the sprint

For the core project:

```text
validated signal regime
+ source localization
+ one controlled amplifier
+ fixed interactive evidence views
+ agent-generated explanation and analyst actions
```

That is complete.

I would make automated feature/relation refinement an optional, explicitly exploratory extension. If included, allow exactly one versioned proposal and rerun—not an open-ended agent loop.

So the best final design is:

> The engine computes the evidence, graph operators enhance it deterministically, the agent explains it and proposes bounded actions, and the analyst decides whether to launch a separate refinement or steering run.

That keeps the project agentic without allowing the LLM to manufacture the scientific result.

> and is that whole project novel with that

<details><summary>2 previous messages</summary>

> I can give you a provisional answer from the design, but “novel” is a literature claim, so I’m checking the closest published work before saying yes. I’ll separate novelty of the individual ingredients from novelty of the combined research procedure—because your strongest contribution is likely the integration and controlled localization workflow, not inventing every component.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site:arxiv.org graph signal processing cybersecurity anomaly detection telemetry graph filter ...`
>
> Searched the web for `"graph signal processing" cybersecurity intrusion detection ...`
>
> Searched the web for `site:arxiv.org LLM cyber telemetry feature engineering schema mapping anomaly detection ...`
>
> Searched the web for `site:arxiv.org unsupervised graph anomaly detection frequency adaptive high low frequency graph signal ...`
>
> Searched the web for `site:arxiv.org graph representation selection anomaly detection compare structural node2vec graphsage cybersecurity ...`
>
> Searched the web for `"AutoG" "automatic graph construction" ICLR 2025 title ...`
>
> </details>
</details>

Yes—potentially novel as an integrated research framework, but not because every individual ingredient is new.

The defensible position is:

> AutoSignal’s novelty lies in combining agentic schema adaptation, controlled representation-family localization, graph-signal regime diagnosis, topology-preserving validation, and actionable analyst evidence into one dataset-portable cyber-telemetry procedure.

I would not claim that AutoSignal invents LLM feature engineering, graph anomaly detection, GraphSAGE, graph filtering, or analyst attribution individually.

## What already exists

Several parts have close prior work:

- LLM-driven feature engineering and candidate proposal already exist. Recent work explicitly separates LLM proposal from deterministic or human-guided selection, which resembles your trust boundary. [Human–LLM Collaborative Feature Engineering](https://arxiv.org/abs/2601.21060)
- LLM-based automatic graph construction from tabular data already exists. AutoG generates graph schemas and evaluates their downstream quality. [AutoG, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c01dfe01b97aadc10fc16a201faa80d8-Abstract-Conference.html)
- Cybersecurity systems already use provenance graphs and self-supervised representation learning. MAGIC uses masked graph representation learning for APT detection; PROGRAPHER embeds temporal provenance-graph snapshots. [MAGIC](https://www.usenix.org/conference/usenixsecurity24/presentation/jia-zian), [PROGRAPHER](https://www.usenix.org/conference/usenixsecurity23/presentation/yang-fan)
- Graph-signal and multiscale anomaly detection are established ideas. Prior work already detects anomalous nodes relative to local and multiscale graph contexts. [Multi-Scale Anomaly Detection on Attributed Networks](https://ojs.aaai.org/index.php/AAAI/article/view/5409)
- Analyst-facing graph attribution is also an active area. ORTHRUS focuses specifically on producing higher-quality attribution and concise evidence for analysts. [ORTHRUS](https://www.usenix.org/conference/usenixsecurity25/presentation/jiang-baoxiang)

Therefore, avoid claims such as:

- “The first agent to construct graphs from tabular data.”
- “The first graph-based cyber anomaly detector.”
- “The first application of GSP to anomaly detection.”
- “The first analyst-facing explanation system.”

## What appears distinctive about AutoSignal

Based on this targeted search, I did not find a system with this exact combination:

```text
arbitrary telemetry dataset
→ LLM proposes bounded feature hypotheses and typed relations
→ deterministic schema/type/leakage validation
→ one canonical session population
→ common comparison across:
     raw behavior
     explicit structural roles
     short-walk topology
     learned typed feature–topology interaction
→ determine where task-relevant organization appears
→ diagnose its smooth/contrastive/intermediate regime
→ choose one matching graph operation
→ require gain beyond a degree-preserving rewire
→ return intrinsic evidence, graph increment, sources, and analyst actions
```

The unusual part is that AutoSignal is not merely choosing the highest-performing detector. It asks a structured scientific question:

> Where does useful evidence appear in an unfamiliar telemetry dataset, what form does that evidence take on the graph, and is graph-based amplification genuinely topology specific?

Most related systems concentrate on one of these problems:

- automatically constructing a graph;
- learning one anomaly detector;
- learning one provenance embedding;
- finding graph anomalies;
- or reconstructing analyst attribution.

AutoSignal treats those as stages of a controlled localization procedure.

## Your strongest potential contributions

I would describe four contributions.

### 1. Agentic telemetry adaptation under a strict trust boundary

The agent proposes:

- behavioral feature hypotheses;
- session fields;
- typed graph relations;
- quality and uncertainty assessments.

The deterministic engine validates and executes them. The LLM neither generates arbitrary transformations nor declares the winner.

The idea of constrained LLM planning is not itself unique, but applying it to produce a shared experimental contract for arbitrary cyber telemetry is potentially distinctive.

### 2. Representation-family signal localization

Rather than proposing another detector, AutoSignal compares where evidence appears:

- aggregate behavior;
- explicit graph roles;
- short-walk proximity;
- learned feature–relation interaction.

Everything uses the same canonical sessions and scorer.

That shared comparison is important. It turns:

> GraphSAGE achieved AP 0.14.

into:

> Under a controlled session and scoring contract, useful evidence appeared primarily in explicit structural roles rather than raw features, walk proximity, or learned relational encoding.

That is a much more interesting research result.

### 3. Regime-matched, null-gated amplification

AutoSignal does not assume all useful graph evidence should be smoothed. It diagnoses:

- neighborhood-supported evidence;
- local contrast;
- intermediate-scale pockets;
- structural-role organization;
- or no usable organization.

It then tests only the matching operation and compares its improvement with a degree-preserving rewire.

That coupling is likely the most original part:

```text
diagnose the evidence regime
→ choose the corresponding operator
→ require topology-specific improvement
→ otherwise decline amplification
```

Graph-frequency anomaly models exist, but your project applies the idea as a controlled decision protocol across agent-generated cyber representations—not merely as another fixed spectral neural network.

### 4. Evidence-plane analyst interaction

The analyst does not receive only an embedding or anomaly score. They receive:

- intrinsic score;
- neighborhood support;
- graph-derived increment;
- local feature residuals;
- supporting and contradicting sessions;
- relation or feature sources;
- null verdict;
- recommended investigation mode.

This is valuable, although it becomes a strong research contribution only if you evaluate faithfulness or analyst utility. Otherwise, it is an excellent system contribution.

## Does the final agent make it more novel?

A final explanation agent does not add much novelty by itself. LLM-generated explanations and recommendations are now common.

It strengthens the project if the agent is constrained to:

- translate computed evidence;
- cite exact sessions, features, relations, and control results;
- recommend an analyst view based on the diagnosed regime;
- propose at most one versioned follow-up experiment;
- never alter the frozen scientific result.

If you want to claim that agent as a research contribution, evaluate something measurable:

- factual grounding rate;
- unsupported-claim rate;
- analyst task completion time;
- analyst identification accuracy;
- cognitive load;
- agreement between reported explanations and deletion-faithfulness results.

Without that evaluation, present it as the analyst interface, not a central novelty claim.

## How novel is it at different levels?

### Master’s project or dissertation

Yes—comfortably novel enough if completed rigorously. It combines a real system contribution with a focused empirical research question and falsifiable controls.

### Workshop or applied research paper

Potentially strong. You would need:

- clear comparison with AutoG-like graph construction and provenance anomaly systems;
- at least two meaningfully different telemetry schemas or datasets;
- ablations for agent-selected features and relations;
- representation and signal-regime results;
- rewired controls;
- an honest negative-result path;
- frozen evaluation.

### Major security or ML venue

Promising, but the novelty burden would be higher. You would likely need:

- multiple datasets;
- stronger contemporary baselines;
- repeated agent/configuration reliability experiments;
- uncertainty across seeds and datasets;
- formal evaluation of analyst attribution;
- evidence that the integrated procedure solves something existing end-to-end systems do not.

## The novelty statement I would currently use

> We introduce AutoSignal, a schema-adaptive cyber-telemetry triage framework in which an LLM proposes bounded behavioral feature and typed-relation hypotheses, while a deterministic engine evaluates them across aggregate, structural, walk-based, and learned relational representations under a common session and scoring contract. AutoSignal then diagnoses the graph-signal regime of the strongest supported representation and conditionally applies one matched amplifier whose gain must exceed a degree-preserving topology null. The resulting ranking preserves intrinsic, neighborhood, feature, and relation-level evidence for analyst review.

That is specific, defensible, and meaningfully different from claiming “we built an agentic GNN detector.”

The honest bottom line: the individual pieces are not novel, but the full constrained procedure appears plausibly novel and research-worthy. A formal related-work review could still uncover a closer system, so you should call it a proposed contribution until the literature review and experiments substantiate it.

> well long as it's METHOD wise novel. Like of course the individual components aren't novel. I can take anything and pull it apart and be like well THAT part isnt' novel because we alraedy do that somehow. I understand what you mean but the point of this project was to handle unstructured telemetry in a way that might show what parts are worth exploring and how. If this is on the road to that in a novel way, then I'm fine with that. Of course if I was to publish I would do all kinds of experiments that's a different story from is this something on its own

Yes—method-wise, this is a coherent and plausibly novel contribution.

The method is not “LLM + GraphSAGE + UMAP.” It is the decision procedure connecting them:

```text
unfamiliar telemetry schema
→ agent proposes behavioral and relational hypotheses
→ deterministic engine validates them
→ common method suite tests where useful organization appears
→ representation comparison localizes the promising evidence plane
→ signal-regime analysis determines how that evidence is organized
→ matched controls determine whether the graph genuinely contributes
→ analyst receives what to explore, why, and how
```

That is a method for answering:

> Given unfamiliar telemetry, which behavioral features, relations, representations, and neighborhood patterns deserve investigation?

That is different from ordinary anomaly detection, whose main question is:

> Which rows are anomalous?

## Why it is more than pipeline glue

The stages constrain one another scientifically:

- The agent proposes possibilities but cannot select the winner.
- Every representation uses the same sessions and scorer.
- The comparison identifies where evidence appears—not merely the highest-performing model.
- The signal regime determines the permitted next operation.
- The rewire determines whether the apparent graph benefit is genuine.
- The method can abstain when no representation or amplifier is supported.
- The analyst receives an investigation strategy, not only a model score.

The conditional logic is the contribution:

```text
if evidence is neighborhood-supported:
    investigate groups and test shallow support

elif evidence is locally contrastive:
    investigate exceptions and retain residual evidence

elif evidence is intermediate-scale:
    investigate the immediate pocket without broad diffusion

elif evidence is role-based:
    investigate repeated structural patterns

else:
    avoid graph amplification and retain the intrinsic ranking
```

Most systems commit to one graph, representation, and anomaly assumption. AutoSignal is instead a bounded procedure for determining which assumption the current dataset supports.

## It matches your original vision

Your vision was not simply “build a better detector.” It was:

> Take unfamiliar telemetry and determine what parts of its behavioral and relational structure are worth exploring—and how they should be explored.

AutoSignal is directly on that road:

| Original question | AutoSignal answer |
|---|---|
| Which columns might matter? | Agent-proposed feature hypotheses |
| Which relationships might matter? | Agent-proposed typed relations |
| Does behavioral or graph structure matter more? | Shared representation comparison |
| What kind of graph pattern exists? | Signal-regime diagnosis |
| Which specific evidence drove it? | Source localization |
| Should the graph expand the evidence? | Matched amplification and rewire gate |
| What should the analyst do? | Regime-specific investigation workflow |

That is a unified methodological contribution even though its operators and models have prior foundations.

## Experiments establish value, not existence

You are also right about the distinction.

The method can be original as a designed research procedure before a publication-scale evaluation. Experiments would establish:

- whether the agent proposes meaningful configurations;
- whether different datasets select different evidence planes;
- whether the localization is stable;
- whether the controls reject shortcuts;
- whether analysts benefit;
- whether the method ports across schemas.

Those experiments determine how strongly you can claim it works and generalizes. They do not create the conceptual method from nothing.

## One terminology adjustment

For CSV, Parquet, or tables with unfamiliar column semantics, I would say:

- **schema-heterogeneous telemetry**;
- **unfamiliar telemetry schemas**;
- **semantically unstandardized telemetry**;
- or **arbitrary tabular telemetry**.

“Unstructured telemetry” commonly suggests raw natural-language logs, command-line text, packet payloads, or documents. AutoSignal currently assumes the input has rows and columns, even if their meanings and types are unknown.

A precise framing would be:

> AutoSignal is a schema-adaptive method for discovering which behavioral and relational views of unfamiliar tabular cyber telemetry merit analyst investigation.

## The method-level novelty statement

> AutoSignal operationalizes telemetry exploration as a constrained localization problem. An agent maps an unfamiliar schema into bounded behavioral-feature and typed-relation hypotheses. A deterministic engine evaluates those hypotheses across complementary representation families under a common session and scoring contract. Graph-signal analysis then identifies how evidence is organized and conditionally selects an analyst investigation and amplification strategy, subject to matched topology controls.

Yes—that stands on its own as a legitimate method contribution. The models are ingredients; the novel object is the schema-to-investigation decision procedure.

> was the filter bank the signal regime?

Almost. The filter bank is the tool used to diagnose the signal regime; the regime is the conclusion drawn from its results.

```text
Filter bank = the tests
Signal regime = what the tests reveal
```

The fixed filter bank is:

| Channel | Question | Possible regime |
|---|---|---|
| \(s\) | Is the session suspicious by itself? | Intrinsic evidence |
| \(Ps\) | Are its neighbors also suspicious? | Neighborhood-supported/smooth |
| \(s-Ps\) | Is it different from its neighbors? | Contrastive |
| \(Ps-P^2s\) | Is support concentrated nearby rather than broadly? | Intermediate-scale |

For example:

```text
Original AP:             0.10
Neighbor-support AP:     0.16
Residual AP:             0.07
Scale-difference AP:     0.09
```

If neighbor support also exceeds the appropriate null controls, the conclusion might be:

> The evidence is predominantly neighborhood-supported.

Then the filter bank has diagnosed the regime.

Afterward, one corresponding operation may become the amplifier:

```text
diagnosis: neighborhood-supported
→ test: shallow support/restart diffusion
```

So the filter bank has two roles:

1. **Diagnosis:** expose how evidence is organized.
2. **Candidate action:** provide the matching operation for one controlled amplification test.

The important guardrail is that the bank is small and declared in advance. We should not test dozens of filters, choose the best label result, and retroactively name that the “regime.” The regime should be supported by the fixed channels, graph diagnostics, and null comparisons—not merely whichever column has the highest AP.

> okay so if we change the filter bank to be
>
> Neighborhood-Supported (Homophily)You want to find nodes where *both* the intrinsic score and the neighbor score are high. You can evaluate this using an element-wise product or a simple weighted combination:$$s_{\text{supported}} = \alpha s + (1 - \alpha) Ps$$*(Where $\\alpha$ is a tuning parameter, usually $0.5$)*.Locally Contrastive (The Residual)You want to find nodes that are highly suspicious, but whose neighbors are completely normal. You subtract the neighbor average from the node's intrinsic score:$$s_{\text{residual}} = s - Ps$$A high positive number here flags a "sore thumb" anomaly. If a node scores $0.9$ but its neighbors average $0.2$, its residual is $0.7$.Intermediate-Scale (The Pocket)You want to find nodes where the immediate neighborhood is suspicious, but the broader network is normal.$$s_{\text{pocket}} = Ps - P^2s$$A high positive number means the suspicion is concentrated strictly within a 1-hop radius and dilutes rapidly at 2 hops, telling you to restrict your investigation to the immediate cluster.
>
> and then the No useful organization one
>
> then that would be the diagnosis?

Yes—with one important separation:

- \(Ps\), \(s-Ps\), and \(Ps-P^2s\) diagnose the regime.
- \(\alpha s+(1-\alpha)Ps\) is the candidate amplified ranking after neighborhood support has been diagnosed.
- “No useful organization” is an outcome, not a filter.

A clean structure is:

## Diagnostic channels

\[
\begin{aligned}
\text{intrinsic} &= s\\
\text{neighbor evidence} &= Ps\\
\text{local contrast} &= s-Ps\\
\text{pocket evidence} &= Ps-P^2s
\end{aligned}
\]

Then classify:

| Evidence observed | Diagnosis |
|---|---|
| High-score sessions also have high \(Ps\) | Neighborhood-supported |
| Malicious/high-priority sessions have large positive \(s-Ps\) | Locally contrastive |
| They have large positive \(Ps-P^2s\) | Intermediate-scale pocket |
| None exceeds the appropriate nulls reliably | No useful organization |

## Candidate rankings shown to the analyst

Once diagnosed, the analyst-facing scores can be:

### Neighborhood-supported

\[
s_{\text{supported}}
=
\alpha s+(1-\alpha)Ps.
\]

This balances intrinsic and neighboring evidence.

For the minimal experiment, freeze \(\alpha=0.5\). Do not repeatedly tune it against the small label set.

### Locally contrastive

\[
s_{\text{residual}}=s-Ps.
\]

Rank high positive values when specifically looking for:

> Suspicious session, ordinary neighborhood.

You may also visualize \(|s-Ps|\), but that answers a broader question: “Which sessions disagree with their neighborhood in either direction?”

### Intermediate-scale pocket

\[
s_{\text{pocket}}=Ps-P^2s.
\]

Rank high positive values when immediate-neighborhood support is stronger than two-step context.

One wording adjustment: this does not prove suspicion exists “strictly within one hop.” \(P^2s\) aggregates two-step walks, including possible returns through the graph. The defensible interpretation is:

> Immediate-neighborhood support decays at the two-step scale under this operator.

### No useful organization

Keep the original score:

\[
s_{\text{final}}=s.
\]

Do not apply graph amplification.

## The complete decision

```text
Compute s, Ps, s−Ps, and Ps−P²s
→ compare their behavior with labels and nulls
→ identify the dominant supported regime
→ select its one matching analyst ranking
→ test that ranking on the real and rewired graph
→ retain it only if the real topology provides specific gain
```

For example:

```text
Observation:
- high-score sessions have high neighbor support
- residual channel is weak
- pocket channel is weak
- neighbor organization exceeds label-shuffle null
- supported ranking improves real graph more than rewire

Diagnosis:
Neighborhood-supported

Final analyst ranking:
0.5s + 0.5Ps
```

Or:

```text
Observation:
- suspicious sessions have ordinary neighbors
- positive residual is strong
- smoothing makes AP worse
- residual behavior exceeds nulls

Diagnosis:
Locally contrastive

Final analyst ranking:
s − Ps
```

One final nuance: a dataset can exhibit mixed regimes. Some attacks may be clustered while others are sore-thumb anomalies. For the bounded research experiment, report a dominant regime and any clear secondary regime, but choose at most one primary amplifier. If no regime is stable enough to dominate, report the result as mixed/inconclusive rather than forcing a winner.

> okay so right now I have to compute s, A, D, which will allow me to compute P, which will allow me to compute Ps which will allow me to compute P2s?

Exactly. For the first session-level signal analysis, the dependency chain is:

```text
selected representation X
        ↓
session adjacency A
        ↓
degree matrix D
        ↓
transition matrix P = D⁻¹A
        ↓
Ps
        ↓
P²s = P(Ps)
```

More precisely:

## 1. Start with \(X\) and \(s\)

From the selected method you need:

- \(X\in\mathbb{R}^{N\times F}\): original session representation
- \(s\in\mathbb{R}^{N}\): anomaly score for each session
- ordered session IDs shared by both

Use \(X\), not UMAP coordinates.

## 2. Construct \(A\)

Build a \(k\)-nearest-neighbor graph from \(X\), initially with \(k=15\).

\[
A_{ij}=
\begin{cases}
1,&\text{sessions }i,j\text{ are connected}\\
0,&\text{otherwise}
\end{cases}
\]

If you use weighted edges, call it \(W\), but the procedure is identical.

For the first experiment, this should be a session-to-session adjacency matrix—not the original process/file heterogeneous adjacency.

## 3. Compute \(D\)

\(D\) contains each session’s degree:

\[
D_{ii}=\sum_j A_{ij}.
\]

For example:

\[
D=
\begin{bmatrix}
3&0&0\\
0&5&0\\
0&0&2
\end{bmatrix}
\]

means the sessions have 3, 5, and 2 neighbors.

## 4. Compute \(P\)

\[
P=D^{-1}A.
\]

Each row of \(P\) should sum to 1. Therefore:

\[
(Ps)_i=\sum_jP_{ij}s_j
\]

is session \(i\)’s neighbor-average anomaly score.

You need an explicit policy for degree-zero isolates. A conservative option is to set \(P_{ii}=1\) for isolates, meaning that no graph evidence changes their score.

## 5. Compute \(Ps\)

```python
p1s = P @ s
```

This is the one-hop neighborhood evidence.

## 6. Compute \(P^2s\)

```python
p2s = P @ p1s
```

Equivalent to:

```python
p2s = P @ P @ s
```

Do not calculate `(P @ s) ** 2`. \(P^2s\) means applying the neighbor operator twice, not squaring the values.

## 7. Build the channels

```python
intrinsic = s
neighbor_support = p1s
local_contrast = s - p1s
local_contrast_magnitude = abs(s - p1s)
pocket = p1s - p2s
supported_candidate = 0.5 * s + 0.5 * p1s
```

So the full minimal calculation is:

```python
A = build_session_knn_adjacency(X, k=15)
D = diagonal_matrix(A.sum(axis=1))
P = inverse(D) @ A

p1s = P @ s
p2s = P @ p1s

channels = {
    "intrinsic": s,
    "neighbor_support": p1s,
    "local_contrast": s - p1s,
    "pocket": p1s - p2s,
}
```

The crucial alignment assertion is:

```python
assert X.shape[0] == len(s) == A.shape[0] == A.shape[1]
```

And the session ordering used by \(X\), \(s\), and \(A\) must be identical. Once those objects exist, the actual filter-bank computation is very small; most of the care belongs in constructing \(A\), handling isolates, and preserving alignment.

> so for each method, X is the session feature set? and s are the knn scores?

Yes, with one terminology adjustment:

> For every method, \(X\) is its session-level representation matrix—not necessarily an original feature set.

And:

> \(s\) is the kNN anomaly-score vector computed from that method’s \(X\).

| Method | What \(X\) contains | What \(s\) contains |
|---|---|---|
| Raw | Session aggregates from one agent-proposed feature set | kNN distances in that behavioral feature space |
| M1 structural | Session-level degree/relation/structural statistics | kNN distances in structural-statistics space |
| Node2Vec | Pooled session Node2Vec embeddings | kNN distances in walk-embedding space |
| GraphSAGE random | Pooled random GraphSAGE embeddings | kNN distances in random-encoder space |
| GraphSAGE trained | Pooled trained GraphSAGE embeddings | kNN distances in learned embedding space |

For method \(m\):

\[
X_m
\rightarrow
s_m=\operatorname{kNNScore}(X_m)
\]

Then construct that representation’s session graph:

\[
X_m
\rightarrow
A_m
\rightarrow
D_m
\rightarrow
P_m
\]

And calculate:

\[
P_ms_m,\qquad P_m^2s_m,\qquad
s_m-P_ms_m,\qquad
P_ms_m-P_m^2s_m.
\]

## Example

For the Raw “Network Activity” hypothesis:

```text
X_raw_network:
rows    = sessions
columns = connection_count, bytes_out, tcp_send_size, ...

s_raw_network:
one kNN anomaly score per session
```

For Node2Vec:

```text
X_node2vec:
rows    = sessions
columns = latent embedding dimensions 1–64

s_node2vec:
one kNN anomaly score per session
```

Both are session representations, but only the Raw dimensions have direct feature meanings.

## Method keys matter

Every complete variant has its own \(X\) and \(s\):

```text
raw_session_knn::Network Activity
raw_session_knn::Resource Activity
node2vec_knn::seed=42
graphsage_trained::Network Activity::seed=42
```

Stochastic seeds should not be treated as competing feature hypotheses. Run the signal audit per seed and look for a stable regime across seeds.

## Scaling matters

The session graph and kNN score should use the same declared representation geometry. If the kNN scorer standardizes \(X\), retain the standardized matrix used by the scorer:

```text
X_original
→ declared scaling
→ X_scaled
→ kNN score s
→ session graph A
```

Otherwise, the graph and anomaly score could be based on different distance definitions.

So the precise contract for each method is:

```text
method_key
ordered session_ids
X_scaled
dimension_names, when meaningful
s
seed
representation type
scaling metadata
```

The random ranking baseline does not need a signal-regime analysis because it has no meaningful representation to interpret. GraphSAGE random initialization is retained as a control for trained GraphSAGE.

> from scipy import sparse
>
> def build_session_knn_operator(X, k = 15):
>     """Construct a sparse kNN operator for the given feature matrix X.
>     This is a session similarity graph where each session is connected to its k nearest neighbors based on the feature representation.
>     Constructed from raw features from the session table.
>     """
>
>     X = np.asarray(X, dtype=np.float32)
>     n = len(X)
>     effective_k = min(k, n - 1)
>
>     # Use cKDTree to find the k nearest neighbors for each session
>     _, neighbors = cKDTree(X).query(X, k=effective_k + 1, workers=-1)
>
>     neighbors = np.asarray(neighbors)[:, 1:]  # Exclude self (the first neighbor is the point itself)
>
>     rows = np.repeat(np.arange(n), effective_k)
>     cols = neighbors.reshape(-1)
>     values = np.ones(len(rows), dtype=float)
>
>     # Binary directed kNN adjacency
>     A = sparse.csr_matrix((values, (rows, cols)), shape=(n, n))
>
>     #
>     A = A.maximum(A.T)  # Make it symmetric (undirected)
>     A.setdiag(0)  # Remove self-loops
>     A.eliminate_zeros()  # Remove explicit zeros
>
>     # Row-normalized propagation operator P = D^(-1) A
>     degree = np.asarray(A.sum(axis=1)).ravel()
>     inverse_degree = np.divide(
>         1.0,
>         degree,
>         out=np.zeros_like(degree),
>         where=degree > 0,
>     )
>
>     P = sparse.diags(inverse_degree) @ A
>
>     return A, P
>
> does this already do it

Yes—this already constructs \(A\) and \(P\).

Specifically:

```python
A = sparse.csr_matrix(...)
```

creates the directed kNN adjacency, and:

```python
A = A.maximum(A.T)
```

turns it into a symmetric union-kNN adjacency.

Then:

```python
degree = np.asarray(A.sum(axis=1)).ravel()
```

is the diagonal of \(D\), and:

```python
P = sparse.diags(inverse_degree) @ A
```

computes:

\[
P=D^{-1}A.
\]

You are computing \(D\) implicitly as a degree vector rather than constructing and returning the full diagonal matrix—which is completely fine.

It does not yet calculate \(s\), \(Ps\), or \(P^2s\). After calling it:

```python
A, P = build_session_knn_operator(X_scaled, k=15)

s = np.asarray(knn_scores, dtype=float)

assert X_scaled.shape[0] == len(s)
assert A.shape == (len(s), len(s))
assert P.shape == A.shape

Ps = P @ s
P2s = P @ Ps

channels = {
    "intrinsic": s,
    "neighbor_support": Ps,
    "local_contrast": s - Ps,
    "local_contrast_magnitude": np.abs(s - Ps),
    "pocket": Ps - P2s,
    "supported_candidate": 0.5 * s + 0.5 * Ps,
}
```

A few important corrections are needed before relying on it scientifically.

### Use the method representation, not always raw features

This docstring line is too specific:

```python
Constructed from raw features from the session table.
```

It should say:

```python
Constructed from the selected method's scaled session representation.
```

For Raw, \(X\) is the session feature matrix. For M1 it is structural statistics; for Node2Vec and GraphSAGE it is the pooled embedding matrix.

### Ensure \(X\) is finite and scaled

Add checks such as:

```python
if X.ndim != 2:
    raise ValueError("X must be a two-dimensional representation matrix.")

if len(X) < 2:
    raise ValueError("At least two sessions are required.")

if not np.isfinite(X).all():
    raise ValueError("X must contain only finite values.")

if k < 1:
    raise ValueError("k must be at least 1.")
```

The graph should use the same scaled geometry used by the kNN scorer.

### Duplicate rows can break the self-removal assumption

This line assumes the first returned index is always the query session itself:

```python
neighbors = np.asarray(neighbors)[:, 1:]
```

Normally it is, but exact duplicate representations can tie at distance zero, so another duplicate may appear first. Then the session’s own index could remain in `neighbors` before you later remove the diagonal, leaving that row with fewer than \(k\) selected neighbors.

For exploratory work this may not immediately break the pipeline, but the robust implementation should remove each row’s own index explicitly.

### Your graph has union symmetrization

```python
A.maximum(A.T)
```

means:

> Connect sessions \(i\) and \(j\) when either one considers the other a neighbor.

That is the union-kNN graph discussed in the study guide. It usually gives good coverage. It is not mutual kNN, which would retain an edge only when both sessions select each other.

### Useful validation

For this union graph, with at least two sessions and \(k\geq1\), every session should have a nonzero degree. Confirm:

```python
row_sums = np.asarray(P.sum(axis=1)).ravel()

assert np.all(degree > 0)
assert np.allclose(row_sums, 1.0)
assert A.diagonal().sum() == 0
assert (A != A.T).nnz == 0
```

So the short answer is:

```text
Yes:
X → A → degree/D → P

Still needed:
s → Ps → P²s → diagnostic channels
```

The mathematical structure is already correct; the main outstanding concerns are representation scaling, alignment with `s`, small-input validation, and robust self-removal for duplicate sessions.

> and s is the knn distance anomoly scores?

Yes.

\[
s = \text{kNN anomaly scores computed from }X.
\]

For each session \(i\), \(s_i\) measures how far that session is from its nearby sessions in the selected method’s representation space. Higher distance means more anomalous and therefore higher review priority.

For method \(m\):

```text
X_m
├── kNN anomaly scorer → s_m
└── kNN graph builder  → A_m → P_m
```

Then:

```python
s = knn_anomaly_scores(X_scaled, k=15)

A, P = build_session_knn_operator(X_scaled, k=15)

Ps = P @ s
P2s = P @ Ps
```

One distinction is important:

- The **scoring kNN** determines how unusual each session is.
- The **graph kNN** determines which sessions provide neighborhood context.

They may both initially use `k=15`, but they are separate declared parameters:

```python
k_score = 15
k_graph = 15
```

Keeping separate names prevents accidentally changing both experiments when you intended to change only one.

Also, because both are currently constructed from the same \(X\), the signal audit diagnoses organization within that representation’s geometry. It does not yet prove that native telemetry relations provide the organization. That stronger claim requires the telemetry graph or a corresponding null/control.

> can you put all method calls to the knn_distance anomoly scores and the computation of X in one cell at like cell 90

<details><summary>8 previous messages</summary>

> I’ll inspect the notebook’s current cell order and trace every representation-matrix construction and kNN anomaly-score call. Then I’ll consolidate the orchestration calls into one cell near cell 90 while leaving the reusable function definitions in their existing sections.
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> I found the right consolidation point: the notebook ends at cell 92, and cell 91 is already empty beneath “Signal Diagnosis.” I’m using that cell as the single method-artifact assembly point—raw features, M1, every M2 seed, and both M3 variants—so each method’s scaled `X` and kNN-distance score vector `s` are collected consistently.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+107 -2)
>
> </details>
>
> The consolidation cell is in place. While wiring it, I also found the preceding diagnosis cell defines `compute_signal_diagnostic_channels` twice; the second definition silently overwrites the first, and its docstring incorrectly calls `s` the labels. I’m cleaning that handoff now so the new cell reliably means `X = representation`, `s = anomaly scores`, then `A/P/channels`.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+23 -142)
>
> </details>
>
> The new cell now produces a uniform artifact for every representation: `X`, `s`, `A`, `P`, and the diagnostic channels, all aligned to the same `session_ids`. I also removed the accidental duplicate diagnosis definition and the label/score confusion; I’m doing the final notebook-structure and syntax checks now.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+2 -2)
>
> </details>
</details>

Done in [Agentic Feature Extractor and Signal Localizer.ipynb](<./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb>), cells 89–91.

Cell 91 now centrally assembles:

- Raw session features
- M1 structural features
- Every M2 Node2Vec seed
- M3 random-init and trained representations for every seed

Each entry in `signal_method_artifacts` contains:

```python
artifact["X"]         # scaled session representation
artifact["s"]         # kNN-distance anomaly scores
artifact["A"]         # session adjacency
artifact["P"]         # propagation operator
artifact["channels"]  # Ps, s-Ps, Ps-P²s, etc.
```

For example:

```python
selected = signal_method_artifacts["m2_node2vec_seed_42"]

X = selected["X"]
s = selected["s"]
P = selected["P"]
channels = selected["channels"]
```

I also corrected the duplicate/broken diagnostic function in cell 89. The original scoring calls remain in the earlier method-evaluation sections because those results are needed to compare and select methods; cell 91 is now the canonical signal-analysis handoff.

Notebook JSON, edited-cell syntax, and diff formatting all pass validation.

> so now do I diagnose the signal?

Yes. Now that every method has a consistent `X`, `s`, `P`, and diagnostic channels, the next stage is to diagnose the signal—but only for the representation you selected/froze from the method comparison.

For example:

```python
selected = signal_method_artifacts["m2_node2vec_seed_42"]

s = selected["s"]
channels = selected["channels"]

Ps = channels["neighbor_support"]
residual = channels["local_contrast"]   # s - Ps
pocket = channels["pocket"]             # Ps - P²s
```

Then evaluate these four hypotheses:

- `s`: anomaly is intrinsic to individual sessions.
- `Ps` or `0.5*s + 0.5*Ps`: suspicious sessions form neighborhoods.
- `s - Ps`: suspicious sessions are isolated “sore thumbs.”
- `Ps - P²s`: suspicion forms small local pockets but disappears at broader scale.

Compare each channel against the original `s` and an appropriate null distribution. The diagnosis should be:

- Neighborhood-supported if neighbor support is consistently useful beyond null behavior.
- Locally contrastive if the positive residual is consistently useful.
- Intermediate-scale if the pocket channel is consistently useful.
- No useful organization if none survives the null comparison reliably.

Do not restore the old threshold code that said things like `max > 0.5`. Those numbers have no universal meaning. The regime must be inferred from real-versus-null evidence, stability across seeds, and—when labels are available—performance on development data.

After diagnosing one regime, you:

1. Visualize and localize the sessions producing it.
2. Explain which sessions/features/relations support the finding.
3. Optionally run exactly one amplification transform matched to that regime.
4. Compare it to the original `s`.

So yes: the immediate next notebook section should be the actual real-versus-null signal-regime diagnosis table and visualization.

> honestly just write it, I'm so tired today just write the regime picker and make it work with the stuff I have under the cell under signal diagnosis header

<details><summary>3 previous messages</summary>

> I’ll replace the current Signal Diagnosis section with a complete regime picker that consumes `signal_method_artifacts`, compares the three graph hypotheses against permutation nulls, and returns a defensible regime plus a compact evidence table. I’ll keep the method-selection key explicit so you can change it without touching the diagnosis logic.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+164 -1)
>
> </details>
>
> The picker is written in the empty cell directly below your selected M2 artifact. It does not use labels or arbitrary `0.5` cutoffs: it permutes the score-to-graph alignment, corrects for testing three regimes, and only chooses a regime when the evidence survives that null. I’m smoke-testing it on synthetic supported and isolated-anomaly cases before handing it back.
</details>

Done in [Agentic Feature Extractor and Signal Localizer.ipynb](<./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb>).

Run the cells beneath **Signal Diagnosis** through the final cell. It will:

- Use your selected `m2_node2vec_seed_42` artifact.
- Test neighborhood-supported, locally contrastive, and intermediate-scale organization.
- Run 999 score-permutation nulls.
- Correct for testing all three regimes.
- Return `No useful organization` when none passes.
- Display the selected regime and its evidence table.
- Save the answer as `signal_regime`.
- Save the complete result as `signal_regime_result`.

I syntax-checked it and smoke-tested both an organized signal and a no-organization case.

> and so if mu,tiple pass then I take the highest one?

Yes. If multiple regimes pass the family-wise significance test, the picker chooses the one with the highest `effect_z`.

That means it selects the regime whose observed organization is furthest above what its own permutation null would normally produce:

```python
winner_index = eligible_indices[
    np.argmax(effect_z[eligible_indices])
]
```

So the logic is:

1. Discard regimes where `passes == False`.
2. Among the passing regimes, choose the largest positive `effect_z`.
3. If none pass, return `No useful organization`.

Keep the other passing regimes in the evidence table, though. They are legitimate secondary structure, and you should report something like:

> “The dominant regime was neighborhood-supported, with weaker but significant intermediate-scale organization.”

Only the dominant regime should determine your one matched amplification test.

> okay with that regime I would amplify using my function?
>
> def apply_matched_amplification(s, channels, regime, alpha=0.5):
>     """Return at most one score transform matched to a diagnosed regime."""
>     s = np.asarray(s, dtype=float).ravel()
>     if regime == "Neighborhood-supported":
>         return alpha * s + (1.0 - alpha) * channels["neighbor_support"]
>     if regime == "Locally Contrastive":
>         return channels["local_contrast"]
>     if regime == "Intermediate-scale":
>         return channels["pocket"]
>     if regime == "No useful organization":
>         return s
>     raise ValueError(f"Unknown signal regime: {regime}")

Yes. That function applies exactly one transformation matched to the selected regime:

```python
amplified_scores = apply_matched_amplification(
    s=selected["s"],
    channels=selected["channels"],
    regime=signal_regime,
    alpha=0.5,
)
```

Its behavior is:

- `Neighborhood-supported` → combines intrinsic and neighbor scores.
- `Locally Contrastive` → uses \(s-Ps\).
- `Intermediate-scale` → uses \(Ps-P^2s\).
- `No useful organization` → keeps the original \(s\).

Then compare `amplified_scores` against the original `selected["s"]` using your evaluation metrics and null test. Treat it as one matched confirmatory test—not another opportunity to try several transformations.

One detail: `alpha` only affects the neighborhood-supported case. Keep `alpha=0.5` fixed before evaluation; don’t search different values using the holdout labels.

> and what to do with the result

The amplified result is a new session-ranking score—not a new embedding. Use it to decide which sessions the analyst should inspect first.

Create an analyst-facing table:

```python
signal_results = pd.DataFrame({
    "session_id": selected["session_ids"],
    "intrinsic_score": selected["s"],
    "amplified_score": amplified_scores,
})

signal_results["intrinsic_rank"] = (
    signal_results["intrinsic_score"]
    .rank(ascending=False, method="min")
)

signal_results["amplified_rank"] = (
    signal_results["amplified_score"]
    .rank(ascending=False, method="min")
)

# Positive means amplification moved the session closer to the top.
signal_results["rank_gain"] = (
    signal_results["intrinsic_rank"]
    - signal_results["amplified_rank"]
)

signal_results["signal_regime"] = signal_regime

signal_results = signal_results.sort_values(
    "amplified_score",
    ascending=False,
)

signal_results.head(25)
```

Then:

1. Compare `amplified_scores` against the original `s` using AP, precision/recall@K, reviews-to-first-malicious, and your null test.
2. If amplification reliably improves the development results, use `amplified_score` as the analyst’s priority ranking.
3. If it does not improve, keep the original `s`. The regime diagnosis is still useful for explaining the signal’s structure.
4. Investigate:
   - Highest amplified scores: inspect first.
   - Largest positive `rank_gain`: sessions specifically promoted by graph context.
   - Largest negative `rank_gain`: sessions discounted because their surrounding context did not support them.
5. Perform source localization on those sessions to show which processes, features, or relations produced the suspicious representation.

The final analyst message becomes something like:

> “This representation exhibits neighborhood-supported anomalies. These 20 sessions should be reviewed first because they are individually unusual and surrounded by similarly unusual sessions.”

One important experimental constraint: your existing frozen holdout has already been evaluated. Don’t use that same holdout to decide whether amplification works. Test this on development data, freeze the amplifier, and use a new untouched holdout for a publishable final claim.

> User context
>
> Attachments:
> - <div> <style scoped> .dataframe tbody tr th:only-of-type { vertical-align: midd…: `/work/home/mwasti/.codex/attachments/3777c884-82e2-448e-9366-d2c9fc0d0dff/pasted-text.txt`

<details><summary>2 previous messages</summary>

> I’ll read the attached notebook output and interpret what the regime picker actually concluded, including what you should do next with the result.
>
> This output is behaving like an intermediate-scale pocket score should: it is promoting sessions whose immediate neighborhood is anomalous even when the session’s own kNN-distance score is only moderate. I’m checking your notebook’s existing evaluation variable names so I can give you the exact comparison cell rather than generic pseudocode.
</details>

This result means the picker chose **Intermediate-scale**, so the ranking is now based on:

\[
Ps-P^2s
\]

The top sessions are located inside suspicious immediate pockets that fade when you look two hops outward.

For example, session `241` moved from intrinsic rank `508` to pocket rank `1`. That does not mean its individual anomaly score suddenly improved. It means its immediate neighborhood looks much more suspicious than its broader surroundings.

A few important points:

- The dramatic rank changes are expected for a pocket score.
- `intrinsic_score` and `amplified_score` are different quantities, so don’t compare their numerical values directly.
- This table shows that the transformation changed the ranking—not that it improved malicious-session detection yet.

Now evaluate the two rankings on your development labels:

```python
diagnosis_y_true = (
    session_table["label"]
    .map({"benign": 0, "malicious": 1})
    .to_numpy(dtype=int)
)

amplification_results = {
    "original_m2_knn": evaluate_precomputed_scores(
        diagnosis_y_true,
        selected["s"],
    ),
    "matched_intermediate_scale": evaluate_precomputed_scores(
        diagnosis_y_true,
        amplified_scores,
    ),
}

amplification_summary = metric_summary_from_method_results(
    amplification_results
)

amplification_summary
```

Interpret it as follows:

- If the pocket score improves AP, early malicious discovery, and recall/precision@K, keep it as the analyst ranking.
- If it performs worse, keep the original `s`. The intermediate-scale diagnosis can still be reported as a structural observation.
- Inspect sessions such as `241`, `68`, `215`, and `1211`, plus their immediate neighbors, to localize what created those pockets.

For investigating the components directly:

```python
pocket_details = pd.DataFrame({
    "session_id": selected["session_ids"],
    "s": selected["s"],
    "Ps": selected["channels"]["neighbor_support"],
    "P2s": (
        selected["channels"]["neighbor_support"]
        - selected["channels"]["pocket"]
    ),
    "pocket_score": selected["channels"]["pocket"],
}).sort_values("pocket_score", ascending=False)

pocket_details.head(25)
```

That table will show exactly why each session was promoted: high immediate-neighbor suspicion (`Ps`) that drops at two hops (`P2s`).

> take a look

<details><summary>1 previous message</summary>

> I’ll inspect the latest outputs in the Signal Diagnosis section—especially the regime evidence and original-versus-amplified metrics—and tell you whether the pocket transformation actually helped.
</details>

I looked closely. The result is very clear:

- Neighborhood-supported also passed: `effect_z = 2.51`, family-wise `p = 0.027`.
- Intermediate-scale passed much more strongly: `effect_z = 6.12`, family-wise `p = 0.001`.
- Therefore the picker correctly selected **Intermediate-scale**.

But the matched pocket amplification failed badly:

| Metric | Original M2 | Pocket score |
|---|---:|---:|
| Average precision | 0.0458 | 0.0077 |
| Reviews to first malicious | 47 | 379 |
| Malicious in top 100 | 2 | 0 |
| Malicious in top 250 | 15 | 0 |

The pocket AP is even below the approximate malicious prevalence of `19 / 1457 ≈ 0.013`.

So the scientifically correct conclusion is:

> The anomaly scores have strong intermediate-scale geometric organization, but that organization is not aligned with malicious sessions.

The picker worked. The amplifier worked mathematically. It simply discovered mostly benign pockets.

What you should do:

- Keep the original M2 kNN score as the analyst ranking.
- Reject the pocket score as an amplifier.
- Preserve the intermediate-scale diagnosis as an explanatory result.
- Localize the top pocket sessions to understand what benign structural pattern produced them.
- Report neighborhood-supported as a weaker secondary regime.
- Do not now try the neighborhood amplifier on the same evaluation data—the protocol allowed one matched test, and trying the runner-up afterward becomes post-hoc tuning.

This is actually a meaningful outcome: signal organization and threat usefulness are different questions. You found strong organization, tested whether it improved triage, and correctly learned that it did not.

> how do I visualize this with an interactive plot?

<details><summary>2 previous messages</summary>

> The clearest interactive view is a 2D map of the selected M2 representation with a dropdown that switches among `s`, `Ps`, `P²s`, and the pocket score. I’ll check whether your notebook already computed reusable UMAP coordinates and which plotting library is available, then add a ready-to-run cell that highlights the suspicious pockets and exposes session details on hover.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+168 -0)
> - Wrote `./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb` (+8 -2)
>
> </details>
</details>

I added an interactive dashboard as the final notebook cell in [Agentic Feature Extractor and Signal Localizer.ipynb](<./Notebooks/Agentic Feature Extractor and Signal Localizer.ipynb>).

Run the final cell. It provides:

- A UMAP map of the selected M2 representation.
- A dropdown switching between `s`, `Ps`, `P²s`, and `Ps−P²s`.
- Hover details with scores, ranks, and rank gain.
- Circles for benign sessions and triangles for malicious sessions.
- Click selection, with Shift-click for multiple sessions.
- Zooming and panning.
- A linked ranking plot showing how the pocket score reordered the original M2 ranking.
- Red points showing malicious sessions, making the failed amplification visually apparent.

The colors use percentiles so channels with different numerical scales remain visually comparable. I also verified the chart compiles with the Altair version installed in your environment.

> can we integrate all this signal stuff into the streamlit ui so that I can test this across different methods easier with different feature sets?

<details><summary>7 previous messages</summary>

> Yes. I’m going to wire the signal workflow into the existing Streamlit experiment flow—not as a separate demo—so you can choose a method/feature representation, build its `X/s/P`, diagnose the regime, inspect the null evidence, run the one matched transform, and compare rankings interactively. I’ll first map the current UI and engine boundaries, then implement against the path the app actually runs.
>
> The app’s real integration seam is clear: each method’s full representation exists inside the engine but is currently discarded after UMAP. I’m keeping the sparse graph internal, emitting JSON-safe signal evidence and per-session channels for every non-random method, then adding a dedicated Streamlit tab that switches instantly across method keys and feature hypotheses. The UI will also make the crucial distinction between “structure detected” and “amplification helped.”
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/main.py` (+32 -0)
> - Wrote `./Notebooks/main.py` (+10 -0)
> - Wrote `./Notebooks/main.py` (+12 -10)
> - Wrote `./Notebooks/main.py` (+371 -2)
> - Wrote `./Notebooks/main.py` (+20 -12)
> - Wrote `./Notebooks/main.py` (+3 -1)
>
> </details>
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./Notebooks/main.py` (+38 -18)
> - Wrote `./Notebooks/README_AUTOSIGNAL.md` (+21 -0)
> - Wrote `./requirements.txt` (+2 -0)
>
> </details>
>
> The engine and UI are now connected. Every eligible method/feature hypothesis emits aligned signal channels and a label-blind regime result; the new tab can switch among them, visualize any channel, inspect rank movement, and automatically warn when the matched transform hurts development triage. I’m running the expanded engine suite and then a Streamlit smoke test against the actual app entrypoint.
>
> The populated UI rendered without an application exception; the first smoke assertion only tripped because Streamlit’s test API does not expose download buttons through its ordinary button collection. I’m rerunning the smoke check against the actual rendered tab and regime metrics only, which are the meaningful integration assertions.
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Notebooks/main.py` (+20 -0)
> - Wrote `./Notebooks/main.py` (+9 -0)
> - Wrote `./Notebooks/main.py` (+3 -1)
> - Wrote `./Notebooks/autosignal_engine.py` (+3 -0)
> - Wrote `./Notebooks/main.py` (+1 -0)
> - Wrote `./Notebooks/main.py` (+7 -1)
>
> </details>
</details>

Integrated into the Streamlit UI.

The new **Signal diagnosis** tab lets you:

- Switch across methods, feature sets, and seeds.
- View the diagnosed regime and corrected permutation evidence.
- Color the interactive UMAP by `s`, `Ps`, `P²s`, residual, pocket, or matched score.
- Compare intrinsic versus matched rankings.
- Inspect promoted sessions and download results.
- See whether amplification improved or harmed development metrics.
- Distinguish exploratory cross-method browsing from a confirmatory one-method test.

Signal analysis is computed from the original high-dimensional `X`, never the UMAP projection. Random scoring is excluded.

Key changes:

- Signal engine: [autosignal_engine.py](./Notebooks/autosignal_engine.py:569)
- Streamlit tab: [main.py](./Notebooks/main.py:604)
- Tests: [test_autosignal_engine.py](./Notebooks/test_autosignal_engine.py:141)
- Documentation: [README_AUTOSIGNAL.md](./Notebooks/README_AUTOSIGNAL.md:46)

Run AutoSignal again once to generate the new signal payload. The sidebar defaults to 199 null permutations; use 999 for a final development run.

Validation completed:

- 6/6 signal/dashboard engine tests passed.
- 6/6 reusable package tests passed.
- Streamlit pre-run and populated Signal diagnosis smoke tests passed.

> how to kill the previous streamlit runs like on the port cause I'm killing it with the terminal by ending the call to stramlit app but it keeps loadinag a white page

<details><summary>1 previous message</summary>

> I’ll check which Streamlit processes and listeners are still alive in this workspace so I can give you the exact kill command instead of guessing.
</details>

Right now I don’t see any Streamlit process or listener on ports `8501–8503` in this Linux workspace. The white page is probably a stale browser/VS Code port-forward page with no server behind it.

On Linux/WSL, check and kill port `8501`:

```bash
lsof -nP -iTCP:8501 -sTCP:LISTEN
fuser -k 8501/tcp
```

Or kill all Streamlit runs owned by you:

```bash
pkill -f "streamlit run"
```

Then verify the port is free:

```bash
ss -ltnp | rg ":8501"
```

Restart exactly one instance:

```bash
GraphTriage/bin/python -m streamlit run Notebooks/main.py --server.port 8501
```

If you’re running on Windows PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen
```

Then kill its owning process:

```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501 -State Listen).OwningProcess -Force
```

Afterward:

1. Close the white browser tab.
2. In VS Code’s **Ports** panel, remove the old forwarded `8501` port.
3. Restart Streamlit.
4. Reopen the newly printed URL.
5. If necessary, hard-refresh with `Ctrl+Shift+R`.

A white page after the process is killed is normal—the browser shell may remain cached while its Streamlit WebSocket is gone.

<details><summary>4 previous messages</summary>

> Context compaction
>
> Source: automatic
> Status: completed
>
> do the graphsage methods get node attributes as part of the relations or is it just relations
>
> I’ll trace the GraphSAGE input construction in the active engine so I can answer exactly whether it receives session/node features, graph edges, or both.
>
> I found the key split: the dashboard’s GraphSAGE receives both edges and node features, but the node-feature choice differs by node type. I’m checking the exact construction now so I can describe what your feature-set selector actually changes.
</details>

The GraphSAGE methods currently use **both node attributes and relations**.

For each feature-set hypothesis:

- The selected feature columns become attributes for the **primary nodes**—usually your process/session-identifying nodes.
- If multiple telemetry rows refer to the same primary node, their feature values are averaged.
- Other node types currently receive only a constant feature of `1`, so they are distinguished mainly through their graph relationships.
- GraphSAGE then propagates information through every configured typed relation and reverse relation.

Conceptually:

\[
\text{GraphSAGE embedding}
=
f(\text{selected node attributes},\ \text{typed relations})
\]

So when you test:

- `graphsage_trained + feature set A`
- `graphsage_trained + feature set B`

the **relations remain the same**, but the attributes initialized on the primary nodes change. This lets you ask:

> “Does this feature set become more informative when interpreted through the relational structure?”

The trained version learns by reconstructing the configured relations. Then the resulting node embeddings are pooled into sessions, and kNN distance produces the anomaly score \(s\).

One important limitation: attributes are currently assigned only to the automatically selected primary node type. Executable, user, host, or other secondary node types do **not** yet receive their own meaningful attributes—only constant inputs. So it is attribute-aware GraphSAGE, but not yet fully attributed across every node type.

> I might want to add that. Right now the graphsage trained always does as well as teh random, maybe sometimes EVERY SO SLIGHTLY better but negligible. Okay the problem now is that I need to run some tests like automl style with different agent feature sets across the methods and see if there's anything actually statistically interesting? cause right now with the one feature prompt and with max 5k dev slices I can't really tell it seems random even going through the different sets and methods

Yes—you’ve reached the point where manually inspecting a few runs is no longer informative. You need an **evaluation harness around the agent**, essentially constrained AutoML for feature hypotheses.

The fact that trained GraphSAGE performs almost identically to random GraphSAGE is itself important. It usually means at least one of these is happening:

- The selected attributes already contain nearly all useful information, and graph training adds nothing.
- The configured relations do not align with malicious behavior.
- Constant attributes on secondary node types prevent GraphSAGE from distinguishing meaningful neighbors.
- The link-reconstruction objective learns ordinary graph structure, not anomaly-relevant structure.
- The graph is too sparse, too dense, or dominated by high-degree identifiers.
- The evaluation slice contains too few malicious examples to distinguish genuine performance from luck.
- The random GraphSAGE projection is acting like a random-feature kernel, which can occasionally look surprisingly competitive after kNN.

A 5,000-row development slice can be useful for debugging, but it is usually inadequate for making statistical claims—especially if there are only a handful of malicious sessions.

## What the AutoML-style experiment should do

For each dataset or development split:

1. Ask the feature agent for several distinct hypotheses.
2. Materialize each feature set once.
3. Run every compatible representation method across that same data.
4. Run stochastic methods over multiple seeds.
5. Save per-session scores—not just aggregate metrics.
6. Compare methods using paired statistical tests.
7. Test the winning configuration on untouched data.
8. Only then run signal-regime diagnosis on the selected representation.

The experiment matrix would resemble:

| Dimension | Examples |
|---|---|
| Agent feature proposal | behavioral, temporal, rarity, process-chain, interaction |
| Feature set | individual proposal and selected combinations |
| Method | raw kNN, structural statistics, Node2Vec, GraphSAGE random, GraphSAGE trained |
| Relations | base relation suite and controlled ablations |
| Seed | ideally 5–10 for stochastic methods |
| Data split | development folds plus untouched test split |

## What “statistically interesting” should mean

Do not select a winner merely because its average precision is slightly higher.

Track at least:

- Average precision, which is preferable to ROC AUC for rare malicious sessions
- Recall at fixed review budgets such as top 25, 50, 100, and 250
- Precision at those budgets
- Rank of the first malicious session
- Number of malicious sessions discovered before a fixed analyst cutoff
- Stability across seeds and data splits

Because every method scores the **same sessions**, comparisons should be paired. Useful approaches include:

- Bootstrap confidence intervals for the difference in average precision
- Paired bootstrap comparisons for recall at \(K\)
- Seed-to-seed variance for GraphSAGE and Node2Vec
- Rank correlation between repeated runs
- Overlap of the top-\(K\) queues
- Permutation tests when the number of malicious examples is particularly small

The important quantity is not:

\[
AP_{\text{trained}} > AP_{\text{random}}
\]

It is:

\[
\Delta AP =
AP_{\text{trained}}-AP_{\text{random}}
\]

with a confidence interval demonstrating whether that improvement is consistent and meaningfully above zero.

## Essential controls

Your experiment needs these comparisons:

- Raw features + kNN
- GraphSAGE random initialization + kNN
- GraphSAGE trained + kNN
- Shuffled relations + trained GraphSAGE
- Real relations + shuffled node attributes
- Feature-set variants with the same method and split

These let you separate the source of any gain:

| Result | Likely interpretation |
|---|---|
| Trained ≈ random | Graph training provides no demonstrated value |
| Trained ≈ shuffled-edge control | Relations provide no demonstrated value |
| GraphSAGE > raw kNN | Relational aggregation may add value |
| Raw kNN changes across feature sets | Agent feature proposal matters |
| All configurations unstable | Dataset/evaluation sample is too small or signal is weak |
| Development improves but held-out test does not | Search overfit |

Adding attributes to secondary node types is worth testing, but it should be an **experimental variant**, not an assumed improvement. For example, executable nodes might receive prevalence, rarity, signer, path-category, or behavioral-summary attributes. Host and user nodes could receive aggregated historical features. Then compare:

1. Primary-node attributes only
2. Attributes on all meaningful node types
3. Constant attributes everywhere
4. Shuffled secondary-node attributes

That will tell you whether the extra attributes actually contribute.

## Avoid agent-search overfitting

If the agent proposes 30 feature sets and you report the best one on the same 5,000 rows, something will look good by chance.

Use three levels:

- **Search data:** generate and eliminate hypotheses.
- **Selection data:** choose the final feature/method configuration.
- **Untouched test data:** make the actual claim.

The agent should not see test-set labels, performance results, or examples while generating revisions. Otherwise it becomes an iterative label-fitting process.

## My recommendation for the project

Build a batch experiment runner above the existing engine that:

- accepts a saved bank of agent feature proposals;
- evaluates the full proposal × method × seed matrix;
- caches representations and scores;
- produces confidence intervals and paired comparisons;
- compares GraphSAGE trained directly against its random control;
- shows performance and stability in a Streamlit experiment leaderboard;
- marks results as exploratory until confirmed on held-out data.

Then your next question becomes precise:

> Across datasets and held-out splits, do agent-proposed representations produce reproducible improvements, and do relational methods add value beyond raw features and random graph propagation?

That experiment—not a single attractive plot—is what will tell you whether there is a real method here. Right now, the near-tie between trained and random GraphSAGE means **GraphSAGE has not yet demonstrated added value**, but it does not establish that the broader agentic feature-discovery pipeline is random. Those are separate hypotheses and should be tested separately.

> there are different slics and stuff where different methods work better. Maybe that's useful if the study shows signficiance in findings. but what if NOTHING ends up working

That is still a valid—and potentially important—result.

Your project does not need to establish that one method always wins. A more realistic and interesting finding may be:

> Different representations work under different telemetry conditions, and the system can identify when a method has credible signal—and when none does.

That “when none does” capability is especially valuable for an analyst-facing gateway. A responsible system should be able to abstain instead of manufacturing a confident anomaly ranking.

## If different methods win on different slices

That could support a strong result if the variation is reproducible rather than noise. You would want to demonstrate:

- The same method tends to win on similar kinds of slices.
- Its improvement over baselines is statistically credible.
- The winner remains reasonably stable across seeds and resampling.
- Characteristics of the slice explain when it works.
- A selection rule can choose the method without using the slice’s hidden labels.

For example, you may discover:

- Rarity features work on slices containing unusual executables.
- Temporal features work during bursty activity.
- Relational methods help when malicious sessions form neighborhoods.
- Locally contrastive scores help when malicious sessions are isolated.
- No method helps when the available telemetry lacks behavioral separation.

That becomes a **regime-dependent method-selection** contribution, rather than a universal detector.

Be careful, however: choosing the best method after examining labels is an oracle analysis. It proves that methods differ, but not that your system can select the correct one in production. Your signal-regime diagnosis could eventually become part of a label-blind selection or abstention rule, but that must be validated separately.

## If absolutely nothing works

First determine what “nothing” means. There are several distinct negative outcomes:

### 1. Features contain no recoverable signal

If raw kNN, conventional models, relational methods, and supervised sanity checks all fail, then the slice may not contain enough information to distinguish malicious sessions.

That finding means:

> The telemetry available to the gateway is insufficient for this target—not that the implementation failed.

A supervised upper-bound test is crucial here. Train a reasonable supervised model using labels strictly for diagnosis. If even that cannot generalize to held-out data, unsupervised GraphSAGE should not be expected to succeed.

### 2. Signal exists, but unsupervised scores cannot recover it

If supervised models work while your unsupervised methods do not, the representation may contain information, but rarity or geometric distance is the wrong objective.

You might then need:

- a weakly supervised objective;
- contrastive learning using domain-informed positive pairs;
- relation-aware reconstruction designed around unusual behavior;
- temporal prediction;
- ranking from limited analyst feedback.

That is a useful boundary finding: generic unsupervised anomaly scoring is insufficient.

### 3. Development results appear good but do not reproduce

That indicates selection overfitting, slice instability, or too few malicious examples. The correct system output is “insufficient evidence,” not a winner.

### 4. No single method works consistently

This may support the gateway concept most strongly, provided some methods work reliably in identifiable regimes. Then the contribution is conditional routing plus abstention.

## Build “no credible winner” into the design

The final gateway should have three possible outcomes:

1. **Recommend a representation**
   Evidence is stable and materially better than controls.

2. **Return an exploratory ranking**
   Some structure exists, but performance evidence is uncertain.

3. **Abstain**
   No representation demonstrates credible organization or stability.

For example, a method should be recommended only if it satisfies prespecified requirements such as:

- improvement over a simple baseline;
- confidence interval excludes a negligible improvement;
- acceptable stability across seeds or resamples;
- useful top-\(K\) retrieval;
- consistent results on selection data;
- confirmation on held-out data.

Otherwise, report:

> No tested representation produced sufficiently stable and actionable separation on this slice.

That is much better than silently returning whichever method happened to be least bad.

## The project can survive a negative result

If nothing works, the contribution needs to shift from “we detect malicious sessions” to a rigorously supported conclusion such as:

> Across controlled feature, relation, and representation searches, commonly used unsupervised geometric and graph methods did not reliably recover malicious activity from this telemetry. Apparent development gains were unstable or indistinguishable from random controls.

That can still be useful research if:

- the benchmark and protocol are sound;
- the search space is principled;
- strong baselines and controls are included;
- uncertainty is quantified;
- failure modes are diagnosed;
- conclusions are not overstated.

For the product itself, a complete failure across all datasets would mean it is not yet an effective detection system. But it could remain valuable as an **evidence-generating triage framework** that tells analysts what structure exists, where it exists, and whether a ranking deserves trust.

The important conceptual change is this:

> Your gateway should not promise to find signal. It should test whether actionable signal exists, characterize it when found, and abstain when the evidence is weak.

That makes “nothing worked” an expected system state rather than a catastrophic exception.

> and if I HAD to MUST had to add more embedding or graph or whatever methods, what would you list top 5. if I HAD to later after everything to test more stuff

<details><summary>2 previous messages</summary>

> I’ll rank additions by what new hypothesis they test—not by novelty or popularity—so each method tells you something your current raw kNN, Node2Vec, and link-reconstruction GraphSAGE suite cannot. I’ll also separate genuinely useful additions from redundant graph variants.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site:arxiv.org graph anomaly detection DOMINANT deep anomaly detection attributed networks ...`
>
> Searched the web for `DOMINANT deep anomaly detection attributed networks paper SIAM 2019 ...`
>
> Searched the web for `site:proceedings.mlr.press Deep One-Class Classification Deep SVDD ICML 2018 ...`
>
> </details>
</details>

If you later had to add exactly five, I would choose methods that test five genuinely different explanations for anomaly signal—not five small variations of GraphSAGE.

## My top five

### 1. Isolation Forest on the agent-produced session features

This would be my first addition.

Your current kNN score asks:

> Is this session far from its neighbors?

Isolation Forest asks:

> Can this session be separated unusually quickly using combinations of feature splits?

That matters because kNN can struggle with varying density, irrelevant dimensions, and unusual combinations of otherwise ordinary values. Isolation Forest is inexpensive, scalable, and gives you a strong non-neural control based on a fundamentally different scoring mechanism. [The original method explicitly isolates anomalies rather than estimating distance or density.](https://doi.org/10.1109/ICDM.2008.17)

Run:

\[
X_{\text{feature set}}\rightarrow\text{Isolation Forest}\rightarrow s
\]

This directly tests whether a feature proposal was useful but kNN was the wrong detector.

### 2. Deep SVDD or another one-class neural representation

Deep SVDD learns a transformation that maps normal-looking sessions into a compact region. Distance from that learned region becomes the anomaly score.

It asks:

> Can a nonlinear representation learn the shape of ordinary telemetry better than raw kNN?

Unlike your GraphSAGE objective, its training objective is explicitly connected to anomaly detection. [Deep SVDD minimizes the volume of a hypersphere enclosing learned representations.](https://proceedings.mlr.press/v80/ruff18a/ruff18a.pdf)

Use it first on session feature matrices without the graph:

\[
X\rightarrow f_\theta(X)\rightarrow
\lVert f_\theta(x_i)-c\rVert^2
\]

This tells you whether the problem is your detector/representation rather than your relations.

### 3. DOMINANT-style attributed graph autoencoder

DOMINANT jointly reconstructs:

- node attributes;
- graph structure.

Its anomaly score can combine attribute reconstruction error and structural reconstruction error.

It asks:

> Is this node unusual because its attributes, relationships, or the combination of both cannot be explained?

That is much better matched to your attributed telemetry graph than your current GraphSAGE link-reconstruction objective, which primarily rewards learning common relations. [DOMINANT was designed specifically to model topology and node attributes for attributed-network anomaly detection.](https://epubs.siam.org/doi/abs/10.1137/1.9781611975673.67)

It also provides useful localization:

\[
s_i =
\alpha\,e_{\text{attribute},i}
+(1-\alpha)e_{\text{structure},i}
\]

That would fit your analyst-facing goal particularly well.

### 4. CoLA-style contrastive graph anomaly detection

CoLA compares a node with sampled local subgraphs and learns whether they belong together.

It asks:

> Does this node agree with the behavioral context around it?

This is especially relevant to your signal regimes:

- A node inconsistent with its neighborhood should produce contrastive evidence.
- A node embedded in a suspicious local pocket may exhibit a different agreement pattern.
- It targets anomaly-related node–neighborhood compatibility more directly than generic link prediction.

[CoLA was introduced specifically as contrastive self-supervised anomaly detection for attributed networks.](https://arxiv.org/abs/2103.00113)

This would be my strongest graph-specific alternative after DOMINANT.

### 5. Temporal Graph Network—or a simpler temporal event encoder first

Your telemetry is intrinsically temporal, but your present graph largely collapses events into a static graph. That can erase ordering such as:

```text
login → process launch → unusual child → network connection
```

A Temporal Graph Network maintains node state over a sequence of timestamped events. It asks:

> Is this relationship or behavior unusual given what happened before it?

[TGN was designed for dynamic graphs represented as sequences of timed events.](https://arxiv.org/abs/2006.10637)

This has the highest implementation cost, so I would add it last. Before implementing a full TGN, I would test a cheaper sequential baseline—such as a GRU/Transformer autoencoder over events within each session. If sequence information does not help, a TGN probably will not justify its complexity.

## Priority order

My practical implementation order would be:

1. Isolation Forest
2. Deep SVDD
3. DOMINANT
4. CoLA
5. Temporal encoder/TGN

The first two determine whether nonlinear or non-distance session modeling helps. The next two determine whether attributed graph context helps. The last determines whether static aggregation has been destroying temporal signal.

## What I would not prioritize

I would not immediately add:

- GCN
- GAT
- deeper GraphSAGE
- Heterogeneous Graph Transformer
- another Node2Vec variation
- more embedding dimensions

Those may be useful eventually, but they mostly change the encoder while leaving the critical question—**what self-supervised objective produces anomaly-relevant information?**—unanswered.

For example, HGT can model typed nodes and relations more expressively, but using HGT with the same link-reconstruction objective may simply give you a more expensive version of the current trained-versus-random tie.

The clean five-method story would be:

| Method | New hypothesis tested |
|---|---|
| Isolation Forest | Non-distance anomaly isolation |
| Deep SVDD | Anomaly-oriented nonlinear session representation |
| DOMINANT | Attribute and structural reconstruction inconsistency |
| CoLA | Node–neighborhood contextual inconsistency |
| Temporal model | Unusual event ordering and evolving relations |

If none of these beats the controls reproducibly, you would have tested the major reasonable signal families: global feature rarity, nonlinear one-class structure, attributed-graph reconstruction, local graph context, and temporal behavior. At that point, adding yet another generic graph encoder would be difficult to justify.

> the good thing is like yeah with this whole system set up, you can shove any method implementation in ONCE and test through the ENTIRE scientific workflow which I think is valuable

Exactly. That may be the project’s strongest contribution.

The value is not necessarily that you invented the universally best embedding. It is that a method can be inserted once and evaluated through a consistent, end-to-end scientific workflow:

\[
\text{data slice}
\rightarrow
\text{agent feature/relation hypotheses}
\rightarrow
\text{representation method}
\rightarrow
\text{anomaly scores}
\rightarrow
\text{controlled evaluation}
\rightarrow
\text{signal diagnosis}
\rightarrow
\text{matched intervention or abstention}
\rightarrow
\text{analyst output}
\]

Once a new method produces a session-aligned representation \(X\) and/or anomaly score \(s\), the rest of the system can automatically test:

- Multiple datasets and slices
- Different agent-proposed feature sets
- Relation configurations and ablations
- Repeated seeds
- Performance against shared baselines
- Statistical uncertainty and stability
- Score organization and signal regime
- Whether matched amplification helps
- Top-session analyst utility
- Whether the system should recommend, explore, or abstain

That gives every method the same “scientific wind tunnel.” You are evaluating much more than whether its AP happened to be highest once.

The particularly valuable separation is:

- **Method adapters** generate \(X\), embeddings, and \(s\).
- **The evaluation protocol** determines whether the apparent gain is real.
- **Signal diagnosis** explains how the scores are organized.
- **The analyst layer** translates credible findings into an investigation queue.
- **Abstention** prevents weak experiments from becoming confident recommendations.

That separation also makes negative findings reusable. If GraphSAGE fails, you do not discard the pipeline. You insert DOMINANT, CoLA, Isolation Forest, or a temporal model and run the identical protocol. Likewise, when a new technique appears later, you do not rebuild data preparation, controls, plots, statistics, and reporting.

Methodologically, the claim could eventually be:

> We introduce an agentic, method-agnostic experimentation gateway for unstructured telemetry that proposes candidate representations and relations, evaluates heterogeneous anomaly methods under controlled comparisons, diagnoses the spatial organization of their scores, and reports actionable evidence or abstains.

The novelty would live in the **orchestration and decision protocol**, particularly if you demonstrate that it:

1. Searches structured hypotheses without leaking labels.
2. Makes unlike methods comparable through one session-level contract.
3. Identifies slice-dependent method behavior.
4. distinguishes real training gains from random encoders and shuffled controls.
5. Diagnoses score geometry after selection.
6. Rejects amplification when it does not improve held-out analyst utility.
7. Explicitly reports “no credible signal.”

So yes: “implement once, test through the entire scientific workflow” is not merely convenient engineering. If the contracts, controls, and selection rules are rigorous, it is a legitimate methodological contribution.

> okay it's the next day. Forget what i said is next, make a straightforward plan for what should be next

The next step should be to stop expanding the method suite and build a repeatable experiment runner around what already exists.

## Immediate objective

Answer this question first:

> Do any current feature-set × method combinations produce reproducible, useful anomaly rankings—and under which data conditions?

## Straightforward plan

### 1. Freeze the current method suite

Use only:

- Raw feature-set + kNN
- Typed structural statistics + kNN
- Node2Vec + kNN
- Random GraphSAGE + kNN
- Trained GraphSAGE + kNN
- Random-score baseline

Do not add more methods yet. The existing suite is enough to validate the scientific workflow.

### 2. Define the experiment data

Create several reproducible slices representing meaningfully different telemetry conditions—not arbitrary random subsets.

For every slice, record:

- Slice definition
- Number of rows and sessions
- Number and prevalence of malicious sessions
- Time range
- Hosts/users represented
- Relation counts and coverage
- Any known attack or behavioral characteristics

Use larger slices than 5,000 rows wherever computationally feasible. Keep at least one dataset or time range completely untouched for final confirmation.

### 3. Generate a feature-hypothesis bank

Have the agent produce perhaps 8–15 deliberately distinct hypotheses, such as:

- Frequency and rarity
- Temporal behavior
- Process ancestry
- Identity/host behavior
- Executable behavior
- Cross-entity interaction
- Burst/activity intensity
- Relation-aware behavioral summaries

Save the hypotheses as versioned configuration. Do not regenerate them separately during every run, because then you cannot tell whether changes came from the method, data, or agent output.

Validate that every feature is computable without using labels or future information.

### 4. Build the batch experiment runner

Run the full matrix:

\[
\text{slices}
\times
\text{feature sets}
\times
\text{methods}
\times
\text{seeds}
\]

For every run, save:

- Exact configuration and data-slice identifier
- Session IDs in their original order
- Representation metadata
- Per-session anomaly scores
- Random seed
- Training diagnostics
- Runtime and failure information
- AP, recall@K, precision@K, first-malicious rank
- Signal analysis only when appropriate

Cache intermediate representations so repeated statistical analysis does not retrain everything.

### 5. Add the essential controls

At minimum, compare:

- Trained GraphSAGE against random GraphSAGE
- Real relations against shuffled relations
- Real features against shuffled features
- Every method against random scores
- Agent features against a simple human/basic feature baseline

These controls tell you whether gains come from:

- The proposed features
- The relations
- Graph training
- Chance

### 6. Add statistical comparison

For each slice, calculate:

- Bootstrap confidence intervals for AP
- Confidence intervals for recall@K
- Paired performance differences between methods
- Variability across seeds
- Top-\(K\) overlap and rank stability

Define practical significance too. A statistically detectable AP improvement may still be useless if it retrieves no additional malicious sessions within the analyst’s review budget.

Use language such as:

- Credible improvement
- Indistinguishable from baseline
- Unstable
- Promising but unconfirmed
- No useful signal

### 7. Build an experiment leaderboard in Streamlit

The next UI addition should summarize batches—not add more signal plots.

It should allow filtering by:

- Dataset and slice
- Feature hypothesis
- Method
- Seed
- Signal regime

Show:

- Mean performance with uncertainty
- Best and worst slices
- Trained-versus-random GraphSAGE difference
- Stability across seeds
- Top-\(K\) analyst utility
- Statistical comparison against the selected baseline
- A warning when the sample has too few malicious sessions

### 8. Select candidates before signal diagnosis

Use development results to choose a small number of candidates based on predetermined rules.

For example, require:

- Improvement over the basic baseline
- Reasonable seed stability
- Useful recall at the analyst budget
- Evidence across more than one compatible slice

Then freeze the chosen representation.

Only after selection should you perform deeper signal-regime diagnosis and one matched amplification test. Otherwise, the signal analysis becomes another large search space.

### 9. Confirm on untouched data

Run the frozen candidate once on held-out data.

Possible final outcomes:

- A method generalizes across slices.
- Different methods work in reproducible, identifiable conditions.
- Feature proposals help, but graph methods do not.
- Graph structure helps only on particular relation regimes.
- No tested method produces credible signal.

All five are scientifically meaningful outcomes.

### 10. Only then decide what to add

Use the observed failure mode to choose the next method:

- kNN fails but features appear predictive → Isolation Forest or Deep SVDD
- Node attributes and topology disagree → DOMINANT
- Local node-context inconsistency matters → CoLA
- Static slices erase important ordering → temporal encoder/TGN
- Secondary node attributes appear impoverished → attributed node types

Do not add a method merely to enlarge the suite.

## The very next implementation task

Build a **batch experiment specification and runner** that invokes the existing engine repeatedly and writes one tidy results table plus per-session score files.

The first milestone should be:

> Run three fixed feature hypotheses across three meaningful slices, all current methods, and five seeds; then display performance, uncertainty, and trained-versus-random comparisons in one report.

That modest experiment will expose problems in the workflow before you spend time generating dozens of features or implementing additional models.

> can you take the pipelien from teh streamlit files and make a NEW organized notebook so I can iterate fast there

<details><summary>6 previous messages</summary>

> I’ll turn the active Streamlit pipeline into a separate experiment notebook—not copy the UI code. The notebook will call the same engine, expose configuration near the top, run one slice quickly, inspect method/signal results, and include a batch-loop scaffold for feature sets, slices, and seeds.
>
> The engine already exposes the right stable contract, so the notebook can stay thin. I’m structuring it into four phases: configure/load, run/cache, compare methods, then diagnose one selected signal. Batch experiments will be opt-in so opening or “Run All” doesn’t accidentally launch a large search.
>
> <details><summary>Created a file</summary>
>
> - Wrote `./Notebooks/build_autosignal_workbench.py` (+1061 -0)
>
> </details>
>
> The notebook is generated and structurally valid. I’m running it end-to-end on a 300-row smoke slice with one training epoch and the minimum valid permutation count; this checks the real engine calls, table joins, signal selection, plot construction, and opt-in batch guards.
>
> The full smoke run passed: all 30 cells executed, 12 methods completed, signal artifacts joined correctly, the interactive chart object built, and the batch section stayed off. I’m cleaning the temporary generator/cache and adding the new notebook to the project handoff documentation.
>
> <details><summary>Edited a file, deleted a file</summary>
>
> - Wrote `./Notebooks/README_AUTOSIGNAL.md` (+8 -0)
> - Deleted `./Notebooks/build_autosignal_workbench.py` (+0 -1061)
>
> </details>
</details>

Created the new organized notebook: [AutoSignal Experiment Workbench.ipynb](<./Notebooks/AutoSignal Experiment Workbench.ipynb>).

It includes:

- Central experiment-settings cell
- Dataset slicing: tail, head, or random
- Feature-set filtering
- Shared Streamlit engine execution
- Automatic result caching
- Method leaderboard
- GraphSAGE trained-versus-random controls
- Graph/relation coverage diagnostics
- Signal-regime leaderboard
- Interactive Altair signal visualization
- Analyst priority queue
- Optional paired AP bootstrap
- Opt-in multi-slice, multi-seed batch runner
- Batch stability summary and CSV export
- Scientific-iteration checklist

The expensive batch section is disabled by default. The normal starting configuration is 1,000 rows, one seed, two GraphSAGE epochs, and 99 permutations.

I executed all 30 notebook cells against a real 300-row slice:

- 12 methods completed
- No method failures
- Signal analysis and table joins worked
- Interactive plot construction worked
- Batch jobs correctly remained disabled

I also added notebook instructions to [README_AUTOSIGNAL.md](./Notebooks/README_AUTOSIGNAL.md).

Open it with the `GraphTriage` environment and begin in **“2. Edit experiment settings here.”** If you modify the engine itself, set `FORCE_RERUN = True` once so an older cached payload is not reused.

> take note that an important to do is that the agent when given a dataset to parse, should also be given the feature list somehow other wise it will just be guessing

<details><summary>2 previous messages</summary>

> Agreed. I’m recording this as a pipeline requirement, not a casual reminder: the schema/feature agent must receive an explicit feature catalog alongside the dataset profile, including names and enough semantics to judge valid combinations. Without that, its hypotheses are guesses based on column names.
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./Notebooks/AutoSignal Experiment Workbench.ipynb` (+4 -0)
> - Wrote `./Notebooks/README_AUTOSIGNAL.md` (+20 -0)
>
> </details>
</details>

Noted as an explicit pipeline requirement in both:

- [README_AUTOSIGNAL.md](./Notebooks/README_AUTOSIGNAL.md:54)
- [AutoSignal Experiment Workbench.ipynb](<./Notebooks/AutoSignal Experiment Workbench.ipynb>)

The future feature-agent input must include a versioned catalog describing:

- Feature name and meaning
- Entity/granularity
- Units
- Derivation
- Valid aggregations
- Availability time
- Missing/sentinel behavior
- Leakage restrictions

The agent should only propose cataloged features, cite what it used, and report unsupported needs instead of inventing columns. The catalog version should also be saved in every run manifest.

> for headerless datasets where the columns are not labeled but there is a separaete header csv, to account for that I can either make the schema include the col index and use THAT to fetch each column or I can merge the header with the dataset itself before running it rhough the pipeline

You should apply the separate header file during ingestion and pass a properly named DataFrame into the pipeline.

Conceptually:

\[
\text{headerless data}+\text{header specification}
\rightarrow
\text{named canonical DataFrame}
\rightarrow
\text{AutoSignal}
\]

Do not make the rest of the pipeline fetch columns by numeric index. That would spread dataset-format details into feature extraction, graph construction, agent configuration, and evaluation.

Use column indices only inside the ingestion adapter.

## Recommended ingestion behavior

1. Read the header specification.
2. Read the dataset with `header=None`.
3. Confirm that the number of supplied names equals the number of data columns.
4. Assign the names to the DataFrame.
5. Validate that names are unique and nonempty.
6. Pass the named DataFrame through the existing pipeline.
7. Preserve the original index-to-name mapping in an ingestion manifest.

For example:

```python
headers = pd.read_csv(header_path)["column_name"].tolist()
df = pd.read_csv(data_path, header=None)

if df.shape[1] != len(headers):
    raise ValueError(
        f"Dataset has {df.shape[1]} columns, "
        f"but the header file defines {len(headers)}."
    )

if len(headers) != len(set(headers)):
    raise ValueError("Header file contains duplicate column names.")

df.columns = headers
```

The manifest could record:

```json
{
  "source_format": "headerless_csv",
  "header_source": "headers.csv",
  "column_mapping": [
    {"source_index": 0, "column": "timestamp"},
    {"source_index": 1, "column": "hostname"},
    {"source_index": 2, "column": "process_id"}
  ]
}
```

This gives you both benefits:

- The entire scientific pipeline uses meaningful, stable feature names.
- You retain the original positional mapping for provenance and debugging.

It also fits the feature-catalog requirement. The agent sees meaningful feature names and definitions, while the loader knows that, for this particular dataset, `hostname` originally came from column index 1.

One terminology distinction: you are not really “merging” the header file with the data as additional rows. You are using it to **assign the canonical column schema during loading**. This should become a dataset-adapter option in front of AutoSignal.

> the malicious label values column from the agent schema is NOT leaking into the dev slice right?
>
> User context
>
> Images:
> - `data:image/png;base64,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AKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKgTMAAAAAAAAAICqEDADAAAAAAAAAKpCwAwAAAAAAAAAqAoBMwAAAAAAAACgKv8fe96NzZgnxvwAAAAASUVORK5CYII=`

<details><summary>2 previous messages</summary>

> I’ll verify the exact code path rather than relying on the intended design. The all-red plot is suspicious enough to check separately: it could mean labels were revealed and every session in that slice was mapped as malicious, which is different from labels entering the representation.
>
> The important distinction is: `malicious_label_values` is not a dataset column—it is only the lookup list used to translate the configured `label_col` into benign/malicious evaluation labels. I found the current safeguard, and I’m checking the exact sample configuration and the all-red slice because there is one broader validation gap worth being precise about.
</details>

For the current ACME configuration, the malicious label is **not entering the feature matrices, embeddings, anomaly scores, or label-blind regime selection**.

I verified the 1,000-row tail slice:

- Raw rows: 998 benign, 2 malicious
- Sessions: 922 benign, 2 malicious
- `red_team` is not in any feature set
- It is not a graph relation
- It is not a session-grouping column
- It is not the timestamp or session identifier

`malicious_label_values` is not itself a column. It is the list `[1]`, used only to interpret values from `label_col: "red_team"` when creating evaluation labels at [autosignal_engine.py:512](./Notebooks/autosignal_engine.py:512).

The pipeline explicitly rejects the label as a selected feature at [autosignal_engine.py:201](./Notebooks/autosignal_engine.py:201), and feature matrices are built only from each feature set’s declared columns at [autosignal_engine.py:1873](./Notebooks/autosignal_engine.py:1873).

However, I found one validation gap: the engine currently prevents the label from being a feature, but does not explicitly prevent a bad agent configuration from using it as:

- A graph-relation endpoint
- A session-grouping column
- A timestamp
- An existing session identifier

Your current ACME config does none of those, so this run is safe. But we should strengthen validation to reject the label everywhere except evaluation.

The all-red image therefore does not indicate feature leakage. It suggests the visualization was told that every displayed session was malicious—or that it is using a red score palette rather than label colors. Check:

```python
pd.Series(result["sessions"]).head()
```

Better:

```python
pd.DataFrame(result["sessions"])["label"].value_counts()
```

For the verified ACME 1,000-row slice, that should not be all malicious.

One more issue: [sample_agent_config.json](./Notebooks/sample_agent_config.json) now contains a list of three dataset configurations. The engine expects exactly one configuration object, so the notebook must explicitly select the matching entry before running. A mismatched configuration should fail validation, but selecting the wrong label definition could otherwise explain confusing label displays.

> well I'm testing a new dataset and it has benign or bot as the labels in its final column. The agent is spotting in the schema the correct malicious label value but that's why I'm asking that if it correctly finds the malicious label value, the engine doesn't use it in the pipeline right?

<details><summary>1 previous message</summary>

> Yes—the correct distinction is “used for evaluation” versus “used to create the anomaly signal.” I’ll check the new Bot/Benign configuration specifically so the answer applies to the dataset you are running, not only the earlier ACME schema.
</details>

Correct. For your new dataset, the agent correctly identifies:

```json
"label_col": " Label",
"malicious_label_values": ["Bot"]
```

The engine uses that information **only after scoring** to evaluate the results:

- Convert `Bot` to `malicious`
- Convert other values, such as `Benign`, to `benign`
- Calculate AP, recall@K, precision@K, and first-malicious rank
- Color or reveal labels when requested
- Compare intrinsic and matched rankings

It does **not** use `Bot` or `Benign` to:

- Build the feature matrix
- Train GraphSAGE
- Train Node2Vec
- Construct kNN anomaly scores
- Construct the signal-neighborhood graph
- Select the signal regime
- Produce matched amplification scores

I checked this specific Bot configuration. The label column is not present in:

- Selected features
- Feature sets
- Relation endpoints
- Session grouping
- Timestamp configuration
- Session ID configuration

Therefore, this particular run is label-isolated correctly.

The pipeline sequence is effectively:

\[
X,\text{ relations}
\rightarrow
\text{embeddings}
\rightarrow
s
\rightarrow
\text{signal diagnosis}
\]

and only afterward:

\[
s+\text{Bot/Benign labels}
\rightarrow
\text{development evaluation metrics}
\]

The all-red visualization can still happen if your selected slice contains only—or mostly—`Bot` rows/sessions and you enabled label display. Check it directly with:

```python
dataset[" Label"].value_counts(dropna=False)
```

and after sessionization:

```python
pd.DataFrame(result["sessions"])["label"].value_counts()
```

So yes: the engine knows which value means malicious, but it does not use that knowledge to generate the representation or anomaly ranking.

> so with that specific dataset it grouped ALL malicious very well but the signal was USELESS. The signal BEEN useless in everything I've seen so far

That is a coherent result, and it tells us something specific:

> The representation may contain malicious/benign separation, while the anomaly score and its graph-relative transformations fail to exploit it.

Those are different layers.

\[
\text{representation }X
\rightarrow
\text{anomaly score }s
\rightarrow
\text{signal transforms of }s
\]

If the Bot sessions form their own tight cluster, kNN distance can fail because every Bot has other Bots nearby. Within that cluster, they look locally normal:

```text
Benign cluster: dense
Bot cluster:    dense
```

The embedding separated the behaviors, but the scorer asked the wrong question:

> “Does this individual session have distant neighbors?”

The useful question may instead be:

> “Does this entire cluster represent a separate, uncommon behavioral population?”

Signal diagnosis cannot recover information that was lost when \(X\) became \(s\). It only rearranges or contextualizes the existing anomaly scores:

- \(Ps\)
- \(s-Ps\)
- \(Ps-P^2s\)

If the Bot cluster received ordinary or low intrinsic scores, propagating those scores will not magically identify it as malicious.

## First verify that the grouping is real

The picture alone is insufficient because UMAP can manufacture visually persuasive clusters. On development data, measure separation in the original representation:

- Malicious-neighbor purity in full \(X\)
- Benign/malicious centroid separation
- Cross-validated linear probe
- Label-based silhouette score
- Stability across seeds
- Stability across slices

Labels may be used here because this is explicitly post-hoc development evaluation.

If those tests confirm separation, you have a useful representation even though AP from kNN is poor.

## What scorer would match this behavior?

A cluster-level anomaly scorer would make more sense:

1. Cluster sessions in the original representation.
2. Measure each cluster’s size, separation, and distance from the dominant population.
3. Assign cluster-level unusualness to its members.
4. Evaluate the resulting ranking.

Strong candidates include:

- HDBSCAN with cluster rarity/separation scoring
- Gaussian mixture likelihood
- Cluster-Based Local Outlier Factor
- Distance from the dominant or largest-cluster prototype
- Isolation Forest on the embedding
- Spectral clustering followed by cluster-level rarity

This would introduce a distinct regime:

> **Distinct anomalous population:** the suspicious sessions are mutually similar, separated from the dominant population, but not individually isolated.

Your existing regimes do not properly represent that situation. “Neighborhood-supported” only means high anomaly scores have high-scoring neighbors. It does not detect a separated cluster whose members initially have low scores.

## What to do with the existing signal stage

For now:

- Keep signal diagnosis as an optional diagnostic.
- Continue rejecting matched amplification whenever analyst metrics worsen.
- Do not describe statistically significant score organization as malicious signal.
- Allow the stage to output “structurally organized but not label-useful.”
- Do not make amplification a mandatory part of the final workflow.

If it has been useless across every tested dataset, that is evidence that the current \(s, Ps, s-Ps, Ps-P^2s\) family is not adding analyst value. You do not need to protect it merely because it was part of the original plan.

The most informative next experiment is therefore not another signal-regime run. It is:

> Determine whether the apparent malicious cluster is stable in the full embedding; if it is, test one cluster-level scorer against kNN using the same representation.

If that succeeds, your system has demonstrated exactly why its method-agnostic workflow matters: the embedding worked, the original scorer failed, and the evaluation layer identified what needed replacing.

> yeah okay I agree I think even with just these slight manual tests it is showing that there's a LOT of garbage behaviour and if the system is cleaned up and evaluated in a statistical manner that this is a real contribution and leaves a lot open for extensibility. I think the cluster level anomaly score and the post hoc development evaluation is good FINAL idea

Yes. That gives the project a clean stopping point without endlessly adding methods.

The contribution becomes:

> A method-agnostic scientific workflow that tests agent-proposed telemetry representations, identifies genuine and spurious behavior, distinguishes representation quality from anomaly-scoring quality, and either produces an analyst ranking or abstains.

The final analytical structure should be:

\[
\text{agent hypotheses}
\rightarrow X
\rightarrow \text{multiple scorers}
\rightarrow s
\rightarrow \text{controlled evaluation}
\rightarrow
\begin{cases}
\text{actionable ranking}\\
\text{useful representation but failed scorer}\\
\text{no credible signal}
\end{cases}
\]

## Final two additions

### 1. One cluster-level anomaly scorer

Treat it as another scoring method—not as signal amplification.

It should consume the same representation \(X\) and produce a session-aligned score \(s_{\text{cluster}}\). A reasonable first implementation is:

- HDBSCAN or another stable clustering method
- Cluster size/rarity
- Cluster separation from the dominant population
- Optional within-cluster outlier component
- Noise points handled explicitly

Then compare:

\[
s_{\text{kNN}} \quad\text{versus}\quad s_{\text{cluster}}
\]

on exactly the same representation.

This addresses the “malicious sessions form a coherent separate population” case that kNN distance misses.

### 2. Post-hoc development representation evaluation

Evaluate \(X\) independently of its anomaly score:

- Full-space malicious-neighbor purity
- Label silhouette score
- Cross-validated linear-probe performance
- Separation stability across seeds
- Stability across slices
- UMAP only as visualization—not evidence

That lets the system report:

> This representation contains recoverable malicious/benign separation, but the selected unsupervised scorer does not convert it into a useful ranking.

That is a far more informative conclusion than simply saying the method had low AP.

## Treatment of signal diagnosis

Keep the signal-regime stage, but demote it from a presumed enhancement to an optional diagnostic:

- Label-blind structural description
- At most one matched amplification
- Automatically rejected if analyst utility worsens
- “No useful organization” is valid
- Structural significance must not be described as malicious relevance

If it repeatedly fails, report that transparently. Quantifying its failure is part of the study.

## Then stop expanding

After those additions, focus on:

- Clean method interfaces
- Reproducible slices
- Fixed feature hypotheses
- Random and shuffled controls
- Multiple seeds
- Paired uncertainty estimates
- Held-out confirmation
- Clear recommend/explore/abstain outcomes

The apparent “garbage behavior” becomes publishable evidence only when translated into measurable findings such as:

- Trained GraphSAGE is indistinguishable from random initialization.
- Results vary substantially across slices.
- Visually separated UMAP clusters do not imply useful anomaly rankings.
- Significant score geometry does not necessarily align with maliciousness.
- Some representations preserve label separation even when their scorer fails.
- Cluster-level scoring recovers—or fails to recover—that separation.
- The system correctly rejects unsupported amplification.

That is a strong final scope: add cluster-level scoring, add representation-level post-hoc evaluation, and then spend the remaining effort making the experiment rigorous rather than making the method list longer.

> at least a paper on this would LOOK cool

It genuinely would—and it has a strong visual and conceptual narrative.

The central paper figure could show:

```text
Unstructured telemetry
        ↓
Agent-proposed features and relations
        ↓
Shared representation-method interface
        ↓
Raw, structural, random, trained, and cluster-level methods
        ↓
Scientific evaluation gateway
        ├── useful ranking
        ├── useful representation / failed scorer
        └── no credible signal / abstain
        ↓
Signal characterization and analyst investigation
```

The compelling figures practically fall out of the experiments:

- A matrix showing which feature–method combinations work on which slices
- Trained GraphSAGE versus random initialization
- Embeddings where malicious sessions visibly cluster but kNN scoring fails
- Representation quality versus anomaly-ranking quality
- Statistically significant score geometry that nevertheless harms analyst retrieval
- Original versus amplified rankings
- Stability across seeds and slices
- Recommend/explore/abstain outcomes
- Feature and relation ablation results
- Interactive analyst views adapted into clean static figures

The malicious-cluster example is especially strong because it communicates the core argument immediately:

> A representation can organize malicious behavior correctly while an apparently reasonable anomaly scorer completely misses it.

That supports the need for the gateway. A conventional benchmark table would merely declare one method bad; your workflow diagnoses **where** it failed.

A credible paper framing could be:

> **Beyond the Winning Anomaly Score: An Agentic Scientific Gateway for Representation, Scoring, and Signal Diagnosis in Unstructured Telemetry**

The paper does not need every component to win. The interesting result is that anomaly pipelines have several independently failing layers:

\[
\text{feature hypothesis}
\neq
\text{representation quality}
\neq
\text{score quality}
\neq
\text{score organization}
\neq
\text{analyst utility}
\]

Your system separates and evaluates those layers instead of collapsing everything into one AP number.

So yes, it would look cool—but more importantly, it could have an unusually coherent story: good visuals, negative controls, unexpected failures, extensibility, analyst relevance, and an honest abstention mechanism. The remaining work is turning those attractive examples into reproducible evidence.

> so like I have just under a week of HARD sprint time left to get just a presentation out that presents the cohesive defensible story and looks visually great. I think it's enough time if I execute cleary. Can you make a final high level to do list

You have enough time if you freeze scope now. The goal is a cohesive, defensible presentation—not a finished publication or production system.

## 1. Freeze the project claim

Use one consistent claim:

> AutoSignal is a method-agnostic scientific gateway that converts agent-proposed telemetry hypotheses into comparable representations and anomaly rankings, diagnoses where the pipeline succeeds or fails, and returns actionable evidence or abstains.

Do not claim:

- Universal detection
- Automatic discovery of the best method
- Production readiness
- That signal-regime significance implies malicious relevance

## 2. Clean the experimental contract

Make sure every method emits the same core artifacts:

- Session-aligned representation \(X\)
- Session-aligned anomaly score \(s\)
- Method, feature-set, relation-set, slice, and seed metadata
- Evaluation metrics
- Failure diagnostics

Also finish:

- Explicit feature-catalog requirement
- Headerless-dataset ingestion adapter
- Strict label isolation everywhere
- Versioned configuration and dataset/slice identifiers

## 3. Add only the two final analytical components

### Cluster-level anomaly scorer

Implement one straightforward cluster-based score that consumes an existing \(X\). Do not create a large cluster-method suite.

Compare it directly with kNN on the same representation.

### Post-hoc representation evaluation

Add:

- Full-space malicious-neighbor purity
- Label silhouette score
- Cross-validated linear probe
- Stability across seeds where applicable

Clearly mark all of these as development-only evaluation.

## 4. Define a small, fixed experiment matrix

Use a manageable selection such as:

- 2–3 datasets
- 2–3 meaningful slices per dataset
- 3–5 agent feature hypotheses
- Existing method suite
- Cluster scorer
- 3–5 seeds for stochastic methods

Freeze this matrix before reviewing the final results. Do not keep adding configurations because something looked interesting.

## 5. Run essential controls

At minimum:

- Random-score baseline
- Raw feature kNN
- GraphSAGE random versus trained
- Real versus shuffled relations if time permits
- kNN versus cluster scoring on the same \(X\)
- Original versus matched signal ranking

Record failures rather than silently dropping them.

## 6. Produce one tidy result table

Every row should represent one:

\[
\text{dataset}
\times
\text{slice}
\times
\text{feature set}
\times
\text{method}
\times
\text{seed}
\]

Include:

- Average precision
- Recall/precision at analyst budgets
- First-malicious rank
- Representation-quality metrics
- Signal regime
- Matched-amplification delta
- Runtime/failure status

This table should drive every presentation figure.

## 7. Select three illustrative case studies

Aim for three distinct outcomes:

1. **Successful ranking**
   A representation and scorer retrieve malicious sessions usefully.

2. **Useful representation, failed scorer**
   Malicious sessions separate in full \(X\), but kNN does not rank them well; test whether cluster scoring helps.

3. **No credible signal**
   Methods are unstable, indistinguishable from controls, or amplification worsens retrieval.

These cases communicate the gateway’s purpose better than a wall of benchmark numbers.

## 8. Create the core visuals

Prioritize six polished figures:

1. End-to-end system architecture
2. Dataset × feature × method performance heatmap
3. Trained GraphSAGE versus random GraphSAGE
4. Representation separation versus anomaly-ranking performance
5. The malicious-cluster/kNN-failure case study
6. Recommend / representation-only / abstain outcome summary

Optional:

- Seed/slice stability plot
- Original versus amplified rank movement
- Feature/relation ablation
- Streamlit analyst screenshot

Keep colors, typography, terminology, and method names consistent.

## 9. Build the presentation around one argument

Suggested flow:

1. Unstructured telemetry makes feature and relation choices uncertain.
2. No representation method is reliably best across conditions.
3. Winning metrics alone hide why a pipeline works or fails.
4. AutoSignal standardizes hypothesis generation, methods, scoring, and evaluation.
5. Controlled experiments expose random, unstable, and non-actionable behavior.
6. Representation quality and anomaly-score quality are distinct.
7. Signal organization can be statistically real but operationally useless.
8. The gateway recommends, reports partial value, or abstains.
9. New methods can enter once and inherit the complete workflow.
10. Results, limitations, and next research steps.

## 10. Be explicit about limitations

Include one honest limitations slide:

- Agent feature quality depends on the supplied feature catalog.
- Current feature proposals are exploratory.
- Dataset slices may contain few malicious sessions.
- UMAP is visualization only.
- Post-hoc label metrics do not drive production scoring.
- Cross-method search requires held-out confirmation.
- Current GraphSAGE objective may not align with anomaly discovery.
- Signal amplification has not consistently improved analyst utility.

This increases credibility.

## Suggested sprint schedule

### Day 1

- Freeze claim and experiment matrix
- Fix label-isolation validation
- Finalize ingestion and feature-catalog contracts
- Verify batch runner outputs tidy results

### Day 2

- Implement cluster-level score
- Implement post-hoc representation metrics
- Add focused tests

### Day 3

- Run the fixed experiment matrix
- Cache everything
- Resolve only experiment-blocking failures

### Day 4

- Analyze results
- Choose the three case studies
- Generate statistical summaries and controls

### Day 5

- Produce final figures
- Draft the complete presentation
- Write conclusions from evidence actually obtained

### Day 6

- Simplify slides
- Validate every number and caption
- Rehearse and identify unclear transitions
- Prepare backup/detail slides

### Final buffer

- Rerun only broken or essential experiments
- Improve visual consistency
- Export and test the presentation
- Prepare a short demo or recorded fallback

## Explicitly cut

Do not spend this sprint on:

- More graph architectures
- A full AutoML optimizer
- Production deployment
- Perfect agent automation
- A comprehensive paper draft
- Large hyperparameter searches
- Rebuilding the Streamlit design
- Forcing signal amplification to work

The presentation succeeds if it shows one clean system, controlled evidence, several revealing outcomes, and a credible path forward.

> Can you output a SUPER detailed prompt here that would be a prompt for an agent to draft up a paper with AS MUCH information as can be said about the project thus far

<details><summary>1 previous message</summary>

> I’ll make this copy-pasteable and explicitly separate what is implemented, what has only been observed informally, and what remains proposed. That distinction is essential so a paper-drafting agent produces a defensible manuscript instead of quietly turning planned experiments into claimed results.
</details>

Copy the prompt below as-is. It tells the drafting agent what is implemented, what is preliminary, what remains proposed, and what it must not fabricate.

```text
You are an expert research scientist and technical writer specializing in anomaly detection, graph machine learning, self-supervised representation learning, cybersecurity telemetry, scientific evaluation, and human-centered analyst systems.

Your task is to draft a rigorous research paper about the project described below. The manuscript should be technically detailed, visually motivated, scientifically honest, and suitable as the foundation for both a research presentation and a later conference/workshop submission.

The project is currently called AutoSignal. Treat that as a working name.

======================================================================
PRIMARY OBJECTIVE
======================================================================

Write a cohesive paper presenting AutoSignal as a method-agnostic, agent-guided scientific gateway for unstructured telemetry.

The central claim is not that AutoSignal has invented a universally superior anomaly detector. The central claim is:

“AutoSignal converts agent-proposed telemetry feature and relation hypotheses into comparable session-level representations and anomaly rankings, evaluates those methods through a shared scientific workflow, diagnoses where the pipeline succeeds or fails, and returns an actionable ranking, a qualified exploratory result, or an abstention.”

The paper should emphasize that telemetry anomaly detection has several separable layers:

1. Dataset interpretation
2. Feature and relation hypothesis generation
3. Session construction
4. Representation learning
5. Anomaly scoring
6. Score-organization diagnosis
7. Analyst-ranking evaluation
8. Recommendation, qualification, or abstention

A major conceptual point is:

representation quality
≠ anomaly-score quality
≠ score-organization quality
≠ malicious-label separation
≠ analyst utility

A visually compelling embedding does not necessarily produce a useful anomaly ranking. A statistically significant organization of anomaly scores does not necessarily align with malicious behavior. A graph encoder can appear sophisticated while performing no better than its randomly initialized control.

The paper should show why these distinctions justify a unified scientific gateway.

======================================================================
EPISTEMIC AND SCIENTIFIC RULES
======================================================================

Follow these rules strictly:

1. Do not fabricate numerical results, dataset counts, confidence intervals, statistical significance, citations, or experimental outcomes.

2. Clearly distinguish among:
   - IMPLEMENTED: present in the current code.
   - PRELIMINARY OBSERVATION: seen during manual development but not yet established through a fixed statistical experiment.
   - PROPOSED: planned but not yet implemented or evaluated.
   - RESULT NEEDED: an experiment that must still be run.

3. Use explicit placeholders such as:
   - [RESULT NEEDED]
   - [DATASET COUNT NEEDED]
   - [CONFIDENCE INTERVAL NEEDED]
   - [CITATION NEEDED]
   - [VERIFY AGAINST CURRENT CODE]
   whenever evidence is unavailable.

4. Do not imply that UMAP visualization proves class separation. UMAP is a visualization artifact. Any claim of representation separation must be supported in the original representation space.

5. Do not claim that the signal-regime analysis detects maliciousness. It diagnoses label-blind organization of the anomaly-score field over a representation-derived neighborhood graph.

6. Do not claim that the current signal amplification improves performance consistently. Preliminary evidence has frequently shown no benefit or substantial harm.

7. Do not claim that trained GraphSAGE currently adds value. Preliminary observations indicate that it often performs nearly identically to its random-initialization control.

8. Do not describe development-label evaluation as unsupervised discovery. The representations and scores are label-free, but AP, Recall@K, post-hoc separation analysis, and method comparisons use labels for development evaluation.

9. Do not claim that the current project is a fully autonomous agent loop. The active system accepts validated agent-produced JSON. The Streamlit application presently allows the user to paste or upload that configuration. The methodological design is agent-guided and intended to become more automated.

10. Novelty should be framed as a possible methodological and systems contribution arising from the integration, contracts, controls, layered diagnosis, and abstention behavior—not from claiming that kNN, GraphSAGE, Node2Vec, permutation tests, or graph smoothing are individually novel.

11. Perform a real related-work search using primary sources before claiming novelty. Cite original papers or authoritative documentation. Never invent a reference.

12. When discussing the project’s strongest claims, use calibrated language such as:
   - “we introduce a framework”
   - “we investigate”
   - “we operationalize”
   - “preliminary evidence suggests”
   - “the framework is designed to”
   - “our controlled evaluation tests whether”
   rather than:
   - “we solve”
   - “we guarantee”
   - “we consistently outperform”
   unless final experiments actually support those statements.

======================================================================
REPOSITORY AND SOURCES OF TRUTH
======================================================================

If repository access is available, inspect these files before drafting:

1. Notebooks/autosignal_engine.py
   - This is the active implementation used by the Streamlit interface.
   - It contains validation, preprocessing, sessionization, graph construction,
     method execution, evaluation, signal-regime diagnosis, and payload creation.

2. Notebooks/main.py
   - Streamlit analyst interface.
   - Shows method comparisons, representations, signal diagnosis, top sessions,
     configuration, and diagnostics.

3. Notebooks/AutoSignal Experiment Workbench.ipynb
   - Organized research interface for fast iteration.
   - Includes cached execution, method leaderboard, GraphSAGE controls,
     graph diagnostics, signal inspection, an interactive plot, an optional
     paired AP bootstrap, and an opt-in multi-slice/multi-seed batch scaffold.

4. Notebooks/sample_agent_config.json
   - Currently contains configurations for multiple datasets.
   - Be careful: the file may now be a list of configuration objects rather than
     one object.
   - The engine expects one matching configuration object per execution.

5. Notebooks/test_autosignal_engine.py
   - Tests configuration behavior, label isolation, result alignment, signal
     formulas, deterministic diagnosis, and JSON-safe payload generation.

6. Notebooks/README_AUTOSIGNAL.md
   - Current execution contract and recorded feature-catalog TODO.

7. SIGNAL_ANALYSIS_STUDY_GUIDE.md
   - Conceptual background for the signal diagnosis.

There is also a separate root-level autosignal package. Do not assume it is the active Streamlit implementation. The current Streamlit path imports Notebooks/autosignal_engine.py.

======================================================================
PROBLEM SETTING
======================================================================

The target domain is heterogeneous, partially structured telemetry.

A dataset may contain process behavior, network flows, timestamps, hosts, users,
executables, parent-child process relationships, resource consumption,
registry activity, communication volume, or other telemetry-specific fields.

The system must cope with datasets whose schemas differ substantially.

Examples of schema problems include:

- Different timestamp-column names
- Missing timestamps
- Existing versus inferred sessions
- Renamed identifiers
- Different label representations
- Different available entity relations
- Leading whitespace in column names
- Headerless datasets accompanied by a separate header specification
- Columns whose names do not convey sufficient semantics

The system is not intended to assume one hard-coded schema.

The agent-generated configuration currently specifies:

- timestamp_col
- existing_session_id_col
- session_group_cols
- graph_relations
- label_col
- malicious_label_values
- selected_columns
- feature_sets

Selected columns include a compact type declaration such as:

- numeric
- boolean
- category
- timestamp

Each feature set includes:

- a name
- a collection of selected columns
- a rationale

Each graph relation includes:

- relation_name
- source_node_type
- source_column
- target_node_type
- target_column
- directed
- meaning

The current system validates that declared columns exist and that feature sets
refer only to selected features.

======================================================================
IMPORTANT FEATURE-AGENT INPUT REQUIREMENT
======================================================================

An essential but not yet fully implemented requirement is that the feature/schema
agent must receive an explicit feature catalog in addition to a dataframe profile.

A profile containing only column names, dtypes, missingness, and cardinality is
not enough. Without semantic information, the agent is guessing from column names.

The future feature catalog should include, where available:

- Feature name
- Human-readable meaning
- Entity or granularity
- Units
- Data type
- Derivation
- Valid aggregation operations
- Availability time
- Missing-value interpretation
- Sentinel-value interpretation
- Whether the feature is raw or engineered
- Leakage restrictions
- Whether the feature is available at scoring time
- Dataset or schema version

The feature agent should:

- Be constrained to cataloged features
- Cite the catalog entries used in each proposal
- Return unsupported feature requirements separately
- Never silently invent columns
- Avoid labels and post-outcome information
- Produce a versioned configuration
- Persist the feature-catalog version in the run manifest

Treat this as an important limitation and future engineering requirement.

======================================================================
HEADERLESS DATASET INGESTION
======================================================================

Some datasets may be headerless but accompanied by a separate header CSV or
schema file.

The recommended architecture is:

headerless data
+ header specification
→ named canonical DataFrame
→ AutoSignal pipeline

Column indices should be used only by an ingestion adapter.

The rest of the system should operate on stable semantic column names.

The ingestion adapter should:

1. Load the header specification.
2. Load the data with header=None.
3. Verify that the number of names equals the number of columns.
4. Reject empty or duplicated names unless an explicit normalization rule exists.
5. Assign canonical names.
6. Preserve an index-to-name provenance manifest.
7. Pass the named dataframe to AutoSignal.

Do not describe this as appending a header row. It is schema assignment during ingestion.

======================================================================
CANONICAL SESSIONIZATION
======================================================================

Every method must operate on the same ordered session IDs.

This is critical because plausible-looking mathematical results can still be
invalid if scores and labels refer to different session orders.

The current implementation supports:

1. Existing session IDs, when configured.
2. Activity-window sessionization, when timestamps are available.
3. One row per session as a fallback.

Current activity-window defaults include approximately:

- Five-minute inactivity boundary
- Thirty-minute maximum session duration

When creating activity-window sessions, configured identity/grouping columns
such as host and user are combined.

The session manifest reports properties including:

- Number of sessions
- Number of rows
- Sessionization strategy
- Timestamp parse success
- Singleton fraction
- Median session size
- 95th-percentile session size
- Largest session size
- Median and 95th-percentile session duration
- Inactivity threshold
- Maximum-duration threshold

This manifest should be part of the scientific record because sessionization
can materially affect every downstream method.

======================================================================
LABEL ISOLATION
======================================================================

Labels are intended to be evaluation-only.

The configuration contains:

- label_col
- malicious_label_values

For example, one newer dataset has a final column named approximately " Label"
with values such as:

- Benign
- Bot

The agent correctly identified:

- label_col: " Label"
- malicious_label_values: ["Bot"]

The engine uses this information to convert row labels into session labels:

- A session is malicious if any row in that session matches a configured
  malicious value.
- Otherwise, it is benign.

The labels are then used to calculate development metrics and optionally color
or reveal points in the interface.

The labels are not intended to be used to:

- Construct feature matrices
- Train GraphSAGE
- Train Node2Vec
- Produce kNN anomaly scores
- Build the session signal graph
- Select a signal regime
- Produce a matched score transform

The current validator explicitly rejects label_col when it is included as a
selected feature.

However, there is a known validation gap that should be described honestly:
the current validator does not yet reject a malicious configuration that uses
the label column as:

- A session-grouping column
- A graph-relation endpoint
- A timestamp
- An existing session ID

The currently inspected Bot/Benign configuration does not use the label in any
of those roles, so that particular configuration is isolated correctly.

A strict future validation rule should reserve the label column exclusively for
evaluation and reject it everywhere else.

For the strongest label-blind agentic protocol, feature/relation generation
should not receive label values at all. Label configuration can be attached by
a separate evaluation wrapper after the agent produces its hypotheses.

======================================================================
FEATURE PREPROCESSING
======================================================================

The active engine builds row-level numeric matrices from declared feature sets.

Current transformations include:

Numeric:
- Coerce to numeric
- Replace infinities with missing values
- Median imputation
- Apply log1p when values are nonnegative and highly skewed
- Standardization

Boolean:
- Normalize string representations such as true/false, yes/no, and 1/0
- Convert to numeric
- Impute missing values

Categorical:
- Normalize identifiers
- Encode using observed frequency

Timestamp:
- Parse timestamps
- Encode hour of day using sine and cosine components

Constant or invalid dimensions are removed where possible.

Rows are pooled into session representations using operations including:

- Mean
- Standard deviation
- Maximum
- Sum
- Log session size

Every method must ultimately produce a session-aligned representation and/or
session-aligned score.

======================================================================
CURRENT METHOD SUITE
======================================================================

The current suite deliberately contains methods that test different representation
hypotheses.

----------------------------------------------------------------------
A. Random-score baseline
----------------------------------------------------------------------

Produces random session scores.

Purpose:

- Establish a sanity floor
- Detect whether apparent performance is plausibly above chance

The random-score baseline is excluded from signal-regime analysis because
building a graph from a one-dimensional random score representation would
manufacture artificial neighborhood organization.

----------------------------------------------------------------------
B. Raw session feature representation plus kNN scoring
----------------------------------------------------------------------

Runs once per agent-proposed feature hypothesis.

Pipeline:

selected row features
→ preprocessing
→ session pooling
→ standardized session representation X
→ mean distance to k nearest neighbors
→ anomaly score s

The kNN anomaly score is the average distance to the nearest non-self neighbors.

Scientific question:

“Does unusual aggregate behavior in this feature hypothesis provide useful
analyst ranking?”

----------------------------------------------------------------------
C. Typed structural statistics plus kNN
----------------------------------------------------------------------

Constructs interpretable graph-derived features based on configured typed relations.

Current structural features include log-transformed in-degree and/or out-degree
statistics for relations incident to the primary node type.

These node-level structural features are mapped and pooled to sessions before
kNN scoring.

Scientific question:

“Do explicit local graph-role statistics carry useful signal?”

----------------------------------------------------------------------
D. Node2Vec/DeepWalk-style topology embedding plus kNN
----------------------------------------------------------------------

The current dependency-light implementation uses the p=q=1 special case,
corresponding closely to unbiased DeepWalk-style random walks.

It operates on a homogeneous projection of the configured typed graph.

Primary-node embeddings are mapped back to rows and pooled into sessions,
followed by kNN anomaly scoring.

Scientific question:

“Does higher-order random-walk proximity reveal useful session structure?”

----------------------------------------------------------------------
E. Random-initialization heterogeneous GraphSAGE plus kNN
----------------------------------------------------------------------

This is a crucial control.

The same GraphSAGE architecture is evaluated before training.

Scientific purpose:

- Determine whether a trained encoder adds value beyond random nonlinear graph
  propagation
- Prevent architectural complexity from being mistaken for learned information

----------------------------------------------------------------------
F. Trained heterogeneous GraphSAGE plus kNN
----------------------------------------------------------------------

The engine builds a typed heterogeneous graph.

Configured forward relations and reverse relations are included.

The system identifies a primary node type, generally corresponding to the most
session-aligned high-uniqueness entity.

Primary-node attributes:

- Receive the selected feature hypothesis
- When multiple rows map to one primary node, row features are averaged
- Include an indicator distinguishing observed nodes

Non-primary node types currently receive only a constant feature of one.

This is an important limitation. Executable, host, user, or other secondary
node types do not yet receive meaningful type-specific attributes.

The GraphSAGE encoder uses relation-specific heterogeneous message passing.

The training objective uses forward-relation reconstruction with:

- Relation-specific bilinear decoders
- Positive observed edges
- Negative edge sampling

After training:

primary-node embeddings
→ row mapping
→ session pooling
→ kNN anomaly score

Scientific question:

“Does learned interaction between the selected attributes and configured typed
relations improve session anomaly ranking beyond the random GraphSAGE control?”

A major preliminary observation is that trained GraphSAGE has often performed
identically or only negligibly better than random GraphSAGE.

Possible explanations include:

- The attributes already carry nearly all usable information
- Relations do not align with malicious behavior
- Constant attributes on secondary node types limit meaningful propagation
- Link reconstruction learns common graph structure rather than anomaly-relevant
  structure
- Graph density or sparsity makes the objective uninformative
- The development slices contain too few malicious sessions
- Random graph propagation acts like a useful random-feature kernel
- Training epochs or the objective are insufficient

Do not select one explanation without controlled evidence.

======================================================================
METHOD-AGNOSTIC ARTIFACT CONTRACT
======================================================================

A key systems contribution is that a method should be implemented once and then
inherit the complete scientific workflow.

Each completed method emits aligned artifacts such as:

- method_key
- method
- hypothesis
- seed
- session_id
- representation coordinates for visualization
- per-session anomaly score
- optional development label
- method-level metrics
- signal-regime result
- signal-channel scores
- failure status and diagnostics

The stable conceptual adapter contract is:

Input:
- Canonical sessions
- Agent feature/relation configuration
- Optional seed and method parameters

Output:
- Session-aligned representation X and/or
- Session-aligned anomaly score s
- Metadata sufficient to reproduce the result

Once a future method emits these artifacts, it can be evaluated through the
same:

- Dataset slices
- Feature hypotheses
- Seeds
- Baselines
- Analyst-budget metrics
- Stability analysis
- Signal diagnosis
- Visualizations
- Recommend/explore/abstain decision

This “implement once, test through the entire scientific workflow” property is
one of the project’s strongest possible methodological contributions.

======================================================================
SIGNAL-REGIME ANALYSIS
======================================================================

For every completed representation except the random baseline, AutoSignal
constructs a session-level similarity graph from that representation.

Let:

- N be the number of canonical sessions
- X ∈ R^(N×F) be a method’s original session representation
- s ∈ R^N be that method’s intrinsic anomaly scores
- A be a symmetric binary session kNN adjacency matrix
- D be the diagonal degree matrix
- P = D^(-1)A be the row-normalized propagation operator

The graph is constructed from the same full representation used for kNN anomaly
scoring—not from the two-dimensional UMAP projection.

The implementation:

1. Uses cKDTree nearest neighbors.
2. Explicitly removes self-neighbors, including duplicate-vector edge cases.
3. Forms a directed kNN graph.
4. Symmetrizes using the union of directed edges.
5. Removes self-loops.
6. Row-normalizes to obtain P.

The diagnostic channels are:

Intrinsic anomaly:
s

Immediate-neighbor support:
Ps

Second-hop support:
P²s

Local signed contrast:
s - Ps

Local contrast magnitude:
|s - Ps|

Intermediate-scale pocket:
Ps - P²s

Neighborhood-supported candidate:
αs + (1-α)Ps

The default amplification mixing coefficient is approximately α=0.5.

The intended interpretations are:

1. Neighborhood-supported / homophily
   High intrinsic anomaly scores have high-scoring immediate neighbors.

2. Locally contrastive
   High intrinsic anomaly scores stand above comparatively normal immediate
   neighbors.

3. Intermediate-scale pocket
   High score support is concentrated in the immediate neighborhood and
   dissipates at the second hop.

4. No useful organization
   None of the three predefined regimes exceeds the label-blind null after
   family-wise correction.

----------------------------------------------------------------------
Exact regime statistics
----------------------------------------------------------------------

The engine first standardizes s.

The tail size is:

max(minimum tail size, ceiling(tail_fraction × N))

bounded by N.

Current defaults include approximately:

- Tail fraction: 5%
- Minimum tail size: 10
- Family-wise alpha: 0.05
- At least 99 permutations
- Higher counts such as 999 intended for stronger final development runs

The three targeted statistics are:

Neighborhood-supported:
- Select the sessions in the highest intrinsic-score tail
- Compute the mean standardized neighbor support Ps over those sessions

Locally contrastive:
- Select the sessions in the highest intrinsic-score tail
- Compute the mean standardized residual s-Ps over those sessions

Intermediate-scale:
- Select the sessions in the highest neighbor-support tail
- Compute the mean Ps-P²s over those sessions

----------------------------------------------------------------------
Permutation null and family-wise correction
----------------------------------------------------------------------

The diagnosis is label-blind.

The engine holds P fixed and repeatedly permutes the intrinsic score vector
across sessions.

For each candidate regime, it computes:

- Observed statistic
- Null mean
- Null standard deviation
- Standardized effect z
- Raw permutation p-value

It then uses the maximum standardized null statistic across the three regimes
to produce a family-wise p-value.

A regime passes only when:

- Its effect z is positive
- Its family-wise p-value is at or below alpha

If multiple regimes pass, the engine selects the passing regime with the
largest effect z.

If none passes, the result is “No useful organization.”

Important qualification:

The family-wise p-value corrects the three regime hypotheses inside one
representation. It does not correct for browsing many:

- Methods
- Feature sets
- Seeds
- Datasets
- Slices

Cross-representation browsing is exploratory. A confirmatory workflow must
freeze one representation before interpreting its regime test.

----------------------------------------------------------------------
Matched amplification
----------------------------------------------------------------------

At most one transform is applied, based on the selected regime:

Neighborhood-supported:
s_supported = αs + (1-α)Ps

Locally contrastive:
s_residual = s-Ps

Intermediate-scale:
s_pocket = Ps-P²s

No useful organization:
retain s unchanged

The resulting ranking is compared with the intrinsic ranking using development
labels only after the label-blind regime selection.

The implementation records:

- Intrinsic score
- Neighbor support
- Second-hop support
- Local contrast
- Contrast magnitude
- Pocket score
- Supported candidate
- Matched score
- Intrinsic rank
- Matched rank
- Rank gain

A matched transform should be rejected when it does not improve analyst utility.

The current interface uses a conservative development interpretation:
amplification is supported only when AP improves and the first-malicious review
position does not worsen.

======================================================================
PRELIMINARY SIGNAL FINDINGS
======================================================================

Treat the following as preliminary development observations, not final claims.

In one recorded Node2Vec/M2 seed-42 development result:

- Neighborhood-supported structure passed:
  effect z approximately 2.51
  family-wise p approximately 0.027

- Intermediate-scale structure also passed and was stronger:
  effect z approximately 6.12
  family-wise p approximately 0.001

- The system selected Intermediate-scale.

However, the matched pocket transform substantially harmed malicious-session
retrieval:

- Intrinsic AP approximately 0.045818
- Pocket AP approximately 0.007705
- First malicious moved from approximately rank 47 to rank 379
- Malicious sessions in top 250 moved from approximately 15 to 0

Interpretation:

- There was statistically detectable organization of the anomaly-score field.
- That organization did not align with malicious analyst utility.
- Structural significance was not equivalent to malicious relevance.
- The correct operational choice was to reject the amplifier and retain the
  intrinsic ranking.
- This is a valuable negative-control example if it is reproducible and clearly
  presented as development evidence.

Across other manual tests, the signal-regime transformations have frequently
appeared useless or harmful.

Do not conceal this.

Possible paper interpretation:

- Signal diagnosis may remain useful as a descriptive or abstention mechanism.
- Its current matched transformations have not demonstrated consistent
  analyst-value improvements.
- The framework is valuable partly because it can reject its own proposed
  intervention.

Do not force the signal stage into the paper as a successful enhancement.

======================================================================
PRELIMINARY BOT/BENIGN DATASET OBSERVATION
======================================================================

A newer dataset uses a final label column containing values such as:

- Benign
- Bot

The agent correctly identified Bot as the malicious value.

In preliminary manual visualization, malicious/Bot sessions appeared to group
together strongly.

At the same time, the current signal-regime analysis appeared useless.

This observation motivates an important distinction:

A representation may separate malicious behavior while the chosen anomaly
scorer fails to assign high anomaly scores.

One possible geometry is:

- Benign sessions form a dense population
- Bot sessions form a separate but internally dense population

A pointwise kNN-distance scorer asks:

“Is this individual session far from its nearest neighbors?”

If Bot sessions are nearest neighbors to each other, they may receive ordinary
scores even when the Bot population is globally distinct from the benign
population.

The score s can therefore discard information present in X.

The subsequent channels Ps, s-Ps, and Ps-P²s operate on s. They cannot reliably
recover class information already lost during X→s.

This is only a hypothesis until the separation is validated in the original
representation space.

The paper must not use an attractive UMAP plot as proof.

======================================================================
PROPOSED FINAL ADDITION: POST-HOC REPRESENTATION EVALUATION
======================================================================

This is proposed and may be implemented during the final sprint.

The goal is to evaluate representation X independently from anomaly score s.

Development-only post-hoc metrics should include:

1. Full-space malicious-neighbor purity
   - For each session, examine labels among nearest neighbors in X
   - Quantify whether malicious sessions share neighborhoods
   - Compare against class-prevalence and permutation baselines

2. Label-based silhouette score
   - Computed in the original representation
   - Treated cautiously under severe imbalance

3. Cross-validated linear probe
   - Fit a simple classifier on frozen representations
   - Use strict cross-validation or grouped/temporal splits
   - This tests recoverable label information, not deployment anomaly scoring
   - Avoid interpreting training-set separability as generalization

4. Centroid or distribution separation
   - Distance between benign and malicious representation distributions
   - Include uncertainty and sensitivity to scaling

5. Seed stability
   - Compare separation across stochastic representations

6. Slice stability
   - Determine whether apparent separation recurs under related data conditions

This enables a more informative result taxonomy:

A. Useful representation and useful anomaly ranking
B. Useful representation but failed anomaly scorer
C. No credible representation-level separation
D. Insufficient evidence due to low malicious count or instability

======================================================================
PROPOSED FINAL ADDITION: CLUSTER-LEVEL ANOMALY SCORING
======================================================================

This is proposed unless confirmed in the current code.

It should be implemented as one additional scorer consuming an existing
session representation X.

The purpose is to test:

“Does a distinct, internally coherent, relatively uncommon behavioral population
deserve a high anomaly score even when its individual members are not isolated
from one another?”

Possible implementations include:

- HDBSCAN followed by cluster rarity and separation scoring
- Gaussian-mixture likelihood
- Cluster-Based Local Outlier Factor
- Distance from the dominant-cluster prototype
- Isolation Forest operating on the embedding
- Spectral clustering followed by cluster rarity

For the near-term scope, choose one straightforward and defensible method.
Do not implement a large cluster-scoring suite.

The cluster scorer should emit the same session-aligned score contract as other
methods and should be compared directly against kNN on the exact same X.

A useful cluster score might combine:

- Inverse cluster prevalence
- Separation from the dominant cluster
- Cluster density
- Distance to a global or dominant normal prototype
- Explicit handling of noise points

Any formula must be specified before looking at its final labeled performance,
or described as exploratory.

The cluster scorer is not a signal amplifier. It is a separate X→s scoring
method.

======================================================================
KEY RESEARCH QUESTIONS
======================================================================

Organize the paper around questions like these:

RQ1:
Do agent-proposed feature hypotheses produce materially different and
reproducible session representations across telemetry datasets and slices?

RQ2:
Do graph-based representations add analyst value beyond raw feature geometry
and simple structural statistics?

RQ3:
Does trained GraphSAGE improve over the same architecture at random
initialization?

RQ4:
Are method rankings stable across seeds and meaningful data slices, or are
apparent winners driven by sampling noise?

RQ5:
Can a representation contain recoverable malicious separation even when its
unsupervised anomaly score fails?

RQ6:
Does cluster-level scoring recover distinct malicious populations that
pointwise kNN distance misses?

RQ7:
Does label-blind signal-regime diagnosis predict when a matched score transform
will improve analyst triage?

RQ8:
Can the gateway recognize unsupported results and abstain instead of always
declaring a winner?

RQ9:
What aspects of a result arise from:
- Agent feature hypotheses
- Relations
- Representation training
- The anomaly scorer
- Random initialization
- Data-slice composition

Do not require every research question to have a positive answer.

======================================================================
EXPERIMENTAL DESIGN
======================================================================

The desired experiment is a controlled matrix over:

- Dataset
- Data slice
- Agent feature hypothesis
- Relation configuration
- Representation method
- Anomaly scorer
- Random seed

A tidy result row should correspond to:

dataset
× slice
× feature set
× method
× scorer
× seed

Recommended near-term scope:

- 2–3 datasets
- 2–3 meaningful slices per dataset
- 3–5 deliberately distinct feature hypotheses
- Current implemented method suite
- One cluster-level scorer
- 3–5 stochastic seeds

Slices should represent meaningful telemetry conditions rather than arbitrary
post-hoc subsets.

For every slice, record:

- Definition
- Time range if available
- Number of rows
- Number of sessions
- Malicious-session count and prevalence
- Entity counts
- Relation counts
- Relation coverage
- Session-size distribution
- Any known attack/behavioral context

Use at least one untouched dataset, time period, or split for confirmation.

Separate:

1. Search/development data
   - Generate and eliminate hypotheses

2. Selection data
   - Choose a final candidate and decision rule

3. Untouched confirmation data
   - Test the frozen choice once

The agent should not repeatedly revise feature proposals after seeing test-label
performance.

======================================================================
ESSENTIAL CONTROLS
======================================================================

Include as many of these as time permits, clearly labeling those not yet run:

1. Random-score baseline

2. Raw feature representation plus kNN

3. Typed structural statistics plus kNN

4. Node2Vec plus kNN

5. Random GraphSAGE plus kNN

6. Trained GraphSAGE plus kNN

7. Real relations versus shuffled relations

8. Real node attributes versus shuffled attributes

9. Primary-node attributes only versus meaningful attributes on secondary
   node types, if implemented

10. kNN scoring versus cluster-level scoring on the same X

11. Intrinsic score versus the single regime-matched transform

12. Agent-proposed features versus a simple human/basic feature baseline

13. Labels removed entirely in score-only mode, verifying identical scores

Controls should isolate where any improvement comes from.

Example interpretations:

- Trained GraphSAGE ≈ random GraphSAGE:
  graph training has not demonstrated value.

- Trained GraphSAGE ≈ shuffled-relation control:
  configured relations have not demonstrated value.

- GraphSAGE > raw kNN:
  relational aggregation may add useful information.

- Full-space representation separation is good but AP is poor:
  scorer failure rather than representation failure.

- Development gains disappear on untouched data:
  selection overfitting.

- Significant score organization but worse matched ranking:
  structural organization does not align with malicious utility.

======================================================================
EVALUATION METRICS
======================================================================

Primary anomaly-ranking metrics:

- Average precision
- Recall@25
- Recall@50
- Recall@100
- Recall@250
- Precision at the same review budgets
- Number of malicious sessions found at each budget
- Reviews required to find the first malicious session

Why average precision:

- Malicious sessions may be rare
- ROC AUC can appear optimistic under extreme class imbalance
- Analyst review is a ranked-retrieval problem

Representation-quality metrics:

- Full-space neighbor purity
- Cross-validated linear-probe AP
- Label silhouette score
- Distribution/centroid separation
- Stability across seeds
- Stability across slices

Stability metrics:

- Score-rank correlation
- Top-K overlap
- Variance across seeds
- Variance across slices
- Confidence interval of paired method differences

Operational metrics where possible:

- Runtime
- Memory
- Method failures
- Graph-construction failures
- Number of usable sessions
- Relation coverage

======================================================================
STATISTICAL ANALYSIS
======================================================================

Because methods score the same sessions, use paired comparisons.

Recommended analyses:

1. Paired bootstrap confidence intervals for AP differences

2. Paired bootstrap intervals for Recall@K differences

3. Seed-to-seed variability

4. Rank correlation across repeated runs

5. Top-K overlap across seeds and slices

6. Permutation tests when malicious sample sizes are extremely small

7. Family-wise or false-discovery correction where many confirmatory
   comparisons are performed

8. Effect sizes and practical thresholds, not p-values alone

For trained versus random GraphSAGE, emphasize:

ΔAP =
AP_trained - AP_random

Report uncertainty around ΔAP.

A tiny positive difference should not be described as meaningful merely because
the trained value is numerically larger.

Define practical significance relative to analyst review.

For example:

- Does the method retrieve additional malicious sessions within the first 25,
  50, or 100 reviews?
- Does it reduce reviews required to reach the first malicious session?
- Is the improvement stable enough to matter?

Avoid selecting the best result from dozens of configurations and reporting it
without accounting for the search.

======================================================================
RECOMMEND / EXPLORE / ABSTAIN
======================================================================

The final gateway should support at least three outcomes:

1. Recommend
   - The method shows stable, materially useful improvement over controls
   - Performance is supported across seeds/slices
   - Analyst-budget utility is credible
   - Confirmation evidence is available

2. Exploratory or representation-only finding
   - Interesting structure or separation exists
   - Evidence is unstable or scorer performance is weak
   - The result is useful for further investigation but not a deployment claim

3. Abstain
   - No tested representation produces credible signal
   - Results are indistinguishable from controls
   - Sample size is inadequate
   - Stability is poor
   - Amplification worsens utility
   - The telemetry does not contain recoverable target information

The system should not always return whichever method is least bad.

An honest output may be:

“No tested representation produced sufficiently stable and actionable
separation on this slice.”

This is a feature of the methodology, not a software exception.

======================================================================
POSSIBLE CONTRIBUTIONS
======================================================================

Frame contributions conservatively and revise them after the related-work review.

Possible contribution 1:
A schema-adaptive, agent-guided contract that translates heterogeneous telemetry
into explicit feature and relation hypotheses.

Possible contribution 2:
A method-agnostic session representation interface enabling raw, structural,
random-walk, graph-neural, and future methods to enter one evaluation workflow.

Possible contribution 3:
A layered evaluation framework that separates:
- representation quality
- anomaly-score quality
- score organization
- malicious retrieval
- analyst utility

Possible contribution 4:
Mandatory random and structural controls that expose when trained graph methods
do not add value.

Possible contribution 5:
A label-blind graph-relative signal diagnosis with family-wise correction,
paired with a rule allowing at most one matched transform.

Possible contribution 6:
An explicit mechanism for rejecting harmful amplification and abstaining when
evidence is weak.

Possible contribution 7:
An analyst-facing workflow that converts scientific evidence into ranked review
queues, visual diagnostics, and downloadable session-level artifacts.

Possible contribution 8:
Evidence that visually or structurally compelling behavior can be scientifically
misleading:
- trained GraphSAGE may match random GraphSAGE
- UMAP grouping may not imply useful ranking
- significant score geometry may not imply malicious relevance
- a useful representation may be paired with the wrong anomaly scorer

Do not state that all of these are novel until related work confirms it.

======================================================================
NOVELTY FRAMING
======================================================================

The individual components are not expected to be novel:

- kNN anomaly scoring is established
- Node2Vec is established
- GraphSAGE is established
- Graph reconstruction is established
- UMAP is established
- Permutation testing is established
- Graph propagation and residual channels are established
- Streamlit visualization is engineering

The potential novelty is method-level and systems-level:

- Agent-guided schema adaptation
- Explicit feature/relation hypotheses
- One canonical session contract
- Pluggable representation and scoring methods
- Random and shuffled controls
- Layer-separated evaluation
- Label-blind score-regime diagnosis
- One matched intervention
- Analyst-utility validation
- Recommend/explore/abstain outcomes
- Extensibility through one method adapter

A possible novelty statement is:

“Rather than proposing another fixed anomaly encoder, AutoSignal operationalizes
a scientific gateway that asks where evidence enters a telemetry pipeline,
whether learned structure adds value beyond controls, whether the resulting
representation and scorer agree, and whether any intervention improves the
analyst review queue.”

This statement still requires literature support.

======================================================================
RELATED-WORK CATEGORIES
======================================================================

Research and cite primary sources for:

1. Classical unsupervised anomaly detection
   - kNN distance
   - Local Outlier Factor
   - Isolation Forest
   - cluster-based anomaly detection

2. Deep one-class and representation-based anomaly detection
   - autoencoders
   - Deep SVDD
   - self-supervised tabular representations

3. Graph representation learning
   - DeepWalk
   - Node2Vec
   - GraphSAGE
   - heterogeneous graph neural networks
   - heterogeneous graph transformers where relevant

4. Attributed graph anomaly detection
   - DOMINANT
   - CoLA
   - graph autoencoder approaches
   - contrastive graph anomaly methods

5. Temporal graph learning
   - Temporal Graph Networks
   - temporal event encoders
   but treat these as future extensions unless implemented

6. Automated feature engineering and agentic data systems
   - LLM-based schema interpretation
   - data-centric agents
   - automated feature generation
   - scientific agents
   - agent-based AutoML
   Carefully distinguish AutoSignal from unconstrained AutoML.

7. Graph signal processing
   - propagation
   - smoothing
   - graph residuals
   - multi-scale graph filters

8. Evaluation under class imbalance
   - precision-recall analysis
   - analyst-budget ranking
   - uncertainty for paired retrieval comparisons

9. Selective prediction and abstention
   - systems that decline unsupported predictions
   - uncertainty-aware decision systems

10. Human-centered cybersecurity triage
   - ranked analyst workflows
   - alert fatigue
   - interpretable investigation support

Do not cite secondary summaries when original papers are available.

======================================================================
PAPER NARRATIVE
======================================================================

A strong narrative is:

1. Unstructured telemetry creates uncertainty before model selection even begins.

2. Feature, session, and relation decisions determine what every downstream
   representation can learn.

3. Existing workflows often compare a few final metrics without separating:
   - feature quality
   - representation quality
   - scorer quality
   - random architectural effects
   - analyst usefulness

4. AutoSignal converts schema interpretation into explicit, inspectable
   hypotheses.

5. Every method shares the same sessions and artifact contract.

6. Random and structural controls test whether graph training contributes
   anything real.

7. Label-blind signal diagnosis characterizes the organization of anomaly
   scores, while development labels independently test malicious utility.

8. Preliminary failures are informative:
   - trained GraphSAGE can resemble random GraphSAGE
   - significant score geometry can harm retrieval
   - a representation may visually group malicious behavior while kNN scoring
     fails

9. These cases motivate separating representation assessment from scoring.

10. A cluster-level scorer tests whether coherent anomalous populations require
    a different X→s mapping.

11. The gateway returns a recommendation only when evidence is credible;
    otherwise it reports a representation-only finding or abstains.

12. Any future method can be implemented once and inherit the complete
    experimental workflow.

======================================================================
REQUIRED PAPER STRUCTURE
======================================================================

Produce a complete draft with the following sections.

1. Title
   Provide 5 candidate titles and select one.

Possible title directions:

- Beyond the Winning Anomaly Score: An Agentic Scientific Gateway for
  Unstructured Telemetry

- AutoSignal: Separating Representation, Scoring, and Signal Quality in
  Agent-Guided Telemetry Triage

- When the Embedding Works but the Anomaly Score Fails: A Scientific Gateway
  for Telemetry Representation Search

- From Schema Hypotheses to Analyst Triage: A Method-Agnostic Evaluation
  Framework for Telemetry Anomaly Detection

- Diagnosing the Anomaly Pipeline: Agent-Guided Representation and Scoring
  Analysis for Heterogeneous Telemetry

2. Abstract
   Approximately 200–250 words.
   Include:
   - Problem
   - System idea
   - Layered evaluation
   - Method suite
   - Controls
   - Preliminary or final results, clearly qualified
   - Main contribution
   Do not fabricate final results.

3. Introduction
   Explain:
   - Why telemetry schemas vary
   - Why feature and relation selection are uncertain
   - Why one winning AP score is insufficient
   - Why random graph controls matter
   - Why representation and scorer quality must be separated
   - Why abstention is useful
   End with a conservative contribution list.

4. Related Work
   Organize by the categories listed above.
   Explain the gap without exaggeration.

5. Problem Formulation
   Define:
   - Raw telemetry rows
   - Canonical sessions
   - Feature hypothesis h
   - Relation set R
   - Method m
   - Representation X_(m,h)
   - Score s_(m,h)
   - Evaluation label y
   - Review budget K
   - Representation-quality and ranking-quality objectives
   - Recommend/explore/abstain decision

6. System Overview
   Describe:
   - Ingestion
   - Feature catalog
   - Agent configuration
   - Validation
   - Sessionization
   - Graph construction
   - Method execution
   - Scoring
   - Evaluation
   - Signal diagnosis
   - Analyst output
   Clearly identify current versus planned components.

7. Agent-Guided Feature and Relation Hypotheses
   Cover:
   - JSON contract
   - Feature sets
   - Graph relations
   - Need for a semantic feature catalog
   - Prevention of invented features
   - Label exclusion
   - Headerless ingestion
   - Versioning and provenance

8. Canonical Session and Graph Construction
   Cover:
   - Shared session order
   - Sessionization strategies
   - Typed graph construction
   - Primary node selection
   - Forward and reverse edges
   - Relation manifests
   - Coverage diagnostics
   - Current limitations

9. Representation and Scoring Methods
   Give each current method its own subsection.
   Include random GraphSAGE as a first-class control.
   Clearly distinguish X from s.

10. Signal-Regime Diagnosis
    Include:
    - A, D, and P
    - s, Ps, P²s
    - Residual and pocket formulas
    - Exact regime statistics
    - Permutation null
    - Max-stat family-wise correction
    - Winner rule
    - One matched transform
    - Why labels are excluded from selection
    - Why statistical score organization is not malicious relevance

11. Representation-Level Post-Hoc Evaluation
    Mark as proposed or implemented based on repository inspection.
    Cover:
    - Neighbor purity
    - Silhouette
    - Linear probes
    - Stability
    - Development-only status

12. Cluster-Level Scoring
    Mark as proposed or implemented.
    Explain the dense-but-distinct malicious-population failure mode.
    Specify the selected cluster-scoring formula if implemented.
    Otherwise provide a clearly labeled proposed design.

13. Experimental Protocol
    Include:
    - Datasets
    - Slices
    - Feature sets
    - Methods
    - Seeds
    - Controls
    - Metrics
    - Development/selection/holdout split
    - Statistical comparisons
    - Multiple-comparison policy
    - Runtime environment
    Use placeholders where information is missing.

14. Results
    Do not invent.
    Organize results by research question.
    Include preliminary observations only when explicitly labeled.
    Create empty or partially populated table templates when needed.

15. Case Studies
    Include three desired case-study structures:

    Case A: Useful ranking
    - [RESULT NEEDED]

    Case B: Useful representation, failed scorer
    - Bot/Benign visual observation
    - Full-space verification required
    - kNN versus cluster-level score

    Case C: Significant structure, harmful amplification
    - Node2Vec intermediate-scale preliminary example
    - Clearly mark as development evidence

    Optional Case D: Trained GraphSAGE ≈ random GraphSAGE
    - Show paired seed/hypothesis comparisons

16. Discussion
    Discuss:
    - What “failure” means at each pipeline layer
    - Why negative findings are useful
    - When graph methods are justified
    - Why method extensibility matters
    - Why the system should abstain
    - Whether signal diagnosis belongs in the final core or optional diagnostics

17. Limitations
    Include at minimum:
    - Feature-agent dependence on the feature catalog
    - Current manual configuration transfer
    - Potential label configuration leakage if validation is not strengthened
    - Limited dataset/slice counts
    - Low malicious prevalence
    - UMAP limitations
    - Current secondary-node constant attributes
    - Link-reconstruction objective may not align with anomaly detection
    - Signal diagnosis and scorer graph are both derived from X
    - Multiple-method exploratory search
    - Need for untouched holdout confirmation
    - Cluster-level method not yet established
    - No production claim

18. Ethical and Operational Considerations
    Discuss:
    - Analyst overtrust
    - Alert fatigue
    - False positives
    - Dataset bias
    - Security consequences of missed detections
    - Transparency of abstention
    - Labels as imperfect ground truth
    - Need for human review

19. Reproducibility
    Cover:
    - Versioned configs
    - Feature-catalog versions
    - Dataset fingerprints
    - Slice definitions
    - Seeds
    - Cached result payloads
    - Session alignment
    - Failure logging
    - Tests
    - Exact method adapters
    - Streamlit and notebook interfaces

20. Conclusion
    Reiterate the layered scientific-gateway contribution.
    Do not claim universal detection.
    Emphasize extensibility and evidence-aware abstention.

21. Appendix
    Include:
    - Configuration schema
    - Metric definitions
    - Signal formulas
    - Additional controls
    - Example run manifest
    - Example method adapter
    - Label-isolation checklist
    - Feature-catalog schema
    - Headerless ingestion manifest
    - Additional result-table templates

======================================================================
REQUIRED FIGURES
======================================================================

Design detailed figure specifications and captions.

Figure 1: End-to-end architecture
Show:

Unstructured telemetry
→ ingestion/schema normalization
→ feature catalog
→ agent feature/relation hypotheses
→ validation
→ canonical sessions and typed graph
→ representation methods
→ anomaly scorers
→ controlled evaluation
→ signal diagnosis
→ recommend / representation-only / abstain
→ analyst output

Figure 2: Layer decomposition
Show that:

feature hypothesis
→ representation X
→ anomaly score s
→ score organization
→ analyst ranking

Include separate failure markers at every transition.

Figure 3: Experiment matrix heatmap
Rows:
- Dataset/slice

Columns:
- Feature × method × scorer

Color:
- AP or Recall@K

Overlay:
- Stability or uncertainty

Figure 4: Trained versus random GraphSAGE
Use paired points or a difference plot.
Each pair should share:
- Dataset
- Slice
- Feature hypothesis
- Seed

Figure 5: Representation quality versus anomaly-ranking quality
X-axis:
- Full-space separation or linear-probe metric

Y-axis:
- Unsupervised anomaly AP or Recall@K

This should make “useful representation, failed scorer” visually obvious.

Figure 6: Bot/Benign case study
Potential panels:
A. UMAP visualization, explicitly labeled exploratory
B. Full-space neighbor-purity result
C. kNN score distribution
D. Cluster-level score distribution
E. Analyst retrieval curves

Do not create panels without actual evidence.

Figure 7: Signal diagnosis case
Show:
- Intrinsic s
- Ps
- s-Ps
- Ps-P²s
- Regime evidence
- Original versus matched ranking
- The harmful intermediate-scale example

Figure 8: Outcome taxonomy
Three destinations:
- Recommend
- Useful representation / investigate scorer
- Abstain

Figure 9: Analyst interface
Optional screenshot or polished mockup showing:
- Method selection
- Signal channel
- Regime evidence
- Ranking comparison
- Top sessions

All figures should share one visual language and color palette.

Do not use red/green alone for accessibility.

======================================================================
REQUIRED TABLES
======================================================================

Table 1:
Dataset and slice characteristics

Table 2:
Feature hypotheses and source columns

Table 3:
Method suite and the scientific question each method tests

Table 4:
Control matrix

Table 5:
Main ranking results with uncertainty

Table 6:
Representation-quality versus score-quality metrics

Table 7:
Trained-minus-random GraphSAGE differences

Table 8:
Signal-regime evidence and matched-transform outcomes

Table 9:
Failure and abstention cases

Create templates with [RESULT NEEDED] where data is unavailable.

======================================================================
WRITING STYLE
======================================================================

Write for a technically sophisticated audience in machine learning systems,
cybersecurity analytics, graph learning, or applied anomaly detection.

The prose should be:

- Clear
- Precise
- Critical
- Evidence-driven
- Visually oriented
- Honest about negative results
- Free of marketing language
- Explicit about implementation status

Use equations where they improve precision.

Avoid unnecessary jargon.

Define “signal” carefully. In this paper, signal can mean several things:

- Information present in representation X
- Anomaly values in score vector s
- Organization of s over a neighborhood graph
- Malicious-label retrieval performance

Never switch among these meanings without qualification.

Prefer phrases such as:

- “representation-level separation”
- “intrinsic anomaly score”
- “graph-relative score organization”
- “development-label retrieval”
- “analyst-budget utility”

======================================================================
EXPECTED OUTPUT
======================================================================

Produce the following in order:

1. Five candidate titles
2. Selected title with justification
3. One-sentence thesis
4. Paper abstract
5. Detailed contribution list
6. Full paper draft in Markdown
7. All equations in readable LaTeX
8. Detailed figure storyboard and captions
9. Detailed table templates
10. A list of every claim requiring additional evidence
11. A list of every experiment still required
12. A list of potential reviewer objections and proposed responses
13. A short “presentation version” of the paper story in 10–12 slides
14. A concise checklist for converting the draft into a submission
15. A bibliography containing only verified references

If repository access is available, inspect the implementation before writing.

If repository access is not available, use the project description above but
mark implementation-sensitive claims as [VERIFY AGAINST CURRENT CODE].

Do not stop merely because some results are missing. Draft the strongest honest
paper possible, using explicit placeholders and alternative wording for
different possible outcomes.

Where appropriate, provide two versions of conclusions:

- Conclusion if cluster-level scoring improves retrieval
- Conclusion if cluster-level scoring also fails

The paper should remain valuable under either result.

The ultimate message should be:

AutoSignal does not assume that a sophisticated representation, significant
score structure, or visually compelling embedding is automatically useful.
It places each layer under controlled evaluation, identifies where information
is gained or lost, and exposes enough evidence for a human analyst or researcher
to recommend a method, investigate a partial success, or abstain.
```
