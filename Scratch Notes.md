## Metric Suite to expand to later

#### Triage Method score:

These are label-free scores that could actually rank sessions before you know labels:

- raw_session_stats_knn
- density_peak_score
- compact_isolated_cluster_score

#### Representation diagnostic:

These use labels after the representation/neighbors are fixed:

- malicious_knn_enrichment
- malicious_neighbor_purity
- label_homophily_at_k

If I had to pick the core three:

``malicious_neighbor_purity_at_15`

``malicious_mean_neighbor_rank`

``malicious_cluster_fragmentation`

Why those three:

`malicious_neighbor_purity_at_15`: “When I stand on a malicious session, how many nearby sessions are also malicious?” This is closest to what your enrichment diagnostic is trying to capture.

`malicious_mean_neighbor_rank`: “How close are malicious sessions to each other relative to all sessions?” This avoids over-fixating on one arbitrary k.

`malicious_cluster_fragmentation`: “Are malicious sessions in one coherent neighborhood, or scattered across unrelated regions?” Very helpful for deciding whether steering/few-shot retrieval is promising.

average_precision
reviews_to_first_malicious
recall_at_25 / 50 / 100 / 250
precision_at_25 / 50 / 100 / 250

Table 1: Triage performance
method | AP | reviews_to_first | recall@25 | recall@50 | ...

Table 2: Representation diagnostics
representation | malicious_neighbor_purity@15 | enrichment_vs_random | malicious_mean_neighbor_rank | fragmentation

---

Chat

# Review notebook baseline

> can you look over the current notebook [Graph Triage Baseline v0.ipynb](Notebooks/Graph Triage Baseline v0.ipynb) and see if its good baseline. Use the [SIMPLIFIED_PLAN.md](SIMPLIFIED_PLAN.md)

<details><summary>9 previous messages</summary>

> I’ll read the simplified plan alongside the notebook structure first, then I’ll sanity-check the actual code/outputs against what the baseline is supposed to prove.
>
> The first pass already shows a mismatch with the plan: the notebook is still carrying exploratory steering/visualization ideas and a placeholder pipeline entry point, while the plan wants a tight v0 discovery comparison. I’m going to inspect the remaining cells and the notebook outputs/metadata so the assessment is grounded rather than vibes-based.
>
> The notebook is short: 26 cells, ending at graph construction. That means the central v0 evidence tables from the plan cannot exist yet in this version, so I’m now checking the exact spots where it diverges and whether any cells already leak labels or make evaluation claims.
>
> One important thing I noticed from saved outputs: the graph builder produced 3,131 sessions while the strawman baseline produced 1,457 sessions. That alone makes the current baseline comparison undefined unless the sessionization is unified, so I’m going to try a non-mutating notebook execution in `/tmp` to see whether there are also runtime issues.
>
> `jupyter` isn’t installed in this environment, so I can’t execute the notebook as a notebook here. I can still run a small direct Python check against the parquet files to validate the most important protocol questions: session counts, holdout viability, and the strawman’s actual review metric.
>
> I found the data files and the core Python stack is available. I’m running the protocol-level check now; this will give us concrete numbers for whether the current strawman is at least behaving plausibly and whether the holdout has malicious sessions.
>
> The direct Python check hit a local environment gap: pandas is installed, but neither `pyarrow` nor `fastparquet` is available here, so parquet loading fails outside your notebook kernel. I’ll avoid installing anything and finish the review from the notebook’s saved code/outputs plus the plan.
>
> Saved outputs are still useful: they include the dev slice manifest, the strawman score distribution, malicious-session rows, and the graph build summary. I’m extracting just the plain-text parts now so the final assessment can cite actual notebook evidence without dumping the giant HTML plot output.
>
> I’ve got enough to give you a clean answer now. Short version before the full notes: it has the bones of the v0 baseline, but I would not treat this notebook as a defensible baseline yet.

</details>

Short answer: not yet. It has good scaffolding, but I would not treat the current notebook as a defensible v0 baseline under [SIMPLIFIED_PLAN.md](./SIMPLIFIED_PLAN.md:5).

**Findings**

- The pipeline entry point is still a stub. `run_discovery_pipeline` returns `None` for `session_table`, `baseline_scores`, `graph_scores`, and `metric_summary`, while the plan asks for a real `run_minimal_discovery_pipeline` result bundle. See [notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:16469>) and [plan](./SIMPLIFIED_PLAN.md:92).

- There is no v0 graph-vs-strawman result yet. The notebook defines raw kNN scoring, but does not compute `average_precision`, `reviews_to_first_malicious`, random expectation, recall/precision budgets, graph embeddings, graph kNN scores, or seed mean/std. Those are the central acceptance criteria in [SIMPLIFIED_PLAN.md](./SIMPLIFIED_PLAN.md:182).

- Sessionization is inconsistent. The strawman groups by `session_identity`, while graph sessions group by `session_host` plus `session_identity`; saved outputs show `1457` raw-session rows but `3131` graph sessions. That makes the baseline and graph scores non-comparable until they share one frozen session table. See [strawman sessionization](<./Notebooks/Graph Triage Baseline v0.ipynb:24684>), [graph sessionization](<./Notebooks/Graph Triage Baseline v0.ipynb:30183>), and saved graph output at [notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:30066>).

- Label leakage risk is present. `neighbour_distance_weighted_enrichment` directly uses `session_table["label"]` to produce a score, and the graph object stores `red_team` as `data["process"].y`. Even if not used for training yet, this violates the spirit of labels-as-evaluation-only and should be removed or isolated from v0 scoring. See [notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:24807>) and [notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:30172>).

- The manifest is incomplete and will mislabel non-dev runs. `get_slice_manifest` uses global `DATA_PATH`, comments out session counts, and lacks git hash, config dump, malicious session counts, and file-node count. The holdout is loaded, but no viability check is recorded. See [notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:270>) and [plan](./SIMPLIFIED_PLAN.md:62).

What is good: the fixed chronological `tail(100_000)` slice is aligned with the plan, the raw-stats plus `StandardScaler` plus kNN strawman is the right first baseline shape, and the numeric-column exclusions are thoughtful. The minimal graph also avoids same-user/same-host edges, which is correct for v0.

I could not execute the notebook cleanly here: `jupyter` is not installed, and the shell Python lacks `pyarrow`/`fastparquet` for parquet reads. This review is based on the notebook code and saved outputs. Best next step is to collapse this into the minimal pipeline: one sessionizer, one strawman score, one graph score over seeds 42/43/44, one `metric_summary`, and the five v0 tables only.

> okay I made the pipeline entry point. It lacks all the graph stuff because I meant the actual RAW baseline part, after that I will fix up the graph stuff to make equal sessions an whatever and so now the pipeline entry point I think is close to being set up in a way that it can be easy to make it modular and just add each future method into the config and all that and then attach a scoring parser later which can keep track of the scoring and format into a thing which I can then put into tables in a paper etc etc
>
> So yes graph baseline will come next
>
> Sessionization is inconsistent because the graph thing will come next. It's inconsistent because the graph creates sessions based on the process and file node connections, and I will have to find a way to make that consistent with the number of sessions that came out of the raw one, which I guess is by using the same time cut off rules?
>
> Label leakage in the score is good to point out but isn't it okay to be in the score as it is? Liek genuine question, not a challenge. It's being used to CHECK which ones were malicious and which not, as far as I understand. Like don't you have to check at some point? The data["process"].y aren't those supposed to be ground truth labels? I know it's supposed to be unsupervised but if I do not use them is that not okay?
>
> I don't fully understand the issues you are pointing out about the slice manifest

<details><summary>1 previous message</summary>

> Got it. I’ll look at the updated entry point first so I can separate “raw baseline is shaping up” from “graph v0 still pending,” then I’ll answer the label/session/manifest questions directly.

</details>

Yep, that framing makes sense: for the _raw baseline only_, the new entry point is closer. I’d think of the graph as the next method plugin, but the evaluation session IDs should be shared.

**Labels / Leakage**
You are exactly right that you must check labels at some point. The clean boundary is:

```python
scores = method(features)          # no labels available here
metrics = evaluate(scores, labels) # labels used here only
```

So `red_team` is fine for `session_table["label"]`, top-25 inspection, AP, recall@K, reviews-to-first-malicious, etc.

The leakage issue is specifically `distance_weighted_enrichment_score`: it uses `session_table["label"]` inside the score itself in [the notebook](<./Notebooks/Graph Triage Baseline v0.ipynb:24761>). That makes it an oracle/semi-supervised diagnostic, not an unsupervised anomaly score. It is okay as an after-the-fact analysis, but I would not report it as a v0 baseline method.

For `data["process"].y`: PyG commonly stores ground-truth labels there. It is okay if training/scoring never reads it. For strict hygiene, though, I’d keep labels outside `graph_data` until evaluation, because it makes accidental use much harder.

**Sessionization**
For v0, I would not let the graph define evaluation sessions by connected components. That makes each method answer a different question.

Better shape:

1. Run one frozen sessionizer first: user/host identity + 5-minute inactivity + 30-minute max duration.
2. Attach `session_id` to every process row.
3. Raw baseline aggregates rows by that `session_id`.
4. Graph baseline builds process/file/parent graph, learns process embeddings, then mean-pools process embeddings by the same `session_id`.

The graph can have edges that cross sessions; that’s fine. The evaluation unit still stays fixed.

**Manifest**
The manifest is just a reproducibility receipt. The current issue is not graph-specific. It should answer: “What exact slice and config produced this result?”

Right now `get_slice_manifest(df)` still uses global `DATA_PATH`, so a holdout manifest could accidentally say train. It also lacks session count, malicious session count, config, git hash, and the sessionizer parameters. Also, the notebook currently references `dev_df` before creating it in a clean run.

For raw v0, I’d include at least:

```text
source_file
slice_rule = tail(100000) after sort by process_started
row_count
start/end timestamp
num_processes
num_sessions
num_malicious_processes
num_malicious_sessions
session_inactivity_minutes = 5
max_session_duration_minutes = 30
k = 15
scaler = StandardScaler
feature_builder = raw_session_stats
git_commit
```

Your entry point is moving in the right direction. The main next cleanup is to split `metric_eval` into two pieces: one scorer that returns score columns, and one evaluator that uses labels only after scores already exist.

> okay so for the enrichment score, if I don't use labels, what do I do? I want a score for when malicious clusters are close together. Like they don't have to be outliers right, they could be tightly packed as long as they ARE packed together. Need a score for that
>
> and but what happens later when I try different ways to sessionize implicitly with the graph?

Totally fair question. The key distinction is:

You can use labels to **evaluate** whether a tight cluster was malicious.
You cannot use labels to **create the score** if the method is supposed to be unsupervised discovery.

Your current enrichment score is basically asking: “are my neighbors malicious?” That is a valid diagnostic, but as a scoring method it already knows the answer.

**What To Use Instead**
For unlabeled “tight suspicious cluster” behavior, score geometry, not maliciousness. A good raw-baseline add-on would be a `rare_compact_cluster_score` or `density_peak_score`.

Conceptually:

```python
local_density = 1 / mean_distance_to_k_neighbors
separation = distance_to_nearest_point_with_higher_density
score = local_density * separation
```

Higher score means: “this session sits in a dense pocket that is separated from other dense pockets.” That catches the case you care about better than pure outlier distance, because the session itself does not need to be lonely. It can be part of a tight group.

Another version:

```python
score = high_if(
    cluster_is_small
    and cluster_is_internally_tight
    and cluster_is_separated_from_other_clusters
)
```

So your raw v0 methods could become:

```text
raw_session_stats_knn
raw_session_stats_density_peak
raw_session_stats_rare_compact_cluster
```

Then labels come in afterward:

```python
scores = compute_unsupervised_scores(X)
metrics = evaluate(scores, session_table["label"])
```

Important limitation: if malicious sessions are tightly packed but embedded inside a big benign dense region, no unsupervised score can know they are malicious. You’d need better features, graph structure, text/process semantics, or a few-shot/anchor setup.

**What To Do With The Current Enrichment Score**
Keep it, but rename it mentally to something like:

```text
oracle_neighbor_label_enrichment
```

Use it only as a diagnostic question:

“Given the current representation, are malicious sessions near each other?”

That is useful! It tells you whether the representation has malicious cluster structure. It just should not be reported as an unsupervised baseline score.

**Graph Sessionization Later**
For the main comparison, keep one fixed evaluation unit: bounded sessions from the same time cutoff rules.

Graph method should do this:

```text
process/file graph -> process embeddings -> pool by fixed session_id -> session score
```

So yes, use the same 5-minute inactivity and 30-minute duration rules to define the sessions you evaluate. The graph can still have process/file edges across those sessions, but the final score gets assigned back to the fixed sessions.

If later you want the graph to implicitly create its own “sessions” or communities, treat that as a separate experiment:

```text
Experiment A: fixed session triage, fair comparison against raw baseline
Experiment B: graph-native grouping / campaign discovery
```

For graph-native groups, you can label a group malicious if any process inside is malicious, but the review unit has changed. A graph component with 200 processes is not the same analyst burden as a 2-process session, so report group counts and maybe process-count cost too.

Best next raw-only addition: replace label enrichment with `density_peak_score`, then evaluate AP/reviews-to-first using labels afterward.

> I don't understand what you mean about the score. I get that its a good diagnostic but I don't get why it can't be a score. Lke SPECIFICALLY why. You're saying the method already knows the answer... that's kind of the point? Like when you get scored on a test, you need to know the answer. If you check accuracy or percision of something, you need to know the correct answer to measure against it. What do you mean specifically cause I think you're touching on something that I'm not getting fully.

Ah, yes. This is the crux. You’re not wrong about “you need the answer key to score a test.” The confusion is that we’re using the word **score** for two different things.

There are two separate stages:

```python
# Stage 1: detector / triage method
session_score = method(telemetry_features)

# Stage 2: evaluation
metrics = compare(session_score, ground_truth_labels)
```

Your enrichment score currently does this:

```python
session_score = method(telemetry_features, ground_truth_labels)
```

That is the specific problem.

The test analogy is:

- The **student’s answer** is like the model’s triage ranking.
- The **answer key** is like `red_team`.
- The **grade** is AP / precision / recall / reviews-to-first.

It is totally valid for the grader to use the answer key. But if the student uses the answer key while writing the answers, the grade no longer measures whether the student understood the material.

In your current function, this line is the answer key entering the detector:

```python
is_malicious = (session_table["label"] == "malicious").values
```

Then the score becomes:

```python
score_for_session_i = weighted_average(labels_of_i_neighbors)
```

So the score is not saying:

> “This session is geometrically suspicious.”

It is saying:

> “This session is near sessions that I already know are malicious.”

That can absolutely be useful. It just answers a different question.

For unsupervised discovery, the real-world situation is: you have telemetry, but you do not know which sessions are malicious yet. So a valid unsupervised score must be computable before seeing `red_team`.

A clean rule of thumb:

```text
If changing red_team labels changes the score values, then the score is label-aware.
If changing red_team labels only changes the evaluation metrics, then the method is label-isolated.
```

Your `raw_session_stats_knn` passes this. If you shuffled `red_team`, the raw kNN anomaly scores would stay identical, but AP/precision/recall would change.

Your enrichment score does not pass this. If you shuffled `red_team`, the enrichment scores themselves would change, even though the telemetry stayed the same. That means the score is partly made from the ground truth.

So the answer is: it **can** be a score, but it is not an unsupervised discovery score. I would name it something like:

```text
oracle_neighbor_label_enrichment
```

and use it as a diagnostic:

> “Does this representation place malicious sessions near each other?”

That is a good, meaningful diagnostic.

If you want to make it a legitimate method, you need to define it as **semi-supervised / few-shot / steering**:

```text
Given 1 known malicious session, find other sessions near it.
```

Then the split is:

```python
known_labels = only the anchor / seed labels
hidden_eval_labels = labels used only for evaluation
```

In that setting, neighbor enrichment is valid if it only uses the known anchor labels, not the labels of all sessions you are trying to discover.

So:

```text
Unsupervised v0:
telemetry -> score -> compare to labels

Oracle diagnostic:
telemetry + all labels -> label-neighborhood score -> inspect representation

Few-shot steering:
telemetry + a small set of known labels -> score -> compare to hidden labels
```

Your instinct is good: “malicious clusters might be tight, not outliers” is real. The fix is not “never use this idea.” The fix is to decide which experiment it belongs to. For v0 unsupervised baseline, use label-free cluster geometry. For steering/few-shot, use known malicious anchors and evaluate on labels that were not used to create the score.

> but WHO Is the student? The features coming in ARE the student. The test is DONE by the time the score is called. The is malicious is checking the sessiont table to grade the test. The cluster is already made. Now we check to see if the malicious ended up packing together... no?

Yes, exactly: **if the cluster is already made, and you are checking whether malicious sessions packed together, that is valid.** That is not the part I’m objecting to.

The issue is what you do with that value afterward.

Let’s drop the student analogy and make it concrete.

Your current enrichment score is basically:

```python
score_i = weighted_average(red_team labels of i's neighbors)
```

So for each session `i`, you are assigning a suspiciousness score by looking at the ground-truth labels of nearby sessions.

That is fine if the question is:

> “Did my representation put malicious sessions near other malicious sessions?”

That is a **representation diagnostic**.

It is not fine if the question is:

> “Can this method rank sessions for analyst review before labels are known?”

Because in that second case, the analyst does not already know which neighbors are malicious. The score would not be computable in deployment.

So you are right here:

> “The cluster is already made. Now we check to see if the malicious ended up packing together.”

Yes. That should be written as an evaluation metric, something like:

```text
malicious_knn_enrichment
malicious_neighbor_purity
label_homophily_at_k
```

For example:

```python
# After embeddings/neighbors are already built
malicious_neighbor_rate = mean(
    fraction of each malicious session's neighbors that are also malicious
)
```

That answers:

> “Are malicious sessions locally clustered in this representation?”

Great diagnostic. Very useful.

The line gets crossed when you turn that into a per-session ranking score and say:

```text
top_25_by_distance_weighted_enrichment_score
```

Because now the score is no longer just grading the cluster. It is using labels to decide which sessions should rank high.

A tiny example:

```text
Cluster A: 10 sessions, tightly packed, all benign
Cluster B: 10 sessions, tightly packed, all malicious
```

A label-free method can see:

```text
A is tight
B is tight
```

But it cannot know:

```text
B is the malicious one
```

Your enrichment score can know that because it reads the labels inside Cluster B. That’s why it’s an oracle diagnostic, not an unsupervised triage score.

So I’d separate them like this:

```text
Method score:
raw_session_stats_knn
density_peak_score
compact_isolated_cluster_score

Representation diagnostic:
malicious_knn_enrichment
malicious_neighbor_purity
label_homophily_at_k
```

Your intuition is good. Keep the enrichment idea. Just don’t put it in the same bucket as “scores an analyst could use before knowing labels.”

> Okay I will call it a diagnostic then. Because honestly that test tells me more about the efficacy of the method than the score does. So what score is best match for that? what score suite would you say to use? Not now, later, right now I ahve my raw distance score for anomaly detection, and then I have the representation diagnostic (the enrichment) I will note the ones you listed to expand to later but are those the ones you would make a test suite out of?

Yes, I’d absolutely make a small **representation diagnostic suite** out of those. And I agree with your instinct: for understanding whether the representation is useful, the diagnostic can be more informative than the anomaly score. The anomaly score answers “would this rank well today?” The diagnostic answers “is there signal here worth building on?”

For later, I’d split the suite into two buckets.

**Triage Scores**
These are label-free scores that could actually rank sessions before you know labels:

```text
raw_knn_distance
density_peak_score
compact_isolated_cluster_score
cluster_rarity_score
```

For your current notebook, `raw_knn_distance` is enough.

**Representation Diagnostics**
These use labels after the representation/neighbors are fixed:

```text
malicious_knn_enrichment
malicious_neighbor_purity_at_k
malicious_mean_neighbor_rank
same_label_homophily_at_k
malicious_cluster_fragmentation
```

If I had to pick the core three:

```text
malicious_neighbor_purity_at_15
malicious_mean_neighbor_rank
malicious_cluster_fragmentation
```

Why those three:

`malicious_neighbor_purity_at_15`: “When I stand on a malicious session, how many nearby sessions are also malicious?” This is closest to what your enrichment diagnostic is trying to capture.

`malicious_mean_neighbor_rank`: “How close are malicious sessions to each other relative to all sessions?” This avoids over-fixating on one arbitrary `k`.

`malicious_cluster_fragmentation`: “Are malicious sessions in one coherent neighborhood, or scattered across unrelated regions?” Very helpful for deciding whether steering/few-shot retrieval is promising.

Then report the normal triage metrics separately:

```text
average_precision
reviews_to_first_malicious
recall_at_25 / 50 / 100 / 250
precision_at_25 / 50 / 100 / 250
```

So later your paper table shape could be:

```text
Table 1: Triage performance
method | AP | reviews_to_first | recall@25 | recall@50 | ...

Table 2: Representation diagnostics
representation | malicious_neighbor_purity@15 | enrichment_vs_random | malicious_mean_neighbor_rank | fragmentation
```

That separation is clean and honest. It lets you say something like:

> “The raw anomaly score did/did not rank malicious sessions early, but the representation diagnostic shows malicious sessions are locally enriched, motivating a steering/few-shot next step.”

That is a strong story. It’s not trying to smuggle labels into the detector; it’s using labels to understand what the geometry learned.

> yes I agree and I like this a lot. Let's just pick the strongest for now to replace teh enrichment one with for this notebook

<details><summary>18 previous messages</summary>

> Agreed. The strongest single replacement is a label-aware **diagnostic**, not a per-session triage score: `malicious_neighbor_purity_at_k` plus its enrichment over random base rate. I’ll patch the notebook so the raw anomaly score remains label-free and the neighborhood-label check is clearly reported as a diagnostic.
>
> <details><summary>Explored 6 files, a search</summary>
>
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
> - Searched for `def metric_eval|distance_weighted|anomaly_enrichment|run_triage_baseline|from regex` in `Graph Triage Baseline v0.ipynb`
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
> - Read `./Notebooks/Graph Triage Baseline v0.ipynb`
>
> </details>
>
> I’m going to make the notebook say this distinction in code: one label-free anomaly score, then one label-aware representation diagnostic. The diagnostic I’m choosing is `malicious_neighbor_purity_at_k`, with `enrichment_vs_random` as the most paper-friendly number.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Graph Triage Baseline v0.ipynb` (+39 -14)
>
> </details>
>
> The old per-session enrichment function is now a one-row diagnostic summary. Next I’m updating the evaluator so it no longer writes an enrichment “score” column into `session_table`.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Graph Triage Baseline v0.ipynb` (+3 -3)
>
> </details>
>
> Now I’m swapping the evaluator return shape: `anomaly_distance_z_score` remains the raw-score helper output, and the second return is the diagnostic table.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Graph Triage Baseline v0.ipynb` (+6 -8)
>
> </details>
>
> I’m also renaming the local variables in the pipeline entry point so future-you does not accidentally treat the diagnostic as a scoring method.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Graph Triage Baseline v0.ipynb` (+10 -7)
>
> </details>
>
> The notebook JSON needs a quick validity check after patching; then I’ll scan for stale references to the old enrichment score name.
>
> <details><summary>Explored a search, ran 2 commands</summary>
>
> <details><summary>Explored a search</summary>
>
> - Searched for `distance_weighted_enrichment|anomaly_enrichment|neighbour_distance|malicious_neighbor_purity|representation_diagnostic|from regex` in `Graph Triage Baseline v0.ipynb`
>
> </details>
>
> - Ran `jq empty "Notebooks/Graph Triage Baseline v0.ipynb"`
> - Ran `git diff -- "Notebooks/Graph Triage Baseline v0.ipynb"`
>
> </details>
>
> The only remaining old enrichment references are saved notebook outputs from a previous run, not source code. I’m checking the source-only view now; the notebook will need a rerun to refresh those displayed outputs.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | rg -n "malicious_neighbor_purity|representation_diagnostic|raw_session_stats_knn"`
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | rg -n "distance_weighted_enrichment|anomaly_enrichment|neighbour_distance|from regex"`
> - Ran `git diff --stat -- "Notebooks/Graph Triage Baseline v0.ipynb"`
>
> </details>
>
> One tiny robustness tweak: if there is only one malicious session, “enrichment over random” has a zero denominator, so I’m making that `NaN` rather than infinity.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./Notebooks/Graph Triage Baseline v0.ipynb` (+1 -1)
>
> </details>
>
> The source is clean now; I’ll do one last JSON check and source scan before wrapping up.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `jq empty "Notebooks/Graph Triage Baseline v0.ipynb"`
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | rg -n "distance_weighted_enrichment|anomaly_enrichment|neighbour_distance|from regex"`
> - Ran `git diff --stat -- "Notebooks/Graph Triage Baseline v0.ipynb"`
>
> </details>

</details>

Picked and wired in the strongest single diagnostic for now: `malicious_neighbor_purity_diagnostic` in [Graph Triage Baseline v0.ipynb](<./Notebooks/Graph Triage Baseline v0.ipynb:24822>).

What changed:

- Replaced the old distance-weighted enrichment “score” with a label-aware representation diagnostic.
- The raw anomaly score remains `raw_session_stats_knn`.
- The diagnostic now reports:
  - `malicious_neighbor_purity_at_k`
  - `median_malicious_neighbor_purity_at_k`
  - `malicious_sessions_with_any_malicious_neighbor_at_k`
  - `base_malicious_rate_excluding_self`
  - `enrichment_vs_random`
- Updated `metric_eval` to return `anomaly_distance_z_score` plus `representation_diagnostic`, instead of a second score column.

I also removed the stray `from regex import T`.

I did not rerun the notebook, so some saved outputs may still show the old `anomaly_enrichment_z_score` display until you execute the cells again. The notebook JSON validates cleanly, and the source no longer references the old enrichment function.

> <div>
> <style scoped>
>     .dataframe tbody tr th:only-of-type {
>         vertical-align: middle;
>     }
>
>     .dataframe tbody tr th {
>         vertical-align: top;
>     }
>
>     .dataframe thead th {
>         text-align: right;
>     }
>
> </style>
> <table border="1" class="dataframe">
>   <thead>
>     <tr style="text-align: right;">
>       <th></th>
>       <th>diagnostic</th>
>       <th>k</th>
>       <th>n_sessions</th>
>       <th>n_malicious_sessions</th>
>       <th>base_malicious_rate_excluding_self</th>
>       <th>malicious_neighbor_purity_at_k</th>
>       <th>median_malicious_neighbor_purity_at_k</th>
>       <th>malicious_sessions_with_any_malicious_neighbor_at_k</th>
>       <th>enrichment_vs_random</th>
>     </tr>
>   </thead>
>   <tbody>
>     <tr>
>       <th>0</th>
>       <td>malicious_neighbor_purity_at_k</td>
>       <td>15</td>
>       <td>1457</td>
>       <td>19</td>
>       <td>0.012363</td>
>       <td>0.207018</td>
>       <td>0.266667</td>
>       <td>0.842105</td>
>       <td>16.745419</td>
>     </tr>
>   </tbody>
> </table>
> </div>

This is a strong diagnostic result.

Read it as:

```text
Base chance of a neighbor being malicious: ~1.24%
Actual malicious-neighbor purity around malicious sessions: ~20.7%
Enrichment over random: ~16.7x
84.2% of malicious sessions have at least one malicious neighbor in top-15
```

So the raw session feature space is absolutely putting malicious sessions near other malicious sessions. That does **not** mean the anomaly score will necessarily rank them early, but it does mean the representation has real local malicious structure.

The one mildly funny-looking bit is:

```text
mean purity = 0.207
median purity = 0.267
```

That means the typical malicious session has about `4 / 15` malicious neighbors, but some malicious sessions have few or none, pulling the mean down. That is useful: there is a cluster signal, but it may be fragmented.

This is exactly the kind of sentence I’d put in notes:

> The raw session representation shows strong malicious local enrichment: malicious sessions have malicious top-15 neighbors at 16.7x the random baseline, and 84.2% have at least one malicious neighbor. This supports using the representation for steering/few-shot retrieval even if pure anomaly ranking is weaker.

I’d keep this diagnostic. It’s doing real work.

> so I like this diagonistic and the raw distance score. what else is left for this baseline

For the **raw baseline**, you’re close. I’d say what’s left is mostly turning it from “good exploratory notebook” into “paper-ready baseline artifact.”

**Must-Have Left**

1. Add triage metrics for `raw_session_stats_knn`:
   - `average_precision`
   - `reviews_to_first_malicious`
   - `random_expected_reviews_to_first`
   - `found_at_25/50/100/250`
   - `recall_at_25/50/100/250`
   - `precision_at_25/50/100/250`

2. Add a `random_score` sanity control:
   - It should be bad-ish.
   - It gives you a calibration point for reviews-to-first and recall@K.

3. Return clean tables from the pipeline:

   ```python
   {
       "slice_manifest": ...,
       "session_table": ...,
       "score_table": ...,
       "metric_summary": ...,
       "representation_diagnostic": ...,
       "top_25_by_raw_score": ...,
   }
   ```

4. Fix/expand the slice manifest:
   - source file
   - slice rule
   - row count
   - timestamp range
   - number of sessions
   - malicious sessions
   - sessionization params
   - `k`
   - scaler
   - feature columns or feature count
   - git hash/config if easy

5. Make label usage explicit:
   - `raw_session_stats_knn` does not use labels.
   - `metric_summary` uses labels.
   - `malicious_neighbor_purity_diagnostic` uses labels and is reported as diagnostic.

**Nice But Not Required Yet**

- Holdout viability check: confirm test split has malicious sessions before making claims.
- Determinism check: run raw baseline twice and confirm same scores.
- Clean `metric_eval` so it returns tables rather than displaying as its main behavior.
- Remove old exploratory UMAP/datamapplot from the baseline reporting path, or keep it clearly marked as exploration.

**Not Needed For This Raw Baseline**

- Graph score.
- Graph sessionization.
- Density peak score.
- Compact cluster score.
- Steering/few-shot retrieval.

So the baseline story becomes:

> Raw session stats + StandardScaler + kNN distance gives an unsupervised anomaly ranking. We evaluate that ranking with AP/reviews-to-first/recall@K. Separately, malicious-neighbor purity tests whether the raw representation clusters malicious behavior locally.

That’s a solid v0 raw baseline.

> okay I will do that, can you just look over the raw session creation and assure there's no like leakage. If it comes from the actual DATASET then FINE cause that's not my problem that's the data that I'm working with but note if it's an identity issue or not it's just a good clustering job.

<details><summary>6 previous messages</summary>

> I’ll treat this as a focused leakage/identity review of the raw session path only: sessionization, feature construction, excluded columns, and what the selected feature list likely contains.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | nl -ba | sed -n '360,520p'`
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | rg -n "bad_user|red_team|label_|process_started_seconds|process_stop_seconds|num_user_name|session_identity|feature_columns|STRAWMAN_EXCLUDE"`
> - Ran `jq -r '.cells[] | select((.outputs // []) | length > 0) | .outputs[]?.data["application/vnd.microsoft.datawrangler.viewer.v0+json"]?.columns[]?.name' "Notebooks/Graph Triage Baseline v0.ipynb" | sort -u`
>
> </details>
>
> I’m checking the actual raw feature path, not the graph bits. The two things I’m looking for are label-like columns that slip past your exclusions, and identity/time proxies that could make the clustering “good” for a brittle reason.
>
> <details><summary>Explored a search, ran a command</summary>
>
> - Ran `jq -r '.cells[] | select(any(.outputs[]?.data["application/vnd.microsoft.datawrangler.viewer.v0+json"]?.columns[]?.name; . == "session_size")) | .outputs[]?.data["application/vnd.microsoft.datawrangler.viewer.v0+json"]?.columns[]?.name' "Notebooks/Graph Triage Baseline v0.ipynb"`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `session_size|bad_user_mean|process_started_seconds_mean|first_seen_mean|feature_builder` in `Graph Triage Baseline v0.ipynb`
>
> </details>
>
> </details>
>
> The feature exclusion list is doing some important cleanup already: `red_team`, `label_*`, sigma hit/count columns, MITRE/LOLBAS rows, and several numeric encodings of names/hashes are excluded. I’m checking the remaining likely proxies now.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | nl -ba | sed -n '110,155p;275,340p;1000,1040p'`
> - Ran `jq -r '.cells[].source[]?' "Notebooks/Graph Triage Baseline v0.ipynb" | rg -n 'bad_user|process_started_seconds|process_stop_seconds|first_seen|last_seen|_first_seen|_last_seen|file_id|agent_id|hostname|user_name|token_elevation_type|duration_seconds'`
>
> </details>

</details>

I looked over the raw session creation path. I would **not fully assure it yet**. The structure is mostly clean, but there are a couple of likely leak/proxy columns to tighten.

The good parts:

- `red_team` is excluded from numeric features.
- `label_*` columns are excluded.
- Sigma rule outputs are excluded via `_sigma_hits` / `_sigma_rows`.
- `lolbas_num_rows` and `mitre_num_rows` are excluded.
- Several encoded identity/hash columns are excluded: `num_user_name`, `num_process_name`, `num_parent_pid_hash`, hashes, etc.
- `user_name` / `hostname` are used for sessionization, not directly as score features. That is fine under your plan.

The two things I would fix:

1. **Exclude `bad_user` if it is numeric.**
   That column name is extremely label-like. If `bad_user` is in the dataset and numeric, your current `strawman_numeric_columns` will include it, because it is not `red_team`, not `label_*`, and not in the exclude sets. That would be leakage.

2. **Exclude absolute timestamp features from the raw score.**
   Columns like `process_started_seconds`, `process_stop_seconds`, and possibly `first_seen` / `last_seen` / `*_first_seen` / `*_last_seen` can make the representation cluster by chronology. If red-team activity happens in a narrow time window, you get a “good” malicious cluster because the attack happened together in time. That is a real dataset fact, but it is a different claim than “process/session behavior clusters maliciously.”

I’d add something like:

```python
STRAWMAN_EXCLUDE_EXACT = {
    "bad_user",
    "lolbas_num_rows",
    "mitre_num_rows",
    "process_started_seconds",
    "process_stop_seconds",
}

def strawman_numeric_columns(sessionized_df):
    return [
        c for c in sessionized_df.select_dtypes(include=[np.number]).columns
        if c not in {"session_id", "red_team"}
        and not c.startswith("label_")
        and not c.endswith("_sigma_hits")
        and not c.endswith("_sigma_rows")
        and not c.endswith("_first_seen")
        and not c.endswith("_last_seen")
        and c not in STRAWMAN_EXCLUDE_EXACT
        and c not in STRAWMAN_EXCLUDE_ID_LIKE
    ]
```

Identity note: if the diagnostic is strong after this cleanup, I’d be more comfortable calling it a real behavioral/session-stat clustering result. If it drops a lot, then the current clustering was probably helped by label-like or chronology proxies. Still useful to know, just a different interpretation.

can you try it without changing my notebook

I tried it without changing the notebook.

Result: the raw baseline looks **not obviously label-leaky**, and the malicious clustering diagnostic survives removing the absolute time columns.

I compared:

```text
current features
tight features = current minus process_started_seconds/process_stop_seconds,
                 plus explicit bad_user exclusion
```

Key result:

```text
current enrichment_vs_random: 16.75x
tight enrichment_vs_random:   19.02x
```

So the malicious-neighbor clustering is **not being propped up by absolute process start/stop timestamps**. It actually got a bit stronger after removing them.

The raw anomaly ranking is still weak in both:

```text
current AP: 0.0163, first malicious at rank 128
tight AP:   0.0150, first malicious at rank 126
random expected first malicious: ~72.85
```

So the story is consistent:

> Raw distance anomaly score is not great for first-hit triage, but the raw representation has strong malicious local clustering.

On `bad_user`: it is `object` dtype with value `'BAD'`, so your current numeric-only feature builder was **not including it**. Still worth explicitly excluding it later so it doesn’t sneak in if you add categorical/text encoding.

The only actual feature cleanup from the tight run was:

```text
process_started_seconds_mean
process_started_seconds_std
process_stop_seconds_mean
process_stop_seconds_std
```

Identity-wise: I don’t see explicit identity leakage in the raw score path. `user_name`/`hostname` are used for sessionization, but not as features; numeric identity encodings like `num_user_name`, `num_process_name`, hashes, etc. are excluded. So I’d call this a good clustering diagnostic, not just identity leakage, with the caveat that the sessionization itself is identity-bounded by design.

---

# catch up on the MASTER_PLAN.md and this

> catch up on the [MASTER_PLAN.md](MASTER_PLAN.md) and this
>
> User context
>
> Attachments:
>
> - I'm working on a project. My project details are in this directory. The main no…: `~/.codex/attachments/ff9c640d-8ea9-46d8-9b85-16af37b23d21/pasted-text.txt`

<details><summary>2 previous messages</summary>

> I’ll read the master plan and the attached context, then reconcile them with the currently open planning notes so I can give you a crisp project-state summary.
>
> The attached thread clarifies the current interpretation: ignore the discarded telemetry graph, freeze the strawman sessions as the review unit, and keep methods label-free while using labels only for post-hoc diagnostics/evaluation. I’m checking the notebook’s present cells against that handoff so I don’t inherit stale assumptions.

</details>

Caught up. My current working understanding is:

- The strawman sessionizer defines the canonical review unit: sessions.
- The frozen dev slice is the development dataset; it does not itself define review units.
- The previous telemetry graph is discarded, so its sparsity and repair phases are currently irrelevant.
- All method scores must be label-free.
- Labels may be used afterward for metrics and behavioral diagnostics—such as malicious-neighbor purity, conductance, and spectral energy.
- Any choice made using those diagnostics becomes development-label-informed and must be frozen before holdout evaluation.
- The immediate next implementation is the session-similarity graph and fixed GSP filter bank using the existing session feature matrix and raw score.
- The signal regime is an empirical diagnosis, not a prior assumption. Filter behavior plus label-aware audits and matched nulls provide evidence for smooth, contrastive, multiscale, or absent relational signal.
- The later telemetry graph should be designed fresh and audited before structural statistics, Node2Vec, or GraphSAGE.

One nuance I’ll preserve: a winning filter channel is evidence about the useful transformation, but the regime claim should also be supported by energy/conductance diagnostics and null comparisons—not inferred from ranking performance alone.

No files changed.

> okay thanks. What does that mean the filter bank thing, can you explain that. I have session feature matrix as in my table of sessions which is a raw session stats feature matrix whatever. I don't have a graph yet, unless you mean the knn is the similarity graph

Yes—the kNN structure is the similarity graph.

Your current pipeline already computes distances between session feature vectors. Instead of using those neighbors only to produce one anomaly score, the filter-bank approach treats them as graph edges:

```text
raw telemetry
    ↓
session feature matrix X
    ↓
k-nearest-neighbor graph between sessions
    ↓
initial score s₀ for every session
    ↓
several fixed transformations (“filters”) of s₀
```

Each node is one session. An edge means “these sessions are similar in raw session-stat space.” This is a session-similarity graph, distinct from the heterogeneous telemetry graph you may build later.

If \(P\) is the row-normalized neighbor matrix, then:

- \(s_0\): original kNN anomaly score.
- \(Ps_0\): average score among a session’s neighbors. Tests whether anomaly evidence is locally shared.
- \((I-P)s_0 = s_0-Ps_0\): difference from neighbors. Tests whether a session is locally surprising.
- \(Ps_0-P^2s_0\): difference between one-hop and two-hop neighborhoods. Tests intermediate-scale/local-boundary structure.
- Restart diffusion: repeatedly spreads scores through nearby sessions while retaining some original score. Tests whether evidence becomes stronger over several hops.

It is called a “filter bank” because you apply several fixed graph transformations to the same signal \(s_0\), analogous to examining an image with smoothing, edge-detection, and scale-specific filters.

The important distinction is:

- \(X\) constructs the similarity graph.
- \(s_0\) is a signal located on its session nodes.
- The filters test how that signal behaves relationally.

One caveat: because both the graph and \(s_0\) come from the same feature space, this is a geometry baseline, not yet evidence that explicit telemetry relations help. That comes later with the heterogeneous telemetry graph.

> so this filter bank, I would apply to all graph methods I do later?

Not automatically.

The filter bank is initially a standalone baseline on the session-similarity graph. It answers:

> Does relationally transforming the raw anomaly score reveal signal that the raw score misses?

Later graph methods—structural statistics, Node2Vec, GraphSAGE—primarily produce new session representations. First evaluate each cleanly:

```text
representation → common scoring rule → ranking metrics
```

Only afterward, if justified, you can apply the same general filtering idea:

```text
method’s initial session scores → chosen session graph → graph filter → amplified scores
```

Keep these two stages separate:

1. Representation comparison
   Evaluate raw features, structural features, Node2Vec, and GraphSAGE without amplification. This determines where useful signal exists.

2. Conditional amplification
   Apply a filter only when diagnostics support it—for example:
   - Smooth/clustered signal → neighbor averaging or restart diffusion
   - Contrastive signal → residual/high-pass filter
   - Intermediate-scale signal → one-hop versus two-hop filter
   - No graph signal → no filtering

Also, you must explicitly choose which graph performs the filtering. It could be:

- the raw-feature session kNN graph,
- a kNN graph built from a learned representation, or
- a session-level graph derived from telemetry relations.

Those are different hypotheses and should not be mixed casually.

So the short answer is: use the filter bank now as a basic method and diagnostic; later, apply a preselected filter to other methods only as a separate amplification experiment—not as a mandatory part of every graph method.

> okay so why are we doing it on the session similarity graph

Because it is the simplest graph you already implicitly have: your kNN scorer finds each session’s nearest neighbors, and those neighbor relationships form a session-similarity graph.

It gives us a cheap first question:

> Does the local geometry of the raw session features contain useful information that the original point-anomaly score fails to use?

For example, a malicious session may not be individually unusual, but it may belong to a suspicious group of mutually similar sessions. Filtering can expose that group-level pattern.

However, this has strict limits:

- It tests similarity in raw feature space—not telemetry relationships.
- The graph and original score come from the same features, so results may be partly redundant.
- Any “smooth versus contrastive” diagnosis applies only to this similarity graph.
- It cannot determine the signal regime of a future heterogeneous telemetry graph.

So we are doing it as a low-cost geometry baseline and proof of the score-amplification concept. It is not the project’s main graph, and it is not mandatory. If your research question is specifically whether explicit telemetry relations carry signal, the heterogeneous graph remains the important experiment.

> okay so this is what I do now? How do I do it

<details><summary>2 previous messages</summary>

> Yes—this is a sensible next baseline. I’ll map it directly onto your notebook’s existing feature and scoring variables so the implementation is concrete.
>
> <details><summary>Ran a command</summary>
>
> - Ran `$nb = Get-Content -Raw -Encoding UTF8 'Notebooks\Graph Triage Baseline v0.ipynb' | ConvertFrom-Json; foreach ($i in 12,13,15,21,23) { "===== CELL $i ====="; ($nb.cells[$i].source -join '') }`
>
> </details>

</details>

Yes. Implement it as a new baseline section after sessionization.

### 1. Build the session-similarity graph

Use the scaled session feature matrix. Each session becomes a node; kNN relationships become edges.

```python
from scipy import sparse

def build_session_knn_operator(X, k=15):
    X = np.asarray(X, dtype=np.float32)
    n = len(X)
    effective_k = min(k, n - 1)

    _, neighbors = cKDTree(X).query(
        X,
        k=effective_k + 1,
        workers=-1,
    )
    neighbors = neighbors[:, 1:]  # remove self

    rows = np.repeat(np.arange(n), effective_k)
    cols = neighbors.reshape(-1)
    values = np.ones(len(rows), dtype=float)

    # Binary directed kNN adjacency
    A = sparse.csr_matrix((values, (rows, cols)), shape=(n, n))

    # Symmetric union graph: i--j if either selected the other
    A = A.maximum(A.T)
    A.setdiag(0)
    A.eliminate_zeros()

    # Row-normalized propagation operator P = D^-1 A
    degree = np.asarray(A.sum(axis=1)).ravel()
    inverse_degree = np.divide(
        1.0,
        degree,
        out=np.zeros_like(degree),
        where=degree > 0,
    )
    P = sparse.diags(inverse_degree) @ A

    return A, P
```

Binary edges are a good first version because they avoid introducing another distance-weighting parameter.

### 2. Apply the filter bank

```python
def session_score_filter_bank(s0, P, restart_alpha=0.5, steps=3):
    s0 = np.asarray(s0, dtype=float)

    p1 = np.asarray(P @ s0).ravel()
    p2 = np.asarray(P @ p1).ravel()

    # Restart diffusion: preserve original evidence while propagating locally
    diffusion = s0.copy()
    for _ in range(steps):
        diffusion = (
            restart_alpha * s0
            + (1.0 - restart_alpha) * np.asarray(P @ diffusion).ravel()
        )

    return {
        "raw_knn_distance": s0,
        "neighbor_support": p1,
        "local_residual": s0 - p1,
        "one_vs_two_hop": p1 - p2,
        "restart_diffusion": diffusion,
    }
```

### 3. Run it on your existing session table

```python
sessionized_df, sessions = make_strawman_sessions(dev_df)
session_table = build_raw_session_stats(sessionized_df)

feature_columns = [
    c for c in session_table.columns
    if c not in {"session_id", "label"}
]

X = StandardScaler().fit_transform(session_table[feature_columns])

s0 = knn_distance_anomaly_scores(X, k=15)
A, P = build_session_knn_operator(X, k=15)
filter_scores = session_score_filter_bank(s0, P)

y_true = (
    session_table["label"]
    .map({"benign": 0, "malicious": 1})
    .to_numpy()
)

filter_results = {
    name: evaluate_precomputed_scores(y_true, scores)
    for name, scores in filter_scores.items()
}

filter_summary = metric_summary_from_method_results(filter_results)
filter_summary
```

Interpret the rows as:

- `raw_knn_distance`: original baseline
- `neighbor_support`: are high scores supported by similar sessions?
- `local_residual`: is a session more anomalous than its neighbors?
- `one_vs_two_hop`: is evidence concentrated at an intermediate/local scale?
- `restart_diffusion`: does controlled propagation improve retrieval?

This is the first mechanical version. Do not select a “winner” permanently yet. First confirm the code, inspect the metrics, and then add label-shuffle and graph-null diagnostics before making a signal-regime claim.

> <div>
> <style scoped>
>     .dataframe tbody tr th:only-of-type {
>         vertical-align: middle;
>     }
>
>     .dataframe tbody tr th {
>         vertical-align: top;
>     }
>
>     .dataframe thead th {
>         text-align: right;
>     }
>
> </style>
> <table border="1" class="dataframe">
>   <thead>
>     <tr style="text-align: right;">
>       <th></th>
>       <th>method</th>
>       <th>average_precision</th>
>       <th>reviews_to_first_malicious</th>
>       <th>random_expected_reviews_to_first</th>
>       <th>found_at_25</th>
>       <th>recall_at_25</th>
>       <th>precision_at_25</th>
>       <th>found_at_50</th>
>       <th>recall_at_50</th>
>       <th>precision_at_50</th>
>       <th>found_at_100</th>
>       <th>recall_at_100</th>
>       <th>precision_at_100</th>
>       <th>found_at_250</th>
>       <th>recall_at_250</th>
>       <th>precision_at_250</th>
>     </tr>
>   </thead>
>   <tbody>
>     <tr>
>       <th>0</th>
>       <td>raw_knn_distance</td>
>       <td>0.016299</td>
>       <td>128</td>
>       <td>72.9</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.000000</td>
>       <td>0.00</td>
>       <td>2</td>
>       <td>0.105263</td>
>       <td>0.008</td>
>     </tr>
>     <tr>
>       <th>1</th>
>       <td>neighbour-support</td>
>       <td>0.022011</td>
>       <td>120</td>
>       <td>72.9</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.000000</td>
>       <td>0.00</td>
>       <td>7</td>
>       <td>0.368421</td>
>       <td>0.028</td>
>     </tr>
>     <tr>
>       <th>2</th>
>       <td>local_residual</td>
>       <td>0.009252</td>
>       <td>272</td>
>       <td>72.9</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.000000</td>
>       <td>0.00</td>
>       <td>0</td>
>       <td>0.000000</td>
>       <td>0.000</td>
>     </tr>
>     <tr>
>       <th>3</th>
>       <td>one_vs_two_hop</td>
>       <td>0.019823</td>
>       <td>56</td>
>       <td>72.9</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>4</td>
>       <td>0.210526</td>
>       <td>0.04</td>
>       <td>7</td>
>       <td>0.368421</td>
>       <td>0.028</td>
>     </tr>
>     <tr>
>       <th>4</th>
>       <td>restart_diffusion</td>
>       <td>0.019326</td>
>       <td>131</td>
>       <td>72.9</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.0</td>
>       <td>0.0</td>
>       <td>0</td>
>       <td>0.000000</td>
>       <td>0.00</td>
>       <td>3</td>
>       <td>0.157895</td>
>       <td>0.012</td>
>     </tr>
>   </tbody>
> </table>
> </div>

This is a promising but preliminary result.

- There are 19 malicious sessions out of roughly 1,457, so prevalence—and random expected AP—is about 0.013.
- `neighbour-support` has the best AP: 0.022 versus 0.016 raw, and retrieves 7/19 malicious sessions by rank 250.
- `one_vs_two_hop` gives the best early retrieval: first malicious at rank 56 versus 128 raw and 72.9 expected randomly; it finds 4 malicious sessions by rank 100.
- `local_residual` performs poorly, so malicious sessions do not appear individually surprising relative to their immediate neighborhoods.
- No method finds anything in the first 50 reviews, so the overall ranking remains weak.

The cautious interpretation is:

> Raw-feature similarity contains some useful locally shared or scale-dependent structure that the point-anomaly score does not exploit well.

It does not yet prove a smooth or multiscale signal regime. The differences could arise by chance with only 19 positives, and all filters are correlated because they use the same features and graph.

Your next step should be null testing:

1. Keep \(s_0\) fixed.
2. Degree-preserving rewire the similarity graph many times.
3. Apply the same filters to every rewired graph.
4. Compare the real improvements in AP and recall@100/250 against the resulting null distributions.
5. Run label permutations to establish chance metric distributions.
6. Record that choosing `neighbour-support` or `one_vs_two_hop` from this table is development-label-informed; any selected method must be frozen before holdout.

For now, the most interesting candidate is `one_vs_two_hop` for early triage and `neighbour-support` for overall retrieval—but neither is established as the winner yet.

> okay and after I do null testing what should I do

After null testing, close out this similarity-graph experiment and move to the actual telemetry graph.

Two possible outcomes:

- If the real filter beats the rewired/null graphs: retain it as the M0 geometry baseline and record which transformation appears useful.
- If it does not: report that raw-feature neighborhood filtering adds no reliable signal and stop amplifying this graph.

Then proceed:

1. Build the heterogeneous telemetry graph from raw events using label-free semantic rules.
2. Map every graph node/process back to your frozen session IDs.
3. Audit the graph before training anything:
   - isolates and components
   - edge counts by relation
   - session coverage
   - degree distributions
   - one/two/three-hop coverage
4. Build typed structural-statistics session representations and evaluate them with the same kNN scorer and metrics.
5. If graph coverage is adequate, evaluate Node2Vec, followed later by relational GraphSAGE.
6. Compare every representation before applying amplification.
7. Diagnose where the best representation’s signal lives—relations, hops, smoothness, roles—and only then select a matching amplification mechanism.
8. Freeze the complete method and evaluate once on holdout.

So the immediate sequence is:

```text
finish M0 null tests
→ record its conclusion
→ construct fresh telemetry graph
→ audit coverage
→ typed structural-statistics baseline
```

Do not automatically apply the current filter winner to subsequent graph methods; first determine whether those representations contain useful signal on their own.

> okay can you give the null tests

Use two complementary nulls:

1. Label permutation: are the rankings better than chance?
2. Degree-preserving graph rewiring: does the real similarity neighborhood matter beyond node degree?

The second is the important graph-specific test.

### Shared metric helpers

This assumes these variables already exist:

```python
A
s0
filter_scores
y_true
```

```python
import networkx as nx

NULL_METRICS = (
    "average_precision",
    "reviews_to_first_malicious",
    "recall_at_100",
    "recall_at_250",
)

METRIC_DIRECTION = {
    "average_precision": "higher",
    "reviews_to_first_malicious": "lower",
    "recall_at_100": "higher",
    "recall_at_250": "higher",
}

def compact_metrics(y_true, scores):
    result = evaluate_precomputed_scores(y_true, scores)
    ranking = result["ranking_at_k_metrics"]

    return {
        "average_precision": result["average_precision"],
        "reviews_to_first_malicious": result["reviews_to_first_malicious"],
        "recall_at_100": ranking["recall_at_100"],
        "recall_at_250": ranking["recall_at_250"],
    }

def summarize_null(observed_scores, y_true, null_runs):
    rows = []

    for method in null_runs["method"].unique():
        observed = compact_metrics(y_true, observed_scores[method])
        method_null = null_runs[null_runs["method"] == method]

        for metric in NULL_METRICS:
            null_values = method_null[metric].dropna().to_numpy()
            observed_value = observed[metric]

            if METRIC_DIRECTION[metric] == "higher":
                extreme = np.sum(null_values >= observed_value)
            else:
                extreme = np.sum(null_values <= observed_value)

            rows.append({
                "method": method,
                "metric": metric,
                "observed": observed_value,
                "null_mean": null_values.mean(),
                "null_median": np.median(null_values),
                "null_95th_percentile": np.quantile(null_values, 0.95),
                "empirical_p": (extreme + 1) / (len(null_values) + 1),
            })

    return pd.DataFrame(rows)
```

### 1. Label-permutation null

This keeps every score fixed and randomly moves the 19 malicious labels.

```python
def label_permutation_null(
    filter_scores,
    y_true,
    n_permutations=1000,
    seed=42,
):
    rng = np.random.default_rng(seed)
    rows = []

    for permutation in range(n_permutations):
        permuted_labels = rng.permutation(y_true)

        for method, scores in filter_scores.items():
            rows.append({
                "replicate": permutation,
                "method": method,
                **compact_metrics(permuted_labels, scores),
            })

    return pd.DataFrame(rows)

label_null_runs = label_permutation_null(
    filter_scores,
    y_true,
    n_permutations=1000,
)

label_null_summary = summarize_null(
    filter_scores,
    y_true,
    label_null_runs,
)

label_null_summary
```

This tests whether each ranking is associated with the malicious labels beyond chance. It does not prove that the graph caused the improvement.

### 2. Degree-preserving graph-rewiring null

This keeps:

- the same nodes,
- the same degree of every node,
- the same initial score \(s_0\),
- the same filter parameters,

but randomizes which sessions are connected.

```python
def row_normalize_adjacency(A):
    degree = np.asarray(A.sum(axis=1)).ravel()

    inverse_degree = np.divide(
        1.0,
        degree,
        out=np.zeros_like(degree, dtype=float),
        where=degree > 0,
    )

    return sparse.diags(inverse_degree) @ A

def degree_preserving_rewire(
    A,
    seed,
    swaps_per_edge=5,
):
    binary_A = (A > 0).astype(np.int8)

    G = nx.from_scipy_sparse_array(
        binary_A,
        create_using=nx.Graph,
    )

    rewired = G.copy()
    n_edges = rewired.number_of_edges()
    n_swaps = swaps_per_edge * n_edges

    nx.double_edge_swap(
        rewired,
        nswap=n_swaps,
        max_tries=20 * n_swaps,
        seed=seed,
    )

    A_rewired = nx.to_scipy_sparse_array(
        rewired,
        nodelist=np.arange(A.shape[0]),
        format="csr",
        dtype=float,
    )

    # Confirm that every node retained its degree.
    original_degree = np.asarray(A.sum(axis=1)).ravel()
    rewired_degree = np.asarray(A_rewired.sum(axis=1)).ravel()
    assert np.array_equal(original_degree, rewired_degree)

    return A_rewired

def graph_rewiring_null(
    A,
    s0,
    y_true,
    n_rewirings=200,
    seed=42,
):
    rng = np.random.default_rng(seed)
    rows = []

    for replicate in range(n_rewirings):
        rewire_seed = int(rng.integers(0, 2**31 - 1))

        A_null = degree_preserving_rewire(
            A,
            seed=rewire_seed,
            swaps_per_edge=5,
        )
        P_null = row_normalize_adjacency(A_null)

        null_scores = session_score_filter_bank(
            s0,
            P_null,
            restart_alpha=0.5,
            steps=3,
        )

        for method, scores in null_scores.items():
            # The raw score does not depend on graph edges.
            if method == "raw_knn_distance":
                continue

            rows.append({
                "replicate": replicate,
                "method": method,
                **compact_metrics(y_true, scores),
            })

    return pd.DataFrame(rows)

graph_null_runs = graph_rewiring_null(
    A,
    s0,
    y_true,
    n_rewirings=200,
)

graph_null_summary = summarize_null(
    filter_scores,
    y_true,
    graph_null_runs,
)

graph_null_summary
```

Start with 20 rewires to debug, then run at least 200 for the recorded result.

### Selection-aware test

Because you examined multiple filters and noticed the best one, compare your best observed filter against the best filter in every null replicate:

```python
def filter_bank_selection_test(observed_scores, y_true, null_runs):
    available_methods = list(null_runs["method"].unique())
    observed = {
        method: compact_metrics(y_true, observed_scores[method])
        for method in available_methods
    }

    rows = []

    for metric in NULL_METRICS:
        direction = METRIC_DIRECTION[metric]

        observed_values = {
            method: values[metric]
            for method, values in observed.items()
        }

        if direction == "higher":
            best_method = max(observed_values, key=observed_values.get)
            null_best = null_runs.groupby("replicate")[metric].max()
            extreme = np.sum(null_best >= observed_values[best_method])
        else:
            best_method = min(observed_values, key=observed_values.get)
            null_best = null_runs.groupby("replicate")[metric].min()
            extreme = np.sum(null_best <= observed_values[best_method])

        rows.append({
            "metric": metric,
            "best_observed_method": best_method,
            "best_observed_value": observed_values[best_method],
            "null_best_mean": null_best.mean(),
            "selection_adjusted_p": (
                (extreme + 1) / (len(null_best) + 1)
            ),
        })

    return pd.DataFrame(rows)

graph_bank_test = filter_bank_selection_test(
    filter_scores,
    y_true,
    graph_null_runs,
)

graph_bank_test
```

Interpretation:

- Passing only the label null means the ranking is better than random labels.
- Passing the graph-rewiring null means the actual similarity neighborhoods add information beyond the degree distribution.
- `graph_bank_test` protects against declaring victory simply because you tried several filters and selected the best one.

Treat AP and one early-retrieval metric—preferably recall@100—as the primary conclusions. The other metrics should be supporting evidence.

> take a look

<details><summary>4 previous messages</summary>

> I’ll inspect the new filter-bank and null-test cells, including their outputs, and check whether the implementation and conclusions are statistically sound.
>
> <details><summary>Ran a command</summary>
>
> - Ran ``$nb = Get-Content -Raw -Encoding UTF8 'Notebooks\Graph Triage Baseline v0.ipynb' | ConvertFrom-Json; $start=[Math]::Max(0,$nb.cells.Count-12); for($i=$start;$i -lt $nb.cells.Count;$i++){ "===== CELL $i [$($nb.cells[$i].cell_type)] ====="; ($nb.cells[$i].source -join ''); if($nb.cells[$i].outputs){ '--- OUTPUTS ---'; foreach($o in $nb.cells[$i].outputs){ if($o.output_type -eq 'stream'){ $o.text -join '' } elseif($o.output_type -eq 'error'){ "ERROR: $($o.ename): $($o.evalue)"; $o.traceback -join "`n" } elseif($o.data.'text/plain'){ $o.data.'text/plain' -join '' } } } }``
>
> </details>
>
> The implementation is mostly sound. I found one important interpretation issue: the graph-null result survives choosing among filters for recall@100 and recall@250, but it has not yet been corrected for looking across four different metrics.
>
> <details><summary>Ran a command</summary>
>
> - Ran `Get-Content -Encoding UTF8 'MASTER_PLAN.md' | Select-Object -Skip 225 -First 31`
>
> </details>

</details>

The code is structurally correct, and the result is a narrow exploratory positive:

- After accounting for choosing among filters, the real similarity graph beats degree-preserving rewires for:
  - recall@100: \(p=0.0398\)
  - recall@250: \(p=0.0398\)
- It does not beat the graph null for:
  - AP: \(p=0.189\)
  - reviews-to-first: \(p=0.547\)

So the defensible conclusion is:

> The raw-feature similarity graph contains some neighborhood structure useful at fixed review budgets, but it does not produce a reliable overall-ranking improvement.

Before closing this experiment, fix four things:

1. Delete cell 28 containing `sparse.cs`; it will break a clean top-to-bottom run.
2. Run the selection-aware test on the label null too:

```python
label_bank_test = filter_bank_selection_test(
    filter_scores,
    y_true,
    label_null_runs,
)
label_bank_test
```

3. Rename `selection_adjusted_p` to `filter_selection_p`. It adjusts for inspecting several filters within one metric—not for inspecting four metrics.
4. Add a host/user-blocked label permutation. Your 19 malicious sessions come from only two user/host identities, so ordinary session-level permutation assumes more independence than the data supports. This is the most important remaining statistical control.

Because you inspected four metrics, the two \(p=0.0398\) results are not automatically confirmatory across the entire metric suite. Treat them as development evidence, freeze the candidate, and eventually confirm it on holdout.

Also record basic graph reliability before moving on: edge count, component count, degree quantiles, and row-sum assertions for \(P\). No notebook files were changed.

> and then what phase are we on after this

You are currently in Phase 2: M0 session-similarity filter-bank baseline.

After completing the remaining null controls and recording the conclusion, Phase 2 is complete. Then return to Phase 1 because the old telemetry graph was discarded:

```text
Current: Phase 2 — similarity-graph filter bank
    ↓
Phase 1 — construct fresh heterogeneous telemetry graph
    ↓
Audit coverage, components, relations, degrees and hop reachability
    ↓
Phase 3 — typed structural-statistics baseline
```

Do not proceed directly to Node2Vec or GraphSAGE. The next substantial task is building the telemetry graph using label-free semantic decisions and verifying that it provides adequate session coverage.

One small prerequisite: confirm the Phase 0 alignment assertions—one canonical session table and identical ordered session IDs for every method. Then Phase 1 begins.
