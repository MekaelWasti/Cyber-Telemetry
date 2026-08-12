"""Parameterized AutoSignal v1 engine.

The schema agent proposes a JSON configuration.  This module validates and
executes that configuration; it never asks an LLM to run preprocessing code.
The implementation deliberately keeps the contract bounded:

* one canonical activity-window sessionization;
* one typed graph shared by all methods;
* registered session representations separated from scorer adapters;
* kNN, Isolation Forest, and one HDBSCAN population scorer;
* structural statistics, Node2Vec, GraphSAGE controls, and DOMINANT-style
  reconstruction;
* one aligned, frontend-friendly result payload.
"""

from __future__ import annotations

import copy
import importlib.metadata
import math
import os
import platform
import random
import re
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    os.path.join(tempfile.gettempdir(), "autosignal_numba_cache"),
)

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from scipy import sparse
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv
from torch_geometric.utils import negative_sampling
from umap import UMAP

from autosignal_analysis import (
    evaluate_representation,
    isolation_forest_anomaly_scores,
    rare_cluster_anomaly_scores,
    representation_stability,
)


SEED = 42
DEFAULT_K = 15
DEFAULT_INACTIVITY_MINUTES = 5
DEFAULT_MAX_DURATION_MINUTES = 30
DEFAULT_GRAPH_EPOCHS = 4
DEFAULT_EMBEDDING_DIM = 32
DEFAULT_MAX_POSITIVE_EDGES = 3_000
DEFAULT_NODE2VEC_PAIRS = 200_000
DEFAULT_SIGNAL_PERMUTATIONS = 199
SIGNAL_TAIL_FRACTION = 0.05
SIGNAL_MIN_TAIL_SIZE = 10
SIGNAL_ALPHA = 0.05
SIGNAL_AMPLIFICATION_ALPHA = 0.5
DOMINANT_ATTRIBUTE_ALPHA = 0.5
SUPPORTED_REPRESENTATIONS = frozenset(
    {
        "random_score",
        "raw_session",
        "typed_structural_stats",
        "node2vec",
        "graphsage_random",
        "graphsage_trained",
        "dominant_style_untrained",
        "dominant_style_trained",
    }
)
SUPPORTED_COMMON_SCORERS = frozenset(
    {"knn_mean_distance", "isolation_forest", "hdbscan_rare_cluster"}
)


def _software_environment() -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for distribution in (
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "torch",
        "torch-geometric",
        "umap-learn",
    ):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None
    return {
        "python": platform.python_version(),
        "packages": packages,
    }


def _record_runtime(
    payload: dict[str, Any],
    *,
    stage: str,
    seconds: float,
    status: str = "completed",
    representation: str | None = None,
    scorer: str | None = None,
    hypothesis: str | None = None,
    representation_seed: int | None = None,
    scorer_seed: int | None = None,
) -> None:
    payload["runtime_diagnostics"].append(
        {
            "stage": stage,
            "status": status,
            "seconds": float(max(seconds, 0.0)),
            "representation": representation,
            "scorer": scorer,
            "hypothesis": hypothesis,
            "representation_seed": representation_seed,
            "scorer_seed": scorer_seed,
        }
    )


SIGNAL_REGIME_NAMES = (
    "Neighborhood-supported",
    "Locally Contrastive",
    "Intermediate-scale",
)

ALLOWED_FEATURE_TYPES = {"numeric", "boolean", "category", "timestamp"}
REQUIRED_TOP_LEVEL_KEYS = {
    "timestamp_col",
    "existing_session_id_col",
    "session_group_cols",
    "graph_relations",
    "label_col",
    "malicious_label_values",
    "selected_columns",
    "feature_sets",
}
RELATION_KEYS = {
    "relation_name",
    "source_node_type",
    "source_column",
    "target_node_type",
    "target_column",
    "directed",
    "meaning",
}


class ConfigValidationError(ValueError):
    """Raised when an agent configuration cannot safely drive the engine."""


@dataclass
class GraphBundle:
    data: HeteroData
    node_maps: dict[str, dict[str, int]]
    primary_node_type: str
    primary_id_column: str
    row_primary_index: np.ndarray
    forward_edge_types: list[tuple[str, str, str]]
    relation_by_edge_type: dict[tuple[str, str, str], dict[str, Any]]
    manifest: dict[str, Any]


def load_df_slice(path: str | Path, rows: int | None = None) -> pd.DataFrame:
    """Load a CSV, Parquet, or JSON file without dataset-specific semantics."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif suffix in {".json", ".jsonl", ".ndjson"}:
        try:
            df = pd.read_json(path)
        except ValueError:
            # Accept newline-delimited telemetry as well as JSON arrays/objects.
            df = pd.read_json(path, lines=True)
    else:
        raise ValueError(f"Unsupported dataset type: {suffix or '<none>'}")

    if rows is not None and rows > 0 and len(df) > rows:
        df = df.tail(int(rows))
    return df.reset_index(drop=True).copy()


def dataframe_profile(df: pd.DataFrame) -> dict[str, Any]:
    """Small label-blind profile suitable for the UI and schema-agent prompt."""
    columns = []
    for column in df.columns:
        series = df[column]
        non_null = int(series.notna().sum())
        try:
            unique = int(series.nunique(dropna=True))
        except TypeError:
            # List/array-valued telemetry fields are valid profile inputs but
            # are not hashable in pandas' ordinary cardinality routine.
            unique = int(
                series.dropna().map(lambda value: repr(value)).nunique()
            )
        columns.append(
            {
                "column": str(column),
                "dtype": str(series.dtype),
                "non_null": non_null,
                "missing_fraction": float(1 - non_null / max(len(df), 1)),
                "unique": unique,
            }
        )
    return {"rows": int(len(df)), "columns": columns}


def _column_exists(column: Any, df: pd.DataFrame) -> bool:
    return column is None or column == "$row_id" or column in df.columns


def validate_config(config: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    """Validate references, feature isolation, and the fixed v1 JSON contract."""
    if not isinstance(config, dict):
        raise ConfigValidationError("Agent output must be a JSON object.")

    errors: list[str] = []
    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - set(config))
    if missing_keys:
        errors.append(f"Missing top-level keys: {missing_keys}")

    cfg = copy.deepcopy(config)
    if errors:
        raise ConfigValidationError("; ".join(errors))

    for key in ("timestamp_col", "existing_session_id_col", "label_col"):
        if not _column_exists(cfg.get(key), df):
            errors.append(f"{key} references missing column {cfg.get(key)!r}")

    group_columns = cfg.get("session_group_cols")
    if not isinstance(group_columns, list):
        errors.append("session_group_cols must be a list.")
        group_columns = []
    for column in group_columns:
        if column not in df.columns:
            errors.append(f"session_group_cols references missing column {column!r}")

    selected = cfg.get("selected_columns")
    if not isinstance(selected, list) or not selected:
        errors.append("selected_columns must be a non-empty list.")
        selected = []

    selected_names: list[str] = []
    selected_types: dict[str, str] = {}
    for item in selected:
        if not isinstance(item, dict):
            errors.append("Every selected_columns entry must be an object.")
            continue
        column = item.get("column")
        kind = item.get("type")
        if column not in df.columns:
            errors.append(f"Selected feature column {column!r} does not exist.")
        if kind not in ALLOWED_FEATURE_TYPES:
            errors.append(
                f"Selected feature {column!r} has unsupported type {kind!r}."
            )
        if column in selected_names:
            errors.append(f"Selected feature {column!r} is duplicated.")
        selected_names.append(column)
        selected_types[column] = kind

    label_col = cfg.get("label_col")
    if label_col in selected_names:
        errors.append("The evaluation label cannot be a selected feature.")
    if label_col is not None:
        if cfg.get("timestamp_col") == label_col:
            errors.append("The evaluation label cannot be the timestamp column.")
        if cfg.get("existing_session_id_col") == label_col:
            errors.append("The evaluation label cannot define session IDs.")
        if label_col in group_columns:
            errors.append("The evaluation label cannot define session groups.")

    feature_sets = cfg.get("feature_sets")
    if not isinstance(feature_sets, list) or not feature_sets:
        errors.append("feature_sets must be a non-empty list.")
        feature_sets = []

    set_names: set[str] = set()
    used_features: set[str] = set()
    for feature_set in feature_sets:
        if not isinstance(feature_set, dict):
            errors.append("Every feature set must be an object.")
            continue
        name = str(feature_set.get("name", "")).strip()
        columns = feature_set.get("columns")
        if not name:
            errors.append("Every feature set requires a non-empty name.")
        if name in set_names:
            errors.append(f"Feature-set name {name!r} is duplicated.")
        set_names.add(name)
        if not isinstance(columns, list) or not columns:
            errors.append(f"Feature set {name!r} must contain columns.")
            continue
        for column in columns:
            if column not in selected_names:
                errors.append(
                    f"Feature set {name!r} references unselected column {column!r}."
                )
            used_features.add(column)

    unused = sorted(set(selected_names) - used_features)
    if unused:
        errors.append(f"Selected features are not assigned to a feature set: {unused}")

    relations = cfg.get("graph_relations")
    if not isinstance(relations, list):
        errors.append("graph_relations must be a list.")
        relations = []

    relation_names: set[str] = set()
    for relation in relations:
        if not isinstance(relation, dict):
            errors.append("Every graph relation must be an object.")
            continue
        missing_relation_keys = RELATION_KEYS - set(relation)
        if missing_relation_keys:
            errors.append(
                f"Relation is missing keys: {sorted(missing_relation_keys)}"
            )
        unknown_relation_keys = set(relation) - RELATION_KEYS
        if unknown_relation_keys:
            errors.append(
                f"Relation has unknown keys: {sorted(unknown_relation_keys)}"
            )
        name = relation.get("relation_name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            errors.append(f"Invalid relation_name {name!r}; use snake_case.")
        if name in relation_names:
            errors.append(f"Relation name {name!r} is duplicated.")
        relation_names.add(name)
        for endpoint in ("source_column", "target_column"):
            column = relation.get(endpoint)
            if not _column_exists(column, df):
                errors.append(
                    f"Relation {name!r} references missing {endpoint} {column!r}."
                )
            if label_col is not None and column == label_col:
                errors.append(
                    f"Relation {name!r} cannot use the evaluation label as "
                    f"{endpoint}."
                )
        if not isinstance(relation.get("directed"), bool):
            errors.append(f"Relation {name!r} directed must be true or false.")

    if errors:
        raise ConfigValidationError("\n".join(f"- {error}" for error in errors))

    cfg["_selected_types"] = selected_types
    return cfg


def _normalize_identifier(series: pd.Series) -> pd.Series:
    result = series.astype("string").str.strip()
    return result.mask(result.isin(["", "nan", "None", "<NA>"]))


def _malicious_mask(
    series: pd.Series, malicious_values: list[Any]
) -> np.ndarray:
    direct = series.isin(malicious_values)
    string_values = {str(value).strip().lower() for value in malicious_values}
    normalized = series.astype("string").str.strip().str.lower()
    return (direct | normalized.isin(string_values)).fillna(False).to_numpy(bool)


def sessionize(
    df: pd.DataFrame,
    config: dict[str, Any],
    inactivity_minutes: int = DEFAULT_INACTIVITY_MINUTES,
    maximum_duration_minutes: int = DEFAULT_MAX_DURATION_MINUTES,
) -> tuple[pd.DataFrame, list[list[int]], dict[str, Any]]:
    """Create one deterministic canonical session assignment."""
    work = df.copy().reset_index(drop=False).rename(columns={"index": "_source_row"})
    existing = config.get("existing_session_id_col")
    timestamp_col = config.get("timestamp_col")
    group_columns = list(config.get("session_group_cols", []))

    if timestamp_col:
        work["_event_time"] = pd.to_datetime(
            work[timestamp_col], errors="coerce", utc=True
        )
    else:
        work["_event_time"] = pd.NaT

    parse_success = float(work["_event_time"].notna().mean()) if len(work) else 0.0

    if existing:
        raw_ids = _normalize_identifier(work[existing]).fillna("__missing_session__")
        work["session_id"] = pd.factorize(raw_ids, sort=False)[0].astype(int)
        work = work.sort_values(
            ["session_id", "_event_time", "_source_row"],
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)
        # Refactor after sorting so IDs are contiguous in first-observed order.
        work["session_id"] = pd.factorize(work["session_id"], sort=False)[0]
        strategy = "existing_session_id"
    elif timestamp_col:
        identity_parts = []
        for column in group_columns:
            part = _normalize_identifier(work[column]).fillna(f"__missing_{column}__")
            identity_parts.append(column + "=" + part)
        if identity_parts:
            identity = identity_parts[0]
            for part in identity_parts[1:]:
                identity = identity + "|" + part
        else:
            identity = pd.Series("__global_identity__", index=work.index, dtype="string")

        work["_session_identity"] = identity
        work = work.sort_values(
            ["_session_identity", "_event_time", "_source_row"],
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)

        inactivity = pd.Timedelta(minutes=inactivity_minutes)
        maximum_duration = pd.Timedelta(minutes=maximum_duration_minutes)
        session_ids = np.empty(len(work), dtype=np.int64)
        next_id = 0

        for _, indices in work.groupby("_session_identity", sort=False).groups.items():
            session_start = None
            previous_time = None
            for position in indices:
                event_time = work.at[position, "_event_time"]
                new_session = session_start is None
                if pd.isna(event_time):
                    new_session = True
                elif previous_time is not None and event_time - previous_time > inactivity:
                    new_session = True
                elif session_start is not None and event_time - session_start > maximum_duration:
                    new_session = True

                if new_session:
                    if session_start is not None:
                        next_id += 1
                    session_start = event_time
                session_ids[position] = next_id
                previous_time = event_time if pd.notna(event_time) else None

            next_id += 1

        work["session_id"] = pd.factorize(session_ids, sort=False)[0].astype(int)
        strategy = "activity_window"
    else:
        work["session_id"] = np.arange(len(work), dtype=int)
        strategy = "one_row_per_session"

    session_ids = np.sort(work["session_id"].unique())
    sessions = [
        work.index[work["session_id"].eq(session_id)].tolist()
        for session_id in session_ids
    ]
    sizes = np.asarray([len(indices) for indices in sessions], dtype=int)

    durations = []
    for indices in sessions:
        times = work.loc[indices, "_event_time"].dropna()
        duration = (
            (times.max() - times.min()).total_seconds() / 60.0
            if len(times)
            else 0.0
        )
        durations.append(float(duration))

    manifest = {
        "strategy": strategy,
        "sessions": int(len(sessions)),
        "rows": int(len(work)),
        "timestamp_parse_success": parse_success,
        "singleton_fraction": float((sizes == 1).mean()) if len(sizes) else 0.0,
        "median_session_size": float(np.median(sizes)) if len(sizes) else 0.0,
        "p95_session_size": float(np.quantile(sizes, 0.95)) if len(sizes) else 0.0,
        "largest_session_size": int(sizes.max()) if len(sizes) else 0,
        "median_session_minutes": float(np.median(durations)) if durations else 0.0,
        "p95_session_minutes": (
            float(np.quantile(durations, 0.95)) if durations else 0.0
        ),
        "inactivity_minutes": int(inactivity_minutes),
        "maximum_duration_minutes": int(maximum_duration_minutes),
    }
    return work, sessions, manifest


def _numeric_column(series: pd.Series) -> tuple[np.ndarray, dict[str, Any]]:
    values = pd.to_numeric(series, errors="coerce").astype(float)
    values = values.replace([np.inf, -np.inf], np.nan)
    missing_fraction = float(values.isna().mean())
    median = float(values.median()) if values.notna().any() else 0.0
    values = values.fillna(median)

    transformed = values.to_numpy(dtype=np.float64)
    nonnegative = bool(np.all(transformed >= 0))
    skew = float(pd.Series(transformed).skew()) if len(transformed) > 2 else 0.0
    used_log1p = bool(nonnegative and np.isfinite(skew) and skew > 2.0)
    if used_log1p:
        transformed = np.log1p(transformed)
    return transformed, {
        "missing_fraction": missing_fraction,
        "imputation": "median",
        "log1p": used_log1p,
    }


def build_row_feature_matrix(
    df: pd.DataFrame,
    columns: list[str],
    selected_types: dict[str, str],
) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    """Create safe numeric row features from the compact agent type contract."""
    features: list[np.ndarray] = []
    names: list[str] = []
    diagnostics: dict[str, Any] = {}

    for column in columns:
        kind = selected_types[column]
        series = df[column]
        if kind == "numeric":
            values, diag = _numeric_column(series)
            features.append(values)
            names.append(column)
            diagnostics[column] = diag
        elif kind == "boolean":
            normalized = series.astype("string").str.strip().str.lower()
            values = normalized.map(
                {
                    "true": 1.0,
                    "1": 1.0,
                    "yes": 1.0,
                    "false": 0.0,
                    "0": 0.0,
                    "no": 0.0,
                }
            )
            values = values.fillna(float(values.median()) if values.notna().any() else 0)
            features.append(values.to_numpy(float))
            names.append(column)
            diagnostics[column] = {"encoding": "boolean_to_int"}
        elif kind == "category":
            normalized = _normalize_identifier(series).fillna("__missing__")
            frequencies = normalized.map(normalized.value_counts(normalize=True))
            features.append(frequencies.to_numpy(float))
            names.append(f"{column}__frequency")
            diagnostics[column] = {"encoding": "frequency"}
        elif kind == "timestamp":
            parsed = pd.to_datetime(series, errors="coerce", utc=True)
            hour = (
                parsed.dt.hour.fillna(0).to_numpy(float)
                + parsed.dt.minute.fillna(0).to_numpy(float) / 60
            )
            features.extend(
                [
                    np.sin(2 * np.pi * hour / 24),
                    np.cos(2 * np.pi * hour / 24),
                ]
            )
            names.extend([f"{column}__hour_sin", f"{column}__hour_cos"])
            diagnostics[column] = {
                "encoding": "cyclical_hour",
                "parse_success": float(parsed.notna().mean()),
            }

    if not features:
        raise ValueError("No usable features were produced.")

    matrix = np.column_stack(features).astype(np.float64)
    finite = np.isfinite(matrix)
    if not finite.all():
        matrix[~finite] = 0.0

    varying = np.nanstd(matrix, axis=0) > 1e-12
    if varying.any():
        matrix = matrix[:, varying]
        names = [name for name, keep in zip(names, varying) if keep]
    else:
        # Preserve one deterministic channel so a sparse hypothesis can run.
        matrix = np.zeros((len(df), 1), dtype=np.float64)
        names = ["constant_zero"]

    matrix = StandardScaler().fit_transform(matrix).astype(np.float32)
    return matrix, names, diagnostics


def _session_labels(
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
    config: dict[str, Any],
) -> np.ndarray | None:
    label_col = config.get("label_col")
    if not label_col or label_col not in sessionized_df.columns:
        return None
    row_malicious = _malicious_mask(
        sessionized_df[label_col],
        list(config.get("malicious_label_values", [])),
    )
    return np.asarray(
        [
            "malicious" if row_malicious[indices].any() else "benign"
            for indices in sessions
        ],
        dtype=object,
    )


def _pool_rows(
    row_matrix: np.ndarray,
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
) -> tuple[np.ndarray, list[str]]:
    pooled = []
    for indices in sessions:
        values = row_matrix[indices]
        pooled.append(
            np.concatenate(
                [
                    values.mean(axis=0),
                    values.std(axis=0),
                    values.max(axis=0),
                    values.sum(axis=0),
                    np.asarray([math.log1p(len(indices))], dtype=float),
                ]
            )
        )
    matrix = np.asarray(pooled, dtype=np.float32)
    if len(matrix):
        matrix = StandardScaler().fit_transform(matrix).astype(np.float32)
    return matrix, ["mean", "std", "max", "sum", "log_session_size"]


def _pooled_dimension_names(row_dimension_names: list[str]) -> list[str]:
    return [
        f"{aggregation}::{name}"
        for aggregation in ("mean", "std", "max", "sum")
        for name in row_dimension_names
    ] + ["log_session_size"]


def knn_anomaly_scores(matrix: np.ndarray, k: int = DEFAULT_K) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    if len(matrix) <= 1:
        return np.zeros(len(matrix), dtype=float)
    effective_k = min(int(k), len(matrix) - 1)
    distances, candidates = cKDTree(matrix).query(
        matrix, k=effective_k + 1, workers=-1
    )
    distances = np.asarray(distances, dtype=float)
    candidates = np.asarray(candidates, dtype=np.int64)
    if distances.ndim == 1:
        distances = distances[:, None]
        candidates = candidates[:, None]
    selected = np.empty((len(matrix), effective_k), dtype=float)
    for row_index, (row_distances, row_candidates) in enumerate(
        zip(distances, candidates)
    ):
        non_self = row_distances[row_candidates != row_index]
        if len(non_self) < effective_k:
            # This is only expected under unusual duplicate/tie behavior.
            all_distances, all_candidates = cKDTree(matrix).query(
                matrix[row_index], k=len(matrix)
            )
            non_self = np.asarray(all_distances, dtype=float)[
                np.asarray(all_candidates, dtype=np.int64) != row_index
            ]
        selected[row_index] = non_self[:effective_k]
    return selected.mean(axis=1)


def build_session_knn_operator(
    matrix: np.ndarray,
    k: int = DEFAULT_K,
) -> tuple[sparse.csr_matrix, sparse.csr_matrix]:
    """Build a symmetric session kNN graph and row-normalized operator.

    The graph must be constructed from the same session representation used
    for intrinsic kNN scoring. Sparse matrices stay internal to the engine;
    only the derived, JSON-safe signal channels are returned to the frontend.
    """

    values = np.asarray(matrix, dtype=np.float32)
    if values.ndim != 2:
        raise ValueError("Session representation must be a 2D matrix.")
    if not np.isfinite(values).all():
        raise ValueError("Session representation must contain finite values.")
    if isinstance(k, (bool, np.bool_)) or not isinstance(k, (int, np.integer)):
        raise ValueError("Signal graph k must be an integer.")
    if int(k) < 1:
        raise ValueError("Signal graph k must be positive.")

    n_sessions = len(values)
    if n_sessions <= 1:
        empty = sparse.csr_matrix(
            (n_sessions, n_sessions),
            dtype=float,
        )
        return empty, empty.copy()

    effective_k = min(int(k), n_sessions - 1)
    _, neighbor_candidates = cKDTree(values).query(
        values,
        k=effective_k + 1,
        workers=-1,
    )
    neighbor_candidates = np.asarray(
        neighbor_candidates,
        dtype=np.int64,
    )
    if neighbor_candidates.ndim == 1:
        neighbor_candidates = neighbor_candidates[:, None]

    # cKDTree does not guarantee that self is the first result when duplicate
    # vectors tie at distance zero. Remove the actual row index explicitly.
    selected_neighbors = np.empty(
        (n_sessions, effective_k),
        dtype=np.int64,
    )
    for session_id, candidates in enumerate(neighbor_candidates):
        without_self = candidates[candidates != session_id]
        if len(without_self) < effective_k:
            raise RuntimeError(
                "kNN query did not return enough non-self session neighbors."
            )
        selected_neighbors[session_id] = without_self[:effective_k]

    rows = np.repeat(np.arange(n_sessions), effective_k)
    columns = selected_neighbors.reshape(-1)
    adjacency = sparse.csr_matrix(
        (
            np.ones(len(rows), dtype=float),
            (rows, columns),
        ),
        shape=(n_sessions, n_sessions),
    )

    # Use the union of directed kNN edges so neighborhood support is symmetric.
    adjacency = adjacency.maximum(adjacency.T).tocsr()
    adjacency.setdiag(0)
    adjacency.eliminate_zeros()

    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    inverse_degree = np.divide(
        1.0,
        degree,
        out=np.zeros_like(degree, dtype=float),
        where=degree > 0,
    )
    propagation = (sparse.diags(inverse_degree) @ adjacency).tocsr()
    return adjacency, propagation


def compute_signal_diagnostic_channels(
    propagation: sparse.spmatrix,
    scores: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute graph-relative diagnostic channels for intrinsic scores."""

    intrinsic = np.asarray(scores, dtype=float).ravel()
    if propagation.shape != (len(intrinsic), len(intrinsic)):
        raise ValueError("Propagation operator and score vector are not aligned.")
    if not np.isfinite(intrinsic).all():
        raise ValueError("Intrinsic anomaly scores must be finite.")

    neighbor_support = np.asarray(propagation @ intrinsic).ravel()
    second_hop_support = np.asarray(
        propagation @ neighbor_support
    ).ravel()
    local_contrast = intrinsic - neighbor_support
    return {
        "intrinsic": intrinsic,
        "neighbor_support": neighbor_support,
        "second_hop_support": second_hop_support,
        "local_contrast": local_contrast,
        "local_contrast_magnitude": np.abs(local_contrast),
        "pocket": neighbor_support - second_hop_support,
        "supported_candidate": (
            SIGNAL_AMPLIFICATION_ALPHA * intrinsic
            + (1.0 - SIGNAL_AMPLIFICATION_ALPHA) * neighbor_support
        ),
    }


def _signal_regime_statistics(
    propagation: sparse.spmatrix,
    scores: np.ndarray,
    *,
    tail_fraction: float,
    min_tail_size: int,
) -> np.ndarray:
    """Return one targeted statistic for each candidate signal regime."""

    intrinsic = np.asarray(scores, dtype=float).ravel()
    if len(intrinsic) < 2 or not np.isfinite(intrinsic).all():
        raise ValueError(
            "Signal diagnosis requires at least two finite anomaly scores."
        )
    if propagation.shape != (len(intrinsic), len(intrinsic)):
        raise ValueError("Propagation operator and score vector are not aligned.")
    if not 0 < tail_fraction <= 1:
        raise ValueError("tail_fraction must be in (0, 1].")
    if min_tail_size < 1:
        raise ValueError("min_tail_size must be positive.")

    score_std = float(np.std(intrinsic))
    if score_std <= np.finfo(float).eps:
        raise ValueError(
            "Signal diagnosis requires non-constant anomaly scores."
        )

    standardized = (intrinsic - np.mean(intrinsic)) / score_std
    neighbor_support = np.asarray(propagation @ standardized).ravel()
    second_hop_support = np.asarray(
        propagation @ neighbor_support
    ).ravel()

    tail_size = min(
        len(standardized),
        max(
            int(min_tail_size),
            int(np.ceil(tail_fraction * len(standardized))),
        ),
    )
    intrinsic_tail = np.argpartition(
        standardized,
        len(standardized) - tail_size,
    )[-tail_size:]
    neighborhood_tail = np.argpartition(
        neighbor_support,
        len(neighbor_support) - tail_size,
    )[-tail_size:]

    return np.asarray(
        [
            # Do intrinsically anomalous sessions have anomalous neighbors?
            np.mean(neighbor_support[intrinsic_tail]),
            # Do intrinsically anomalous sessions rise above normal neighbors?
            np.mean(
                (standardized - neighbor_support)[intrinsic_tail]
            ),
            # Do the strongest one-hop neighborhoods dilute at two hops?
            np.mean(
                (
                    neighbor_support
                    - second_hop_support
                )[neighborhood_tail]
            ),
        ],
        dtype=float,
    )


def pick_signal_regime(
    propagation: sparse.spmatrix,
    scores: np.ndarray,
    *,
    n_permutations: int = DEFAULT_SIGNAL_PERMUTATIONS,
    tail_fraction: float = SIGNAL_TAIL_FRACTION,
    min_tail_size: int = SIGNAL_MIN_TAIL_SIZE,
    alpha: float = SIGNAL_ALPHA,
    random_state: int = SEED,
) -> dict[str, Any]:
    """Choose a signal regime using a label-blind family-wise null test."""

    if (
        isinstance(n_permutations, (bool, np.bool_))
        or not isinstance(n_permutations, (int, np.integer))
        or int(n_permutations) < 99
    ):
        raise ValueError("n_permutations must be an integer of at least 99.")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1).")

    intrinsic = np.asarray(scores, dtype=float).ravel()
    observed = _signal_regime_statistics(
        propagation,
        intrinsic,
        tail_fraction=tail_fraction,
        min_tail_size=min_tail_size,
    )

    rng = np.random.default_rng(random_state)
    null_statistics = np.empty(
        (int(n_permutations), len(SIGNAL_REGIME_NAMES)),
        dtype=float,
    )
    for permutation_index in range(int(n_permutations)):
        null_statistics[permutation_index] = _signal_regime_statistics(
            propagation,
            rng.permutation(intrinsic),
            tail_fraction=tail_fraction,
            min_tail_size=min_tail_size,
        )

    null_mean = null_statistics.mean(axis=0)
    null_std = null_statistics.std(axis=0, ddof=1)
    safe_null_std = np.where(
        null_std > np.finfo(float).eps,
        null_std,
        np.inf,
    )
    effect_z = (observed - null_mean) / safe_null_std

    raw_p = (
        1
        + np.sum(
            null_statistics >= observed[None, :],
            axis=0,
        )
    ) / (int(n_permutations) + 1)

    # The maximum standardized null statistic controls false selection across
    # all three regime hypotheses in one family.
    standardized_null = (
        null_statistics - null_mean
    ) / safe_null_std
    max_null = np.max(standardized_null, axis=1)
    familywise_p = np.asarray(
        [
            (
                1
                + np.sum(max_null >= candidate_effect)
            )
            / (int(n_permutations) + 1)
            for candidate_effect in effect_z
        ],
        dtype=float,
    )
    passes = (effect_z > 0) & (familywise_p <= alpha)

    evidence = [
        {
            "regime": regime,
            "observed_statistic": float(observed[index]),
            "null_mean": float(null_mean[index]),
            "null_std": float(null_std[index]),
            "effect_z": float(effect_z[index]),
            "raw_p": float(raw_p[index]),
            "familywise_p": float(familywise_p[index]),
            "passes": bool(passes[index]),
        }
        for index, regime in enumerate(SIGNAL_REGIME_NAMES)
    ]

    if np.any(passes):
        eligible = np.flatnonzero(passes)
        winner_index = int(eligible[np.argmax(effect_z[eligible])])
        regime = SIGNAL_REGIME_NAMES[winner_index]
    else:
        winner_index = None
        regime = "No useful organization"

    return {
        "regime": regime,
        "winner_index": winner_index,
        "evidence": evidence,
        "n_permutations": int(n_permutations),
        "tail_fraction": float(tail_fraction),
        "min_tail_size": int(min_tail_size),
        "alpha": float(alpha),
        "random_state": int(random_state),
    }


def apply_matched_amplification(
    scores: np.ndarray,
    channels: dict[str, np.ndarray],
    regime: str,
    *,
    alpha: float = SIGNAL_AMPLIFICATION_ALPHA,
) -> np.ndarray:
    """Apply at most one score transform matched to the diagnosed regime."""

    intrinsic = np.asarray(scores, dtype=float).ravel()
    if not 0 <= alpha <= 1:
        raise ValueError("Amplification alpha must be in [0, 1].")

    if regime == "Neighborhood-supported":
        transformed = (
            alpha * intrinsic
            + (1.0 - alpha)
            * np.asarray(channels["neighbor_support"], dtype=float).ravel()
        )
    elif regime == "Locally Contrastive":
        transformed = np.asarray(
            channels["local_contrast"],
            dtype=float,
        ).ravel()
    elif regime == "Intermediate-scale":
        transformed = np.asarray(
            channels["pocket"],
            dtype=float,
        ).ravel()
    elif regime == "No useful organization":
        transformed = intrinsic.copy()
    else:
        raise ValueError(f"Unknown signal regime: {regime}")

    if transformed.shape != intrinsic.shape or not np.isfinite(
        transformed
    ).all():
        raise ValueError("Matched score transform is not aligned and finite.")
    return transformed


def _representation_key(
    representation: str,
    hypothesis: str | None,
    representation_seed: int | None,
) -> str:
    key = representation
    if hypothesis is not None:
        key = f"{key}::{hypothesis}"
    if representation_seed is not None:
        key = f"{key}::rep_seed={int(representation_seed)}"
    return key


def _method_key(
    method: str,
    hypothesis: str | None,
    representation_seed: int | None,
    scorer_seed: int | None,
) -> str:
    key = method
    if hypothesis is not None:
        key = f"{key}::{hypothesis}"
    if representation_seed is not None:
        key = f"{key}::rep_seed={int(representation_seed)}"
    if scorer_seed is not None and scorer_seed != representation_seed:
        key = f"{key}::score_seed={int(scorer_seed)}"
    elif scorer_seed is not None and representation_seed is None:
        key = f"{key}::score_seed={int(scorer_seed)}"
    return key


def _method_metrics(
    method: str,
    scores: np.ndarray,
    labels: np.ndarray | None,
    hypothesis: str | None,
    seed: int | None = None,
    *,
    representation_key: str | None = None,
    representation_method: str | None = None,
    scorer: str | None = None,
    representation_seed: int | None = None,
    scorer_seed: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "method": method,
        "hypothesis": hypothesis,
        "seed": seed,
        "representation_key": representation_key,
        "representation": representation_method,
        "scorer": scorer,
        "representation_seed": representation_seed,
        "scorer_seed": scorer_seed,
        "status": "completed",
        "average_precision": None,
        "reviews_to_first_malicious": None,
    }
    for budget in (25, 50, 100, 250):
        row[f"found_at_{budget}"] = None
        row[f"recall_at_{budget}"] = None
        row[f"precision_at_{budget}"] = None

    if labels is None:
        return row

    y = (np.asarray(labels) == "malicious").astype(int)
    if y.sum() == 0:
        return row

    scores = np.asarray(scores, dtype=float)
    order = np.argsort(scores)[::-1]
    ranked = y[order]
    positions = np.flatnonzero(ranked == 1)
    row["average_precision"] = float(average_precision_score(y, scores))
    row["reviews_to_first_malicious"] = (
        int(positions[0] + 1) if len(positions) else None
    )
    for budget in (25, 50, 100, 250):
        top = min(budget, len(ranked))
        found = int(ranked[:top].sum())
        row[f"found_at_{budget}"] = found
        row[f"recall_at_{budget}"] = float(found / y.sum())
        row[f"precision_at_{budget}"] = float(found / top) if top else None
    return row


def _embedding_2d(matrix: np.ndarray) -> np.ndarray:
    """Project one method representation to stable 2D UMAP coordinates."""
    matrix = np.asarray(matrix, dtype=float)
    if len(matrix) == 0:
        return np.empty((0, 2), dtype=float)
    if len(matrix) == 1:
        return np.zeros((1, 2), dtype=float)
    if matrix.ndim == 1:
        matrix = matrix[:, None]
    if matrix.shape[1] == 1:
        return np.column_stack([matrix[:, 0], np.zeros(len(matrix))])
    matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
    try:
        return UMAP(
            n_components=2,
            n_neighbors=min(15, len(matrix) - 1),
            min_dist=0.1,
            metric="euclidean",
            init="random",
            random_state=SEED,
            n_jobs=1,
            low_memory=True,
        ).fit_transform(matrix)
    except Exception:
        # A tiny or degenerate representation should not fail the method run.
        return PCA(n_components=2, random_state=SEED).fit_transform(matrix)


def _signal_metric_values(
    method: str,
    scores: np.ndarray,
    labels: np.ndarray,
    hypothesis: str | None,
    seed: int | None,
) -> dict[str, Any]:
    """Return only evaluation values from the existing ranking contract."""

    metrics = _method_metrics(
        method,
        scores,
        labels,
        hypothesis,
        seed,
    )
    metadata = {
        "method",
        "hypothesis",
        "seed",
        "representation_key",
        "representation",
        "scorer",
        "representation_seed",
        "scorer_seed",
        "status",
    }
    return {
        key: value
        for key, value in metrics.items()
        if key not in metadata
    }


def _descending_min_ranks(scores: np.ndarray) -> np.ndarray:
    """Return one-based descending ranks, giving tied scores the minimum rank."""

    return (
        pd.Series(np.asarray(scores, dtype=float))
        .rank(ascending=False, method="min")
        .to_numpy(dtype=np.int64)
    )


def _add_signal_artifacts(
    payload: dict[str, Any],
    *,
    method_key: str,
    method: str,
    hypothesis: str | None,
    seed: int | None,
    representation_key: str,
    representation_method: str,
    scorer: str,
    representation_seed: int | None,
    scorer_seed: int | None,
    representation: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray | None,
) -> None:
    """Diagnose and serialize signal structure for one method representation."""

    config = payload["signal_config"]
    _, propagation = build_session_knn_operator(
        representation,
        k=int(config["k"]),
    )
    channels = compute_signal_diagnostic_channels(
        propagation,
        scores,
    )
    diagnosis = pick_signal_regime(
        propagation,
        scores,
        n_permutations=int(config["n_permutations"]),
        tail_fraction=float(config["tail_fraction"]),
        min_tail_size=int(config["min_tail_size"]),
        alpha=float(config["alpha"]),
        random_state=int(config["random_state"]),
    )
    matched_scores = apply_matched_amplification(
        scores,
        channels,
        diagnosis["regime"],
        alpha=float(config["amplification_alpha"]),
    )

    intrinsic_ranks = _descending_min_ranks(scores)
    matched_ranks = _descending_min_ranks(matched_scores)
    rank_gain = intrinsic_ranks - matched_ranks

    if labels is None:
        evaluation = {
            "labels_available": False,
            "intrinsic": None,
            "matched": None,
        }
    else:
        evaluation = {
            "labels_available": True,
            "intrinsic": _signal_metric_values(
                method,
                scores,
                labels,
                hypothesis,
                seed,
            ),
            "matched": _signal_metric_values(
                method,
                matched_scores,
                labels,
                hypothesis,
                seed,
            ),
        }

    payload["signal_results"].append(
        {
            "method_key": method_key,
            "method": method,
            "hypothesis": hypothesis,
            "seed": seed,
            "representation_key": representation_key,
            "representation": representation_method,
            "scorer": scorer,
            "representation_seed": representation_seed,
            "scorer_seed": scorer_seed,
            "status": "completed",
            "regime": diagnosis["regime"],
            "winner_index": diagnosis["winner_index"],
            "evidence": diagnosis["evidence"],
            "evaluation": evaluation,
        }
    )

    for session_id in range(len(scores)):
        label = (
            str(labels[session_id])
            if labels is not None
            else "unknown"
        )
        payload["signal_scores"].append(
            {
                "method_key": method_key,
                "method": method,
                "hypothesis": hypothesis,
                "seed": seed,
                "representation_key": representation_key,
                "representation": representation_method,
                "scorer": scorer,
                "representation_seed": representation_seed,
                "scorer_seed": scorer_seed,
                "session_id": int(session_id),
                "label": label,
                "intrinsic": float(channels["intrinsic"][session_id]),
                "neighbor_support": float(
                    channels["neighbor_support"][session_id]
                ),
                "second_hop_support": float(
                    channels["second_hop_support"][session_id]
                ),
                "local_contrast": float(
                    channels["local_contrast"][session_id]
                ),
                "local_contrast_magnitude": float(
                    channels["local_contrast_magnitude"][session_id]
                ),
                "pocket": float(channels["pocket"][session_id]),
                "supported_candidate": float(
                    channels["supported_candidate"][session_id]
                ),
                "matched_score": float(matched_scores[session_id]),
                "intrinsic_rank": int(intrinsic_ranks[session_id]),
                "matched_rank": int(matched_ranks[session_id]),
                "rank_gain": int(rank_gain[session_id]),
            }
        )


def _add_method_artifacts(
    payload: dict[str, Any],
    method: str,
    hypothesis: str | None,
    scores: np.ndarray,
    representation: np.ndarray,
    labels: np.ndarray | None,
    seed: int | None = None,
    *,
    representation_key: str | None = None,
    representation_method: str | None = None,
    scorer: str | None = None,
    representation_seed: int | None = None,
    scorer_seed: int | None = None,
    coordinates: np.ndarray | None = None,
    signal_eligible: bool = True,
) -> None:
    values = np.asarray(representation, dtype=float)
    score_values = np.asarray(scores, dtype=float).ravel()
    if values.ndim != 2:
        raise ValueError("A method representation must be a 2D matrix.")
    if len(values) != len(score_values):
        raise ValueError("Representation and scores are not session-aligned.")
    if len(values) != int(payload["run_manifest"]["sessions"]):
        raise ValueError("Method output does not match canonical sessions.")
    if not np.isfinite(values).all() or not np.isfinite(score_values).all():
        raise ValueError("Method representation and scores must be finite.")
    if labels is not None and len(labels) != len(values):
        raise ValueError("Method output and labels are not session-aligned.")

    representation_method = representation_method or method
    scorer = scorer or "native"
    representation_key = representation_key or _representation_key(
        representation_method,
        hypothesis,
        representation_seed,
    )
    key = _method_key(
        method,
        hypothesis,
        representation_seed,
        scorer_seed,
    )
    metric_row = _method_metrics(
        method,
        score_values,
        labels,
        hypothesis,
        seed,
        representation_key=representation_key,
        representation_method=representation_method,
        scorer=scorer,
        representation_seed=representation_seed,
        scorer_seed=scorer_seed,
    )
    metric_row["method_key"] = key
    payload["method_results"].append(metric_row)
    for session_id, score in enumerate(score_values):
        label = str(labels[session_id]) if labels is not None else "unknown"
        payload["session_scores"].append(
            {
                "method_key": key,
                "method": method,
                "hypothesis": hypothesis,
                "seed": seed,
                "representation_key": representation_key,
                "representation": representation_method,
                "scorer": scorer,
                "representation_seed": representation_seed,
                "scorer_seed": scorer_seed,
                "session_id": int(session_id),
                "score": float(score),
                "label": label,
            }
        )

    if payload["run_manifest"].get("include_coordinates", True):
        if coordinates is None:
            coordinates = _embedding_2d(values)
        coordinates = np.asarray(coordinates, dtype=float)
        if coordinates.shape != (len(values), 2) or not np.isfinite(
            coordinates
        ).all():
            raise ValueError(
                "Representation coordinates are not aligned and finite."
            )
        for session_id, coordinate in enumerate(coordinates):
            label = (
                str(labels[session_id]) if labels is not None else "unknown"
            )
            payload["embeddings"].append(
                {
                    "method_key": key,
                    "method": method,
                    "hypothesis": hypothesis,
                    "seed": seed,
                    "representation_key": representation_key,
                    "representation": representation_method,
                    "scorer": scorer,
                    "representation_seed": representation_seed,
                    "scorer_seed": scorer_seed,
                    "session_id": int(session_id),
                    "x": float(coordinate[0]),
                    "y": float(coordinate[1]),
                    "label": label,
                }
            )

    # A random score baseline is not a representation-plus-kNN method. Building
    # a graph from its one-dimensional random scores would manufacture
    # neighborhood support, so it is deliberately excluded from diagnosis.
    signal_allowlist = payload["run_manifest"].get(
        "signal_representation_allowlist"
    )
    if (
        method == "random_baseline"
        or not signal_eligible
        or not payload["run_manifest"].get("include_signal", True)
        or (
            signal_allowlist is not None
            and representation_method not in signal_allowlist
        )
    ):
        return

    try:
        _add_signal_artifacts(
            payload,
            method_key=key,
            method=method,
            hypothesis=hypothesis,
            seed=seed,
            representation_key=representation_key,
            representation_method=representation_method,
            scorer=scorer,
            representation_seed=representation_seed,
            scorer_seed=scorer_seed,
            representation=values,
            scores=score_values,
            labels=labels,
        )
    except Exception as error:
        # Signal diagnosis is a downstream interpretation layer. A degenerate
        # or tiny representation must not erase an otherwise valid method run.
        payload["signal_results"].append(
            {
                "method_key": key,
                "method": method,
                "hypothesis": hypothesis,
                "seed": seed,
                "representation_key": representation_key,
                "representation": representation_method,
                "scorer": scorer,
                "representation_seed": representation_seed,
                "scorer_seed": scorer_seed,
                "status": "unavailable",
                "regime": None,
                "winner_index": None,
                "evidence": [],
                "evaluation": {
                    "labels_available": labels is not None,
                    "intrinsic": None,
                    "matched": None,
                },
                "error": f"{type(error).__name__}: {error}",
            }
        )


def _add_representation_result(
    payload: dict[str, Any],
    *,
    representation_key: str,
    representation_method: str,
    hypothesis: str | None,
    representation_seed: int | None,
    representation: np.ndarray,
    labels: np.ndarray | None,
    dimension_names: list[str] | None = None,
) -> None:
    if any(
        record["representation_key"] == representation_key
        for record in payload["representation_results"]
    ):
        return

    values = np.asarray(representation, dtype=float)
    if values.ndim != 2:
        raise ValueError("A representation must be a 2D matrix.")
    if len(values) != int(payload["run_manifest"]["sessions"]):
        raise ValueError("Representation does not match canonical sessions.")
    if not np.isfinite(values).all():
        raise ValueError("Representation must contain finite values.")
    if dimension_names is not None and len(dimension_names) != values.shape[1]:
        raise ValueError("Representation dimension names are not aligned.")

    evaluation_started = time.perf_counter()
    evaluation = evaluate_representation(
        values,
        labels,
        k=int(payload["run_manifest"]["k"]),
        n_permutations=int(payload["signal_config"]["n_permutations"]),
        random_state=SEED,
    )
    evaluation_seconds = time.perf_counter() - evaluation_started
    payload["representation_results"].append(
        {
            "representation_key": representation_key,
            "representation": representation_method,
            "hypothesis": hypothesis,
            "representation_seed": representation_seed,
            "dimension_names": dimension_names,
            **evaluation,
        }
    )
    payload["_representation_matrices"][representation_key] = values.astype(
        np.float32, copy=True
    )
    _record_runtime(
        payload,
        stage="representation_evaluation",
        seconds=evaluation_seconds,
        representation=representation_method,
        hypothesis=hypothesis,
        representation_seed=representation_seed,
    )


def _add_failed_representation_result(
    payload: dict[str, Any],
    *,
    representation_key: str,
    representation_method: str,
    hypothesis: str | None,
    representation_seed: int | None,
    reason: str,
) -> None:
    """Declare a representation that could not be constructed."""

    if any(
        record["representation_key"] == representation_key
        for record in payload["representation_results"]
    ):
        return
    payload["representation_results"].append(
        {
            "representation_key": representation_key,
            "representation": representation_method,
            "hypothesis": hypothesis,
            "representation_seed": representation_seed,
            "dimension_names": None,
            "status": "failed",
            "reason": reason,
            "labels_available": payload["run_manifest"]["mode"]
            == "development",
            "n_sessions": int(payload["run_manifest"]["sessions"]),
            "n_dimensions": None,
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
            "random_state": None,
        }
    )


def _finalize_representation_stability(payload: dict[str, Any]) -> None:
    """Compare stochastic replicas without serializing high-dimensional X."""

    matrices = payload.pop("_representation_matrices", {})
    groups: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for record in payload["representation_results"]:
        if record.get("representation_seed") is None:
            continue
        group_key = (record["representation"], record.get("hypothesis"))
        groups.setdefault(group_key, []).append(record)

    for (representation_method, hypothesis), records in groups.items():
        ordered = sorted(records, key=lambda record: record["representation_seed"])
        for first, second in combinations(ordered, 2):
            first_matrix = matrices.get(first["representation_key"])
            second_matrix = matrices.get(second["representation_key"])
            if first_matrix is None or second_matrix is None:
                continue
            try:
                stability = representation_stability(
                    first_matrix,
                    second_matrix,
                    k=int(payload["run_manifest"]["k"]),
                    random_state=SEED,
                )
            except Exception as error:
                stability = {
                    "status": "unavailable",
                    "reason": f"{type(error).__name__}: {error}",
                    "n_sessions": int(len(first_matrix)),
                    "distance_rank_correlation": None,
                    "mean_neighbor_jaccard": None,
                    "effective_k": None,
                }
            payload["representation_stability"].append(
                {
                    "representation": representation_method,
                    "hypothesis": hypothesis,
                    "first_representation_key": first["representation_key"],
                    "second_representation_key": second["representation_key"],
                    "first_seed": int(first["representation_seed"]),
                    "second_seed": int(second["representation_seed"]),
                    **stability,
                }
            )


def _unavailable_scorer_result(
    payload: dict[str, Any],
    *,
    method: str,
    hypothesis: str | None,
    representation_key: str,
    representation_method: str,
    scorer: str,
    representation_seed: int | None,
    scorer_seed: int | None,
    status: str,
    reason: str,
) -> None:
    method_key = _method_key(
        method,
        hypothesis,
        representation_seed,
        scorer_seed,
    )
    if any(
        record.get("method_key") == method_key
        for record in payload["method_results"]
    ):
        return
    row = _method_metrics(
        method,
        np.zeros(int(payload["run_manifest"]["sessions"]), dtype=float),
        None,
        hypothesis,
        representation_seed if representation_seed is not None else scorer_seed,
        representation_key=representation_key,
        representation_method=representation_method,
        scorer=scorer,
        representation_seed=representation_seed,
        scorer_seed=scorer_seed,
    )
    row["status"] = status
    row["error"] = reason
    row["method_key"] = method_key
    payload["method_results"].append(row)


def _add_failed_scoring_suite(
    payload: dict[str, Any],
    *,
    representation_method: str,
    method_prefix: str,
    hypothesis: str | None,
    scorer_seeds: tuple[int, ...],
    error: Exception,
    representation_seed: int | None = None,
    scorer_allowlist: frozenset[str] | None = None,
) -> None:
    """Declare every planned scorer when its representation cannot be built."""

    reason = f"{type(error).__name__}: {error}"
    representation_key = _representation_key(
        representation_method,
        hypothesis,
        representation_seed,
    )
    _add_failed_representation_result(
        payload,
        representation_key=representation_key,
        representation_method=representation_method,
        hypothesis=hypothesis,
        representation_seed=representation_seed,
        reason=reason,
    )
    active_scorers = scorer_allowlist or SUPPORTED_COMMON_SCORERS
    if "knn_mean_distance" in active_scorers:
        _unavailable_scorer_result(
            payload,
            method=f"{method_prefix}_knn",
            hypothesis=hypothesis,
            representation_key=representation_key,
            representation_method=representation_method,
            scorer="knn_mean_distance",
            representation_seed=representation_seed,
            scorer_seed=None,
            status="failed",
            reason=reason,
        )
    active_scorer_seeds = (
        (int(representation_seed),)
        if representation_seed is not None
        else tuple(int(seed) for seed in scorer_seeds)
    )
    if "isolation_forest" in active_scorers:
        for scorer_seed in active_scorer_seeds:
            _unavailable_scorer_result(
                payload,
                method=f"{method_prefix}_isolation_forest",
                hypothesis=hypothesis,
                representation_key=representation_key,
                representation_method=representation_method,
                scorer="isolation_forest",
                representation_seed=representation_seed,
                scorer_seed=scorer_seed,
                status="failed",
                reason=reason,
            )
    if "hdbscan_rare_cluster" in active_scorers:
        _unavailable_scorer_result(
            payload,
            method=f"{method_prefix}_rare_cluster",
            hypothesis=hypothesis,
            representation_key=representation_key,
            representation_method=representation_method,
            scorer="hdbscan_rare_cluster",
            representation_seed=representation_seed,
            scorer_seed=None,
            status="failed",
            reason=reason,
        )


def _add_failed_direct_method(
    payload: dict[str, Any],
    *,
    representation_method: str,
    method: str,
    hypothesis: str | None,
    representation_seed: int,
    scorer: str,
    error: Exception,
) -> None:
    """Declare a failed method whose scorer is native to its representation."""

    reason = f"{type(error).__name__}: {error}"
    representation_key = _representation_key(
        representation_method,
        hypothesis,
        representation_seed,
    )
    _add_failed_representation_result(
        payload,
        representation_key=representation_key,
        representation_method=representation_method,
        hypothesis=hypothesis,
        representation_seed=representation_seed,
        reason=reason,
    )
    _unavailable_scorer_result(
        payload,
        method=method,
        hypothesis=hypothesis,
        representation_key=representation_key,
        representation_method=representation_method,
        scorer=scorer,
        representation_seed=representation_seed,
        scorer_seed=None,
        status="failed",
        reason=reason,
    )


def _add_rare_cluster_scorer(
    payload: dict[str, Any],
    *,
    representation_key: str,
    representation_method: str,
    method_prefix: str,
    hypothesis: str | None,
    representation_seed: int | None,
    values: np.ndarray,
    coordinates: np.ndarray,
    labels: np.ndarray | None,
) -> None:
    """Run the deterministic population scorer once for one representation."""

    method = f"{method_prefix}_rare_cluster"
    scorer_started = time.perf_counter()
    try:
        scores, cluster_ids, diagnostics = rare_cluster_anomaly_scores(values)
        scorer_seconds = time.perf_counter() - scorer_started
        method_key = _method_key(
            method,
            hypothesis,
            representation_seed,
            None,
        )
        payload["scorer_diagnostics"].append(
            {
                "method_key": method_key,
                "representation_key": representation_key,
                "representation": representation_method,
                "scorer": "hdbscan_rare_cluster",
                "hypothesis": hypothesis,
                "representation_seed": representation_seed,
                "scorer_seed": None,
                "runtime_seconds": scorer_seconds,
                **diagnostics,
            }
        )
        _record_runtime(
            payload,
            stage="scorer",
            seconds=scorer_seconds,
            status=str(diagnostics["status"]),
            representation=representation_method,
            scorer="hdbscan_rare_cluster",
            hypothesis=hypothesis,
            representation_seed=representation_seed,
        )
        if diagnostics["status"] == "completed":
            artifact_started = time.perf_counter()
            _add_method_artifacts(
                payload,
                method,
                hypothesis,
                scores,
                values,
                labels,
                seed=representation_seed,
                representation_key=representation_key,
                representation_method=representation_method,
                scorer="hdbscan_rare_cluster",
                representation_seed=representation_seed,
                scorer_seed=None,
                coordinates=coordinates,
            )
            _record_runtime(
                payload,
                stage="method_artifacts_and_signal",
                seconds=time.perf_counter() - artifact_started,
                representation=representation_method,
                scorer="hdbscan_rare_cluster",
                hypothesis=hypothesis,
                representation_seed=representation_seed,
            )
            for session_id, (cluster_id, cluster_score) in enumerate(
                zip(cluster_ids, scores)
            ):
                payload["score_components"].append(
                    {
                        "method_key": method_key,
                        "representation_key": representation_key,
                        "scorer": "hdbscan_rare_cluster",
                        "session_id": int(session_id),
                        "cluster_id": int(cluster_id),
                        "is_noise": bool(cluster_id < 0),
                        "cluster_score": float(cluster_score),
                    }
                )
        else:
            _unavailable_scorer_result(
                payload,
                method=method,
                hypothesis=hypothesis,
                representation_key=representation_key,
                representation_method=representation_method,
                scorer="hdbscan_rare_cluster",
                representation_seed=representation_seed,
                scorer_seed=None,
                status=str(diagnostics["status"]),
                reason=str(diagnostics["reason"]),
            )
    except Exception as error:
        _record_runtime(
            payload,
            stage="scorer",
            seconds=time.perf_counter() - scorer_started,
            status="failed",
            representation=representation_method,
            scorer="hdbscan_rare_cluster",
            hypothesis=hypothesis,
            representation_seed=representation_seed,
        )
        _unavailable_scorer_result(
            payload,
            method=method,
            hypothesis=hypothesis,
            representation_key=representation_key,
            representation_method=representation_method,
            scorer="hdbscan_rare_cluster",
            representation_seed=representation_seed,
            scorer_seed=None,
            status="failed",
            reason=f"{type(error).__name__}: {error}",
        )


def _add_scoring_suite(
    payload: dict[str, Any],
    *,
    representation_method: str,
    method_prefix: str,
    hypothesis: str | None,
    representation: np.ndarray,
    labels: np.ndarray | None,
    k: int,
    scorer_seeds: tuple[int, ...],
    representation_seed: int | None = None,
    dimension_names: list[str] | None = None,
    scorer_allowlist: frozenset[str] | None = None,
) -> None:
    """Register one X once, then apply the bounded common scorer battery."""

    values = np.asarray(representation, dtype=float)
    representation_key = _representation_key(
        representation_method,
        hypothesis,
        representation_seed,
    )
    _add_representation_result(
        payload,
        representation_key=representation_key,
        representation_method=representation_method,
        hypothesis=hypothesis,
        representation_seed=representation_seed,
        representation=values,
        labels=labels,
        dimension_names=dimension_names,
    )
    coordinates = None
    if payload["run_manifest"].get("include_coordinates", True):
        coordinate_started = time.perf_counter()
        coordinates = _embedding_2d(values)
        _record_runtime(
            payload,
            stage="coordinate_projection",
            seconds=time.perf_counter() - coordinate_started,
            representation=representation_method,
            hypothesis=hypothesis,
            representation_seed=representation_seed,
        )

    active_scorers = scorer_allowlist or SUPPORTED_COMMON_SCORERS
    if "knn_mean_distance" in active_scorers:
        scorer_started = time.perf_counter()
        knn_scores = knn_anomaly_scores(values, k=k)
        scorer_seconds = time.perf_counter() - scorer_started
        _record_runtime(
            payload,
            stage="scorer",
            seconds=scorer_seconds,
            representation=representation_method,
            scorer="knn_mean_distance",
            hypothesis=hypothesis,
            representation_seed=representation_seed,
        )
        artifact_started = time.perf_counter()
        _add_method_artifacts(
            payload,
            f"{method_prefix}_knn",
            hypothesis,
            knn_scores,
            values,
            labels,
            seed=representation_seed,
            representation_key=representation_key,
            representation_method=representation_method,
            scorer="knn_mean_distance",
            representation_seed=representation_seed,
            scorer_seed=None,
            coordinates=coordinates,
        )
        _record_runtime(
            payload,
            stage="method_artifacts_and_signal",
            seconds=time.perf_counter() - artifact_started,
            representation=representation_method,
            scorer="knn_mean_distance",
            hypothesis=hypothesis,
            representation_seed=representation_seed,
        )

    active_scorer_seeds = (
        (int(representation_seed),)
        if representation_seed is not None
        else tuple(int(seed) for seed in scorer_seeds)
    )
    for scorer_seed in (
        active_scorer_seeds if "isolation_forest" in active_scorers else ()
    ):
        isolation_method = f"{method_prefix}_isolation_forest"
        scorer_started = time.perf_counter()
        try:
            isolation_scores, isolation_diagnostics = (
                isolation_forest_anomaly_scores(
                    values,
                    random_state=scorer_seed,
                )
            )
            scorer_seconds = time.perf_counter() - scorer_started
            isolation_key = _method_key(
                isolation_method,
                hypothesis,
                representation_seed,
                scorer_seed,
            )
            payload["scorer_diagnostics"].append(
                {
                    "method_key": isolation_key,
                    "representation_key": representation_key,
                    "representation": representation_method,
                    "scorer": "isolation_forest",
                    "hypothesis": hypothesis,
                    "representation_seed": representation_seed,
                    "scorer_seed": scorer_seed,
                    "runtime_seconds": scorer_seconds,
                    **isolation_diagnostics,
                }
            )
            _record_runtime(
                payload,
                stage="scorer",
                seconds=scorer_seconds,
                status=str(isolation_diagnostics["status"]),
                representation=representation_method,
                scorer="isolation_forest",
                hypothesis=hypothesis,
                representation_seed=representation_seed,
                scorer_seed=scorer_seed,
            )
            if isolation_diagnostics["status"] == "completed":
                artifact_started = time.perf_counter()
                _add_method_artifacts(
                    payload,
                    isolation_method,
                    hypothesis,
                    isolation_scores,
                    values,
                    labels,
                    seed=scorer_seed,
                    representation_key=representation_key,
                    representation_method=representation_method,
                    scorer="isolation_forest",
                    representation_seed=representation_seed,
                    scorer_seed=scorer_seed,
                    coordinates=coordinates,
                )
                _record_runtime(
                    payload,
                    stage="method_artifacts_and_signal",
                    seconds=time.perf_counter() - artifact_started,
                    representation=representation_method,
                    scorer="isolation_forest",
                    hypothesis=hypothesis,
                    representation_seed=representation_seed,
                    scorer_seed=scorer_seed,
                )
            else:
                _unavailable_scorer_result(
                    payload,
                    method=isolation_method,
                    hypothesis=hypothesis,
                    representation_key=representation_key,
                    representation_method=representation_method,
                    scorer="isolation_forest",
                    representation_seed=representation_seed,
                    scorer_seed=scorer_seed,
                    status=str(isolation_diagnostics["status"]),
                    reason=str(isolation_diagnostics["reason"]),
                )
        except Exception as error:
            _record_runtime(
                payload,
                stage="scorer",
                seconds=time.perf_counter() - scorer_started,
                status="failed",
                representation=representation_method,
                scorer="isolation_forest",
                hypothesis=hypothesis,
                representation_seed=representation_seed,
                scorer_seed=scorer_seed,
            )
            _unavailable_scorer_result(
                payload,
                method=isolation_method,
                hypothesis=hypothesis,
                representation_key=representation_key,
                representation_method=representation_method,
                scorer="isolation_forest",
                representation_seed=representation_seed,
                scorer_seed=scorer_seed,
                status="failed",
                reason=f"{type(error).__name__}: {error}",
            )

    if "hdbscan_rare_cluster" in active_scorers:
        _add_rare_cluster_scorer(
            payload,
            representation_key=representation_key,
            representation_method=representation_method,
            method_prefix=method_prefix,
            hypothesis=hypothesis,
            representation_seed=representation_seed,
            values=values,
            coordinates=coordinates,
            labels=labels,
        )


def _safe_identifier(value: Any) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized if normalized and normalized not in {"nan", "None", "<NA>"} else None


def _primary_endpoint(
    df: pd.DataFrame, relations: list[dict[str, Any]]
) -> tuple[str, str]:
    candidates: dict[tuple[str, str], int] = {}
    for relation in relations:
        for side in ("source", "target"):
            node_type = relation[f"{side}_node_type"]
            column = relation[f"{side}_column"]
            candidates[(node_type, column)] = candidates.get((node_type, column), 0) + 1

    if not candidates:
        raise ValueError("At least one graph relation endpoint is required.")

    scored = []
    for (node_type, column), uses in candidates.items():
        if column == "$row_id":
            non_null = len(df)
            unique = len(df)
        else:
            non_null = int(df[column].notna().sum())
            unique = int(df[column].nunique(dropna=True))
        coverage = non_null / max(len(df), 1)
        uniqueness = unique / max(non_null, 1)
        scored.append(
            (
                uniqueness >= 0.95,
                coverage,
                uses,
                uniqueness,
                node_type,
                column,
            )
        )
    _, _, _, _, node_type, column = max(scored)
    return node_type, column


def build_typed_graph(
    sessionized_df: pd.DataFrame,
    config: dict[str, Any],
) -> GraphBundle:
    relations = list(config.get("graph_relations", []))
    if not relations:
        raise ValueError("No graph relations were configured.")

    primary_node_type, primary_id_column = _primary_endpoint(
        sessionized_df, relations
    )

    endpoint_columns: dict[str, list[str]] = {}
    for relation in relations:
        for side in ("source", "target"):
            node_type = relation[f"{side}_node_type"]
            column = relation[f"{side}_column"]
            endpoint_columns.setdefault(node_type, [])
            if column not in endpoint_columns[node_type]:
                endpoint_columns[node_type].append(column)

    node_maps: dict[str, dict[str, int]] = {}
    for node_type, columns in endpoint_columns.items():
        mapping: dict[str, int] = {}
        for column in columns:
            if column == "$row_id":
                values = [f"row:{value}" for value in sessionized_df["_source_row"]]
            else:
                values = sessionized_df[column]
            for value in values:
                identifier = _safe_identifier(value)
                if identifier is not None and identifier not in mapping:
                    mapping[identifier] = len(mapping)
        node_maps[node_type] = mapping

    primary_map = node_maps[primary_node_type]
    row_primary_index = []
    for position, row in sessionized_df.iterrows():
        primary_value = (
            f"row:{row['_source_row']}"
            if primary_id_column == "$row_id"
            else row[primary_id_column]
        )
        identifier = _safe_identifier(primary_value)
        if identifier is None:
            identifier = f"__missing_primary__:{row['_source_row']}"
            primary_map[identifier] = len(primary_map)
        row_primary_index.append(primary_map[identifier])
    row_primary_index_array = np.asarray(row_primary_index, dtype=np.int64)

    data = HeteroData()
    for node_type, mapping in node_maps.items():
        data[node_type].x = torch.ones((len(mapping), 1), dtype=torch.float32)

    forward_edge_types: list[tuple[str, str, str]] = []
    relation_by_edge_type: dict[tuple[str, str, str], dict[str, Any]] = {}
    relation_manifest = []

    for relation in relations:
        relation_name = relation["relation_name"]
        source_type = relation["source_node_type"]
        target_type = relation["target_node_type"]
        source_column = relation["source_column"]
        target_column = relation["target_column"]
        source_map = node_maps[source_type]
        target_map = node_maps[target_type]
        pairs: list[tuple[int, int]] = []

        for position, row in sessionized_df.iterrows():
            source_value = (
                f"row:{row['_source_row']}"
                if source_column == "$row_id"
                else row[source_column]
            )
            target_value = (
                f"row:{row['_source_row']}"
                if target_column == "$row_id"
                else row[target_column]
            )
            source_id = _safe_identifier(source_value)
            target_id = _safe_identifier(target_value)
            if source_id is None or target_id is None:
                continue
            if source_id in source_map and target_id in target_map:
                pairs.append((source_map[source_id], target_map[target_id]))

        pairs = list(dict.fromkeys(pairs))
        if pairs:
            edge_index = torch.tensor(pairs, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)

        edge_type = (source_type, relation_name, target_type)
        data[edge_type].edge_index = edge_index
        forward_edge_types.append(edge_type)
        relation_by_edge_type[edge_type] = relation

        reverse_name = f"rev_{relation_name}"
        reverse_edge_type = (target_type, reverse_name, source_type)
        data[reverse_edge_type].edge_index = edge_index.flip(0)

        relation_manifest.append(
            {
                "relation": relation_name,
                "source_type": source_type,
                "target_type": target_type,
                "edges": int(edge_index.shape[1]),
                "row_coverage": float(len(pairs) / max(len(sessionized_df), 1)),
            }
        )

    all_primary_nodes = len(node_maps[primary_node_type])
    observed_primary_nodes = int(np.unique(row_primary_index_array).size)
    manifest = {
        "primary_node_type": primary_node_type,
        "primary_id_column": primary_id_column,
        "node_counts": {
            node_type: int(len(mapping)) for node_type, mapping in node_maps.items()
        },
        "observed_primary_nodes": observed_primary_nodes,
        "external_primary_nodes": int(all_primary_nodes - observed_primary_nodes),
        "relations": relation_manifest,
        "total_forward_edges": int(sum(row["edges"] for row in relation_manifest)),
    }
    return GraphBundle(
        data=data,
        node_maps=node_maps,
        primary_node_type=primary_node_type,
        primary_id_column=primary_id_column,
        row_primary_index=row_primary_index_array,
        forward_edge_types=forward_edge_types,
        relation_by_edge_type=relation_by_edge_type,
        manifest=manifest,
    )


def structural_session_representation(
    graph: GraphBundle,
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
) -> tuple[np.ndarray, list[str]]:
    primary_type = graph.primary_node_type
    n_primary = len(graph.node_maps[primary_type])
    node_features: list[np.ndarray] = []
    names: list[str] = []

    for edge_type in graph.forward_edge_types:
        relation = edge_type[1]
        edge_index = graph.data[edge_type].edge_index.cpu()
        if edge_type[0] == primary_type:
            degree = (
                torch.bincount(edge_index[0], minlength=n_primary)
                .numpy()
                .astype(float)
            )
            node_features.append(np.log1p(degree))
            names.append(f"{relation}__out_degree")
        if edge_type[2] == primary_type:
            degree = (
                torch.bincount(edge_index[1], minlength=n_primary)
                .numpy()
                .astype(float)
            )
            node_features.append(np.log1p(degree))
            names.append(f"{relation}__in_degree")

    if not node_features:
        raise ValueError("No configured relation is incident to the primary node type.")

    primary_matrix = np.column_stack(node_features).astype(np.float32)
    row_matrix = primary_matrix[graph.row_primary_index]
    session_matrix, _ = _pool_rows(row_matrix, sessionized_df, sessions)
    return session_matrix, names


def _homogeneous_projection(
    graph: GraphBundle,
) -> tuple[list[list[int]], dict[str, int]]:
    offsets: dict[str, int] = {}
    total = 0
    for node_type, mapping in graph.node_maps.items():
        offsets[node_type] = total
        total += len(mapping)

    adjacency: list[set[int]] = [set() for _ in range(total)]
    for edge_type in graph.forward_edge_types:
        edge_index = graph.data[edge_type].edge_index.cpu().numpy()
        source_offset = offsets[edge_type[0]]
        target_offset = offsets[edge_type[2]]
        for source, target in edge_index.T:
            u = int(source + source_offset)
            v = int(target + target_offset)
            if u != v:
                adjacency[u].add(v)
                adjacency[v].add(u)
    return [sorted(neighbors) for neighbors in adjacency], offsets


def train_node2vec_p1q1(
    adjacency: list[list[int]],
    embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    walk_length: int = 10,
    walks_per_node: int = 2,
    context_window: int = 2,
    epochs: int = 3,
    max_pairs: int = DEFAULT_NODE2VEC_PAIRS,
    seed: int = SEED,
) -> np.ndarray:
    """Dependency-light Node2Vec training for p=q=1 (the DeepWalk special case)."""
    rng = np.random.default_rng(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    n_nodes = len(adjacency)
    pairs: list[tuple[int, int]] = []

    order = np.arange(n_nodes)
    for _ in range(walks_per_node):
        rng.shuffle(order)
        for start in order:
            walk = [int(start)]
            while len(walk) < walk_length and adjacency[walk[-1]]:
                walk.append(int(rng.choice(adjacency[walk[-1]])))
            for i, source in enumerate(walk):
                left = max(0, i - context_window)
                right = min(len(walk), i + context_window + 1)
                for j in range(left, right):
                    if i != j:
                        pairs.append((source, walk[j]))
                        if len(pairs) >= max_pairs:
                            break
                if len(pairs) >= max_pairs:
                    break
            if len(pairs) >= max_pairs:
                break
        if len(pairs) >= max_pairs:
            break

    if not pairs:
        return np.zeros((n_nodes, embedding_dim), dtype=np.float32)

    pair_tensor = torch.tensor(pairs, dtype=torch.long)
    source_embedding = nn.Embedding(n_nodes, embedding_dim)
    context_embedding = nn.Embedding(n_nodes, embedding_dim)
    nn.init.normal_(source_embedding.weight, std=0.1)
    nn.init.zeros_(context_embedding.weight)
    optimizer = torch.optim.Adam(
        list(source_embedding.parameters()) + list(context_embedding.parameters()),
        lr=0.02,
    )
    batch_size = 4096

    for _ in range(epochs):
        permutation = torch.randperm(len(pair_tensor))
        for start in range(0, len(pair_tensor), batch_size):
            batch = pair_tensor[permutation[start : start + batch_size]]
            source = batch[:, 0]
            target = batch[:, 1]
            negative = torch.randint(0, n_nodes, (len(batch), 2))
            source_vectors = source_embedding(source)
            positive_vectors = context_embedding(target)
            negative_vectors = context_embedding(negative)
            positive_score = (source_vectors * positive_vectors).sum(dim=1)
            negative_score = torch.einsum(
                "bd,bnd->bn", source_vectors, negative_vectors
            )
            loss = -(
                F.logsigmoid(positive_score).mean()
                + F.logsigmoid(-negative_score).mean()
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    return source_embedding.weight.detach().cpu().numpy().astype(np.float32)


def node2vec_session_representation(
    graph: GraphBundle,
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
    seed: int = SEED,
) -> np.ndarray:
    adjacency, offsets = _homogeneous_projection(graph)
    embeddings = train_node2vec_p1q1(adjacency, seed=seed)
    primary_offset = offsets[graph.primary_node_type]
    primary_indices = graph.row_primary_index + primary_offset
    row_embeddings = embeddings[primary_indices]
    session_matrix, _ = _pool_rows(row_embeddings, sessionized_df, sessions)
    return session_matrix


class DynamicHeteroGraphSAGE(nn.Module):
    def __init__(
        self,
        edge_types: list[tuple[str, str, str]],
        hidden_dim: int,
        output_dim: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.conv1 = HeteroConv(
            {
                edge_type: SAGEConv((-1, -1), hidden_dim)
                for edge_type in edge_types
            },
            aggr="sum",
        )
        self.conv2 = HeteroConv(
            {
                edge_type: SAGEConv((-1, -1), output_dim)
                for edge_type in edge_types
            },
            aggr="sum",
        )
        self.dropout = dropout

    def forward(
        self,
        x_dict: dict[str, torch.Tensor],
        edge_index_dict: dict[tuple[str, str, str], torch.Tensor],
    ) -> dict[str, torch.Tensor]:
        hidden = self.conv1(x_dict, edge_index_dict)
        hidden = {
            node_type: F.dropout(
                F.relu(features), p=self.dropout, training=self.training
            )
            for node_type, features in hidden.items()
        }
        return self.conv2(hidden, edge_index_dict)


class DynamicLinkDecoder(nn.Module):
    def __init__(
        self,
        relation_count: int,
        embedding_dim: int,
    ):
        super().__init__()
        self.decoders = nn.ModuleList(
            [
                nn.Bilinear(embedding_dim, embedding_dim, 1)
                for _ in range(relation_count)
            ]
        )

    def forward(
        self,
        relation_index: int,
        source_embeddings: torch.Tensor,
        target_embeddings: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        source = F.normalize(source_embeddings[edge_index[0]], dim=-1)
        target = F.normalize(target_embeddings[edge_index[1]], dim=-1)
        return self.decoders[relation_index](source, target).squeeze(-1)


def _graphsage_x_dict(
    graph: GraphBundle,
    row_features: np.ndarray,
) -> dict[str, torch.Tensor]:
    x_dict: dict[str, torch.Tensor] = {}
    primary_type = graph.primary_node_type
    for node_type, mapping in graph.node_maps.items():
        if node_type != primary_type:
            x_dict[node_type] = torch.ones((len(mapping), 1), dtype=torch.float32)
            continue

        dimension = row_features.shape[1]
        values = torch.zeros((len(mapping), dimension + 1), dtype=torch.float32)
        counts = torch.zeros(len(mapping), dtype=torch.float32)
        row_index = torch.as_tensor(graph.row_primary_index, dtype=torch.long)
        values[:, :-1].index_add_(
            0, row_index, torch.as_tensor(row_features, dtype=torch.float32)
        )
        counts.index_add_(0, row_index, torch.ones(len(row_index)))
        observed = counts > 0
        values[observed, :-1] = (
            values[observed, :-1] / counts[observed].unsqueeze(1)
        )
        values[observed, -1] = 1.0
        x_dict[node_type] = values
    return x_dict


def train_graphsage(
    graph: GraphBundle,
    row_features: np.ndarray,
    seed: int = SEED,
    epochs: int = DEFAULT_GRAPH_EPOCHS,
    hidden_dim: int = DEFAULT_EMBEDDING_DIM,
    output_dim: int = DEFAULT_EMBEDDING_DIM,
    patience: int | None = None,
    min_delta: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    x_dict = _graphsage_x_dict(graph, row_features)
    edge_index_dict = {
        edge_type: edge_index.cpu()
        for edge_type, edge_index in graph.data.edge_index_dict.items()
    }
    edge_types = list(edge_index_dict)
    encoder = DynamicHeteroGraphSAGE(
        edge_types=edge_types,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
    )
    decoder = DynamicLinkDecoder(len(graph.forward_edge_types), output_dim)

    encoder.eval()
    with torch.no_grad():
        initial = encoder(x_dict, edge_index_dict)
        random_primary = initial[graph.primary_node_type].detach().cpu().numpy()

    optimizer = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()),
        lr=0.002,
    )
    losses: list[float] = []
    best_loss = math.inf
    best_encoder_state = copy.deepcopy(encoder.state_dict())
    best_decoder_state = copy.deepcopy(decoder.state_dict())
    stale_epochs = 0

    for _ in range(epochs):
        encoder.train()
        decoder.train()
        embeddings = encoder(x_dict, edge_index_dict)
        relation_losses = []

        for relation_index, edge_type in enumerate(graph.forward_edge_types):
            full_edges = edge_index_dict[edge_type]
            if full_edges.shape[1] == 0:
                continue
            n_positive = min(
                int(full_edges.shape[1]), DEFAULT_MAX_POSITIVE_EDGES
            )
            selection = torch.randperm(full_edges.shape[1])[:n_positive]
            positive_edges = full_edges[:, selection]
            source_count = x_dict[edge_type[0]].shape[0]
            target_count = x_dict[edge_type[2]].shape[0]
            try:
                negative_edges = negative_sampling(
                    edge_index=full_edges,
                    num_nodes=(source_count, target_count),
                    num_neg_samples=n_positive,
                    method="sparse",
                )
            except Exception:
                negative_edges = torch.stack(
                    [
                        torch.randint(0, source_count, (n_positive,)),
                        torch.randint(0, target_count, (n_positive,)),
                    ]
                )
            if negative_edges.shape[1] == 0:
                continue

            positive_logits = decoder(
                relation_index,
                embeddings[edge_type[0]],
                embeddings[edge_type[2]],
                positive_edges,
            )
            negative_logits = decoder(
                relation_index,
                embeddings[edge_type[0]],
                embeddings[edge_type[2]],
                negative_edges,
            )
            relation_losses.append(
                F.binary_cross_entropy_with_logits(
                    positive_logits, torch.ones_like(positive_logits)
                )
                + F.binary_cross_entropy_with_logits(
                    negative_logits, torch.zeros_like(negative_logits)
                )
            )

        if not relation_losses:
            break
        loss = torch.stack(relation_losses).mean()
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(encoder.parameters()) + list(decoder.parameters()), 1.0
        )
        optimizer.step()
        loss_value = float(loss.detach())
        losses.append(loss_value)
        if loss_value < best_loss - float(min_delta):
            best_loss = loss_value
            best_encoder_state = copy.deepcopy(encoder.state_dict())
            best_decoder_state = copy.deepcopy(decoder.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if patience is not None and stale_epochs >= int(patience):
                break

    encoder.load_state_dict(best_encoder_state)
    decoder.load_state_dict(best_decoder_state)

    encoder.eval()
    with torch.no_grad():
        trained = encoder(x_dict, edge_index_dict)
        trained_primary = (
            trained[graph.primary_node_type].detach().cpu().numpy()
        )
    return random_primary, trained_primary, losses


class PrimaryAttributeDecoder(nn.Module):
    """Decode observed primary-node attributes from latent graph embeddings."""

    def __init__(self, embedding_dim: int, attribute_dim: int):
        super().__init__()
        self.linear = nn.Linear(embedding_dim, attribute_dim)

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        return self.linear(embeddings)


def _sample_relation_examples(
    edge_index_dict: dict[tuple[str, str, str], torch.Tensor],
    graph: GraphBundle,
    x_dict: dict[str, torch.Tensor],
    *,
    max_positive_edges: int = DEFAULT_MAX_POSITIVE_EDGES,
) -> list[tuple[torch.Tensor, torch.Tensor]]:
    """Sample fixed positive/negative relation examples for one comparison."""

    examples: list[tuple[torch.Tensor, torch.Tensor]] = []
    for edge_type in graph.forward_edge_types:
        full_edges = edge_index_dict[edge_type]
        if full_edges.shape[1] == 0:
            empty = torch.empty((2, 0), dtype=torch.long)
            examples.append((empty, empty.clone()))
            continue
        n_positive = min(int(full_edges.shape[1]), int(max_positive_edges))
        selection = torch.randperm(full_edges.shape[1])[:n_positive]
        positive_edges = full_edges[:, selection]
        source_count = int(x_dict[edge_type[0]].shape[0])
        target_count = int(x_dict[edge_type[2]].shape[0])
        try:
            negative_edges = negative_sampling(
                edge_index=full_edges,
                num_nodes=(source_count, target_count),
                num_neg_samples=n_positive,
                method="sparse",
            )
        except Exception:
            negative_edges = torch.stack(
                [
                    torch.randint(0, source_count, (n_positive,)),
                    torch.randint(0, target_count, (n_positive,)),
                ]
            )
        examples.append((positive_edges, negative_edges))
    return examples


def _dominant_primary_errors(
    *,
    embeddings: dict[str, torch.Tensor],
    x_dict: dict[str, torch.Tensor],
    graph: GraphBundle,
    attribute_decoder: PrimaryAttributeDecoder,
    structure_decoder: DynamicLinkDecoder,
    relation_examples: list[tuple[torch.Tensor, torch.Tensor]],
    attribute_alpha: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute primary-node attribute, sampled-structure, and joint errors."""

    primary_type = graph.primary_node_type
    primary_embeddings = embeddings[primary_type]
    # The final channel is an observed-node indicator, not a telemetry
    # attribute, and is deliberately excluded from reconstruction evidence.
    attribute_target = x_dict[primary_type][:, :-1]
    attribute_prediction = attribute_decoder(primary_embeddings)
    attribute_error = torch.linalg.vector_norm(
        attribute_target - attribute_prediction,
        dim=1,
    )

    structural_sum = torch.zeros(
        len(primary_embeddings), dtype=torch.float32
    )
    structural_count = torch.zeros(
        len(primary_embeddings), dtype=torch.float32
    )
    for relation_index, (edge_type, examples) in enumerate(
        zip(graph.forward_edge_types, relation_examples)
    ):
        positive_edges, negative_edges = examples
        for edge_index, positive in (
            (positive_edges, True),
            (negative_edges, False),
        ):
            if edge_index.shape[1] == 0:
                continue
            logits = structure_decoder(
                relation_index,
                embeddings[edge_type[0]],
                embeddings[edge_type[2]],
                edge_index,
            )
            targets = (
                torch.ones_like(logits)
                if positive
                else torch.zeros_like(logits)
            )
            errors = F.binary_cross_entropy_with_logits(
                logits,
                targets,
                reduction="none",
            )
            if edge_type[0] == primary_type:
                structural_sum.index_add_(0, edge_index[0], errors)
                structural_count.index_add_(
                    0, edge_index[0], torch.ones_like(errors)
                )
            if edge_type[2] == primary_type:
                structural_sum.index_add_(0, edge_index[1], errors)
                structural_count.index_add_(
                    0, edge_index[1], torch.ones_like(errors)
                )

    observed = structural_count > 0
    structural_error = torch.zeros_like(structural_sum)
    structural_error[observed] = (
        structural_sum[observed] / structural_count[observed]
    )
    if torch.any(observed):
        neutral_error = torch.median(structural_error[observed])
        structural_error[~observed] = neutral_error

    joint_error = (
        float(attribute_alpha) * attribute_error
        + (1.0 - float(attribute_alpha)) * structural_error
    )
    return (
        attribute_error.detach().cpu().numpy().astype(float),
        structural_error.detach().cpu().numpy().astype(float),
        joint_error.detach().cpu().numpy().astype(float),
    )


def train_dominant_style(
    graph: GraphBundle,
    row_features: np.ndarray,
    *,
    seed: int = SEED,
    epochs: int = DEFAULT_GRAPH_EPOCHS,
    hidden_dim: int = DEFAULT_EMBEDDING_DIM,
    output_dim: int = DEFAULT_EMBEDDING_DIM,
    attribute_alpha: float = DOMINANT_ATTRIBUTE_ALPHA,
    patience: int | None = None,
    min_delta: float = 1e-4,
) -> dict[str, Any]:
    """Train a sparse heterogeneous DOMINANT-style reconstruction model.

    This is intentionally named ``dominant_style``: classical DOMINANT uses a
    homogeneous graph and dense adjacency reconstruction.  AutoSignal instead
    uses typed message passing plus sampled relation reconstruction so the
    method remains feasible on heterogeneous telemetry graphs.
    """

    if not 0 <= float(attribute_alpha) <= 1:
        raise ValueError("attribute_alpha must be in [0, 1].")
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    x_dict = _graphsage_x_dict(graph, row_features)
    primary_target = x_dict[graph.primary_node_type][:, :-1]
    if primary_target.shape[1] == 0:
        raise ValueError("DOMINANT-style training requires primary attributes.")
    edge_index_dict = {
        edge_type: edge_index.cpu()
        for edge_type, edge_index in graph.data.edge_index_dict.items()
    }
    encoder = DynamicHeteroGraphSAGE(
        edge_types=list(edge_index_dict),
        hidden_dim=hidden_dim,
        output_dim=output_dim,
    )
    structure_decoder = DynamicLinkDecoder(
        len(graph.forward_edge_types), output_dim
    )
    attribute_decoder = PrimaryAttributeDecoder(
        output_dim, int(primary_target.shape[1])
    )

    # The exact same evaluation pairs score the untrained and trained models.
    relation_examples = _sample_relation_examples(
        edge_index_dict,
        graph,
        x_dict,
    )
    primary_count = int(x_dict[graph.primary_node_type].shape[0])
    primary_incident = np.zeros(primary_count, dtype=np.int64)
    relation_example_diagnostics = []
    for edge_type, (positive_edges, negative_edges) in zip(
        graph.forward_edge_types,
        relation_examples,
    ):
        full_edges = edge_index_dict[edge_type]
        if edge_type[0] == graph.primary_node_type and full_edges.shape[1]:
            primary_incident += np.bincount(
                full_edges[0].cpu().numpy(), minlength=primary_count
            )
        if edge_type[2] == graph.primary_node_type and full_edges.shape[1]:
            primary_incident += np.bincount(
                full_edges[1].cpu().numpy(), minlength=primary_count
            )
        relation_example_diagnostics.append(
            {
                "edge_type": list(edge_type),
                "forward_edges": int(full_edges.shape[1]),
                "evaluation_positive_examples": int(positive_edges.shape[1]),
                "evaluation_negative_examples": int(negative_edges.shape[1]),
            }
        )
    incident_total = int(primary_incident.sum())
    primary_neighborhood_diagnostics = {
        "primary_nodes": primary_count,
        "non_isolated_fraction": (
            float(np.mean(primary_incident > 0)) if primary_count else 0.0
        ),
        "degree_at_least_two_fraction": (
            float(np.mean(primary_incident >= 2)) if primary_count else 0.0
        ),
        "maximum_incident_edge_fraction": (
            float(primary_incident.max() / incident_total)
            if incident_total and primary_count
            else 0.0
        ),
        "incident_edge_endpoints": incident_total,
    }

    encoder.eval()
    structure_decoder.eval()
    attribute_decoder.eval()
    with torch.no_grad():
        initial_embeddings = encoder(x_dict, edge_index_dict)
        initial_errors = _dominant_primary_errors(
            embeddings=initial_embeddings,
            x_dict=x_dict,
            graph=graph,
            attribute_decoder=attribute_decoder,
            structure_decoder=structure_decoder,
            relation_examples=relation_examples,
            attribute_alpha=attribute_alpha,
        )
        initial_primary = (
            initial_embeddings[graph.primary_node_type]
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

    optimizer = torch.optim.Adam(
        list(encoder.parameters())
        + list(structure_decoder.parameters())
        + list(attribute_decoder.parameters()),
        lr=0.002,
    )
    losses: list[dict[str, float]] = []
    best_loss = math.inf
    best_encoder_state = copy.deepcopy(encoder.state_dict())
    best_structure_state = copy.deepcopy(structure_decoder.state_dict())
    best_attribute_state = copy.deepcopy(attribute_decoder.state_dict())
    stale_epochs = 0
    for _ in range(int(epochs)):
        encoder.train()
        structure_decoder.train()
        attribute_decoder.train()
        embeddings = encoder(x_dict, edge_index_dict)
        attribute_prediction = attribute_decoder(
            embeddings[graph.primary_node_type]
        )
        attribute_loss = F.mse_loss(
            attribute_prediction,
            primary_target,
        )

        relation_losses: list[torch.Tensor] = []
        training_examples = _sample_relation_examples(
            edge_index_dict,
            graph,
            x_dict,
        )
        for relation_index, (edge_type, examples) in enumerate(
            zip(graph.forward_edge_types, training_examples)
        ):
            positive_edges, negative_edges = examples
            if positive_edges.shape[1] == 0 or negative_edges.shape[1] == 0:
                continue
            positive_logits = structure_decoder(
                relation_index,
                embeddings[edge_type[0]],
                embeddings[edge_type[2]],
                positive_edges,
            )
            negative_logits = structure_decoder(
                relation_index,
                embeddings[edge_type[0]],
                embeddings[edge_type[2]],
                negative_edges,
            )
            relation_losses.append(
                F.binary_cross_entropy_with_logits(
                    positive_logits, torch.ones_like(positive_logits)
                )
                + F.binary_cross_entropy_with_logits(
                    negative_logits, torch.zeros_like(negative_logits)
                )
            )
        structure_loss = (
            torch.stack(relation_losses).mean()
            if relation_losses
            else torch.zeros((), dtype=torch.float32)
        )
        loss = (
            float(attribute_alpha) * attribute_loss
            + (1.0 - float(attribute_alpha)) * structure_loss
        )
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            list(encoder.parameters())
            + list(structure_decoder.parameters())
            + list(attribute_decoder.parameters()),
            1.0,
        )
        optimizer.step()
        losses.append(
            {
                "total": float(loss.detach()),
                "attribute": float(attribute_loss.detach()),
                "structure": float(structure_loss.detach()),
            }
        )
        loss_value = float(loss.detach())
        if loss_value < best_loss - float(min_delta):
            best_loss = loss_value
            best_encoder_state = copy.deepcopy(encoder.state_dict())
            best_structure_state = copy.deepcopy(structure_decoder.state_dict())
            best_attribute_state = copy.deepcopy(attribute_decoder.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if patience is not None and stale_epochs >= int(patience):
                break

    encoder.load_state_dict(best_encoder_state)
    structure_decoder.load_state_dict(best_structure_state)
    attribute_decoder.load_state_dict(best_attribute_state)

    encoder.eval()
    structure_decoder.eval()
    attribute_decoder.eval()
    with torch.no_grad():
        trained_embeddings = encoder(x_dict, edge_index_dict)
        trained_errors = _dominant_primary_errors(
            embeddings=trained_embeddings,
            x_dict=x_dict,
            graph=graph,
            attribute_decoder=attribute_decoder,
            structure_decoder=structure_decoder,
            relation_examples=relation_examples,
            attribute_alpha=attribute_alpha,
        )
        trained_primary = (
            trained_embeddings[graph.primary_node_type]
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

    return {
        "untrained_primary_embeddings": initial_primary,
        "trained_primary_embeddings": trained_primary,
        "untrained_attribute_error": initial_errors[0],
        "untrained_structure_error": initial_errors[1],
        "untrained_joint_error": initial_errors[2],
        "trained_attribute_error": trained_errors[0],
        "trained_structure_error": trained_errors[1],
        "trained_joint_error": trained_errors[2],
        "losses": losses,
        "attribute_alpha": float(attribute_alpha),
        "structure_alpha": float(1.0 - attribute_alpha),
        "structure_reconstruction": "sampled_typed_relation_bce",
        "attribute_reconstruction": "primary_node_l2",
        "secondary_attribute_policy": "constant_inputs_not_reconstructed",
        "relation_example_diagnostics": relation_example_diagnostics,
        "primary_neighborhood_diagnostics": primary_neighborhood_diagnostics,
    }


def _primary_values_to_session_max(
    primary_values: np.ndarray,
    graph: GraphBundle,
    sessions: list[list[int]],
) -> np.ndarray:
    """Pool unique primary-node evidence to sessions using a fixed maximum."""

    values = np.asarray(primary_values, dtype=float).ravel()
    if len(values) != len(graph.node_maps[graph.primary_node_type]):
        raise ValueError("Primary-node values are not graph-aligned.")
    session_values = []
    for indices in sessions:
        primary_indices = np.unique(graph.row_primary_index[indices])
        session_values.append(float(np.max(values[primary_indices])))
    result = np.asarray(session_values, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError("Session-pooled DOMINANT evidence is not finite.")
    return result


def _dominant_errors_to_session(
    attribute_error: np.ndarray,
    structure_error: np.ndarray,
    joint_error: np.ndarray,
    graph: GraphBundle,
    sessions: list[list[int]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pool the highest-joint-error primary node and its exact components."""

    attribute_values = np.asarray(attribute_error, dtype=float).ravel()
    structure_values = np.asarray(structure_error, dtype=float).ravel()
    joint_values = np.asarray(joint_error, dtype=float).ravel()
    expected = len(graph.node_maps[graph.primary_node_type])
    if not (
        len(attribute_values)
        == len(structure_values)
        == len(joint_values)
        == expected
    ):
        raise ValueError("DOMINANT component errors are not graph-aligned.")

    session_attribute = []
    session_structure = []
    session_joint = []
    for indices in sessions:
        primary_indices = np.unique(graph.row_primary_index[indices])
        selected = int(
            primary_indices[np.argmax(joint_values[primary_indices])]
        )
        session_attribute.append(float(attribute_values[selected]))
        session_structure.append(float(structure_values[selected]))
        session_joint.append(float(joint_values[selected]))
    outputs = tuple(
        np.asarray(values, dtype=float)
        for values in (session_attribute, session_structure, session_joint)
    )
    if not all(np.isfinite(values).all() for values in outputs):
        raise ValueError("Session-pooled DOMINANT evidence is not finite.")
    return outputs


def _primary_to_session_representation(
    primary_embeddings: np.ndarray,
    graph: GraphBundle,
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
) -> np.ndarray:
    row_embeddings = primary_embeddings[graph.row_primary_index]
    session_matrix, _ = _pool_rows(row_embeddings, sessionized_df, sessions)
    return session_matrix


def run_autosignal(
    df: pd.DataFrame,
    agent_config: dict[str, Any],
    *,
    k: int = DEFAULT_K,
    seeds: tuple[int, ...] = (SEED,),
    graph_epochs: int = DEFAULT_GRAPH_EPOCHS,
    graph_patience: int | None = None,
    signal_permutations: int = DEFAULT_SIGNAL_PERMUTATIONS,
    include_coordinates: bool = True,
    include_signal: bool = True,
    signal_representation_allowlist: tuple[str, ...] | None = None,
    representation_allowlist: tuple[str, ...] | None = None,
    scorer_allowlist: tuple[str, ...] | None = None,
    feature_hypothesis_allowlist: tuple[str, ...] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """Run the complete aligned representation/scorer battery."""
    run_started = time.perf_counter()
    if isinstance(k, (bool, np.bool_)) or not isinstance(k, (int, np.integer)):
        raise ValueError("k must be an integer.")
    if int(k) < 1:
        raise ValueError("k must be positive.")
    k = int(k)
    if not seeds or any(
        isinstance(seed, (bool, np.bool_))
        or not isinstance(seed, (int, np.integer))
        for seed in seeds
    ):
        raise ValueError("seeds must contain at least one integer seed.")
    seeds = tuple(dict.fromkeys(int(seed) for seed in seeds))
    if (
        isinstance(graph_epochs, (bool, np.bool_))
        or not isinstance(graph_epochs, (int, np.integer))
        or int(graph_epochs) < 1
    ):
        raise ValueError("graph_epochs must be a positive integer.")
    graph_epochs = int(graph_epochs)
    if graph_patience is not None:
        if (
            isinstance(graph_patience, (bool, np.bool_))
            or not isinstance(graph_patience, (int, np.integer))
            or int(graph_patience) < 1
        ):
            raise ValueError("graph_patience must be a positive integer or None.")
        graph_patience = int(graph_patience)
    if (
        isinstance(signal_permutations, (bool, np.bool_))
        or not isinstance(signal_permutations, (int, np.integer))
        or int(signal_permutations) < 99
    ):
        raise ValueError(
            "signal_permutations must be an integer of at least 99."
        )
    signal_permutations = int(signal_permutations)
    active_representations = (
        SUPPORTED_REPRESENTATIONS
        if representation_allowlist is None
        else frozenset(str(value) for value in representation_allowlist)
    )
    unknown_representations = active_representations - SUPPORTED_REPRESENTATIONS
    if unknown_representations:
        raise ValueError(
            "Unknown representation_allowlist values: "
            f"{sorted(unknown_representations)}"
        )
    active_scorers = (
        SUPPORTED_COMMON_SCORERS
        if scorer_allowlist is None
        else frozenset(str(value) for value in scorer_allowlist)
    )
    unknown_scorers = active_scorers - SUPPORTED_COMMON_SCORERS
    if unknown_scorers:
        raise ValueError(
            f"Unknown scorer_allowlist values: {sorted(unknown_scorers)}"
        )

    def report(progress: float, message: str) -> None:
        if progress_callback is not None:
            progress_callback(float(np.clip(progress, 0.0, 1.0)), message)

    report(0.0, "Validating configuration")
    validation_started = time.perf_counter()
    cfg = validate_config(agent_config, df)
    validation_seconds = time.perf_counter() - validation_started
    requested_hypotheses = (
        None
        if feature_hypothesis_allowlist is None
        else set(str(value) for value in feature_hypothesis_allowlist)
    )
    active_feature_sets = [
        feature_set
        for feature_set in cfg["feature_sets"]
        if requested_hypotheses is None
        or feature_set["name"] in requested_hypotheses
    ]
    if requested_hypotheses is not None:
        unknown_hypotheses = requested_hypotheses - {
            feature_set["name"] for feature_set in cfg["feature_sets"]
        }
        if unknown_hypotheses:
            raise ValueError(
                "Unknown feature_hypothesis_allowlist values: "
                f"{sorted(unknown_hypotheses)}"
            )
    feature_names = [feature_set["name"] for feature_set in active_feature_sets]
    seed_count = len(seeds)
    graph_representations = active_representations - {
        "random_score",
        "raw_session",
    }
    progress_stages = [
        "configuration_validation",
        "sessionization",
        *(["random_baseline"] if "random_score" in active_representations else []),
        *(
            [f"raw_session_scorers::{name}" for name in feature_names]
            if "raw_session" in active_representations
            else []
        ),
        *(["graph_construction"] if graph_representations else []),
        *(
            ["typed_structural_stats_scorers"]
            if "typed_structural_stats" in active_representations
            else []
        ),
        *(
            [f"node2vec_scorers::seed={seed}" for seed in seeds]
            if "node2vec" in active_representations
            else []
        ),
        *[
            f"graphsage::{name}::seed={seed}"
            for name in feature_names
            for seed in seeds
            if {
                "graphsage_random",
                "graphsage_trained",
            }
            & active_representations
        ],
        *[
            f"dominant_style::{name}::seed={seed}"
            for name in feature_names
            for seed in seeds
            if {
                "dominant_style_untrained",
                "dominant_style_trained",
            }
            & active_representations
        ],
        "payload_finalization",
    ]
    total_stages = len(progress_stages)
    completed_stages = 1

    report(completed_stages / total_stages, "Creating sessions")
    sessionization_started = time.perf_counter()
    sessionized_df, sessions, session_manifest = sessionize(df, cfg)
    labels = _session_labels(sessionized_df, sessions, cfg)
    sessionization_seconds = time.perf_counter() - sessionization_started
    completed_stages += 1
    selected_types = cfg["_selected_types"]
    public_config = {
        key: value for key, value in cfg.items() if not key.startswith("_")
    }
    payload: dict[str, Any] = {
        "status": "completed",
        "config": public_config,
        "run_manifest": {
            "result_schema_version": "2.0",
            "rows": int(len(sessionized_df)),
            "sessions": int(len(sessions)),
            "mode": "development" if labels is not None else "score_only",
            "coordinate_method": "UMAP" if include_coordinates else None,
            "include_coordinates": bool(include_coordinates),
            "include_signal": bool(include_signal),
            "signal_representation_allowlist": (
                list(signal_representation_allowlist)
                if signal_representation_allowlist is not None
                else None
            ),
            "representation_allowlist": sorted(active_representations),
            "scorer_allowlist": sorted(active_scorers),
            "feature_hypothesis_allowlist": feature_names,
            "k": int(k),
            "seeds": [int(seed) for seed in seeds],
            "graph_epochs": int(graph_epochs),
            "graph_patience": graph_patience,
            "software_environment": _software_environment(),
            "scorers": sorted(
                active_scorers
                | (
                    {"dominant_joint_reconstruction"}
                    if {
                        "dominant_style_untrained",
                        "dominant_style_trained",
                    }
                    & active_representations
                    else set()
                )
            ),
        },
        "session_manifest": session_manifest,
        "graph_manifest": None,
        "feature_diagnostics": {},
        "method_results": [],
        "representation_results": [],
        "representation_stability": [],
        "_representation_matrices": {},
        "scorer_diagnostics": [],
        "score_components": [],
        "dominant_diagnostics": [],
        "runtime_diagnostics": [],
        "session_scores": [],
        "embeddings": [],
        "signal_config": {
            "k": int(k),
            "n_permutations": signal_permutations,
            "tail_fraction": SIGNAL_TAIL_FRACTION,
            "min_tail_size": SIGNAL_MIN_TAIL_SIZE,
            "alpha": SIGNAL_ALPHA,
            "amplification_alpha": SIGNAL_AMPLIFICATION_ALPHA,
            "random_state": SEED,
        },
        "signal_results": [],
        "signal_scores": [],
    }
    _record_runtime(
        payload,
        stage="configuration_validation",
        seconds=validation_seconds,
    )
    _record_runtime(
        payload,
        stage="sessionization",
        seconds=sessionization_seconds,
    )

    if "random_score" in active_representations:
        report(completed_stages / total_stages, "Scoring random baseline")
        random_scores = np.random.default_rng(SEED).random(len(sessions))
        random_representation = random_scores[:, None]
        _add_method_artifacts(
            payload,
            "random_baseline",
            None,
            random_scores,
            random_representation,
            labels,
            seed=SEED,
            representation_key="random_score",
            representation_method="random_score",
            scorer="random",
            representation_seed=None,
            scorer_seed=SEED,
            signal_eligible=False,
        )
        completed_stages += 1

    if "raw_session" in active_representations:
        for feature_set in active_feature_sets:
            name = feature_set["name"]
            columns = list(feature_set["columns"])
            report(completed_stages / total_stages, f"Raw session scorers: {name}")
            try:
                row_matrix, row_feature_names, diagnostics = build_row_feature_matrix(
                    sessionized_df, columns, selected_types
                )
                session_matrix, _ = _pool_rows(
                    row_matrix, sessionized_df, sessions
                )
                payload["feature_diagnostics"][name] = {
                    "source_columns": columns,
                    "numeric_features": row_feature_names,
                    "preprocessing": diagnostics,
                }
                _add_scoring_suite(
                    payload,
                    representation_method="raw_session",
                    method_prefix="raw_session",
                    hypothesis=name,
                    representation=session_matrix,
                    labels=labels,
                    k=k,
                    scorer_seeds=seeds,
                    dimension_names=_pooled_dimension_names(row_feature_names),
                    scorer_allowlist=active_scorers,
                )
            except Exception as error:
                _add_failed_scoring_suite(
                    payload,
                    representation_method="raw_session",
                    method_prefix="raw_session",
                    hypothesis=name,
                    scorer_seeds=seeds,
                    error=error,
                    scorer_allowlist=active_scorers,
                )
            completed_stages += 1

    graph: GraphBundle | None = None
    if graph_representations:
        report(completed_stages / total_stages, "Building typed telemetry graph")
        try:
            graph = build_typed_graph(sessionized_df, cfg)
            payload["graph_manifest"] = graph.manifest
        except Exception as error:
            payload["graph_manifest"] = {
                "status": "failed",
                "error": f"{type(error).__name__}: {error}",
            }
        completed_stages += 1

    if graph_representations and graph is None:
        error = RuntimeError(payload["graph_manifest"]["error"])
        if "typed_structural_stats" in active_representations:
            _add_failed_scoring_suite(
                payload,
                representation_method="typed_structural_stats",
                method_prefix="typed_structural_stats",
                hypothesis=None,
                scorer_seeds=seeds,
                error=error,
                scorer_allowlist=active_scorers,
            )
        if "node2vec" in active_representations:
            for seed in seeds:
                _add_failed_scoring_suite(
                    payload,
                    representation_method="node2vec",
                    method_prefix="node2vec",
                    hypothesis=None,
                    scorer_seeds=seeds,
                    representation_seed=seed,
                    error=error,
                    scorer_allowlist=active_scorers,
                )
        for feature_set in active_feature_sets:
            name = feature_set["name"]
            for seed in seeds:
                for variant in ("graphsage_random", "graphsage_trained"):
                    if variant in active_representations:
                        _add_failed_scoring_suite(
                            payload,
                            representation_method=variant,
                            method_prefix=variant,
                            hypothesis=name,
                            scorer_seeds=seeds,
                            representation_seed=seed,
                            error=error,
                            scorer_allowlist=active_scorers,
                        )
                for variant in ("untrained", "trained"):
                    representation_method = f"dominant_style_{variant}"
                    if representation_method in active_representations:
                        _add_failed_direct_method(
                            payload,
                            representation_method=representation_method,
                            method=f"{representation_method}_reconstruction",
                            hypothesis=name,
                            representation_seed=seed,
                            scorer="dominant_joint_reconstruction",
                            error=error,
                        )
        # Every skipped graph stage now has a declared failure artifact.
        completed_stages = total_stages - 1

    if graph is not None:
        if "typed_structural_stats" in active_representations:
            report(
                completed_stages / total_stages,
                "Scoring typed structural statistics",
            )
            try:
                structural_matrix, structural_features = (
                    structural_session_representation(
                        graph, sessionized_df, sessions
                    )
                )
                payload["structural_features"] = structural_features
                _add_scoring_suite(
                    payload,
                    representation_method="typed_structural_stats",
                    method_prefix="typed_structural_stats",
                    hypothesis=None,
                    representation=structural_matrix,
                    labels=labels,
                    k=k,
                    scorer_seeds=seeds,
                    dimension_names=_pooled_dimension_names(structural_features),
                    scorer_allowlist=active_scorers,
                )
            except Exception as error:
                _add_failed_scoring_suite(
                    payload,
                    representation_method="typed_structural_stats",
                    method_prefix="typed_structural_stats",
                    hypothesis=None,
                    scorer_seeds=seeds,
                    error=error,
                    scorer_allowlist=active_scorers,
                )
            completed_stages += 1

        for seed in (seeds if "node2vec" in active_representations else ()):
            report(
                completed_stages / total_stages,
                f"Training Node2Vec · seed {seed}",
            )
            try:
                node2vec_matrix = node2vec_session_representation(
                    graph, sessionized_df, sessions, seed=seed
                )
                latent_dimension = max(0, (node2vec_matrix.shape[1] - 1) // 4)
                _add_scoring_suite(
                    payload,
                    representation_method="node2vec",
                    method_prefix="node2vec",
                    hypothesis=None,
                    representation=node2vec_matrix,
                    labels=labels,
                    k=k,
                    scorer_seeds=seeds,
                    representation_seed=seed,
                    dimension_names=_pooled_dimension_names(
                        [f"latent_{index}" for index in range(latent_dimension)]
                    ),
                    scorer_allowlist=active_scorers,
                )
            except Exception as error:
                _add_failed_scoring_suite(
                    payload,
                    representation_method="node2vec",
                    method_prefix="node2vec",
                    hypothesis=None,
                    scorer_seeds=seeds,
                    representation_seed=seed,
                    error=error,
                    scorer_allowlist=active_scorers,
                )
            completed_stages += 1

        for feature_set in (
            active_feature_sets
            if {"graphsage_random", "graphsage_trained"}
            & active_representations
            else []
        ):
            name = feature_set["name"]
            columns = list(feature_set["columns"])
            try:
                row_matrix, _, _ = build_row_feature_matrix(
                    sessionized_df, columns, selected_types
                )
            except Exception as error:
                for seed in seeds:
                    for variant in ("graphsage_random", "graphsage_trained"):
                        if variant in active_representations:
                            _add_failed_scoring_suite(
                                payload,
                                representation_method=variant,
                                method_prefix=variant,
                                hypothesis=name,
                                scorer_seeds=seeds,
                                representation_seed=seed,
                                error=error,
                                scorer_allowlist=active_scorers,
                            )
                completed_stages += seed_count
                continue

            for seed in seeds:
                report(
                    completed_stages / total_stages,
                    f"Training GraphSAGE: {name} · seed {seed}",
                )
                try:
                    training_started = time.perf_counter()
                    random_primary, trained_primary, losses = train_graphsage(
                        graph,
                        row_matrix,
                        seed=seed,
                        epochs=graph_epochs,
                        patience=graph_patience,
                    )
                    training_seconds = time.perf_counter() - training_started
                    for variant, primary_embeddings in (
                        ("graphsage_random", random_primary),
                        ("graphsage_trained", trained_primary),
                    ):
                        if variant not in active_representations:
                            continue
                        session_matrix = _primary_to_session_representation(
                            primary_embeddings,
                            graph,
                            sessionized_df,
                            sessions,
                        )
                        latent_dimension = max(
                            0, (session_matrix.shape[1] - 1) // 4
                        )
                        _add_scoring_suite(
                            payload,
                            representation_method=variant,
                            method_prefix=variant,
                            hypothesis=name,
                            representation=session_matrix,
                            labels=labels,
                            k=k,
                            scorer_seeds=seeds,
                            representation_seed=seed,
                            dimension_names=_pooled_dimension_names(
                                [
                                    f"latent_{index}"
                                    for index in range(latent_dimension)
                                ]
                            ),
                            scorer_allowlist=active_scorers,
                        )
                    payload.setdefault("training_diagnostics", []).append(
                        {
                            "method": "graphsage_trained",
                            "hypothesis": name,
                            "seed": int(seed),
                            "losses": losses,
                            "training_runtime_seconds": training_seconds,
                        }
                    )
                except Exception as error:
                    for variant in ("graphsage_random", "graphsage_trained"):
                        if variant in active_representations:
                            _add_failed_scoring_suite(
                                payload,
                                representation_method=variant,
                                method_prefix=variant,
                                hypothesis=name,
                                scorer_seeds=seeds,
                                representation_seed=seed,
                                error=error,
                                scorer_allowlist=active_scorers,
                            )
                completed_stages += 1

        for feature_set in (
            active_feature_sets
            if {"dominant_style_untrained", "dominant_style_trained"}
            & active_representations
            else []
        ):
            name = feature_set["name"]
            columns = list(feature_set["columns"])
            try:
                row_matrix, _, _ = build_row_feature_matrix(
                    sessionized_df, columns, selected_types
                )
            except Exception as error:
                for seed in seeds:
                    for variant in ("untrained", "trained"):
                        representation_method = f"dominant_style_{variant}"
                        if representation_method in active_representations:
                            _add_failed_direct_method(
                                payload,
                                representation_method=representation_method,
                                method=f"{representation_method}_reconstruction",
                                hypothesis=name,
                                representation_seed=seed,
                                scorer="dominant_joint_reconstruction",
                                error=error,
                            )
                    completed_stages += 1
                continue

            for seed in seeds:
                report(
                    completed_stages / total_stages,
                    f"Training DOMINANT-style: {name} · seed {seed}",
                )
                try:
                    training_started = time.perf_counter()
                    dominant_output = train_dominant_style(
                        graph,
                        row_matrix,
                        seed=seed,
                        epochs=graph_epochs,
                        patience=graph_patience,
                    )
                    training_seconds = time.perf_counter() - training_started
                    for variant in ("untrained", "trained"):
                        representation_method = f"dominant_style_{variant}"
                        if representation_method not in active_representations:
                            continue
                        primary_embeddings = dominant_output[
                            f"{variant}_primary_embeddings"
                        ]
                        session_matrix = _primary_to_session_representation(
                            primary_embeddings,
                            graph,
                            sessionized_df,
                            sessions,
                        )
                        (
                            attribute_scores,
                            structure_scores,
                            joint_scores,
                        ) = _dominant_errors_to_session(
                            dominant_output[f"{variant}_attribute_error"],
                            dominant_output[f"{variant}_structure_error"],
                            dominant_output[f"{variant}_joint_error"],
                            graph,
                            sessions,
                        )
                        representation_key = _representation_key(
                            representation_method,
                            name,
                            seed,
                        )
                        latent_dimension = max(
                            0, (session_matrix.shape[1] - 1) // 4
                        )
                        _add_representation_result(
                            payload,
                            representation_key=representation_key,
                            representation_method=representation_method,
                            hypothesis=name,
                            representation_seed=seed,
                            representation=session_matrix,
                            labels=labels,
                            dimension_names=_pooled_dimension_names(
                                [
                                    f"latent_{index}"
                                    for index in range(latent_dimension)
                                ]
                            ),
                        )
                        coordinates = (
                            _embedding_2d(session_matrix)
                            if include_coordinates
                            else None
                        )
                        method = f"{representation_method}_reconstruction"
                        _add_method_artifacts(
                            payload,
                            method,
                            name,
                            joint_scores,
                            session_matrix,
                            labels,
                            seed=seed,
                            representation_key=representation_key,
                            representation_method=representation_method,
                            scorer="dominant_joint_reconstruction",
                            representation_seed=seed,
                            scorer_seed=None,
                            coordinates=coordinates,
                        )
                        method_key = _method_key(
                            method,
                            name,
                            seed,
                            None,
                        )
                        for session_id in range(len(session_matrix)):
                            payload["score_components"].append(
                                {
                                    "method_key": method_key,
                                    "representation_key": representation_key,
                                    "scorer": "dominant_joint_reconstruction",
                                    "session_id": int(session_id),
                                    "attribute_error": float(
                                        attribute_scores[session_id]
                                    ),
                                    "structure_error": float(
                                        structure_scores[session_id]
                                    ),
                                    "joint_score": float(joint_scores[session_id]),
                                    "session_pooling": "max_unique_primary_node",
                                }
                            )
                    payload["dominant_diagnostics"].append(
                        {
                            "method": "dominant_style_trained",
                            "hypothesis": name,
                            "seed": int(seed),
                            "losses": dominant_output["losses"],
                            "attribute_alpha": dominant_output[
                                "attribute_alpha"
                            ],
                            "structure_alpha": dominant_output[
                                "structure_alpha"
                            ],
                            "structure_reconstruction": dominant_output[
                                "structure_reconstruction"
                            ],
                            "attribute_reconstruction": dominant_output[
                                "attribute_reconstruction"
                            ],
                            "secondary_attribute_policy": dominant_output[
                                "secondary_attribute_policy"
                            ],
                            "relation_example_diagnostics": dominant_output[
                                "relation_example_diagnostics"
                            ],
                            "primary_neighborhood_diagnostics": dominant_output[
                                "primary_neighborhood_diagnostics"
                            ],
                            "session_score_pooling": "max_unique_primary_node",
                            "training_runtime_seconds": training_seconds,
                        }
                    )
                except Exception as error:
                    for variant in ("untrained", "trained"):
                        representation_method = f"dominant_style_{variant}"
                        if representation_method in active_representations:
                            _add_failed_direct_method(
                                payload,
                                representation_method=representation_method,
                                method=f"{representation_method}_reconstruction",
                                hypothesis=name,
                                representation_seed=seed,
                                scorer="dominant_joint_reconstruction",
                                error=error,
                            )
                completed_stages += 1

    _finalize_representation_stability(payload)

    # Compact session table for analyst triage.
    report(completed_stages / total_stages, "Finalizing analyst payload")
    session_rows = []
    for session_id, indices in enumerate(sessions):
        times = sessionized_df.loc[indices, "_event_time"].dropna()
        session_rows.append(
            {
                "session_id": int(session_id),
                "rows": int(len(indices)),
                "start_time": times.min().isoformat() if len(times) else None,
                "end_time": times.max().isoformat() if len(times) else None,
                "label": str(labels[session_id]) if labels is not None else "unknown",
            }
        )
    payload["sessions"] = session_rows
    payload["run_manifest"]["total_runtime_seconds"] = float(
        time.perf_counter() - run_started
    )
    report(1.0, "AutoSignal complete")
    return payload


__all__ = [
    "ConfigValidationError",
    "apply_matched_amplification",
    "build_session_knn_operator",
    "build_typed_graph",
    "compute_signal_diagnostic_channels",
    "dataframe_profile",
    "load_df_slice",
    "pick_signal_regime",
    "run_autosignal",
    "sessionize",
    "train_dominant_style",
    "validate_config",
]
