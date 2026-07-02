import numpy as np
import pandas as pd

from scipy.spatial import cKDTree
from scipy.stats import wilcoxon
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import average_precision_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, normalize


SIMPLE_PROVENANCE_RELATIONS = {"parent_child", "touches", "touched_by"}
DISCOVERY_BUDGETS = (25, 50, 100, 250)
STEERING_BUDGETS = (25, 50, 100)


def canonical_relation(edge_type):
    rel = edge_type[1]
    return rel[4:] if rel.startswith("rev_") else rel


def filter_edge_dict(edge_dict, include):
    include = set(include)
    return {
        edge_type: edge_index
        for edge_type, edge_index in edge_dict.items()
        if canonical_relation(edge_type) in include
    }


def knn_anomaly_scores(X, k=15):
    X = np.asarray(X, dtype=np.float32)
    if len(X) <= 1:
        return np.zeros(len(X), dtype=float)
    qk = min(k + 1, len(X))
    dists, _ = cKDTree(X).query(X, k=qk, workers=-1)
    if qk == 1:
        return np.zeros(len(X), dtype=float)
    return np.asarray(dists[:, 1:]).mean(axis=1)


def percentile_rank(values):
    return pd.Series(np.asarray(values)).rank(method="average", pct=True).to_numpy(float)


def discovery_metrics(scores, labels, name, budgets=DISCOVERY_BUDGETS):
    y = (np.asarray(labels) == "malicious").astype(int)
    scores = np.asarray(scores, dtype=float)
    order = np.argsort(scores)[::-1]
    malicious_positions = np.flatnonzero(y[order] == 1)
    reviews_to_first = int(malicious_positions[0] + 1) if len(malicious_positions) else np.nan
    row = {
        "method": name,
        "average_precision": average_precision_score(y, scores) if y.sum() else np.nan,
        "reviews_to_first_malicious": reviews_to_first,
    }
    for budget in budgets:
        n = min(int(budget), len(y))
        hits = int(y[order[:n]].sum())
        row[f"found_at_{budget}"] = hits
        row[f"recall_at_{budget}"] = hits / y.sum() if y.sum() else np.nan
        row[f"precision_at_{budget}"] = hits / n if n else np.nan
    return row


def retrieval_metrics_from_scores(scores, labels, anchor_idx, budgets=STEERING_BUDGETS):
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    keep = np.ones(len(labels), dtype=bool)
    keep[anchor_idx] = False
    y = (labels[keep] == "malicious").astype(int)
    scores = scores[keep]
    order = np.argsort(scores)[::-1]
    row = {"ap": average_precision_score(y, scores) if y.sum() else np.nan}
    for budget in budgets:
        n = min(int(budget), len(y))
        row[f"recall_at_{budget}"] = y[order[:n]].sum() / y.sum() if y.sum() else np.nan
    return row


def steering_from_embedding(X, labels, view_name):
    Z = normalize(np.nan_to_num(np.asarray(X, dtype=float)))
    rows = []
    for anchor_idx in np.where(np.asarray(labels) == "malicious")[0]:
        scores = Z @ Z[anchor_idx]
        row = retrieval_metrics_from_scores(scores, labels, int(anchor_idx))
        row.update(view=view_name, anchor_session=int(anchor_idx))
        rows.append(row)
    return rows


def modal_value(process_df, sessions, column):
    values = []
    for session in sessions:
        if column not in process_df.columns:
            values.append("")
            continue
        counts = process_df.loc[session, column].dropna().astype(str).value_counts()
        values.append(counts.index[0] if len(counts) else "")
    return np.asarray(values, dtype=object)


def same_value_steering(values, labels, view_name, tie_breaker):
    values = np.asarray(values, dtype=object)
    rows = []
    for anchor_idx in np.where(np.asarray(labels) == "malicious")[0]:
        anchor_value = values[int(anchor_idx)]
        scores = (values == anchor_value).astype(float)
        if anchor_value == "":
            scores[:] = 0.0
        scores = scores + 1e-6 * tie_breaker
        row = retrieval_metrics_from_scores(scores, labels, int(anchor_idx))
        row.update(view=view_name, anchor_session=int(anchor_idx))
        rows.append(row)
    return rows


def session_texts(process_df, sessions):
    text_columns = [
        "process_name",
        "parent_process_name",
        "filename",
        "process_path",
        "parent_process_path",
        "command_line",
        "cmd_line",
        "cmdline",
        "process_command_line",
        "image_path",
    ]
    available = [col for col in text_columns if col in process_df.columns]
    if not available:
        available = [
            col for col in process_df.columns
            if process_df[col].dtype == object and col not in {"user_name", "hostname"}
        ][:5]

    texts = []
    for session in sessions:
        rows = process_df.loc[session, available]
        tokens = []
        for col in available:
            tokens.extend(rows[col].dropna().astype(str).head(80).tolist())
        texts.append(" ".join(tokens))
    return texts


def session_text_embedding(process_df, sessions, max_features=8000, n_components=64):
    texts = session_texts(process_df, sessions)
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=2,
        lowercase=True,
        token_pattern=r"(?u)\b[\w][\w./:\\-]+\b",
    )
    try:
        X_tfidf = vectorizer.fit_transform(texts)
    except ValueError:
        return np.zeros((len(texts), 1), dtype=float)
    max_components = min(n_components, X_tfidf.shape[0] - 1, X_tfidf.shape[1] - 1)
    if max_components < 2:
        return np.zeros((len(texts), 1), dtype=float)
    X = TruncatedSVD(n_components=max_components, random_state=42).fit_transform(X_tfidf)
    return StandardScaler().fit_transform(np.nan_to_num(X))


def rare_file_sets(process_df, sessions, rare_files):
    if "filename" not in process_df.columns:
        return [set() for _ in sessions]
    out = []
    rare_files = set(rare_files)
    for session in sessions:
        files = set(process_df.loc[session, "filename"].dropna().astype(str))
        out.append(files & rare_files)
    return out


def jaccard_steering(sets, labels, view_name, tie_breaker):
    rows = []
    for anchor_idx in np.where(np.asarray(labels) == "malicious")[0]:
        anchor_set = sets[int(anchor_idx)]
        scores = []
        for item_set in sets:
            denom = len(anchor_set | item_set)
            scores.append(len(anchor_set & item_set) / denom if denom else 0.0)
        scores = np.asarray(scores, dtype=float) + 1e-6 * tie_breaker
        row = retrieval_metrics_from_scores(scores, labels, int(anchor_idx))
        row.update(view=view_name, anchor_session=int(anchor_idx))
        rows.append(row)
    return rows


def summarize_steering(rows):
    runs = pd.DataFrame(rows)
    metric_cols = ["ap", "recall_at_25", "recall_at_50", "recall_at_100"]
    summary = runs.groupby("view")[metric_cols].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return runs, summary.reset_index().sort_values(["recall_at_100_mean", "ap_mean"], ascending=False)


def safe_wilcoxon_greater(left, right):
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if np.allclose(left - right, 0):
        return np.nan
    return wilcoxon(left, right, alternative="greater").pvalue


def steering_pair_tests(steering_runs, baseline_view):
    metric_cols = ["ap", "recall_at_100"]
    tests = []
    paired = steering_runs.pivot(index="anchor_session", columns="view", values=metric_cols)
    for view in sorted(set(steering_runs["view"])):
        if view == baseline_view:
            continue
        for metric in metric_cols:
            left = paired[(metric, baseline_view)]
            right = paired[(metric, view)]
            tests.append({
                "metric": metric,
                "baseline": baseline_view,
                "comparison": view,
                "baseline_minus_comparison": float(left.mean() - right.mean()),
                "comparison_anchors_better": int((right > left).sum()),
                "p_baseline_gt_comparison": safe_wilcoxon_greater(left, right),
                "p_comparison_gt_baseline": safe_wilcoxon_greater(right, left),
            })
    return pd.DataFrame(tests)


def run_v1_pipeline(
    *,
    graph_data,
    process_df,
    sessions,
    labels_eval,
    X_node_stats,
    X_graph_stats,
    builder,
    base_edge_dict,
    add_reverse_edges,
    make_x_dict,
    train_sage,
    session_embedding_from_z,
    experiment_seeds,
    seed=42,
    display_fn=None,
):
    labels = np.asarray(labels_eval)
    rng = np.random.default_rng(seed)

    if len(process_df) != len(getattr(builder, "process_ids", [])):
        raise ValueError(
            "process_df is not aligned to the graph builder process_ids. "
            "Use late_df.set_index('pid_hash').reindex(builder.process_ids).reset_index()."
        )
    if "pid_hash" in process_df.columns and hasattr(builder, "process_ids"):
        actual_ids = process_df["pid_hash"].astype(str).tolist()
        expected_ids = [str(pid) for pid in builder.process_ids]
        if actual_ids != expected_ids:
            raise ValueError(
                "process_df pid_hash order does not match builder.process_ids; "
                "session-level baselines would be misaligned."
            )

    X_text_svd = session_text_embedding(process_df, sessions)
    raw_knn_scores = knn_anomaly_scores(X_node_stats)
    graph_stats_knn_scores = knn_anomaly_scores(X_graph_stats)
    text_knn_scores = knn_anomaly_scores(X_text_svd)

    iforest = IsolationForest(n_estimators=200, random_state=seed, contamination="auto")
    iforest_scores = -iforest.fit(X_node_stats).decision_function(X_node_stats)

    lof = LocalOutlierFactor(n_neighbors=min(35, max(2, len(X_node_stats) - 1)), contamination="auto")
    lof.fit_predict(X_node_stats)
    lof_scores = -lof.negative_outlier_factor_

    all_edges = add_reverse_edges(base_edge_dict(graph_data))
    simple_edges = filter_edge_dict(all_edges, SIMPLE_PROVENANCE_RELATIONS)
    x_dict = make_x_dict(graph_data)
    simple_embeddings_by_seed = {}
    for model_seed in experiment_seeds:
        z = train_sage(
            f"v1_parent_file_sage seed={model_seed}",
            simple_edges,
            x_dict,
            model_seed,
        )
        simple_embeddings_by_seed[model_seed] = session_embedding_from_z(z, sessions)

    X_simple_graph = np.hstack([
        normalize(np.nan_to_num(simple_embeddings_by_seed[model_seed]))
        for model_seed in experiment_seeds
    ])
    simple_graph_scores = knn_anomaly_scores(X_simple_graph)

    random_scores = rng.random(len(labels))
    discovery_score_map = {
        "random": random_scores,
        "raw_node_stats_knn": raw_knn_scores,
        "graph_stats_knn": graph_stats_knn_scores,
        "raw_node_stats_iforest": iforest_scores,
        "raw_node_stats_lof": lof_scores,
        "session_text_svd_knn": text_knn_scores,
        "v1_parent_file_sage_knn": simple_graph_scores,
    }
    discovery_summary = pd.DataFrame([
        discovery_metrics(scores, labels, name)
        for name, scores in discovery_score_map.items()
    ]).sort_values(["reviews_to_first_malicious", "average_precision"], ascending=[True, False])

    tie_breaker = percentile_rank(raw_knn_scores)
    steering_rows = []
    steering_rows.extend(steering_from_embedding(X_simple_graph, labels, "v1_parent_file_sage_cosine"))
    steering_rows.extend(steering_from_embedding(X_node_stats, labels, "raw_node_stats_cosine"))
    steering_rows.extend(steering_from_embedding(X_text_svd, labels, "session_text_svd_cosine"))
    steering_rows.extend(same_value_steering(modal_value(process_df, sessions, "user_name"), labels, "same_user", tie_breaker))
    steering_rows.extend(same_value_steering(modal_value(process_df, sessions, "hostname"), labels, "same_host", tie_breaker))

    parent_col = "parent_process_name" if "parent_process_name" in process_df.columns else "parent_pid_hash"
    steering_rows.extend(same_value_steering(modal_value(process_df, sessions, parent_col), labels, "same_parent", tie_breaker))
    steering_rows.extend(jaccard_steering(
        rare_file_sets(process_df, sessions, builder.file_index.keys()),
        labels,
        "rare_file_jaccard",
        tie_breaker,
    ))

    steering_runs, steering_summary = summarize_steering(steering_rows)
    pair_tests = steering_pair_tests(steering_runs, "v1_parent_file_sage_cosine")

    session_scores = pd.DataFrame({
        "session_id": np.arange(len(labels)),
        "label": labels,
        "v1_parent_file_sage_score": simple_graph_scores,
        "raw_node_stats_score": raw_knn_scores,
        "session_text_svd_score": text_knn_scores,
        "user": modal_value(process_df, sessions, "user_name"),
        "host": modal_value(process_df, sessions, "hostname"),
        "session_size": [len(session) for session in sessions],
    }).sort_values("v1_parent_file_sage_score", ascending=False)

    edge_summary = pd.DataFrame([{
        "default_graph": "v1_parent_file",
        "relations": ", ".join(sorted(SIMPLE_PROVENANCE_RELATIONS)),
        "directed_edge_count": int(sum(edge_index.shape[1] for edge_index in simple_edges.values())),
        "edge_types": len(simple_edges),
        "candidate_same_user_edges": len(getattr(builder, "same_user_edges", [])),
        "candidate_same_host_edges": len(getattr(builder, "same_host_edges", [])),
    }])

    result = {
        "edge_summary": edge_summary,
        "discovery_summary": discovery_summary,
        "steering_runs": steering_runs,
        "steering_summary": steering_summary,
        "steering_pair_tests": pair_tests,
        "session_scores": session_scores,
        "simple_graph_embeddings_by_seed": simple_embeddings_by_seed,
        "X_simple_graph": X_simple_graph,
        "X_text_svd": X_text_svd,
    }

    if display_fn is not None:
        display_fn(edge_summary)
        display_fn(discovery_summary.round(4))
        display_fn(steering_summary.round(4))
        display_fn(pair_tests.round(6))
        display_fn(session_scores.head(20))

    return result
