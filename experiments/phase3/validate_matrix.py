"""Validate the frozen AutoSignal Phase 3 matrix without reading labels.

The validator checks immutable source fingerprints, loader/config compatibility,
partition isolation, matrix cardinality, and the sealed-confirmation contract.
It never parses a label column or computes a performance result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = Path(__file__).with_name("matrix_v1.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_line_count(path: Path) -> int:
    newlines = 0
    final_byte = b""
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            size += len(block)
            newlines += block.count(b"\n")
            final_byte = block[-1:]
    return newlines + int(size > 0 and final_byte != b"\n")


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return next(csv.reader(handle))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def loader_columns(config: dict[str, Any], source_path: Path) -> list[str]:
    loader = config["loader"]
    if loader["format"] == "parquet":
        return list(pq.ParquetFile(source_path).schema_arrow.names)
    if loader["header"] is None:
        return list(loader["column_names"])
    return csv_header(source_path)


def validate_engine_config(
    config: dict[str, Any], columns: list[str], errors: list[str]
) -> None:
    engine = config["engine_config"]
    available = set(columns)
    selected = [item["column"] for item in engine["selected_columns"]]
    feature_columns = [
        column
        for feature_set in engine["feature_sets"]
        for column in feature_set["columns"]
    ]
    require(len(engine["feature_sets"]) == 3, f"{config['dataset_id']}: expected 3 feature sets", errors)
    require(len(selected) == len(set(selected)), f"{config['dataset_id']}: duplicate selected column", errors)
    require(set(selected) == set(feature_columns), f"{config['dataset_id']}: selected/feature columns differ", errors)
    require(len(feature_columns) == len(set(feature_columns)), f"{config['dataset_id']}: feature appears in multiple sets", errors)
    for column in selected:
        require(column in available, f"{config['dataset_id']}: missing selected column {column!r}", errors)
    for column in engine["session_group_cols"]:
        require(column in available, f"{config['dataset_id']}: missing session group {column!r}", errors)
    for field in ("timestamp_col", "existing_session_id_col", "label_col"):
        column = engine[field]
        require(column is None or column in available, f"{config['dataset_id']}: missing {field} {column!r}", errors)
    require(engine["label_col"] not in selected, f"{config['dataset_id']}: label included as a feature", errors)
    for relation in engine["graph_relations"]:
        for endpoint in ("source_column", "target_column"):
            column = relation[endpoint]
            require(column == "$row_id" or column in available, f"{config['dataset_id']}: missing relation column {column!r}", errors)
            require(column != engine["label_col"], f"{config['dataset_id']}: label used in graph relation", errors)


def expected_cardinality(feature_count: int, seed_count: int) -> dict[str, int]:
    observed_methods = (
        1
        + feature_count * (2 + seed_count)
        + (2 + seed_count)
        + seed_count * 3
        + 2 * feature_count * seed_count * 3
        + 2 * feature_count * seed_count
    )
    graph_null_methods = (
        (2 + seed_count)
        + seed_count * 3
        + feature_count * seed_count * 3
        + feature_count * seed_count
    )
    observed_representations = (
        feature_count
        + 1
        + seed_count
        + 2 * feature_count * seed_count
        + 2 * feature_count * seed_count
    )
    graph_null_representations = 1 + seed_count + feature_count * seed_count * 2
    return {
        "observed_method_rows": observed_methods,
        "graph_null_method_rows": graph_null_methods,
        "total_method_rows": observed_methods + graph_null_methods,
        "observed_representation_rows": observed_representations,
        "graph_null_representation_rows": graph_null_representations,
        "total_representation_rows": observed_representations + graph_null_representations,
    }


def validate(matrix_path: Path, *, verify_hashes: bool) -> dict[str, Any]:
    errors: list[str] = []
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    require(matrix["schema_version"] == "autosignal.phase3_experiment_matrix.v1", "Unexpected matrix schema", errors)
    require(matrix["status"] == "frozen_for_phase4_execution", "Matrix is not frozen", errors)
    require(matrix["immutability"]["overwrite_this_file"] is False, "Matrix overwrite policy must be false", errors)
    require(matrix["partition_and_sampling_policy"]["uses_labels_for_partitioning_or_sampling"] is False, "Sampling must be label-blind", errors)
    require(matrix["partition_and_sampling_policy"]["maximum_source_rows_per_partition"] == 25000, "Source-row cap changed", errors)

    config_ref = matrix["implementation_baseline"]["dataset_configs"]
    config_path = REPO_ROOT / config_ref["path"]
    require(config_path.exists(), "Frozen dataset-config file is missing", errors)
    if config_path.exists():
        require(sha256_file(config_path) == config_ref["sha256"], "Dataset-config hash mismatch", errors)
        config_document = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config_document = {"configs": []}
    configs = {config["dataset_id"]: config for config in config_document["configs"]}

    for code_ref_name in ("engine", "analysis", "runner"):
        code_ref = matrix["implementation_baseline"][code_ref_name]
        code_path = REPO_ROOT / code_ref["path"]
        require(code_path.exists(), f"Missing {code_ref_name} source", errors)
        if code_path.exists() and verify_hashes:
            require(sha256_file(code_path) == code_ref["sha256"], f"{code_ref_name} hash mismatch", errors)

    expected_roles = {"development", "selection", "sealed_confirmation"}
    dataset_ids = [dataset["dataset_id"] for dataset in matrix["datasets"]]
    require(dataset_ids == matrix["scope"]["core_datasets"], "Core dataset order differs from dataset records", errors)
    require(len(dataset_ids) == len(set(dataset_ids)) == 3, "Expected three unique core datasets", errors)
    source_checks = 0
    seen_partition_ids: set[str] = set()

    for dataset in matrix["datasets"]:
        dataset_id = dataset["dataset_id"]
        config = configs.get(dataset["config_id"])
        require(config is not None, f"{dataset_id}: frozen config missing", errors)
        roles = {partition["role"] for partition in dataset["partitions"]}
        require(roles == expected_roles, f"{dataset_id}: partition roles are incomplete", errors)
        schemas: list[list[str]] = []
        role_paths: dict[str, set[str]] = {}
        for partition in dataset["partitions"]:
            partition_id = partition["partition_id"]
            require(partition_id not in seen_partition_ids, f"Duplicate partition id {partition_id}", errors)
            seen_partition_ids.add(partition_id)
            role_paths[partition["role"]] = {source["path"] for source in partition["sources"]}
            require(partition["maximum_review_units"] == matrix["partition_and_sampling_policy"]["maximum_review_units_per_partition"], f"{partition_id}: sampling cap mismatch", errors)
            if partition["role"] == "sealed_confirmation":
                require(partition["labels_may_be_used_for_evaluation"] is False, f"{partition_id}: confirmation labels are not sealed", errors)
                require(partition.get("execute_in_phase") == 6, f"{partition_id}: confirmation execution phase must be 6", errors)
            for source in partition["sources"]:
                source_path = REPO_ROOT / source["path"]
                require(source_path.exists(), f"Missing source {source['path']}", errors)
                if not source_path.exists():
                    continue
                source_checks += 1
                require(source_path.stat().st_size == source["bytes"], f"Byte count mismatch: {source['path']}", errors)
                if verify_hashes:
                    require(sha256_file(source_path) == source["sha256"], f"SHA-256 mismatch: {source['path']}", errors)
                if source_path.suffix.lower() == ".parquet":
                    rows = pq.ParquetFile(source_path).metadata.num_rows
                else:
                    rows = csv_line_count(source_path)
                    if config is not None and config["loader"]["header"] == 0:
                        rows -= 1
                require(rows == source["rows"], f"Row count mismatch: {source['path']} ({rows} != {source['rows']})", errors)
                if config is not None:
                    schemas.append(loader_columns(config, source_path))
        if dataset_id != "acme_process_telemetry":
            for first_role in expected_roles:
                for second_role in expected_roles:
                    if first_role < second_role:
                        require(role_paths[first_role].isdisjoint(role_paths[second_role]), f"{dataset_id}: source overlaps {first_role}/{second_role}", errors)
        if config is not None and schemas:
            require(all(schema == schemas[0] for schema in schemas[1:]), f"{dataset_id}: source schemas differ", errors)
            validate_engine_config(config, schemas[0], errors)

    seeds = matrix["execution_matrix"]["stochastic_seeds"]
    require(len(seeds) == len(set(seeds)) == 3, "Expected three unique stochastic seeds", errors)
    computed = expected_cardinality(feature_count=3, seed_count=len(seeds))
    declared = matrix["execution_matrix"]["expected_rows_per_dataset_partition"]
    for key, value in computed.items():
        require(declared[key] == value, f"Declared cardinality mismatch for {key}", errors)
    phase4_partitions = len(matrix["datasets"]) * len(matrix["execution_matrix"]["execute_partition_roles_in_phase4"])
    totals = matrix["execution_matrix"]["expected_phase4_totals"]
    require(totals["dataset_partitions"] == phase4_partitions == 6, "Phase 4 partition count mismatch", errors)
    require(totals["method_rows"] == phase4_partitions * computed["total_method_rows"], "Phase 4 method-row total mismatch", errors)
    require(totals["representation_rows"] == phase4_partitions * computed["total_representation_rows"], "Phase 4 representation-row total mismatch", errors)
    require(matrix["evaluation"]["analyst_budgets"] == [25, 50, 100, 250], "Analyst budgets changed", errors)
    require(matrix["failure_and_abstention_policy"]["automatic_hyperparameter_retry"] is False, "Automatic retuning must remain disabled", errors)

    return {
        "passed": not errors,
        "matrix_id": matrix["matrix_id"],
        "matrix_sha256": sha256_file(matrix_path),
        "dataset_config_sha256": sha256_file(config_path) if config_path.exists() else None,
        "dataset_count": len(dataset_ids),
        "partition_count": len(seen_partition_ids),
        "source_checks": source_checks,
        "file_hashes_verified": verify_hashes,
        "expected_phase4_method_rows": totals["method_rows"],
        "expected_phase4_representation_rows": totals["representation_rows"],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--skip-file-hashes", action="store_true")
    arguments = parser.parse_args()
    matrix_path = arguments.matrix.resolve()
    result = validate(matrix_path, verify_hashes=not arguments.skip_file_hashes)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
