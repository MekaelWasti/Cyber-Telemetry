"""Parameterized AutoSignal v1 engine.

The schema agent proposes a JSON configuration.  This module validates and
executes that configuration; it never asks an LLM to run preprocessing code.
The implementation deliberately keeps the v1 contract small:

* one canonical activity-window sessionization;
* one typed graph shared by all methods;
* raw kNN and GraphSAGE per feature hypothesis;
* structural statistics and Node2Vec once per topology;
* one aligned, frontend-friendly result payload.
"""

from __future__ import annotations

import copy
import math
import os
import random
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
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
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv
from torch_geometric.utils import negative_sampling
from umap import UMAP


SEED = 42
DEFAULT_K = 15
DEFAULT_INACTIVITY_MINUTES = 5
DEFAULT_MAX_DURATION_MINUTES = 30
DEFAULT_GRAPH_EPOCHS = 4
DEFAULT_EMBEDDING_DIM = 32
DEFAULT_MAX_POSITIVE_EDGES = 3_000
DEFAULT_NODE2VEC_PAIRS = 200_000

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
    """Load a CSV or Parquet file without applying dataset-specific semantics."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
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


def knn_anomaly_scores(matrix: np.ndarray, k: int = DEFAULT_K) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    if len(matrix) <= 1:
        return np.zeros(len(matrix), dtype=float)
    effective_k = min(int(k), len(matrix) - 1)
    distances, _ = cKDTree(matrix).query(
        matrix, k=effective_k + 1, workers=-1
    )
    return np.asarray(distances[:, 1:], dtype=float).mean(axis=1)


def _method_metrics(
    method: str,
    scores: np.ndarray,
    labels: np.ndarray | None,
    hypothesis: str | None,
    seed: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "method": method,
        "hypothesis": hypothesis,
        "seed": seed,
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


def _add_method_artifacts(
    payload: dict[str, Any],
    method: str,
    hypothesis: str | None,
    scores: np.ndarray,
    representation: np.ndarray,
    labels: np.ndarray | None,
    seed: int | None = None,
) -> None:
    payload["method_results"].append(
        _method_metrics(method, scores, labels, hypothesis, seed)
    )
    key = method if hypothesis is None else f"{method}::{hypothesis}"
    if seed is not None:
        key = f"{key}::seed={seed}"
    coordinates = _embedding_2d(representation)
    for session_id, (score, coordinate) in enumerate(zip(scores, coordinates)):
        label = str(labels[session_id]) if labels is not None else "unknown"
        payload["session_scores"].append(
            {
                "method_key": key,
                "method": method,
                "hypothesis": hypothesis,
                "seed": seed,
                "session_id": int(session_id),
                "score": float(score),
                "label": label,
            }
        )
        payload["embeddings"].append(
            {
                "method_key": key,
                "method": method,
                "hypothesis": hypothesis,
                "seed": seed,
                "session_id": int(session_id),
                "x": float(coordinate[0]),
                "y": float(coordinate[1]),
                "label": label,
            }
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
            if column == "$row_id":
                continue
            candidates[(node_type, column)] = candidates.get((node_type, column), 0) + 1

    if not candidates:
        raise ValueError("At least one graph relation endpoint is required.")

    scored = []
    for (node_type, column), uses in candidates.items():
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
        identifier = _safe_identifier(row[primary_id_column])
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
        losses.append(float(loss.detach()))

    encoder.eval()
    with torch.no_grad():
        trained = encoder(x_dict, edge_index_dict)
        trained_primary = (
            trained[graph.primary_node_type].detach().cpu().numpy()
        )
    return random_primary, trained_primary, losses


def _primary_to_session_representation(
    primary_embeddings: np.ndarray,
    graph: GraphBundle,
    sessionized_df: pd.DataFrame,
    sessions: list[list[int]],
) -> np.ndarray:
    row_embeddings = primary_embeddings[graph.row_primary_index]
    session_matrix, _ = _pool_rows(row_embeddings, sessionized_df, sessions)
    return session_matrix


def _failed_method(
    method: str,
    hypothesis: str | None,
    error: Exception,
) -> dict[str, Any]:
    return {
        "method": method,
        "hypothesis": hypothesis,
        "seed": None,
        "status": "failed",
        "error": f"{type(error).__name__}: {error}",
        "average_precision": None,
        "reviews_to_first_malicious": None,
    }


def run_autosignal(
    df: pd.DataFrame,
    agent_config: dict[str, Any],
    *,
    k: int = DEFAULT_K,
    seeds: tuple[int, ...] = (SEED,),
    graph_epochs: int = DEFAULT_GRAPH_EPOCHS,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """Run the complete v1 method battery and return one aligned payload."""
    def report(progress: float, message: str) -> None:
        if progress_callback is not None:
            progress_callback(float(np.clip(progress, 0.0, 1.0)), message)

    report(0.0, "Validating configuration")
    cfg = validate_config(agent_config, df)
    feature_names = [
        feature_set["name"] for feature_set in cfg["feature_sets"]
    ]
    seed_count = len(seeds)
    progress_stages = [
        "configuration_validation",
        "sessionization",
        "random_baseline",
        *[f"raw_session_knn::{name}" for name in feature_names],
        "graph_construction",
        "typed_structural_stats_knn",
        *[f"node2vec_knn::seed={seed}" for seed in seeds],
        *[
            f"graphsage::{name}::seed={seed}"
            for name in feature_names
            for seed in seeds
        ],
        "payload_finalization",
    ]
    total_stages = len(progress_stages)
    completed_stages = 1

    report(completed_stages / total_stages, "Creating sessions")
    sessionized_df, sessions, session_manifest = sessionize(df, cfg)
    labels = _session_labels(sessionized_df, sessions, cfg)
    completed_stages += 1
    selected_types = cfg["_selected_types"]
    public_config = {
        key: value for key, value in cfg.items() if not key.startswith("_")
    }
    payload: dict[str, Any] = {
        "status": "completed",
        "config": public_config,
        "run_manifest": {
            "rows": int(len(sessionized_df)),
            "sessions": int(len(sessions)),
            "mode": "development" if labels is not None else "score_only",
            "coordinate_method": "UMAP",
            "k": int(k),
            "seeds": [int(seed) for seed in seeds],
            "graph_epochs": int(graph_epochs),
        },
        "session_manifest": session_manifest,
        "graph_manifest": None,
        "feature_diagnostics": {},
        "method_results": [],
        "session_scores": [],
        "embeddings": [],
    }

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
    )
    completed_stages += 1

    for feature_set in cfg["feature_sets"]:
        name = feature_set["name"]
        columns = list(feature_set["columns"])
        report(completed_stages / total_stages, f"Raw session kNN: {name}")
        try:
            row_matrix, feature_names, diagnostics = build_row_feature_matrix(
                sessionized_df, columns, selected_types
            )
            session_matrix, _ = _pool_rows(
                row_matrix, sessionized_df, sessions
            )
            scores = knn_anomaly_scores(session_matrix, k=k)
            payload["feature_diagnostics"][name] = {
                "source_columns": columns,
                "numeric_features": feature_names,
                "preprocessing": diagnostics,
            }
            _add_method_artifacts(
                payload,
                "raw_session_knn",
                name,
                scores,
                session_matrix,
                labels,
            )
        except Exception as error:
            payload["method_results"].append(
                _failed_method("raw_session_knn", name, error)
            )
        completed_stages += 1

    graph: GraphBundle | None = None
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

    if graph is not None:
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
            structural_scores = knn_anomaly_scores(structural_matrix, k=k)
            payload["structural_features"] = structural_features
            _add_method_artifacts(
                payload,
                "typed_structural_stats_knn",
                None,
                structural_scores,
                structural_matrix,
                labels,
            )
        except Exception as error:
            payload["method_results"].append(
                _failed_method("typed_structural_stats_knn", None, error)
            )
        completed_stages += 1

        for seed in seeds:
            report(
                completed_stages / total_stages,
                f"Training Node2Vec · seed {seed}",
            )
            try:
                node2vec_matrix = node2vec_session_representation(
                    graph, sessionized_df, sessions, seed=seed
                )
                node2vec_scores = knn_anomaly_scores(node2vec_matrix, k=k)
                _add_method_artifacts(
                    payload,
                    "node2vec_knn",
                    None,
                    node2vec_scores,
                    node2vec_matrix,
                    labels,
                    seed=seed,
                )
            except Exception as error:
                failed = _failed_method("node2vec_knn", None, error)
                failed["seed"] = int(seed)
                payload["method_results"].append(failed)
            completed_stages += 1

        for feature_set in cfg["feature_sets"]:
            name = feature_set["name"]
            columns = list(feature_set["columns"])
            try:
                row_matrix, _, _ = build_row_feature_matrix(
                    sessionized_df, columns, selected_types
                )
            except Exception as error:
                payload["method_results"].append(
                    _failed_method("graphsage_trained", name, error)
                )
                completed_stages += seed_count
                continue

            for seed in seeds:
                report(
                    completed_stages / total_stages,
                    f"Training GraphSAGE: {name} · seed {seed}",
                )
                try:
                    random_primary, trained_primary, losses = train_graphsage(
                        graph,
                        row_matrix,
                        seed=seed,
                        epochs=graph_epochs,
                    )
                    for variant, primary_embeddings in (
                        ("graphsage_random", random_primary),
                        ("graphsage_trained", trained_primary),
                    ):
                        session_matrix = _primary_to_session_representation(
                            primary_embeddings,
                            graph,
                            sessionized_df,
                            sessions,
                        )
                        scores = knn_anomaly_scores(session_matrix, k=k)
                        _add_method_artifacts(
                            payload,
                            variant,
                            name,
                            scores,
                            session_matrix,
                            labels,
                            seed=seed,
                        )
                    payload.setdefault("training_diagnostics", []).append(
                        {
                            "method": "graphsage_trained",
                            "hypothesis": name,
                            "seed": int(seed),
                            "losses": losses,
                        }
                    )
                except Exception as error:
                    failed = _failed_method("graphsage_trained", name, error)
                    failed["seed"] = int(seed)
                    payload["method_results"].append(failed)
                completed_stages += 1

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
    report(1.0, "AutoSignal complete")
    return payload


__all__ = [
    "ConfigValidationError",
    "build_typed_graph",
    "dataframe_profile",
    "load_df_slice",
    "run_autosignal",
    "sessionize",
    "validate_config",
]
