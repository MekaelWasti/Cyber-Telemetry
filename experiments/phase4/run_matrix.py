"""Execute the frozen AutoSignal matrix as small, resumable dataset cases.

The runner deliberately has one job: run the fixed method battery on each
development/selection partition and write compact tables. It does not tune,
select winners, generate visualizations, or open confirmation partitions.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import heapq
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def find_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "Notebooks" / "autosignal_engine.py").exists():
            return candidate
    raise FileNotFoundError("Run this script from inside the AutoSignal repository.")


REPO_ROOT = find_repo_root()
NOTEBOOK_DIR = REPO_ROOT / "Notebooks"
PHASE3_DIR = REPO_ROOT / "experiments" / "phase3"
for import_path in (NOTEBOOK_DIR, PHASE3_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import autosignal_engine as engine
from validate_matrix import validate as validate_frozen_matrix


DEFAULT_MATRIX = PHASE3_DIR / "matrix_v1.json"
SIGNAL_REPRESENTATIONS = (
    "raw_session",
    "typed_structural_stats",
    "node2vec",
    "graphsage_trained",
    "dominant_style_trained",
)
GRAPH_NULL_REPRESENTATIONS = {
    "typed_structural_stats",
    "node2vec",
    "graphsage_trained",
    "dominant_style_trained",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(*arguments: str) -> str | None:
    candidates = (
        Path(r"C:\Program Files\Git\cmd\git.exe"),
        Path(r"C:\Program Files\Git\bin\git.exe"),
    )
    executable = next((path for path in candidates if path.exists()), None)
    if executable is None:
        return None
    process = subprocess.run(
        [str(executable), *arguments],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return process.stdout.strip() if process.returncode == 0 else None


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_gzip_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with gzip.open(temporary, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(value, handle, ensure_ascii=False, allow_nan=False)
    os.replace(temporary, path)


def write_parquet_atomic(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, path)


def required_columns(config: dict[str, Any]) -> list[str]:
    columns: list[str] = []

    def add(value: Any) -> None:
        if value and value != "$row_id" and str(value) not in columns:
            columns.append(str(value))

    add(config.get("timestamp_col"))
    add(config.get("existing_session_id_col"))
    add(config.get("label_col"))
    for column in config.get("session_group_cols", []):
        add(column)
    for item in config.get("selected_columns", []):
        add(item.get("column"))
    for relation in config.get("graph_relations", []):
        add(relation.get("source_column"))
        add(relation.get("target_column"))
    return columns


def allocate_quotas(total: int, source_count: int) -> list[int]:
    base, remainder = divmod(int(total), int(source_count))
    return [base + int(index < remainder) for index in range(source_count)]


def source_row_digest(
    matrix: dict[str, Any],
    dataset_id: str,
    partition_id: str,
    source_sha256: str,
    row_index: int,
) -> bytes:
    fields = [
        matrix["matrix_id"],
        dataset_id,
        partition_id,
        source_sha256,
        int(row_index),
        int(matrix["partition_and_sampling_policy"]["sampling_seed"]),
    ]
    return hashlib.sha256(canonical_json_bytes(fields)).digest()


def session_digest(
    matrix: dict[str, Any],
    dataset_id: str,
    partition_id: str,
    source_sha256: str,
    session_id: int,
) -> bytes:
    fields = [
        matrix["matrix_id"],
        dataset_id,
        partition_id,
        source_sha256,
        int(session_id),
        int(matrix["partition_and_sampling_policy"]["sampling_seed"]),
    ]
    return hashlib.sha256(canonical_json_bytes(fields)).digest()


def lowest_hash_indices(
    *,
    row_count: int,
    quota: int,
    digest_for_index: Any,
) -> list[tuple[int, str]]:
    if quota >= row_count:
        return [
            (index, digest_for_index(index).hex())
            for index in range(int(row_count))
        ]
    heap: list[tuple[int, int, str]] = []
    for index in range(int(row_count)):
        digest = digest_for_index(index)
        rank = int.from_bytes(digest, "big")
        candidate = (-rank, -index, digest.hex())
        if len(heap) < int(quota):
            heapq.heappush(heap, candidate)
        elif candidate > heap[0]:
            heapq.heapreplace(heap, candidate)
    return sorted(
        [(-negative_index, digest) for _, negative_index, digest in heap],
        key=lambda item: item[0],
    )


def lowest_hash_sessions_with_row_cap(
    *,
    sessions: list[list[int]],
    session_quota: int,
    row_quota: int,
    digest_for_session: Any,
) -> list[tuple[int, str, int]]:
    ranked = sorted(
        (
            digest_for_session(session_id),
            int(session_id),
            int(len(indices)),
        )
        for session_id, indices in enumerate(sessions)
    )
    selected: list[tuple[int, str, int]] = []
    retained_rows = 0
    for digest, session_id, session_rows in ranked:
        if len(selected) >= int(session_quota):
            break
        if retained_rows + session_rows > int(row_quota):
            continue
        selected.append((session_id, digest.hex(), session_rows))
        retained_rows += session_rows
    return sorted(selected, key=lambda item: item[0])


def load_csv_rows(
    path: Path,
    loader: dict[str, Any],
    columns: list[str],
    selected_indices: list[int],
) -> pd.DataFrame:
    selected = set(int(value) for value in selected_indices)
    pieces: list[pd.DataFrame] = []
    options: dict[str, Any] = {
        "chunksize": 100000,
        "low_memory": False,
        "usecols": columns,
    }
    if loader["header"] is None:
        options.update({"header": None, "names": loader["column_names"]})
    else:
        options["header"] = int(loader["header"])
    for chunk in pd.read_csv(path, **options):
        mask = chunk.index.to_series().isin(selected).to_numpy()
        if np.any(mask):
            pieces.append(chunk.loc[mask].copy())
    if not pieces:
        raise ValueError(f"No sampled rows loaded from {path}")
    result = pd.concat(pieces, axis=0).sort_index(kind="stable")
    result.insert(0, "_frozen_source_row", result.index.to_numpy(dtype=np.int64))
    result.insert(0, "_frozen_source_file", path.name)
    return result.reset_index(drop=True)


def materialize_network_partition(
    matrix: dict[str, Any],
    dataset: dict[str, Any],
    partition: dict[str, Any],
    config_record: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    quota = int(partition["maximum_review_units"])
    quotas = allocate_quotas(quota, len(partition["sources"]))
    columns = required_columns(config_record["engine_config"])
    frames: list[pd.DataFrame] = []
    key_rows: list[dict[str, Any]] = []
    for source, source_quota in zip(partition["sources"], quotas):
        selected = lowest_hash_indices(
            row_count=int(source["rows"]),
            quota=min(int(source_quota), int(source["rows"])),
            digest_for_index=lambda index, source=source: source_row_digest(
                matrix,
                dataset["dataset_id"],
                partition["partition_id"],
                source["sha256"],
                index,
            ),
        )
        source_path = REPO_ROOT / source["path"]
        frames.append(
            load_csv_rows(
                source_path,
                config_record["loader"],
                columns,
                [row_index for row_index, _ in selected],
            )
        )
        key_rows.extend(
            {
                "source_path": source["path"],
                "source_row": int(row_index),
                "sampling_digest": digest,
            }
            for row_index, digest in selected
        )
    frame = pd.concat(frames, ignore_index=True)
    if len(frame) != sum(min(quota, int(source["rows"])) for quota, source in zip(quotas, partition["sources"])):
        raise ValueError(f"Sample cardinality mismatch for {partition['partition_id']}")
    return frame, copy.deepcopy(config_record["engine_config"]), pd.DataFrame(key_rows)


def materialize_acme_partition(
    matrix: dict[str, Any],
    dataset: dict[str, Any],
    partition: dict[str, Any],
    config_record: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    config = copy.deepcopy(config_record["engine_config"])
    source = partition["sources"][0]
    path = REPO_ROOT / source["path"]
    frame = pd.read_parquet(path, columns=required_columns(config))
    if partition["role"] != "sealed_confirmation":
        timestamp = pd.to_datetime(frame[dataset["partitioning"]["timestamp_column"]], utc=True, errors="coerce")
        cutoff = pd.Timestamp(dataset["partitioning"]["cutoff_utc"])
        if partition["role"] == "development":
            frame = frame.loc[timestamp < cutoff]
        elif partition["role"] == "selection":
            frame = frame.loc[timestamp >= cutoff]
    frame = frame.reset_index(drop=True)
    validated = engine.validate_config(copy.deepcopy(config), frame)
    sessionized, sessions, _ = engine.sessionize(frame, validated)
    session_quota = min(int(partition["maximum_review_units"]), len(sessions))
    row_quota = int(
        matrix["partition_and_sampling_policy"][
            "maximum_source_rows_per_partition"
        ]
    )
    selected = lowest_hash_sessions_with_row_cap(
        sessions=sessions,
        session_quota=session_quota,
        row_quota=row_quota,
        digest_for_session=lambda session_id: session_digest(
            matrix,
            dataset["dataset_id"],
            partition["partition_id"],
            source["sha256"],
            session_id,
        ),
    )
    selected_ids = {session_id for session_id, _, _ in selected}
    sampled = sessionized.loc[sessionized["session_id"].isin(selected_ids)].copy()
    sampled["_frozen_session_id"] = sampled["session_id"].map(
        lambda value: f"{partition['partition_id']}::{int(value)}"
    )
    sampled = sampled[[*required_columns(config), "_frozen_session_id"]].reset_index(drop=True)
    config["existing_session_id_col"] = "_frozen_session_id"
    key_rows = [
        {
            "source_path": source["path"],
            "canonical_session_id": int(session_id),
            "sampling_digest": digest,
        }
        for session_id, digest, session_rows in selected
    ]
    for row, (_, _, session_rows) in zip(key_rows, selected):
        row["source_rows"] = int(session_rows)
    return sampled, config, pd.DataFrame(key_rows)


def materialize_partition(
    matrix: dict[str, Any],
    dataset: dict[str, Any],
    partition: dict[str, Any],
    config_record: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    if dataset["dataset_id"] == "acme_process_telemetry":
        return materialize_acme_partition(matrix, dataset, partition, config_record)
    return materialize_network_partition(matrix, dataset, partition, config_record)


def graph_null_frame(
    matrix: dict[str, Any],
    dataset_id: str,
    partition_id: str,
    frame: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    result = frame.copy()
    null_config = copy.deepcopy(config)
    diagnostics: list[dict[str, Any]] = []
    null_seed = int(matrix["execution_matrix"]["graph_null_seed"])
    for relation in null_config["graph_relations"]:
        target = relation["target_column"]
        if target == "$row_id":
            raise ValueError("A relation target cannot be $row_id for the graph null.")
        values = result[target].to_numpy(copy=True)
        distinct = int(pd.Series(values).nunique(dropna=False))
        if distinct < 2:
            raise ValueError(
                f"Relation {relation['relation_name']} has fewer than two targets."
            )
        shuffled = values.copy()
        attempts = 0
        while attempts < 16 and np.array_equal(shuffled, values):
            seed_fields = [
                matrix["matrix_id"],
                dataset_id,
                partition_id,
                relation["relation_name"],
                null_seed,
                attempts,
            ]
            seed = int.from_bytes(
                hashlib.sha256(canonical_json_bytes(seed_fields)).digest()[:8],
                "big",
            )
            shuffled = np.random.Generator(np.random.PCG64(seed)).permutation(values)
            attempts += 1
        if np.array_equal(shuffled, values):
            raise ValueError(f"Could not permute relation {relation['relation_name']}")
        control_column = f"_null_target_{relation['relation_name']}"
        result[control_column] = shuffled
        relation["target_column"] = control_column
        diagnostics.append(
            {
                "relation_name": relation["relation_name"],
                "distinct_targets": distinct,
                "rows": int(len(values)),
                "attempts": attempts,
                "unchanged_fraction": float(np.mean(shuffled == values)),
            }
        )
    return result, null_config, diagnostics


def add_context(
    records: list[dict[str, Any]],
    *,
    dataset_id: str,
    partition_id: str,
    relation_variant: str,
) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    frame.insert(0, "relation_variant", relation_variant)
    frame.insert(0, "partition_id", partition_id)
    frame.insert(0, "dataset_id", dataset_id)
    return frame


def filter_graph_null(payload: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(payload)
    result["representation_results"] = [
        row
        for row in result["representation_results"]
        if row.get("representation") in GRAPH_NULL_REPRESENTATIONS
    ]
    representation_keys = {
        row["representation_key"] for row in result["representation_results"]
    }
    result["method_results"] = [
        row
        for row in result["method_results"]
        if row.get("representation") in GRAPH_NULL_REPRESENTATIONS
    ]
    method_keys = {row["method_key"] for row in result["method_results"]}
    result["representation_stability"] = [
        row
        for row in result["representation_stability"]
        if row.get("representation") in GRAPH_NULL_REPRESENTATIONS
    ]
    result["session_scores"] = [
        row for row in result["session_scores"] if row.get("method_key") in method_keys
    ]
    result["score_components"] = [
        row for row in result["score_components"] if row.get("method_key") in method_keys
    ]
    result["scorer_diagnostics"] = [
        row
        for row in result["scorer_diagnostics"]
        if row.get("representation_key") in representation_keys
    ]
    result["signal_results"] = []
    result["signal_scores"] = []
    result["embeddings"] = []
    return result


def save_case_tables(
    case_root: Path,
    payload: dict[str, Any],
    *,
    dataset_id: str,
    partition_id: str,
    relation_variant: str,
) -> None:
    table_names = (
        "method_results",
        "representation_results",
        "representation_stability",
        "session_scores",
        "signal_scores",
        "score_components",
        "scorer_diagnostics",
        "runtime_diagnostics",
    )
    for name in table_names:
        frame = add_context(
            payload.get(name, []),
            dataset_id=dataset_id,
            partition_id=partition_id,
            relation_variant=relation_variant,
        )
        if not frame.empty:
            write_parquet_atomic(case_root / f"{name}.parquet", frame)
    details = {
        "run_manifest": payload["run_manifest"],
        "session_manifest": payload["session_manifest"],
        "graph_manifest": payload.get("graph_manifest"),
        "feature_diagnostics": payload.get("feature_diagnostics", {}),
        "signal_results": payload.get("signal_results", []),
        "dominant_diagnostics": payload.get("dominant_diagnostics", []),
        "sessions": payload.get("sessions", []),
    }
    write_gzip_json_atomic(case_root / "details.json.gz", details)


def run_case(
    *,
    matrix: dict[str, Any],
    matrix_sha256: str,
    dataset: dict[str, Any],
    partition: dict[str, Any],
    config_record: dict[str, Any],
    relation_variant: str,
    artifact_root: Path,
    resume: bool,
) -> dict[str, Any]:
    case_id = f"{dataset['dataset_id']}__{partition['partition_id']}__{relation_variant}"
    case_root = artifact_root / "cases" / case_id
    execution_path = case_root / "execution.json"
    if execution_path.exists():
        existing = json.loads(execution_path.read_text(encoding="utf-8"))
        if resume and existing.get("status") == "completed":
            print(f"SKIP {case_id} (completed)", flush=True)
            return existing
        raise FileExistsError(f"Case artifacts already exist: {case_root}")

    print(f"START {case_id}", flush=True)
    started_at = utc_now()
    started = time.perf_counter()
    frame, config, sampling_keys = materialize_partition(
        matrix, dataset, partition, config_record
    )
    sample_manifest = {
        "dataset_id": dataset["dataset_id"],
        "partition_id": partition["partition_id"],
        "rows": int(len(frame)),
        "review_units": int(len(sampling_keys)),
        "sampling_keys_sha256": hashlib.sha256(
            canonical_json_bytes(sampling_keys.to_dict("records"))
        ).hexdigest(),
    }
    null_diagnostics: list[dict[str, Any]] = []
    if relation_variant == "degree_sequence_preserving_target_permutation":
        frame, config, null_diagnostics = graph_null_frame(
            matrix,
            dataset["dataset_id"],
            partition["partition_id"],
            frame,
            config,
        )

    validated = engine.validate_config(copy.deepcopy(config), frame)
    public_config = {
        key: value for key, value in validated.items() if not key.startswith("_")
    }
    parameters = matrix["hyperparameters"]
    payload = engine.run_autosignal(
        frame,
        public_config,
        k=int(parameters["knn_mean_distance"]["k"]),
        seeds=tuple(int(seed) for seed in matrix["execution_matrix"]["stochastic_seeds"]),
        graph_epochs=int(parameters["graphsage"]["epochs"]),
        signal_permutations=int(parameters["signal_localization"]["permutations"]),
        include_coordinates=False,
        include_signal=relation_variant == "observed",
        signal_representation_allowlist=(
            SIGNAL_REPRESENTATIONS if relation_variant == "observed" else None
        ),
    )
    if relation_variant != "observed":
        payload = filter_graph_null(payload)

    save_case_tables(
        case_root,
        payload,
        dataset_id=dataset["dataset_id"],
        partition_id=partition["partition_id"],
        relation_variant=relation_variant,
    )
    write_parquet_atomic(case_root / "sampling_keys.parquet", sampling_keys)
    write_json_atomic(case_root / "selected_config.json", public_config)
    execution = {
        "case_id": case_id,
        "status": "completed",
        "matrix_sha256": matrix_sha256,
        "dataset_id": dataset["dataset_id"],
        "partition_id": partition["partition_id"],
        "partition_role": partition["role"],
        "relation_variant": relation_variant,
        "started_at_utc": started_at,
        "finished_at_utc": utc_now(),
        "wall_seconds": float(time.perf_counter() - started),
        "source_rows_loaded": int(len(frame)),
        "canonical_review_units": int(payload["run_manifest"]["sessions"]),
        "sampling": sample_manifest,
        "graph_null_diagnostics": null_diagnostics,
        "method_rows": int(len(payload["method_results"])),
        "representation_rows": int(len(payload["representation_results"])),
        "engine_sha256": sha256_file(NOTEBOOK_DIR / "autosignal_engine.py"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "git_commit": git_value("rev-parse", "HEAD"),
        "working_tree_status": git_value("status", "--short"),
        "python": platform.python_version(),
    }
    write_json_atomic(execution_path, execution)
    print(
        f"DONE {case_id}: {execution['method_rows']} methods, "
        f"{execution['wall_seconds']:.1f}s",
        flush=True,
    )
    return execution


def record_failure(
    artifact_root: Path,
    case_id: str,
    error: Exception,
) -> dict[str, Any]:
    case_root = artifact_root / "cases" / case_id
    failure = {
        "case_id": case_id,
        "status": "failed",
        "error_type": type(error).__name__,
        "error": str(error),
        "recorded_at_utc": utc_now(),
    }
    write_json_atomic(case_root / "failure.json", failure)
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
    print(f"FAIL {case_id}: {type(error).__name__}: {error}", flush=True)
    return failure


def aggregate_results(artifact_root: Path) -> dict[str, Any]:
    method_files = sorted((artifact_root / "cases").glob("*/method_results.parquet"))
    representation_files = sorted(
        (artifact_root / "cases").glob("*/representation_results.parquet")
    )
    methods = pd.concat([pd.read_parquet(path) for path in method_files], ignore_index=True) if method_files else pd.DataFrame()
    representations = pd.concat([pd.read_parquet(path) for path in representation_files], ignore_index=True) if representation_files else pd.DataFrame()
    tables_root = artifact_root / "tables"
    if not methods.empty:
        write_parquet_atomic(tables_root / "method_results.parquet", methods)
        methods.to_csv(tables_root / "method_results.csv", index=False)
        group_columns = [
            "dataset_id",
            "partition_id",
            "relation_variant",
            "method",
            "representation",
            "scorer",
            "hypothesis",
        ]
        completed = methods.loc[methods["status"].eq("completed")].copy()
        metrics = [
            column
            for column in (
                "average_precision",
                "recall_at_100",
                "precision_at_100",
                "reviews_to_first_malicious",
            )
            if column in completed.columns
        ]
        digest = (
            completed.groupby(group_columns, dropna=False)
            .agg(
                completed_rows=("method_key", "size"),
                **{f"median_{metric}": (metric, "median") for metric in metrics},
            )
            .reset_index()
        )
        digest.to_csv(tables_root / "matrix_digest.csv", index=False)
    else:
        digest = pd.DataFrame()
    if not representations.empty:
        write_parquet_atomic(
            tables_root / "representation_results.parquet", representations
        )
        representations.to_csv(
            tables_root / "representation_results.csv", index=False
        )
    failures = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((artifact_root / "cases").glob("*/failure.json"))
    ]
    if failures:
        pd.DataFrame(failures).to_csv(tables_root / "failure_table.csv", index=False)
    summary = {
        "completed_cases": len(method_files),
        "failed_cases": len(failures),
        "method_rows": int(len(methods)),
        "representation_rows": int(len(representations)),
        "digest_rows": int(len(digest)),
    }
    write_json_atomic(artifact_root / "execution_summary.json", summary)
    return summary


def selected_cases(
    matrix: dict[str, Any],
    dataset_ids: list[str] | None,
    roles: list[str],
) -> list[tuple[dict[str, Any], dict[str, Any], str]]:
    allowed_roles = set(matrix["execution_matrix"]["execute_partition_roles_in_phase4"])
    requested_roles = set(roles)
    if not requested_roles <= allowed_roles:
        forbidden = sorted(requested_roles - allowed_roles)
        raise ValueError(
            f"Phase 4 cannot execute roles {forbidden}; confirmation remains sealed."
        )
    requested_datasets = set(dataset_ids or matrix["scope"]["core_datasets"])
    unknown = requested_datasets - set(matrix["scope"]["core_datasets"])
    if unknown:
        raise ValueError(f"Unknown dataset ids: {sorted(unknown)}")
    cases = []
    for dataset in matrix["datasets"]:
        if dataset["dataset_id"] not in requested_datasets:
            continue
        for partition in dataset["partitions"]:
            if partition["role"] not in requested_roles:
                continue
            for relation in matrix["execution_matrix"]["relation_variants"]:
                cases.append((dataset, partition, relation["variant"]))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--roles", nargs="+", default=["development", "selection"])
    parser.add_argument("--datasets", nargs="+")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    arguments = parser.parse_args()

    matrix_path = arguments.matrix.resolve()
    validation = validate_frozen_matrix(matrix_path, verify_hashes=True)
    if not validation["passed"]:
        raise ValueError(f"Frozen matrix validation failed: {validation['errors']}")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix_sha256 = validation["matrix_sha256"]
    config_ref = matrix["implementation_baseline"]["dataset_configs"]
    config_document = json.loads(
        (REPO_ROOT / config_ref["path"]).read_text(encoding="utf-8")
    )
    configs = {item["dataset_id"]: item for item in config_document["configs"]}
    cases = selected_cases(matrix, arguments.datasets, arguments.roles)
    artifact_root = REPO_ROOT / matrix["artifact_contract"]["root"]

    preflight = {
        **validation,
        "requested_case_count": len(cases),
        "cases": [
            {
                "dataset_id": dataset["dataset_id"],
                "partition_id": partition["partition_id"],
                "partition_role": partition["role"],
                "relation_variant": relation_variant,
            }
            for dataset, partition, relation_variant in cases
        ],
        "artifact_root": str(artifact_root.relative_to(REPO_ROOT)),
    }
    print(json.dumps(preflight, indent=2), flush=True)
    if arguments.preflight_only:
        return 0

    failures = []
    for dataset, partition, relation_variant in cases:
        case_id = f"{dataset['dataset_id']}__{partition['partition_id']}__{relation_variant}"
        try:
            run_case(
                matrix=matrix,
                matrix_sha256=matrix_sha256,
                dataset=dataset,
                partition=partition,
                config_record=configs[dataset["config_id"]],
                relation_variant=relation_variant,
                artifact_root=artifact_root,
                resume=arguments.resume,
            )
        except Exception as error:
            failures.append(record_failure(artifact_root, case_id, error))

    summary = aggregate_results(artifact_root)
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
