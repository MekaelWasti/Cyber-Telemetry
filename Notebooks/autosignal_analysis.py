"""Bounded representation evaluation and anomaly scorers for AutoSignal.

All functions in this module operate on an already-created, session-aligned
representation ``X``.  Labels are accepted only by the post-hoc development
evaluator; the anomaly scorers are strictly label-free.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist
from scipy.stats import rankdata, spearmanr
from sklearn.cluster import HDBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, silhouette_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


DEFAULT_ANALYSIS_SEED = 42
DEFAULT_REPRESENTATION_PERMUTATIONS = 199
DEFAULT_ISOLATION_TREES = 256
DEFAULT_DOMINANCE_RATIO = 1.25


def _finite_matrix(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    if values.ndim != 2:
        raise ValueError("Representation must be a 2D matrix.")
    if not np.isfinite(values).all():
        raise ValueError("Representation must contain only finite values.")
    return values


def _knn_indices(matrix: np.ndarray, k: int) -> np.ndarray:
    values = _finite_matrix(matrix)
    if isinstance(k, (bool, np.bool_)) or not isinstance(
        k, (int, np.integer)
    ):
        raise ValueError("k must be an integer.")
    if int(k) < 1:
        raise ValueError("k must be positive.")
    if len(values) <= 1:
        return np.empty((len(values), 0), dtype=np.int64)

    effective_k = min(int(k), len(values) - 1)
    _, candidates = cKDTree(values).query(
        values,
        k=effective_k + 1,
        workers=-1,
    )
    candidates = np.asarray(candidates, dtype=np.int64)
    if candidates.ndim == 1:
        candidates = candidates[:, None]
    neighbors = np.empty((len(values), effective_k), dtype=np.int64)
    for row_index, row_candidates in enumerate(candidates):
        without_self = row_candidates[row_candidates != row_index]
        neighbors[row_index] = without_self[:effective_k]
    return neighbors


def _malicious_neighbor_purity(
    neighbors: np.ndarray,
    binary_labels: np.ndarray,
) -> float | None:
    positives = np.flatnonzero(binary_labels == 1)
    if len(positives) == 0 or neighbors.shape[1] == 0:
        return None
    return float(np.mean(binary_labels[neighbors[positives]]))


def evaluate_representation(
    matrix: np.ndarray,
    labels: np.ndarray | None,
    *,
    k: int = 15,
    n_permutations: int = DEFAULT_REPRESENTATION_PERMUTATIONS,
    random_state: int = DEFAULT_ANALYSIS_SEED,
) -> dict[str, Any]:
    """Evaluate information in full-dimensional ``X`` on development labels.

    The returned metrics are post-hoc diagnostics.  They never become anomaly
    scores and are never used to train a representation in this function.
    """

    values = _finite_matrix(matrix)
    result: dict[str, Any] = {
        "status": "unavailable",
        "reason": None,
        "labels_available": labels is not None,
        "n_sessions": int(len(values)),
        "n_dimensions": int(values.shape[1]),
        "n_malicious": None,
        "n_benign": None,
        "effective_k": None,
        "malicious_neighbor_purity": None,
        "neighbor_purity_prevalence_reference": None,
        "neighbor_purity_lift": None,
        "neighbor_purity_permutation_p": None,
        "neighbor_purity_permutations": None,
        "label_silhouette": None,
        "linear_probe_average_precision": None,
        "linear_probe_folds": None,
        "linear_probe_split": None,
        "random_state": int(random_state),
    }
    if labels is None:
        result["reason"] = "Development labels are unavailable."
        return result

    label_values = np.asarray(labels)
    if len(label_values) != len(values):
        raise ValueError("Representation and labels are not session-aligned.")
    binary = (label_values == "malicious").astype(np.int64)
    n_positive = int(binary.sum())
    n_negative = int(len(binary) - n_positive)
    result["n_malicious"] = n_positive
    result["n_benign"] = n_negative
    if len(values) < 2:
        result["reason"] = "At least two sessions are required."
        return result
    if n_positive == 0 or n_negative == 0:
        result["reason"] = "Both malicious and benign sessions are required."
        return result

    neighbors = _knn_indices(values, k)
    result["effective_k"] = int(neighbors.shape[1])
    purity = _malicious_neighbor_purity(neighbors, binary)
    prevalence_reference = float((n_positive - 1) / (len(binary) - 1))
    result["malicious_neighbor_purity"] = purity
    result["neighbor_purity_prevalence_reference"] = prevalence_reference
    result["neighbor_purity_lift"] = (
        float(purity - prevalence_reference) if purity is not None else None
    )

    if (
        isinstance(n_permutations, (bool, np.bool_))
        or not isinstance(n_permutations, (int, np.integer))
        or int(n_permutations) < 1
    ):
        raise ValueError("n_permutations must be a positive integer.")
    if purity is not None:
        rng = np.random.default_rng(random_state)
        null_values = np.empty(int(n_permutations), dtype=float)
        for permutation_index in range(int(n_permutations)):
            permuted = rng.permutation(binary)
            null_values[permutation_index] = float(
                _malicious_neighbor_purity(neighbors, permuted)
            )
        result["neighbor_purity_permutation_p"] = float(
            (1 + np.sum(null_values >= purity)) / (int(n_permutations) + 1)
        )
        result["neighbor_purity_permutations"] = int(n_permutations)

    if n_positive >= 2 and n_negative >= 2 and len(values) >= 4:
        try:
            result["label_silhouette"] = float(
                silhouette_score(values, binary, metric="euclidean")
            )
        except Exception:
            result["label_silhouette"] = None

    fold_count = min(5, n_positive, n_negative)
    if fold_count >= 2:
        splitter = StratifiedKFold(
            n_splits=fold_count,
            shuffle=True,
            random_state=random_state,
        )
        out_of_fold = np.empty(len(values), dtype=float)
        for train_index, test_index in splitter.split(values, binary):
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    class_weight="balanced",
                    solver="liblinear",
                    max_iter=1_000,
                    random_state=random_state,
                ),
            )
            model.fit(values[train_index], binary[train_index])
            out_of_fold[test_index] = model.predict_proba(
                values[test_index]
            )[:, 1]
        result["linear_probe_average_precision"] = float(
            average_precision_score(binary, out_of_fold)
        )
        result["linear_probe_folds"] = int(fold_count)
        result["linear_probe_split"] = "stratified_kfold_development_only"

    result["status"] = "completed"
    result["reason"] = None
    return result


def isolation_forest_anomaly_scores(
    matrix: np.ndarray,
    *,
    random_state: int = DEFAULT_ANALYSIS_SEED,
    n_estimators: int = DEFAULT_ISOLATION_TREES,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return label-free Isolation Forest scores; larger means more anomalous."""

    values = _finite_matrix(matrix)
    if len(values) == 0:
        return np.empty(0, dtype=float), {
            "status": "unavailable",
            "reason": "No sessions are available.",
            "random_state": int(random_state),
            "n_estimators": int(n_estimators),
        }
    if len(values) == 1 or np.all(np.ptp(values, axis=0) == 0):
        return np.zeros(len(values), dtype=float), {
            "status": "degenerate",
            "reason": "The representation has fewer than two distinct sessions.",
            "random_state": int(random_state),
            "n_estimators": int(n_estimators),
        }

    scaled = StandardScaler().fit_transform(values)
    model = IsolationForest(
        n_estimators=int(n_estimators),
        max_samples=min(256, len(values)),
        contamination="auto",
        random_state=int(random_state),
        n_jobs=1,
    )
    model.fit(scaled)
    scores = -np.asarray(model.score_samples(scaled), dtype=float)
    if not np.isfinite(scores).all():
        raise RuntimeError("Isolation Forest produced non-finite scores.")
    return scores, {
        "status": "completed",
        "reason": None,
        "random_state": int(random_state),
        "n_estimators": int(n_estimators),
        "max_samples": int(min(256, len(values))),
        "contamination": "auto",
        "higher_is_more_anomalous": True,
    }


def rare_cluster_anomaly_scores(
    matrix: np.ndarray,
    *,
    min_cluster_size: int = 5,
    min_samples: int | None = None,
    dominance_ratio: float = DEFAULT_DOMINANCE_RATIO,
    random_state: int = DEFAULT_ANALYSIS_SEED,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Score coherent rare populations separated from a dominant population.

    The fixed population score for cluster ``c`` is

    ``-log(n_c / N) * ||mu_c - mu_dominant|| / global_rms``.

    HDBSCAN supplies the coherent populations without fixing their count.  The
    dominant cluster receives zero separation.  Noise receives zero because
    this scorer deliberately tests *population* anomalies; isolated-point
    behavior belongs to kNN and Isolation Forest.  When no cluster is at least
    ``dominance_ratio`` times the second-largest cluster, the scorer abstains
    instead of arbitrarily declaring one equally sized population normal.
    """

    values = _finite_matrix(matrix)
    n_sessions = len(values)
    empty_diagnostics = {
        "status": "unavailable",
        "reason": None,
        "random_state": int(random_state),
        "clusterer": "sklearn_hdbscan",
        "min_cluster_size": int(min_cluster_size),
        "min_samples": int(min_samples) if min_samples is not None else None,
        "effective_clusters": 0,
        "dominance_ratio_threshold": float(dominance_ratio),
        "dominant_cluster": None,
        "noise_sessions": 0,
        "noise_policy": "zero_population_score",
        "cluster_counts": [],
        "cluster_population_scores": [],
        "formula": "-log(cluster_fraction) * centroid_separation / global_rms",
        "higher_is_more_anomalous": True,
    }
    if n_sessions == 0:
        empty_diagnostics["reason"] = "No sessions are available."
        return (
            np.empty(0, dtype=float),
            np.empty(0, dtype=np.int64),
            empty_diagnostics,
        )

    if (
        isinstance(min_cluster_size, (bool, np.bool_))
        or not isinstance(min_cluster_size, (int, np.integer))
        or int(min_cluster_size) < 2
    ):
        raise ValueError("min_cluster_size must be an integer of at least two.")
    if min_samples is not None and (
        isinstance(min_samples, (bool, np.bool_))
        or not isinstance(min_samples, (int, np.integer))
        or int(min_samples) < 1
    ):
        raise ValueError("min_samples must be a positive integer or None.")

    unique_count = int(np.unique(values, axis=0).shape[0])
    if (
        n_sessions < 2 * int(min_cluster_size)
        or unique_count < 2
    ):
        empty_diagnostics["status"] = "degenerate"
        empty_diagnostics["reason"] = (
            "At least two minimum-size populations and two distinct vectors "
            "are required."
        )
        return (
            np.zeros(n_sessions, dtype=float),
            np.full(n_sessions, -1, dtype=np.int64),
            empty_diagnostics,
        )

    scaled = StandardScaler().fit_transform(values)
    model = HDBSCAN(
        min_cluster_size=int(min_cluster_size),
        min_samples=(int(min_samples) if min_samples is not None else None),
        metric="euclidean",
        cluster_selection_method="eom",
        allow_single_cluster=False,
        n_jobs=1,
        copy=True,
    )
    assignments = model.fit_predict(scaled).astype(np.int64)
    cluster_ids = np.asarray(
        sorted(int(value) for value in np.unique(assignments) if value >= 0),
        dtype=np.int64,
    )
    effective_clusters = int(len(cluster_ids))
    diagnostics = dict(empty_diagnostics)
    diagnostics["effective_clusters"] = effective_clusters
    diagnostics["noise_sessions"] = int(np.sum(assignments < 0))
    if effective_clusters < 2:
        diagnostics["status"] = "abstained"
        diagnostics["reason"] = (
            "HDBSCAN did not identify at least two coherent populations."
        )
        return np.zeros(n_sessions, dtype=float), assignments, diagnostics

    counts = np.asarray(
        [int(np.sum(assignments == cluster_id)) for cluster_id in cluster_ids],
        dtype=np.int64,
    )
    count_order = np.argsort(-counts, kind="stable")
    dominant_position = int(count_order[0])
    dominant = int(cluster_ids[dominant_position])
    second_count = int(counts[count_order[1]])
    observed_ratio = float(counts[dominant_position] / max(second_count, 1))

    diagnostics.update(
        {
            "dominant_cluster": dominant,
            "dominant_to_second_ratio": observed_ratio,
            "cluster_counts": [int(value) for value in counts],
            "cluster_ids": [int(value) for value in cluster_ids],
        }
    )
    if observed_ratio < float(dominance_ratio):
        diagnostics["status"] = "abstained"
        diagnostics["reason"] = (
            "No clearly dominant reference population under the fixed ratio."
        )
        diagnostics["cluster_population_scores"] = [
            0.0 for _ in range(effective_clusters)
        ]
        return np.zeros(n_sessions, dtype=float), assignments, diagnostics

    centroids = np.vstack(
        [
            scaled[assignments == cluster_id].mean(axis=0)
            for cluster_id in cluster_ids
        ]
    )
    global_center = scaled.mean(axis=0)
    global_rms = float(
        np.sqrt(np.mean(np.sum((scaled - global_center) ** 2, axis=1)))
    )
    global_rms = max(global_rms, np.finfo(float).eps)
    population_scores = np.zeros(effective_clusters, dtype=float)
    for cluster_position, cluster_id in enumerate(cluster_ids):
        if int(cluster_id) == dominant:
            continue
        fraction = float(counts[cluster_position] / n_sessions)
        rarity = -math.log(max(fraction, np.finfo(float).tiny))
        separation = float(
            np.linalg.norm(
                centroids[cluster_position] - centroids[dominant_position]
            )
            / global_rms
        )
        population_scores[cluster_position] = rarity * separation
    score_by_cluster = {
        int(cluster_id): float(population_scores[position])
        for position, cluster_id in enumerate(cluster_ids)
    }
    scores = np.asarray(
        [score_by_cluster.get(int(cluster_id), 0.0) for cluster_id in assignments],
        dtype=float,
    )
    if not np.isfinite(scores).all():
        raise RuntimeError("Rare-cluster scorer produced non-finite scores.")
    diagnostics["status"] = "completed"
    diagnostics["reason"] = None
    diagnostics["global_rms"] = global_rms
    diagnostics["cluster_population_scores"] = [
        float(value) for value in population_scores
    ]
    return scores.astype(float), assignments, diagnostics


def representation_stability(
    first: np.ndarray,
    second: np.ndarray,
    *,
    k: int = 15,
    max_distance_pairs: int = 100_000,
    random_state: int = DEFAULT_ANALYSIS_SEED,
) -> dict[str, Any]:
    """Compare two aligned representations using rotation-invariant geometry."""

    left = _finite_matrix(first)
    right = _finite_matrix(second)
    if len(left) != len(right):
        raise ValueError("Representations must contain the same sessions.")
    if len(left) < 2:
        return {
            "status": "unavailable",
            "reason": "At least two aligned sessions are required.",
            "n_sessions": int(len(left)),
            "distance_rank_correlation": None,
            "mean_neighbor_jaccard": None,
            "effective_k": None,
        }

    total_pairs = len(left) * (len(left) - 1) // 2
    if total_pairs > int(max_distance_pairs):
        rng = np.random.default_rng(random_state)
        first_indices = rng.integers(
            0, len(left), size=int(max_distance_pairs)
        )
        offsets = rng.integers(
            1, len(left), size=int(max_distance_pairs)
        )
        second_indices = (first_indices + offsets) % len(left)
        left_distances = np.linalg.norm(
            left[first_indices] - left[second_indices], axis=1
        )
        right_distances = np.linalg.norm(
            right[first_indices] - right[second_indices], axis=1
        )
    else:
        left_distances = pdist(left, metric="euclidean")
        right_distances = pdist(right, metric="euclidean")
    if np.ptp(left_distances) == 0 or np.ptp(right_distances) == 0:
        distance_correlation = None
    else:
        correlation = spearmanr(
            rankdata(left_distances),
            rankdata(right_distances),
        ).statistic
        distance_correlation = (
            float(correlation) if np.isfinite(correlation) else None
        )

    left_neighbors = _knn_indices(left, k)
    right_neighbors = _knn_indices(right, k)
    jaccards = []
    for left_row, right_row in zip(left_neighbors, right_neighbors):
        left_set = set(int(value) for value in left_row)
        right_set = set(int(value) for value in right_row)
        union = left_set | right_set
        jaccards.append(
            float(len(left_set & right_set) / len(union)) if union else 1.0
        )
    return {
        "status": "completed",
        "reason": None,
        "n_sessions": int(len(left)),
        "distance_rank_correlation": distance_correlation,
        "mean_neighbor_jaccard": float(np.mean(jaccards)),
        "effective_k": int(left_neighbors.shape[1]),
        "max_distance_pairs": int(max_distance_pairs),
        "random_state": int(random_state),
    }


__all__ = [
    "evaluate_representation",
    "isolation_forest_anomaly_scores",
    "rare_cluster_anomaly_scores",
    "representation_stability",
]
