"""Frozen Phase 5 analysis for the completed AutoSignal Phase 4 matrix.

The public output is intentionally small.  Full bootstrap draws stay in memory;
the script writes only tidy comparisons, outcomes, a portability summary, a
case-study manifest, and a short Markdown report.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numba import njit, prange
from sklearn.metrics import average_precision_score


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.phase4 import run_matrix as phase4  # noqa: E402


MATRIX_PATH = REPO_ROOT / "experiments" / "phase3" / "matrix_v1.json"
CONFIG_PATH = REPO_ROOT / "experiments" / "phase3" / "dataset_configs_v1.json"
DEFAULT_ARTIFACT_ROOT = (
    REPO_ROOT / "artifacts" / "final_matrix" / "autosignal_final_matrix_001"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "experiments" / "phase5" / "results" / "analysis_v1"
OBSERVED = "observed"
GRAPH_NULL = "degree_sequence_preserving_target_permutation"
NONE_HYPOTHESIS = "__none__"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hypothesis_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return NONE_HYPOTHESIS
    return str(value)


def display_hypothesis(value: str) -> str:
    return "" if value == NONE_HYPOTHESIS else value


def config_id(kind: str, variant: str, representation: str, scorer: str, hypothesis: str) -> str:
    return "|".join((kind, variant, representation, scorer, hypothesis))


@dataclass
class ScoreConfig:
    config_id: str
    kind: str
    relation_variant: str
    representation: str
    scorer: str
    hypothesis: str
    method: str
    labels: np.ndarray
    score_rows: np.ndarray
    method_keys: tuple[str, ...]
    status: str
    point_ap: float
    point_recall_at_100: float
    point_precision_at_100: float
    reviews_to_first_malicious: float
    top100_jaccard: float
    stochastic: bool
    runtime_seconds: float


def ranking_metrics(labels: np.ndarray, scores: np.ndarray, k: int = 100) -> tuple[float, float, float, float]:
    labels = labels.astype(np.int8, copy=False)
    positives = int(labels.sum())
    if positives == 0 or not np.isfinite(scores).all():
        return (math.nan, math.nan, math.nan, math.nan)
    order = np.argsort(-scores, kind="mergesort")
    effective_k = min(k, len(order))
    found = int(labels[order[:effective_k]].sum())
    malicious_positions = np.flatnonzero(labels[order] == 1)
    first = float(malicious_positions[0] + 1) if len(malicious_positions) else math.nan
    return (
        float(average_precision_score(labels, scores)),
        float(found / positives),
        float(found / effective_k) if effective_k else math.nan,
        first,
    )


def median_pairwise_topk_jaccard(score_rows: np.ndarray, k: int = 100) -> float:
    if len(score_rows) <= 1:
        return 1.0
    effective_k = min(k, score_rows.shape[1])
    sets = [set(np.argsort(-row, kind="mergesort")[:effective_k].tolist()) for row in score_rows]
    values: list[float] = []
    for left in range(len(sets)):
        for right in range(left + 1, len(sets)):
            union = sets[left] | sets[right]
            values.append(len(sets[left] & sets[right]) / len(union) if union else 1.0)
    return float(np.median(values))


def runtime_for_config(runtime: pd.DataFrame, representation: str, scorer: str, hypothesis: str) -> float:
    if runtime.empty:
        return math.nan
    mask = runtime["representation"].eq(representation) & runtime["scorer"].eq(scorer)
    if hypothesis == NONE_HYPOTHESIS:
        mask &= runtime["hypothesis"].isna()
    else:
        mask &= runtime["hypothesis"].eq(hypothesis)
    values = pd.to_numeric(runtime.loc[mask & runtime["status"].eq("completed"), "seconds"], errors="coerce")
    return float(values.sum()) if len(values) else math.nan


def make_score_config(
    group: pd.DataFrame,
    *,
    kind: str,
    variant: str,
    value_column: str,
    runtime: pd.DataFrame,
) -> ScoreConfig:
    representation = str(group["representation"].iloc[0])
    scorer = str(group["scorer"].iloc[0])
    hypothesis = hypothesis_value(group["hypothesis"].iloc[0])
    method = str(group["method"].iloc[0])
    pivot = group.pivot(index="method_key", columns="session_id", values=value_column).sort_index(axis=1)
    if pivot.isna().any().any():
        raise ValueError(f"Unaligned scores for {representation}/{scorer}/{hypothesis}")
    label_series = (
        group[["session_id", "label"]]
        .drop_duplicates("session_id")
        .sort_values("session_id", kind="stable")["label"]
    )
    labels = label_series.eq("malicious").to_numpy(dtype=np.int8)
    score_rows = pivot.to_numpy(dtype=np.float64)
    per_row = np.asarray([ranking_metrics(labels, row) for row in score_rows], dtype=np.float64)
    return ScoreConfig(
        config_id=config_id(kind, variant, representation, scorer, hypothesis),
        kind=kind,
        relation_variant=variant,
        representation=representation,
        scorer=scorer,
        hypothesis=hypothesis,
        method=method,
        labels=labels,
        score_rows=score_rows,
        method_keys=tuple(str(value) for value in pivot.index),
        status="completed",
        point_ap=float(np.median(per_row[:, 0])),
        point_recall_at_100=float(np.median(per_row[:, 1])),
        point_precision_at_100=float(np.median(per_row[:, 2])),
        reviews_to_first_malicious=float(np.median(per_row[:, 3])),
        top100_jaccard=median_pairwise_topk_jaccard(score_rows),
        stochastic=len(score_rows) > 1,
        runtime_seconds=runtime_for_config(runtime, representation, scorer, hypothesis),
    )


def load_case_configs(case_root: Path, variant: str) -> dict[str, ScoreConfig]:
    scores = pd.read_parquet(case_root / "session_scores.parquet")
    method_results = pd.read_parquet(case_root / "method_results.parquet")
    runtime_path = case_root / "runtime_diagnostics.parquet"
    runtime = pd.read_parquet(runtime_path) if runtime_path.exists() else pd.DataFrame()
    scores = scores.copy()
    scores["_hypothesis"] = scores["hypothesis"].map(hypothesis_value)
    result: dict[str, ScoreConfig] = {}
    group_columns = ["representation", "scorer", "_hypothesis"]
    for _, group in scores.groupby(group_columns, sort=False, dropna=False):
        item = make_score_config(
            group,
            kind="intrinsic",
            variant=variant,
            value_column="score",
            runtime=runtime,
        )
        result[item.config_id] = item
    if variant == OBSERVED:
        signal_path = case_root / "signal_scores.parquet"
        if signal_path.exists():
            signal = pd.read_parquet(signal_path)
            if not signal.empty:
                signal = signal.copy()
                signal["_hypothesis"] = signal["hypothesis"].map(hypothesis_value)
                for _, group in signal.groupby(group_columns, sort=False, dropna=False):
                    item = make_score_config(
                        group,
                        kind="matched",
                        variant=variant,
                        value_column="matched_score",
                        runtime=runtime,
                    )
                    result[item.config_id] = item
    labels = next(iter(result.values())).labels
    method_results = method_results.copy()
    method_results["_hypothesis"] = method_results["hypothesis"].map(hypothesis_value)
    for _, group in method_results.groupby(group_columns, sort=False, dropna=False):
        representation = str(group["representation"].iloc[0])
        scorer = str(group["scorer"].iloc[0])
        hypothesis = hypothesis_value(group["hypothesis"].iloc[0])
        key = config_id("intrinsic", variant, representation, scorer, hypothesis)
        if key in result:
            continue
        statuses = set(str(value) for value in group["status"].dropna())
        status = "valid_abstention" if statuses and statuses <= {"abstained"} else "technical_failure"
        result[key] = ScoreConfig(
            config_id=key,
            kind="intrinsic",
            relation_variant=variant,
            representation=representation,
            scorer=scorer,
            hypothesis=hypothesis,
            method=str(group["method"].iloc[0]),
            labels=labels,
            score_rows=np.empty((0, len(labels)), dtype=np.float64),
            method_keys=tuple(str(value) for value in group["method_key"]),
            status=status,
            point_ap=math.nan,
            point_recall_at_100=math.nan,
            point_precision_at_100=math.nan,
            reviews_to_first_malicious=math.nan,
            top100_jaccard=math.nan,
            stochastic=len(group) > 1,
            runtime_seconds=runtime_for_config(runtime, representation, scorer, hypothesis),
        )
    return result


def cluster_ids_for_partition(
    matrix: dict[str, Any],
    dataset: dict[str, Any],
    partition: dict[str, Any],
    config_record: dict[str, Any],
) -> np.ndarray:
    frame, config, _ = phase4.materialize_partition(matrix, dataset, partition, config_record)
    validated = phase4.engine.validate_config(copy.deepcopy(config), frame)
    sessionized, _, _ = phase4.engine.sessionize(frame, validated)
    if dataset["dataset_id"] == "acme_process_telemetry":
        column = "hostname"
    elif dataset["dataset_id"] == "unsw_nb15_raw":
        column = "srcip"
    else:
        column = "_frozen_source_file"
    clusters = (
        sessionized[["session_id", column]]
        .groupby("session_id", sort=True)[column]
        .first()
        .fillna("__missing__")
        .astype(str)
    )
    expected = np.arange(len(clusters), dtype=np.int64)
    if not np.array_equal(clusters.index.to_numpy(dtype=np.int64), expected):
        raise ValueError(f"Non-contiguous session ids in {partition['partition_id']}")
    return pd.factorize(clusters, sort=True)[0].astype(np.int32)


def order_and_ties(scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-scores, kind="mergesort").astype(np.int32)
    sorted_scores = scores[order]
    ends = np.empty(len(order), dtype=np.bool_)
    if len(order):
        ends[:-1] = sorted_scores[:-1] != sorted_scores[1:]
        ends[-1] = True
    return order, ends


@njit(parallel=True, cache=True)
def bootstrap_config_metrics(
    orders: np.ndarray,
    tie_ends: np.ndarray,
    labels: np.ndarray,
    cluster_ids: np.ndarray,
    count_patterns: np.ndarray,
    budget: int,
) -> tuple[np.ndarray, np.ndarray]:
    pattern_count = count_patterns.shape[0]
    row_count = orders.shape[0]
    n = orders.shape[1]
    aps = np.empty(pattern_count, dtype=np.float64)
    recalls = np.empty(pattern_count, dtype=np.float64)
    for pattern_index in prange(pattern_count):
        counts = count_patterns[pattern_index]
        positive_total = 0.0
        for index in range(n):
            positive_total += counts[cluster_ids[index]] * labels[index]
        row_aps = np.empty(row_count, dtype=np.float64)
        row_recalls = np.empty(row_count, dtype=np.float64)
        for row_index in range(row_count):
            cumulative_weight = 0.0
            cumulative_positive = 0.0
            group_positive = 0.0
            ap = 0.0
            reviewed = 0
            found = 0.0
            for rank in range(n):
                source_index = orders[row_index, rank]
                weight = counts[cluster_ids[source_index]]
                if weight <= 0:
                    if tie_ends[row_index, rank]:
                        group_positive = 0.0
                    continue
                positive_weight = weight * labels[source_index]
                cumulative_weight += weight
                cumulative_positive += positive_weight
                group_positive += positive_weight
                if reviewed < budget:
                    take = weight
                    if reviewed + take > budget:
                        take = budget - reviewed
                    found += take * labels[source_index]
                    reviewed += take
                if tie_ends[row_index, rank]:
                    if group_positive > 0.0 and positive_total > 0.0:
                        ap += (group_positive / positive_total) * (
                            cumulative_positive / cumulative_weight
                        )
                    group_positive = 0.0
            row_aps[row_index] = ap if positive_total > 0.0 else np.nan
            row_recalls[row_index] = found / positive_total if positive_total > 0.0 else np.nan
        aps[pattern_index] = np.median(row_aps)
        recalls[pattern_index] = np.median(row_recalls)
    return aps, recalls


def bootstrap_patterns(cluster_ids: np.ndarray, replicates: int, random_state: int) -> tuple[np.ndarray, np.ndarray]:
    cluster_count = int(cluster_ids.max()) + 1
    rng = np.random.default_rng(random_state)
    patterns = rng.multinomial(
        cluster_count,
        np.full(cluster_count, 1.0 / cluster_count),
        size=replicates,
    ).astype(np.int16)
    unique, inverse = np.unique(patterns, axis=0, return_inverse=True)
    return unique, inverse


def bootstrap_for_config(
    item: ScoreConfig,
    labels: np.ndarray,
    cluster_ids: np.ndarray,
    patterns: np.ndarray,
    inverse: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if not np.array_equal(item.labels, labels):
        raise ValueError(f"Label alignment mismatch for {item.config_id}")
    orders: list[np.ndarray] = []
    ends: list[np.ndarray] = []
    for row in item.score_rows:
        order, tie_end = order_and_ties(row)
        orders.append(order)
        ends.append(tie_end)
    unique_ap, unique_recall = bootstrap_config_metrics(
        np.stack(orders),
        np.stack(ends),
        labels.astype(np.int8),
        cluster_ids.astype(np.int32),
        patterns,
        100,
    )
    return unique_ap[inverse], unique_recall[inverse]


def comparison_row(
    *,
    dataset_id: str,
    partition_id: str,
    partition_role: str,
    family: str,
    candidate: ScoreConfig | None,
    reference: ScoreConfig | None,
    bootstrap_cache: dict[str, tuple[np.ndarray, np.ndarray]],
    primary: bool = True,
) -> dict[str, Any]:
    base = {
        "dataset_id": dataset_id,
        "partition_id": partition_id,
        "partition_role": partition_role,
        "comparison_family": family,
        "primary": primary,
        "candidate_config_id": candidate.config_id if candidate else "",
        "reference_config_id": reference.config_id if reference else "",
        "candidate_representation": candidate.representation if candidate else "",
        "candidate_scorer": candidate.scorer if candidate else "",
        "hypothesis": display_hypothesis(candidate.hypothesis) if candidate else "",
        "status": "completed" if candidate is not None and reference is not None else "not_evaluable",
        "candidate_ap": candidate.point_ap if candidate else math.nan,
        "reference_ap": reference.point_ap if reference else math.nan,
        "delta_ap": math.nan,
        "ap_ci_low": math.nan,
        "ap_ci_high": math.nan,
        "candidate_recall_at_100": candidate.point_recall_at_100 if candidate else math.nan,
        "reference_recall_at_100": reference.point_recall_at_100 if reference else math.nan,
        "delta_recall_at_100": math.nan,
        "recall_ci_low": math.nan,
        "recall_ci_high": math.nan,
        "p_value_raw": math.nan,
        "p_value_holm": math.nan,
        "significant_favorable": False,
        "significant_reversal": False,
    }
    if (
        candidate is None
        or reference is None
        or candidate.status != "completed"
        or reference.status != "completed"
    ):
        base["status"] = "not_evaluable"
        return base
    candidate_ap, candidate_recall = bootstrap_cache[candidate.config_id]
    reference_ap, reference_recall = bootstrap_cache[reference.config_id]
    delta_ap_draws = candidate_ap - reference_ap
    delta_recall_draws = candidate_recall - reference_recall
    finite = np.isfinite(delta_ap_draws)
    if not np.any(finite):
        base["status"] = "not_evaluable"
        return base
    valid_ap = delta_ap_draws[finite]
    valid_recall = delta_recall_draws[np.isfinite(delta_recall_draws)]
    left = (np.count_nonzero(valid_ap <= 0.0) + 1.0) / (len(valid_ap) + 1.0)
    right = (np.count_nonzero(valid_ap >= 0.0) + 1.0) / (len(valid_ap) + 1.0)
    base.update(
        {
            "delta_ap": float(candidate.point_ap - reference.point_ap),
            "ap_ci_low": float(np.quantile(valid_ap, 0.025)),
            "ap_ci_high": float(np.quantile(valid_ap, 0.975)),
            "delta_recall_at_100": float(
                candidate.point_recall_at_100 - reference.point_recall_at_100
            ),
            "recall_ci_low": float(np.quantile(valid_recall, 0.025)) if len(valid_recall) else math.nan,
            "recall_ci_high": float(np.quantile(valid_recall, 0.975)) if len(valid_recall) else math.nan,
            "p_value_raw": float(min(1.0, 2.0 * min(left, right))),
        }
    )
    return base


def holm_adjust(values: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=values.index, dtype=np.float64)
    finite = values.dropna().sort_values(kind="stable")
    count = len(finite)
    running = 0.0
    for rank, (index, value) in enumerate(finite.items()):
        adjusted = min(1.0, (count - rank) * float(value))
        running = max(running, adjusted)
        result.loc[index] = running
    return result


def lookup(
    configs: dict[str, ScoreConfig],
    kind: str,
    variant: str,
    representation: str,
    scorer: str,
    hypothesis: str = NONE_HYPOTHESIS,
) -> ScoreConfig | None:
    return configs.get(config_id(kind, variant, representation, scorer, hypothesis))


def add_planned_comparisons(
    rows: list[dict[str, Any]],
    *,
    dataset_id: str,
    partition_id: str,
    partition_role: str,
    configs: dict[str, ScoreConfig],
    hypotheses: list[str],
    bootstrap_cache: dict[str, tuple[np.ndarray, np.ndarray]],
) -> None:
    def add(family: str, candidate: ScoreConfig | None, reference: ScoreConfig | None) -> None:
        rows.append(
            comparison_row(
                dataset_id=dataset_id,
                partition_id=partition_id,
                partition_role=partition_role,
                family=family,
                candidate=candidate,
                reference=reference,
                bootstrap_cache=bootstrap_cache,
            )
        )

    for hypothesis in hypotheses:
        raw_knn = lookup(configs, "intrinsic", OBSERVED, "raw_session", "knn_mean_distance", hypothesis)
        add(
            "raw_isolation_forest_vs_raw_knn",
            lookup(configs, "intrinsic", OBSERVED, "raw_session", "isolation_forest", hypothesis),
            raw_knn,
        )
        add(
            "raw_hdbscan_vs_raw_knn",
            lookup(configs, "intrinsic", OBSERVED, "raw_session", "hdbscan_rare_cluster", hypothesis),
            raw_knn,
        )
        add(
            "graphsage_trained_knn_vs_raw_knn",
            lookup(configs, "intrinsic", OBSERVED, "graphsage_trained", "knn_mean_distance", hypothesis),
            raw_knn,
        )
        add(
            "graphsage_trained_vs_random",
            lookup(configs, "intrinsic", OBSERVED, "graphsage_trained", "knn_mean_distance", hypothesis),
            lookup(configs, "intrinsic", OBSERVED, "graphsage_random", "knn_mean_distance", hypothesis),
        )
        add(
            "dominant_trained_vs_untrained",
            lookup(configs, "intrinsic", OBSERVED, "dominant_style_trained", "dominant_joint_reconstruction", hypothesis),
            lookup(configs, "intrinsic", OBSERVED, "dominant_style_untrained", "dominant_joint_reconstruction", hypothesis),
        )
        for scorer in ("knn_mean_distance", "isolation_forest", "hdbscan_rare_cluster"):
            add(
                "graphsage_observed_vs_permuted",
                lookup(configs, "intrinsic", OBSERVED, "graphsage_trained", scorer, hypothesis),
                lookup(configs, "intrinsic", GRAPH_NULL, "graphsage_trained", scorer, hypothesis),
            )
    for scorer in ("knn_mean_distance", "isolation_forest", "hdbscan_rare_cluster"):
        add(
            "node2vec_observed_vs_permuted",
            lookup(configs, "intrinsic", OBSERVED, "node2vec", scorer),
            lookup(configs, "intrinsic", GRAPH_NULL, "node2vec", scorer),
        )
    for item in list(configs.values()):
        if item.kind != "matched" or item.relation_variant != OBSERVED:
            continue
        add(
            "matched_vs_intrinsic",
            item,
            lookup(configs, "intrinsic", OBSERVED, item.representation, item.scorer, item.hypothesis),
        )


def candidate_configs(configs: dict[str, ScoreConfig]) -> list[ScoreConfig]:
    representations = {
        "raw_session",
        "typed_structural_stats",
        "node2vec",
        "graphsage_trained",
        "dominant_style_trained",
    }
    return sorted(
        (
            item
            for item in configs.values()
            if item.relation_variant == OBSERVED and item.representation in representations
        ),
        key=lambda item: item.config_id,
    )


def required_control_families(item: ScoreConfig) -> tuple[list[str], str]:
    if item.representation == "raw_session":
        return [], ""
    if item.representation == "node2vec":
        return ["node2vec_observed_vs_permuted"], ""
    if item.representation == "dominant_style_trained":
        return ["dominant_trained_vs_untrained"], ""
    if item.representation == "graphsage_trained":
        if item.scorer != "knn_mean_distance":
            return [], "No predeclared trained-versus-random comparison for this scorer."
        return ["graphsage_trained_vs_random", "graphsage_observed_vs_permuted"], ""
    if item.representation == "typed_structural_stats":
        return [], "No predeclared confirmatory observed-versus-null comparison."
    return [], ""


def matching_control_rows(comparisons: pd.DataFrame, item: ScoreConfig, families: list[str]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for family in families:
        subset = comparisons[
            comparisons["comparison_family"].eq(family)
            & comparisons["partition_role"].eq("selection")
            & comparisons["candidate_representation"].eq(item.representation)
            & comparisons["candidate_scorer"].eq(item.scorer)
            & comparisons["hypothesis"].eq(display_hypothesis(item.hypothesis))
        ]
        rows.append(subset)
    return pd.concat(rows, ignore_index=False) if rows else pd.DataFrame()


def outcome_rows(
    pending: list[tuple[str, str, ScoreConfig, float]], comparisons: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dataset_id, partition_id, item, prevalence in pending:
        random_row = comparisons[
            comparisons["dataset_id"].eq(dataset_id)
            & comparisons["partition_id"].eq(partition_id)
            & comparisons["comparison_family"].eq("candidate_vs_random")
            & comparisons["candidate_config_id"].eq(item.config_id)
        ]
        random_ok = (
            len(random_row) == 1
            and float(random_row.iloc[0]["ap_ci_low"]) > 0.0
            and float(random_row.iloc[0]["p_value_holm"]) <= 0.05
        )
        above_random = len(random_row) == 1 and float(random_row.iloc[0]["delta_ap"]) > 0.0
        precision_lift = item.point_precision_at_100 / prevalence if prevalence > 0 else math.nan
        stability_ok = (not item.stochastic) or item.top100_jaccard >= 0.50
        families, control_limitation = required_control_families(item)
        control_rows = matching_control_rows(
            comparisons[comparisons["dataset_id"].eq(dataset_id)], item, families
        )
        control_ok = not control_limitation and (
            not families
            or (
                len(control_rows) == len(families)
                and control_rows["significant_favorable"].astype(bool).all()
            )
        )
        matched_ok = True
        if item.kind == "matched":
            matched_rows = comparisons[
                comparisons["dataset_id"].eq(dataset_id)
                & comparisons["partition_id"].eq(partition_id)
                & comparisons["comparison_family"].eq("matched_vs_intrinsic")
                & comparisons["candidate_config_id"].eq(item.config_id)
            ]
            matched_ok = len(matched_rows) == 1 and bool(matched_rows.iloc[0]["significant_favorable"])
        technical_valid = (
            item.status == "completed"
            and np.isfinite(item.point_ap)
            and int(item.labels.sum()) > 0
        )
        utility_ok = np.isfinite(precision_lift) and precision_lift >= 2.0
        if not technical_valid or not above_random:
            outcome = "Abstain"
        elif random_ok and utility_ok and stability_ok and control_ok and matched_ok:
            outcome = "Recommend"
        else:
            outcome = "Explore"
        reasons: list[str] = []
        if item.status != "completed":
            reasons.append(item.status.replace("_", " "))
        if not random_ok:
            reasons.append("random comparison did not pass adjusted inference")
        if not utility_ok:
            reasons.append("Precision@100 lift is below 2x prevalence")
        if not stability_ok:
            reasons.append("median top-100 Jaccard is below 0.50")
        if not control_ok:
            reasons.append(control_limitation or "graph control did not pass adjusted inference")
        if not matched_ok:
            reasons.append("matched score did not beat its intrinsic score")
        rows.append(
            {
                "dataset_id": dataset_id,
                "partition_id": partition_id,
                "config_id": item.config_id,
                "score_kind": item.kind,
                "representation": item.representation,
                "scorer": item.scorer,
                "hypothesis": display_hypothesis(item.hypothesis),
                "outcome": outcome,
                "median_average_precision": item.point_ap,
                "median_recall_at_100": item.point_recall_at_100,
                "median_precision_at_100": item.point_precision_at_100,
                "prevalence": prevalence,
                "precision_lift_at_100": precision_lift,
                "median_top100_jaccard": item.top100_jaccard,
                "stochastic": item.stochastic,
                "reviews_to_first_malicious": item.reviews_to_first_malicious,
                "runtime_seconds": item.runtime_seconds,
                "random_inference_pass": random_ok,
                "utility_pass": utility_ok,
                "stability_pass": stability_ok,
                "graph_control_pass": control_ok,
                "matched_vs_intrinsic_pass": matched_ok,
                "reason": "; ".join(reasons),
            }
        )
    return pd.DataFrame(rows)


def portability_summary(comparisons: pd.DataFrame) -> pd.DataFrame:
    selection = comparisons[
        comparisons["partition_role"].eq("selection")
        & comparisons["primary"].astype(bool)
        & ~comparisons["comparison_family"].eq("candidate_vs_random")
        & comparisons["status"].eq("completed")
    ]
    rows: list[dict[str, Any]] = []
    for family, family_rows in selection.groupby("comparison_family", sort=True):
        dataset_rows: list[dict[str, Any]] = []
        for dataset_id, dataset_group in family_rows.groupby("dataset_id", sort=True):
            dataset_rows.append(
                {
                    "dataset_id": dataset_id,
                    "median_delta_ap": float(dataset_group["delta_ap"].median()),
                    "favorable": bool(dataset_group["delta_ap"].median() > 0),
                    "supported_reversal": bool(dataset_group["significant_reversal"].any()),
                }
            )
        favorable_count = sum(row["favorable"] for row in dataset_rows)
        reversal = any(row["supported_reversal"] for row in dataset_rows)
        rows.append(
            {
                "comparison_family": family,
                "datasets_evaluable": len(dataset_rows),
                "datasets_favorable_direction": favorable_count,
                "statistically_supported_reversal": reversal,
                "portable_favorable_claim": favorable_count >= 2 and not reversal,
                "dataset_directions": json.dumps(dataset_rows, sort_keys=True),
            }
        )
    return pd.DataFrame(rows)


def select_confirmation(outcomes: pd.DataFrame) -> pd.DataFrame:
    selected: list[pd.Series] = []
    for _, group in outcomes[outcomes["outcome"].eq("Recommend")].groupby("dataset_id"):
        ranked = group.sort_values(
            [
                "median_average_precision",
                "median_recall_at_100",
                "runtime_seconds",
                "config_id",
            ],
            ascending=[False, False, True, True],
            kind="stable",
            na_position="last",
        )
        selected.append(ranked.iloc[0])
    return pd.DataFrame(selected).reset_index(drop=True) if selected else outcomes.head(0).copy()


def case_study_manifest(
    outcomes: pd.DataFrame, comparisons: pd.DataFrame, representations: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    useful = outcomes[outcomes["outcome"].isin(["Recommend", "Explore"])].copy()
    useful["_outcome_rank"] = useful["outcome"].map({"Recommend": 0, "Explore": 1})
    useful = useful.sort_values(
        ["_outcome_rank", "median_average_precision"], ascending=[True, False], kind="stable"
    )
    if len(useful):
        item = useful.iloc[0]
        rows.append(
            {
                "category": "useful_representation_and_ranking",
                "dataset_id": item["dataset_id"],
                "partition_id": item["partition_id"],
                "config_or_comparison": item["config_id"],
                "selection_rule": "highest-AP Recommend, otherwise highest-AP Explore",
            }
        )
    rep = representations[
        representations["relation_variant"].eq(OBSERVED)
        & representations["partition_id"].str.endswith("selection")
        & representations["status"].eq("completed")
    ].copy()
    if len(rep):
        rep["hypothesis"] = rep["hypothesis"].fillna("")
        rep_summary = (
            rep.groupby(["dataset_id", "partition_id", "representation", "hypothesis"], as_index=False)
            ["linear_probe_average_precision"]
            .median()
            .sort_values("linear_probe_average_precision", ascending=False, kind="stable")
        )
        for _, candidate in rep_summary.iterrows():
            matching = outcomes[
                outcomes["dataset_id"].eq(candidate["dataset_id"])
                & outcomes["representation"].eq(candidate["representation"])
                & outcomes["hypothesis"].eq(candidate["hypothesis"])
                & outcomes["outcome"].isin(["Explore", "Abstain"])
            ]
            if len(matching):
                item = matching.sort_values("median_average_precision", ascending=True).iloc[0]
                rows.append(
                    {
                        "category": "useful_representation_failed_scorer",
                        "dataset_id": item["dataset_id"],
                        "partition_id": item["partition_id"],
                        "config_or_comparison": item["config_id"],
                        "selection_rule": "highest linear-probe AP representation with a non-Recommend scorer",
                    }
                )
                break
    harmful = comparisons[
        comparisons["comparison_family"].isin(
            ["graphsage_observed_vs_permuted", "node2vec_observed_vs_permuted"]
        )
        & comparisons["partition_role"].eq("selection")
        & comparisons["status"].eq("completed")
    ].sort_values("delta_ap", ascending=True, kind="stable")
    if len(harmful):
        item = harmful.iloc[0]
        rows.append(
            {
                "category": "structure_operationally_harmful_or_unsupported",
                "dataset_id": item["dataset_id"],
                "partition_id": item["partition_id"],
                "config_or_comparison": item["candidate_config_id"],
                "selection_rule": "most negative observed-minus-permuted AP difference",
            }
        )
    equal = comparisons[
        comparisons["comparison_family"].eq("graphsage_trained_vs_random")
        & comparisons["partition_role"].eq("selection")
        & comparisons["status"].eq("completed")
    ].copy()
    if len(equal):
        equal["absolute_delta"] = equal["delta_ap"].abs()
        item = equal.sort_values("absolute_delta", kind="stable").iloc[0]
        rows.append(
            {
                "category": "trained_graphsage_approximately_random",
                "dataset_id": item["dataset_id"],
                "partition_id": item["partition_id"],
                "config_or_comparison": item["candidate_config_id"],
                "selection_rule": "smallest absolute trained-minus-random GraphSAGE AP difference",
            }
        )
    return pd.DataFrame(rows)


def write_report(
    path: Path,
    *,
    outcomes: pd.DataFrame,
    selected: pd.DataFrame,
    portability: pd.DataFrame,
    comparisons: pd.DataFrame,
    execution: dict[str, Any],
) -> None:
    lines = [
        "# AutoSignal Phase 5 result",
        "",
        "## What was tested",
        "",
        "The same frozen AutoSignal procedure was evaluated on ACME process telemetry, "
        "UNSW-NB15, and CIC-IDS-2017. Development and selection slices were kept "
        "separate. Agent-proposed feature hypotheses and typed relations were evaluated "
        "with raw, structural, Node2Vec, GraphSAGE, DOMINANT-style, Isolation Forest, "
        "kNN, HDBSCAN-population, random, untrained, and relation-permuted controls.",
        "",
        "The score suite used average precision, Recall/Precision@100, reviews to the "
        "first malicious item, seed top-100 overlap, paired cluster-bootstrap uncertainty "
        "(2,000 replicates), and Holm correction within dataset.",
        "",
        "## Execution integrity",
        "",
        f"- Cases complete: {execution['completed_cases']}/12",
        f"- Failed cases: {execution['failed_cases']}",
        f"- Method rows: {execution['method_rows']} (expected 912)",
        f"- Representation rows: {execution['representation_rows']} (expected 390)",
        "- Sealed confirmation partitions were not evaluated.",
        "",
        "## Intrinsic selection-slice outcomes",
        "",
        "| Dataset | Recommend | Explore | Abstain | Confirmation candidate |",
        "|---|---:|---:|---:|---|",
    ]
    intrinsic_outcomes = outcomes[outcomes["score_kind"].eq("intrinsic")]
    for dataset_id, group in intrinsic_outcomes.groupby("dataset_id", sort=True):
        counts = group["outcome"].value_counts()
        picked = selected[selected["dataset_id"].eq(dataset_id)]
        candidate = str(picked.iloc[0]["config_id"]) if len(picked) else "none; keep confirmation sealed"
        lines.append(
            f"| {dataset_id} | {int(counts.get('Recommend', 0))} | "
            f"{int(counts.get('Explore', 0))} | {int(counts.get('Abstain', 0))} | {candidate} |"
        )
    lines.extend(
        [
            "",
            "This table counts the 27 intrinsic configurations per dataset. The full "
            "machine-readable outcome table also retains matched-transform variants; "
            "none of them reached Recommend.",
        ]
    )
    lines.extend(["", "## Best selection result per dataset", ""])
    for dataset_id, group in outcomes.groupby("dataset_id", sort=True):
        group = group.copy()
        group["_outcome_rank"] = group["outcome"].map(
            {"Recommend": 0, "Explore": 1, "Abstain": 2}
        )
        best = group.sort_values(
            ["_outcome_rank", "median_average_precision"],
            ascending=[True, False],
            kind="stable",
        ).iloc[0]
        lines.append(
            f"- **{dataset_id}:** {best['outcome']} - `{best['representation']}` + "
            f"`{best['scorer']}`; AP {best['median_average_precision']:.4f}, "
            f"Recall@100 {best['median_recall_at_100']:.4f}, "
            f"Precision@100 lift {best['precision_lift_at_100']:.2f}x."
        )
    portable = portability[portability["portable_favorable_claim"].astype(bool)]
    reversals = portability[portability["statistically_supported_reversal"].astype(bool)]
    family_sizes = comparisons[
        comparisons["primary"].astype(bool) & comparisons["p_value_raw"].notna()
    ].groupby("dataset_id").size()
    minimum_raw_p = 2.0 / 2001.0
    minimum_adjusted = family_sizes * minimum_raw_p
    portability_by_family = portability.set_index("comparison_family")

    def favorable_count(family: str) -> int:
        if family not in portability_by_family.index:
            return 0
        return int(portability_by_family.loc[family, "datasets_favorable_direction"])
    lines.extend(
        [
            "",
            "## Inference limitation",
            "",
            "The frozen 2,000-draw bootstrap and the conservative two-sided finite-sample "
            "p-value have a minimum raw p-value of 2/2001. With the predeclared Holm "
            "families instantiated for every relevant configuration, the smallest "
            "attainable adjusted p-value is therefore above 0.05 in every dataset. "
            "The adjusted-inference gate cannot pass under this exact operationalization. "
            "This is a design-resolution limitation, not evidence that all methods are equal.",
            "",
            "| Dataset | Holm family size | Smallest attainable adjusted p |",
            "|---|---:|---:|",
            *[
                f"| {dataset_id} | {int(family_sizes.loc[dataset_id])} | {minimum_adjusted.loc[dataset_id]:.4f} |"
                for dataset_id in family_sizes.index
            ],
            "",
            "## Direct method-family findings",
            "",
            f"- Raw Isolation Forest beat raw kNN in median AP direction on {favorable_count('raw_isolation_forest_vs_raw_knn')}/3 datasets; this direction-only result did not satisfy the full recommendation gate.",
            f"- Trained DOMINANT-style reconstruction beat its untrained control in direction on {favorable_count('dominant_trained_vs_untrained')}/3 datasets, but no DOMINANT configuration satisfied inference, analyst-budget, stability, and control requirements together.",
            f"- Trained GraphSAGE beat random GraphSAGE in direction on {favorable_count('graphsage_trained_vs_random')}/3 datasets. Link-reconstruction training therefore showed no portable added value here.",
            f"- Observed GraphSAGE relations beat their permuted control in direction on {favorable_count('graphsage_observed_vs_permuted')}/3 datasets; Node2Vec did so on {favorable_count('node2vec_observed_vs_permuted')}/3.",
            f"- Matched amplification beat its own intrinsic score in direction on {favorable_count('matched_vs_intrinsic')}/3 datasets, so amplification should not be carried forward.",
            "- The best intrinsic UNSW and CIC AP configurations had Recall@100 near zero. High global ranking AP did not translate into the first 100 analyst reviews.",
            "",
            "## Cross-dataset reading",
            "",
            f"- Families passing the frozen direction-only portability rule: {', '.join(portable['comparison_family']) if len(portable) else 'none'}.",
            f"- Families with a statistically supported reversal: {', '.join(reversals['comparison_family']) if len(reversals) else 'none'}.",
            "- A result is not called portable merely because it wins one dataset or one feature hypothesis.",
            "",
            "## Next gate",
            "",
            "Only configurations marked Recommend may be taken to Phase 6. If a dataset "
            "has no Recommend row, its confirmation labels remain sealed and the result is "
            "reported as Explore or Abstain rather than rescued post hoc.",
            "",
            "Supporting details are in `comparisons.csv`, `outcomes.csv`, "
            "`portability_summary.csv`, `case_study_manifest.csv`, and "
            "`cluster_diagnostics.csv`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(artifact_root: Path, output_root: Path) -> dict[str, Any]:
    matrix = read_json(MATRIX_PATH)
    configs_document = read_json(CONFIG_PATH)
    execution = read_json(artifact_root / "execution_summary.json")
    expected = {
        "completed_cases": 12,
        "failed_cases": 0,
        "method_rows": 912,
        "representation_rows": 390,
    }
    for key, value in expected.items():
        if int(execution.get(key, -1)) != value:
            raise ValueError(f"Phase 4 summary mismatch for {key}: {execution.get(key)} != {value}")
    matrix_sha = sha256(MATRIX_PATH)
    case_matrix_hashes = {
        read_json(path)["matrix_sha256"]
        for path in (artifact_root / "cases").glob("*/execution.json")
    }
    if case_matrix_hashes != {matrix_sha}:
        raise ValueError(f"Case matrix hashes do not match {matrix_sha}: {case_matrix_hashes}")

    config_records = {item["dataset_id"]: item for item in configs_document["configs"]}
    comparison_rows: list[dict[str, Any]] = []
    pending_outcomes: list[tuple[str, str, ScoreConfig, float]] = []
    cluster_rows: list[dict[str, Any]] = []
    replicates = int(matrix["planned_comparisons"]["uncertainty"]["replicates"])
    random_state = int(matrix["planned_comparisons"]["uncertainty"]["random_state"])

    for dataset in matrix["datasets"]:
        dataset_id = dataset["dataset_id"]
        hypotheses = [
            str(item["name"])
            for item in config_records[dataset_id]["engine_config"]["feature_sets"]
        ]
        for partition in dataset["partitions"]:
            if partition["role"] not in {"development", "selection"}:
                continue
            partition_id = partition["partition_id"]
            observed_root = artifact_root / "cases" / f"{dataset_id}__{partition_id}__{OBSERVED}"
            null_root = artifact_root / "cases" / f"{dataset_id}__{partition_id}__{GRAPH_NULL}"
            observed_configs = load_case_configs(observed_root, OBSERVED)
            null_configs = load_case_configs(null_root, GRAPH_NULL)
            all_configs = {**observed_configs, **null_configs}
            labels = next(iter(observed_configs.values())).labels
            clusters = cluster_ids_for_partition(
                matrix, dataset, partition, config_records[dataset_id]
            )
            if len(clusters) != len(labels):
                raise ValueError(f"Cluster/session mismatch for {partition_id}")
            cluster_rows.append(
                {
                    "dataset_id": dataset_id,
                    "partition_id": partition_id,
                    "partition_role": partition["role"],
                    "cluster_key": matrix["planned_comparisons"]["uncertainty"][
                        "cluster_keys"
                    ][dataset_id],
                    "review_units": int(len(clusters)),
                    "clusters": int(np.unique(clusters).size),
                    "malicious_review_units": int(labels.sum()),
                    "prevalence": float(labels.mean()),
                }
            )
            patterns, inverse = bootstrap_patterns(
                clusters,
                replicates,
                random_state + sum(ord(char) for char in partition_id),
            )
            needed = set(all_configs)
            bootstrap_cache = {
                key: bootstrap_for_config(item, labels, clusters, patterns, inverse)
                for key, item in all_configs.items()
                if key in needed and item.status == "completed"
            }
            add_planned_comparisons(
                comparison_rows,
                dataset_id=dataset_id,
                partition_id=partition_id,
                partition_role=partition["role"],
                configs=all_configs,
                hypotheses=hypotheses,
                bootstrap_cache=bootstrap_cache,
            )
            if partition["role"] == "selection":
                random_reference = lookup(
                    all_configs, "intrinsic", OBSERVED, "random_score", "random"
                )
                prevalence = float(labels.mean())
                for item in candidate_configs(all_configs):
                    comparison_rows.append(
                        comparison_row(
                            dataset_id=dataset_id,
                            partition_id=partition_id,
                            partition_role="selection",
                            family="candidate_vs_random",
                            candidate=item,
                            reference=random_reference,
                            bootstrap_cache=bootstrap_cache,
                        )
                    )
                    pending_outcomes.append((dataset_id, partition_id, item, prevalence))

    comparisons = pd.DataFrame(comparison_rows)
    for _, indexes in comparisons[comparisons["primary"].astype(bool)].groupby("dataset_id").groups.items():
        comparisons.loc[indexes, "p_value_holm"] = holm_adjust(
            comparisons.loc[indexes, "p_value_raw"]
        )
    comparisons["significant_favorable"] = (
        comparisons["status"].eq("completed")
        & comparisons["ap_ci_low"].gt(0.0)
        & comparisons["p_value_holm"].le(0.05)
    )
    comparisons["significant_reversal"] = (
        comparisons["status"].eq("completed")
        & comparisons["ap_ci_high"].lt(0.0)
        & comparisons["p_value_holm"].le(0.05)
    )
    outcomes = outcome_rows(pending_outcomes, comparisons)
    portability = portability_summary(comparisons)
    selected = select_confirmation(outcomes)
    representations = pd.read_parquet(artifact_root / "tables" / "representation_results.parquet")
    cases = case_study_manifest(outcomes, comparisons, representations)

    output_root.mkdir(parents=True, exist_ok=True)
    comparisons.to_csv(output_root / "comparisons.csv", index=False)
    outcomes.to_csv(output_root / "outcomes.csv", index=False)
    portability.to_csv(output_root / "portability_summary.csv", index=False)
    selected.to_csv(output_root / "confirmation_candidates.csv", index=False)
    cases.to_csv(output_root / "case_study_manifest.csv", index=False)
    pd.DataFrame(cluster_rows).to_csv(output_root / "cluster_diagnostics.csv", index=False)
    finite_family_sizes = (
        comparisons[
            comparisons["primary"].astype(bool) & comparisons["p_value_raw"].notna()
        ]
        .groupby("dataset_id")
        .size()
    )
    summary = {
        "analysis_id": "analysis_v1",
        "matrix_sha256": matrix_sha,
        "phase4_execution": execution,
        "bootstrap_replicates": replicates,
        "comparison_rows": int(len(comparisons)),
        "completed_comparisons": int(comparisons["status"].eq("completed").sum()),
        "outcome_rows": int(len(outcomes)),
        "outcomes": {str(k): int(v) for k, v in outcomes["outcome"].value_counts().items()},
        "confirmation_candidates": int(len(selected)),
        "sealed_confirmation_accessed": False,
        "holm_family_sizes": {
            str(key): int(value)
            for key, value in finite_family_sizes.items()
        },
        "minimum_raw_p_two_sided_finite_sample": 2.0 / (replicates + 1.0),
        "inference_resolution_warning": (
            "The minimum attainable Holm-adjusted p-value exceeds 0.05 in every dataset "
            "under the frozen 2,000-replicate, all-primary-comparisons family."
        ),
    }
    (output_root / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_report(
        output_root / "REPORT.md",
        outcomes=outcomes,
        selected=selected,
        portability=portability,
        comparisons=comparisons,
        execution=execution,
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = analyze(args.artifact_root.resolve(), args.output_root.resolve())
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
