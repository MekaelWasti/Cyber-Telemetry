"""Run the immutable AutoSignal Phase 2 correctness/feasibility pilot.

This runner deliberately validates technical contracts, runtime, memory, and
applicability. It never uses retrieval performance to select methods or tune
parameters. Full payloads live under ``artifacts/``; compact evidence tables
and the technical report are mirrored under ``experiments/phase2/results``.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psutil
import pyarrow.parquet as pq


def find_repo_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "Notebooks" / "autosignal_engine.py").exists():
            return candidate
    raise FileNotFoundError("Run this script from inside the AutoSignal repository.")


REPO_ROOT = find_repo_root()
NOTEBOOK_DIR = REPO_ROOT / "Notebooks"
if str(NOTEBOOK_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_DIR))

import autosignal_engine as engine


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: Any, *, pretty: bool = True) -> None:
    if pretty:
        content = (
            json.dumps(
                value,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    else:
        content = canonical_json_bytes(value)
    write_bytes_atomic(path, content)


def write_gzip_json_atomic(path: Path, value: Any) -> str:
    raw = canonical_json_bytes(value)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, filename="") as handle:
        handle.write(raw)
    write_bytes_atomic(path, buffer.getvalue())
    return sha256_bytes(raw)


def read_gzip_json(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def git_executable() -> Path | None:
    candidates = (
        Path(r"C:\Program Files\Git\cmd\git.exe"),
        Path(r"C:\Program Files\Git\bin\git.exe"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def git_value(*arguments: str) -> str | None:
    executable = git_executable()
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


def select_config(spec: dict[str, Any]) -> dict[str, Any]:
    config_spec = spec["configuration"]
    path = REPO_ROOT / config_spec["path"]
    document = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(document, list):
        config = copy.deepcopy(document[int(config_spec["config_index"])])
    else:
        if int(config_spec.get("config_index", 0)) != 0:
            raise ValueError("A scalar config document only supports config_index=0.")
        config = copy.deepcopy(document)

    requested = set(config_spec["feature_sets"])
    config["feature_sets"] = [
        item for item in config["feature_sets"] if item["name"] in requested
    ]
    found = {item["name"] for item in config["feature_sets"]}
    if found != requested:
        raise ValueError(f"Missing requested feature sets: {sorted(requested - found)}")
    retained_columns = {
        column
        for feature_set in config["feature_sets"]
        for column in feature_set["columns"]
    }
    config["selected_columns"] = [
        item
        for item in config["selected_columns"]
        if item["column"] in retained_columns
    ]
    return config


def required_columns(config: dict[str, Any], parquet_path: Path) -> list[str]:
    requested: set[str] = set()
    for name in (
        config.get("timestamp_col"),
        config.get("existing_session_id_col"),
        config.get("label_col"),
    ):
        if name and name != "$row_id":
            requested.add(str(name))
    requested.update(str(name) for name in config.get("session_group_cols", []))
    requested.update(
        str(item["column"])
        for item in config.get("selected_columns", [])
        if item.get("column") != "$row_id"
    )
    for relation in config.get("graph_relations", []):
        for endpoint in ("source_column", "target_column"):
            name = relation.get(endpoint)
            if name and name != "$row_id":
                requested.add(str(name))
    source_order = pq.ParquetFile(parquet_path).schema_arrow.names
    missing = requested - set(source_order)
    if missing:
        raise ValueError(f"Pilot config references missing columns: {sorted(missing)}")
    return [name for name in source_order if name in requested]


def load_physical_head(
    path: Path,
    *,
    rows: int,
    columns: list[str],
) -> pd.DataFrame:
    parquet = pq.ParquetFile(path)
    batches = parquet.iter_batches(
        batch_size=int(rows),
        columns=columns,
        use_threads=True,
    )
    try:
        batch = next(batches)
    except StopIteration as error:
        raise ValueError("Pilot dataset is empty.") from error
    frame = batch.to_pandas().head(int(rows)).reset_index(drop=True)
    if len(frame) != int(rows):
        raise ValueError(f"Requested {rows} rows but loaded {len(frame)}.")
    return frame


def dataframe_fingerprint(frame: pd.DataFrame) -> str:
    row_hashes = pd.util.hash_pandas_object(frame, index=True).to_numpy(
        dtype=np.uint64
    )
    digest = hashlib.sha256()
    digest.update("\n".join(frame.columns).encode("utf-8"))
    digest.update(row_hashes.tobytes())
    return digest.hexdigest()


class ResourceSampler:
    def __init__(self, interval_seconds: float = 0.2):
        self.interval_seconds = float(interval_seconds)
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._process = psutil.Process(os.getpid())

    def _sample(self) -> None:
        while not self._stop.is_set():
            memory = self._process.memory_info()
            self.samples.append(
                {
                    "monotonic_seconds": time.perf_counter(),
                    "rss_bytes": int(memory.rss),
                    "vms_bytes": int(memory.vms),
                }
            )
            self._stop.wait(self.interval_seconds)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._sample_once()

    def _sample_once(self) -> None:
        memory = self._process.memory_info()
        self.samples.append(
            {
                "monotonic_seconds": time.perf_counter(),
                "rss_bytes": int(memory.rss),
                "vms_bytes": int(memory.vms),
            }
        )

    @property
    def peak_rss_bytes(self) -> int:
        return max((sample["rss_bytes"] for sample in self.samples), default=0)


class ProgressTimeline:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.events: list[dict[str, Any]] = []
        self._active: dict[str, Any] | None = None

    def __call__(self, fraction: float, message: str) -> None:
        now = time.perf_counter()
        if self._active is not None:
            self._active["finished_monotonic_seconds"] = now
            self._active["duration_seconds"] = (
                now - self._active["started_monotonic_seconds"]
            )
            self.events.append(self._active)
        self._active = {
            "case_id": self.case_id,
            "fraction": float(fraction),
            "message": str(message),
            "started_monotonic_seconds": now,
        }
        print(f"[{self.case_id}] {fraction:6.1%} {message}", flush=True)

    def close(self) -> None:
        if self._active is None:
            return
        now = time.perf_counter()
        self._active["finished_monotonic_seconds"] = now
        self._active["duration_seconds"] = (
            now - self._active["started_monotonic_seconds"]
        )
        self.events.append(self._active)
        self._active = None


def check_payload(
    payload: dict[str, Any],
    expected: dict[str, int],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    json.dumps(payload, allow_nan=False)
    add("strict_json", True, "json.dumps(..., allow_nan=False) succeeded")

    methods = pd.DataFrame(payload.get("method_results", []))
    representations = pd.DataFrame(payload.get("representation_results", []))
    stability = pd.DataFrame(payload.get("representation_stability", []))
    scores = pd.DataFrame(payload.get("session_scores", []))
    embeddings = pd.DataFrame(payload.get("embeddings", []))
    session_count = int(payload["run_manifest"]["sessions"])
    canonical_ids = set(range(session_count))

    add("method_row_count", len(methods) == expected["method_rows"], len(methods))
    add(
        "representation_row_count",
        len(representations) == expected["representation_rows"],
        len(representations),
    )
    add(
        "stability_row_count",
        len(stability) == expected["stability_rows"],
        len(stability),
    )
    add(
        "unique_method_keys",
        bool(methods["method_key"].is_unique),
        int(methods["method_key"].nunique()),
    )
    add(
        "unique_representation_keys",
        bool(representations["representation_key"].is_unique),
        int(representations["representation_key"].nunique()),
    )
    failed_methods = methods.loc[methods["status"].eq("failed")]
    failed_representations = representations.loc[
        representations["status"].eq("failed")
    ]
    add(
        "no_hard_method_failures",
        failed_methods.empty,
        failed_methods[["method_key", "error"]].to_dict("records")
        if not failed_methods.empty
        else [],
    )
    add(
        "no_hard_representation_failures",
        failed_representations.empty,
        failed_representations[["representation_key", "reason"]].to_dict(
            "records"
        )
        if not failed_representations.empty
        else [],
    )

    alignment_failures = []
    finite_failures = []
    completed = methods.loc[methods["status"].eq("completed")]
    for method_key in completed["method_key"]:
        method_scores = scores.loc[scores["method_key"].eq(method_key)]
        method_embeddings = embeddings.loc[
            embeddings["method_key"].eq(method_key)
        ]
        if (
            len(method_scores) != session_count
            or set(method_scores["session_id"]) != canonical_ids
            or len(method_embeddings) != session_count
            or set(method_embeddings["session_id"]) != canonical_ids
        ):
            alignment_failures.append(str(method_key))
        if (
            not np.isfinite(method_scores["score"].to_numpy(dtype=float)).all()
            or not np.isfinite(
                method_embeddings[["x", "y"]].to_numpy(dtype=float)
            ).all()
        ):
            finite_failures.append(str(method_key))
    add("completed_outputs_aligned", not alignment_failures, alignment_failures)
    add("completed_outputs_finite", not finite_failures, finite_failures)

    dimension_failures = []
    for record in payload.get("representation_results", []):
        if record.get("status") != "completed":
            continue
        names = record.get("dimension_names")
        if names is not None and len(names) != int(record["n_dimensions"]):
            dimension_failures.append(record["representation_key"])
    add("dimension_names_aligned", not dimension_failures, dimension_failures)

    components = pd.DataFrame(payload.get("score_components", []))
    dominant = components.loc[
        components.get("scorer", pd.Series(dtype=str)).eq(
            "dominant_joint_reconstruction"
        )
    ]
    if dominant.empty:
        dominant_formula_passed = False
        dominant_alignment_passed = False
    else:
        numeric = dominant.dropna(subset=["attribute_error"])
        dominant_formula_passed = bool(
            np.allclose(
                numeric["joint_score"].to_numpy(dtype=float),
                0.5 * numeric["attribute_error"].to_numpy(dtype=float)
                + 0.5 * numeric["structure_error"].to_numpy(dtype=float),
                rtol=1e-6,
                atol=1e-6,
            )
        )
        dominant_alignment_passed = all(
            set(group["session_id"]) == canonical_ids
            and len(group) == session_count
            for _, group in dominant.groupby("method_key")
        )
    add("dominant_component_formula", dominant_formula_passed, len(dominant))
    add("dominant_components_aligned", dominant_alignment_passed, len(dominant))

    scorer_diagnostics = payload.get("scorer_diagnostics", [])
    hdbscan_diagnostics = [
        row
        for row in scorer_diagnostics
        if row.get("scorer") == "hdbscan_rare_cluster"
    ]
    allowed_hdbscan = {"completed", "abstained", "degenerate", "unavailable"}
    add(
        "hdbscan_statuses_declared",
        bool(hdbscan_diagnostics)
        and all(row.get("status") in allowed_hdbscan for row in hdbscan_diagnostics),
        {status: sum(row.get("status") == status for row in hdbscan_diagnostics)
         for status in sorted(allowed_hdbscan)},
    )
    cluster_components = components.loc[
        components.get("scorer", pd.Series(dtype=str)).eq("hdbscan_rare_cluster")
    ]
    noise = cluster_components.loc[
        cluster_components.get("is_noise", pd.Series(dtype=bool)).eq(True)
    ]
    add(
        "hdbscan_noise_score_zero",
        noise.empty
        or bool(np.allclose(noise["cluster_score"].to_numpy(dtype=float), 0.0)),
        int(len(noise)),
    )

    dominant_diagnostics = payload.get("dominant_diagnostics", [])
    relation_support_passed = bool(dominant_diagnostics) and all(
        any(
            relation.get("evaluation_positive_examples", 0) > 0
            and relation.get("evaluation_negative_examples", 0) > 0
            for relation in row.get("relation_example_diagnostics", [])
        )
        for row in dominant_diagnostics
    )
    add(
        "dominant_has_usable_relation_examples",
        relation_support_passed,
        len(dominant_diagnostics),
    )

    runtime = payload.get("runtime_diagnostics", [])
    runtime_passed = bool(runtime) and all(
        np.isfinite(float(row.get("seconds", np.nan)))
        and float(row.get("seconds", -1)) >= 0
        for row in runtime
    )
    add("runtime_diagnostics_finite", runtime_passed, len(runtime))

    passed = all(check["passed"] for check in checks)
    return {"passed": passed, "checks": checks}


def compare_reproducibility(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    rtol: float,
    atol: float,
) -> dict[str, Any]:
    checks = []

    first_scores = pd.DataFrame(first["session_scores"]).sort_values(
        ["method_key", "session_id"]
    ).reset_index(drop=True)
    second_scores = pd.DataFrame(second["session_scores"]).sort_values(
        ["method_key", "session_id"]
    ).reset_index(drop=True)
    identities_match = first_scores[["method_key", "session_id"]].equals(
        second_scores[["method_key", "session_id"]]
    )
    score_match = identities_match and bool(
        np.allclose(
            first_scores["score"].to_numpy(dtype=float),
            second_scores["score"].to_numpy(dtype=float),
            rtol=rtol,
            atol=atol,
        )
    )
    checks.append(
        {
            "name": "same_seed_scores_allclose",
            "passed": score_match,
            "detail": int(len(first_scores)),
        }
    )

    rank_match = False
    if identities_match:
        rank_match = True
        for method_key, first_group in first_scores.groupby("method_key"):
            second_group = second_scores.loc[
                second_scores["method_key"].eq(method_key)
            ]
            first_order = first_group.sort_values(
                ["score", "session_id"], ascending=[False, True]
            )["session_id"].to_numpy()
            second_order = second_group.sort_values(
                ["score", "session_id"], ascending=[False, True]
            )["session_id"].to_numpy()
            if not np.array_equal(first_order, second_order):
                rank_match = False
                break
    checks.append(
        {
            "name": "same_seed_rankings_identical",
            "passed": rank_match,
            "detail": int(first_scores["method_key"].nunique()),
        }
    )

    first_components = pd.DataFrame(first.get("score_components", [])).sort_values(
        ["method_key", "session_id"]
    ).reset_index(drop=True)
    second_components = pd.DataFrame(second.get("score_components", [])).sort_values(
        ["method_key", "session_id"]
    ).reset_index(drop=True)
    component_identity = first_components[["method_key", "session_id"]].equals(
        second_components[["method_key", "session_id"]]
    )
    numeric_columns = [
        column
        for column in (
            "cluster_score",
            "attribute_error",
            "structure_error",
            "joint_score",
        )
        if column in first_components and column in second_components
    ]
    component_match = component_identity
    for column in numeric_columns:
        left = first_components[column].fillna(0).to_numpy(dtype=float)
        right = second_components[column].fillna(0).to_numpy(dtype=float)
        component_match = component_match and bool(
            np.allclose(left, right, rtol=rtol, atol=atol)
        )
    checks.append(
        {
            "name": "same_seed_score_components_allclose",
            "passed": component_match,
            "detail": numeric_columns,
        }
    )
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def run_case(
    *,
    spec: dict[str, Any],
    case: dict[str, Any],
    selected_config: dict[str, Any],
    dataset_path: Path,
    artifact_root: Path,
    pilot_spec_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    case_id = case["case_id"]
    case_root = artifact_root / "runs" / case_id
    payload_path = case_root / "payload.json.gz"
    execution_path = case_root / "execution_manifest.json"
    if payload_path.exists() or execution_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing pilot case artifacts: {case_root}"
        )

    columns = required_columns(selected_config, dataset_path)
    slice_spec = case["slice"]
    if slice_spec["kind"] != "physical_head":
        raise ValueError("Pilot v1 permits only predeclared physical_head slices.")
    frame = load_physical_head(
        dataset_path,
        rows=int(slice_spec["rows"]),
        columns=columns,
    )
    validated = engine.validate_config(copy.deepcopy(selected_config), frame)
    public_config = {
        key: value for key, value in validated.items() if not key.startswith("_")
    }
    selected_config_sha256 = sha256_bytes(canonical_json_bytes(public_config))
    write_json_atomic(case_root / "selected_config.json", public_config)

    timeline = ProgressTimeline(case_id)
    resources = ResourceSampler()
    started_at = utc_now()
    started = time.perf_counter()
    resources.start()
    status = "completed"
    failure_reason = None
    try:
        parameters = case["parameters"]
        payload = engine.run_autosignal(
            frame,
            public_config,
            k=int(parameters["k"]),
            seeds=tuple(int(seed) for seed in parameters["seeds"]),
            graph_epochs=int(parameters["graph_epochs"]),
            signal_permutations=int(parameters["signal_permutations"]),
            progress_callback=timeline,
        )
    except Exception as error:
        status = "failed"
        failure_reason = f"{type(error).__name__}: {error}"
        write_bytes_atomic(
            case_root / "traceback.txt",
            traceback.format_exc().encode("utf-8"),
        )
        raise
    finally:
        timeline.close()
        resources.stop()

    wall_seconds = time.perf_counter() - started
    finished_at = utc_now()
    payload["pilot_context"] = {
        "pilot_id": spec["pilot_id"],
        "pilot_spec_sha256": pilot_spec_sha256,
        "case_id": case_id,
        "study_phase": spec["study_phase"],
        "evidence_role": spec["evidence_role"],
        "confirmation_eligible": spec["confirmation_eligible"],
        "slice_data_sha256": dataframe_fingerprint(frame),
    }
    payload_sha256 = write_gzip_json_atomic(payload_path, payload)
    write_bytes_atomic(
        case_root / "payload.sha256",
        f"{payload_sha256}  payload.json\n".encode("ascii"),
    )
    write_json_atomic(case_root / "progress_events.json", timeline.events)
    write_json_atomic(case_root / "resource_usage.json", resources.samples)

    labels = pd.Series([row["label"] for row in payload["sessions"]])
    execution = {
        "execution_id": f"{spec['pilot_id']}::{case_id}",
        "pilot_id": spec["pilot_id"],
        "pilot_spec_sha256": pilot_spec_sha256,
        "case_id": case_id,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "wall_seconds": float(wall_seconds),
        "status": status,
        "failure_reason": failure_reason,
        "dataset_path": str(dataset_path.relative_to(REPO_ROOT)),
        "dataset_sha256": spec["dataset"]["sha256"],
        "slice": slice_spec,
        "slice_data_sha256": payload["pilot_context"]["slice_data_sha256"],
        "source_rows": int(len(frame)),
        "canonical_sessions": int(payload["run_manifest"]["sessions"]),
        "malicious_sessions": int(labels.eq("malicious").sum()),
        "selected_config_sha256": selected_config_sha256,
        "engine_sha256": sha256_file(NOTEBOOK_DIR / "autosignal_engine.py"),
        "analysis_sha256": sha256_file(NOTEBOOK_DIR / "autosignal_analysis.py"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "requirements_sha256": sha256_file(
            NOTEBOOK_DIR / "requirements-autosignal.txt"
        ),
        "git_commit": git_value("rev-parse", "HEAD"),
        "working_tree_status": git_value("status", "--short"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "total_memory_bytes": int(psutil.virtual_memory().total),
        "peak_rss_bytes": int(resources.peak_rss_bytes),
        "peak_rss_fraction_of_total_memory": float(
            resources.peak_rss_bytes / max(psutil.virtual_memory().total, 1)
        ),
        "payload_path": str(payload_path.relative_to(REPO_ROOT)),
        "payload_sha256": payload_sha256,
        "engine_run_manifest": payload["run_manifest"],
        "session_manifest": payload["session_manifest"],
        "graph_manifest": payload.get("graph_manifest"),
    }
    write_json_atomic(execution_path, execution)
    validation = check_payload(payload, case["expected_contract"])
    validation.update(
        {
            "case_id": case_id,
            "wall_seconds": float(wall_seconds),
            "peak_rss_bytes": int(resources.peak_rss_bytes),
        }
    )
    write_json_atomic(case_root / "checks.json", validation)
    return payload, execution, validation


def add_context(frame: pd.DataFrame, spec: dict[str, Any], case_id: str) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "case_id", case_id)
    result.insert(0, "pilot_id", spec["pilot_id"])
    result.insert(2, "study_phase", spec["study_phase"])
    result.insert(3, "evidence_role", spec["evidence_role"])
    result.insert(4, "confirmation_eligible", spec["confirmation_eligible"])
    return result


def write_derived_artifacts(
    *,
    spec: dict[str, Any],
    artifact_root: Path,
    tracked_root: Path,
    payloads: dict[str, dict[str, Any]],
    executions: list[dict[str, Any]],
    validations: list[dict[str, Any]],
    reproducibility: dict[str, Any],
) -> dict[str, Any]:
    tables_root = artifact_root / "tables"
    validation_root = artifact_root / "validation"
    tables_root.mkdir(parents=True, exist_ok=True)
    validation_root.mkdir(parents=True, exist_ok=True)
    tracked_root.mkdir(parents=True, exist_ok=True)

    method_frames = []
    representation_frames = []
    stability_frames = []
    runtime_frames = []
    for case_id, payload in payloads.items():
        method_frames.append(
            add_context(pd.DataFrame(payload["method_results"]), spec, case_id)
        )
        representation_frames.append(
            add_context(
                pd.DataFrame(payload["representation_results"]), spec, case_id
            )
        )
        if payload.get("representation_stability"):
            stability_frames.append(
                add_context(
                    pd.DataFrame(payload["representation_stability"]),
                    spec,
                    case_id,
                )
            )
        runtime_frames.append(
            add_context(pd.DataFrame(payload["runtime_diagnostics"]), spec, case_id)
        )

    methods = pd.concat(method_frames, ignore_index=True)
    representations = pd.concat(representation_frames, ignore_index=True)
    stability = (
        pd.concat(stability_frames, ignore_index=True)
        if stability_frames
        else pd.DataFrame()
    )
    runtimes = pd.concat(runtime_frames, ignore_index=True)

    status_columns = [
        "pilot_id",
        "case_id",
        "study_phase",
        "evidence_role",
        "confirmation_eligible",
        "method_key",
        "representation_key",
        "representation",
        "scorer",
        "hypothesis",
        "representation_seed",
        "scorer_seed",
        "status",
        "error",
    ]
    methods[[column for column in status_columns if column in methods]].to_csv(
        tables_root / "method_status.csv", index=False
    )
    methods.to_csv(tables_root / "method_metrics_exploratory.csv", index=False)
    representations.to_json(
        tables_root / "representation_results.jsonl",
        orient="records",
        lines=True,
        force_ascii=False,
    )
    stability.to_csv(tables_root / "representation_stability.csv", index=False)
    runtimes.to_csv(tables_root / "runtime_diagnostics.csv", index=False)
    write_json_atomic(validation_root / "checks.json", validations)
    write_json_atomic(validation_root / "reproducibility.json", reproducibility)

    total_wall = float(sum(item["wall_seconds"] for item in executions))
    peak_rss = int(max(item["peak_rss_bytes"] for item in executions))
    acceptance = spec["technical_acceptance"]
    resource_pass = (
        total_wall <= float(acceptance["maximum_total_wall_seconds"])
        and all(
            item["peak_rss_fraction_of_total_memory"]
            <= float(acceptance["maximum_peak_rss_fraction_of_total_memory"])
            for item in executions
        )
    )
    case_pass = all(item["passed"] for item in validations)
    overall_pass = bool(case_pass and reproducibility["passed"] and resource_pass)

    neighborhood_rows = [
        diagnostic.get("primary_neighborhood_diagnostics", {})
        for payload in payloads.values()
        for diagnostic in payload.get("dominant_diagnostics", [])
    ]
    cola = spec["cola_gate"]
    neighborhood_gate = bool(neighborhood_rows) and all(
        row.get("non_isolated_fraction", 0)
        >= float(cola["requires_primary_non_isolated_fraction"])
        and row.get("degree_at_least_two_fraction", 0)
        >= float(cola["requires_primary_degree_at_least_two_fraction"])
        and row.get("maximum_incident_edge_fraction", 1)
        <= float(cola["maximum_single_primary_incident_edge_fraction"])
        for row in neighborhood_rows
    )
    cola_decision = "deferred"
    cola_reasons = []
    if not overall_pass:
        cola_reasons.append("The required current-method pilot contract did not pass.")
    if not neighborhood_gate:
        cola_reasons.append("The predeclared primary-neighborhood coverage gate did not pass.")
    cola_reasons.append("No label-blind CoLA context-sampler prototype is frozen or tested.")
    cola_reasons.append("Retrieval performance was intentionally not used to activate CoLA.")

    summary = {
        "pilot_id": spec["pilot_id"],
        "study_phase": spec["study_phase"],
        "evidence_role": spec["evidence_role"],
        "confirmation_eligible": spec["confirmation_eligible"],
        "overall_pass": overall_pass,
        "case_contract_pass": case_pass,
        "same_seed_reproducibility_pass": reproducibility["passed"],
        "resource_budget_pass": resource_pass,
        "total_wall_seconds": total_wall,
        "peak_rss_bytes": peak_rss,
        "case_summaries": [
            {
                "case_id": item["case_id"],
                "source_rows": item["source_rows"],
                "canonical_sessions": item["canonical_sessions"],
                "malicious_sessions": item["malicious_sessions"],
                "wall_seconds": item["wall_seconds"],
                "peak_rss_bytes": item["peak_rss_bytes"],
            }
            for item in executions
        ],
        "method_status_counts": methods.groupby(["case_id", "status"])
        .size()
        .rename("count")
        .reset_index()
        .to_dict("records"),
        "hdbscan_status_counts": [
            {
                "case_id": case_id,
                "status": status,
                "count": int(count),
            }
            for case_id, payload in payloads.items()
            for status, count in pd.Series(
                [
                    row["status"]
                    for row in payload.get("scorer_diagnostics", [])
                    if row.get("scorer") == "hdbscan_rare_cluster"
                ]
            ).value_counts().items()
        ],
        "cola_decision": cola_decision,
        "cola_reasons": cola_reasons,
        "performance_interpretation_performed": False,
    }
    write_json_atomic(artifact_root / "pilot_summary.json", summary)
    write_json_atomic(tracked_root / "pilot_summary.json", summary)
    write_json_atomic(tracked_root / "checks.json", validations)
    write_json_atomic(tracked_root / "reproducibility.json", reproducibility)
    methods[[column for column in status_columns if column in methods]].to_csv(
        tracked_root / "method_status.csv", index=False
    )
    representations[
        [
            column
            for column in (
                "pilot_id",
                "case_id",
                "representation_key",
                "representation",
                "hypothesis",
                "representation_seed",
                "status",
                "reason",
                "n_sessions",
                "n_dimensions",
                "labels_available",
            )
            if column in representations
        ]
    ].to_csv(tracked_root / "representation_status.csv", index=False)

    report_lines = [
        "# AutoSignal Phase 2 Pilot — Technical Summary",
        "",
        f"- Pilot: `{spec['pilot_id']}`",
        f"- Overall technical pass: **{overall_pass}**",
        f"- Same-seed reproducibility pass: **{reproducibility['passed']}**",
        f"- Resource budget pass: **{resource_pass}**",
        f"- Total measured wall time: **{total_wall:.2f} seconds**",
        f"- Peak measured RSS: **{peak_rss / (1024 ** 3):.2f} GiB**",
        f"- CoLA gate: **{cola_decision}**",
        "",
        "This pilot is correctness/feasibility evidence only. It is not a final",
        "performance estimate and is not confirmation-eligible. AP, Recall@K,",
        "and UMAP appearance were not used for pass/fail or scope decisions.",
        "",
        "## Cases",
        "",
    ]
    for item in summary["case_summaries"]:
        report_lines.append(
            "- `{case_id}`: {source_rows:,} rows, {canonical_sessions:,} sessions, "
            "{malicious_sessions} malicious sessions, {wall_seconds:.2f}s, "
            "peak RSS {rss:.2f} GiB.".format(
                rss=item["peak_rss_bytes"] / (1024 ** 3),
                **item,
            )
        )
    report_lines.extend(["", "## CoLA decision", ""])
    report_lines.extend(f"- {reason}" for reason in cola_reasons)
    report_lines.extend(
        [
            "",
            "## Known scope limits",
            "",
            "- Only the local ACME development schema was exercised.",
            "- Physical parquet head slices are engineering slices, not temporal slices.",
            "- The grouped/forward-temporal linear probe remains unimplemented; its",
            "  current stratified result is exploratory only.",
            "- The sealed test parquet and combined train/test parquet were not read.",
            "",
        ]
    )
    report = "\n".join(report_lines)
    write_bytes_atomic(artifact_root / "pilot_summary.md", report.encode("utf-8"))
    write_bytes_atomic(tracked_root / "REPORT.md", report.encode("utf-8"))
    return summary


def validate_preflight(spec: dict[str, Any], spec_path: Path) -> dict[str, Any]:
    dataset_path = REPO_ROOT / spec["dataset"]["path"]
    config_path = REPO_ROOT / spec["configuration"]["path"]
    checks = {
        "spec_path": str(spec_path.relative_to(REPO_ROOT)),
        "spec_sha256": sha256_bytes(canonical_json_bytes(spec)),
        "dataset_exists": dataset_path.exists(),
        "dataset_sha256_matches": sha256_file(dataset_path)
        == spec["dataset"]["sha256"],
        "dataset_bytes_match": dataset_path.stat().st_size
        == int(spec["dataset"]["bytes"]),
        "config_exists": config_path.exists(),
        "config_sha256_matches": sha256_file(config_path)
        == spec["configuration"]["source_sha256"],
        "checkpoint_commit_exists": bool(
            git_value("cat-file", "-e", f"{spec['checkpoint_commit']}^{{commit}}")
            is not None
        ),
        "excluded_sources_not_selected": spec["dataset"]["path"]
        not in {item["path"] for item in spec["excluded_sources"]},
        "performance_thresholds_absent": spec["technical_acceptance"]
        .get("performance_thresholds")
        is None,
    }
    checks["passed"] = all(
        value
        for key, value in checks.items()
        if key not in {"spec_path", "spec_sha256", "passed"}
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("experiments/phase2/pilot_v1.json"),
    )
    parser.add_argument("--preflight-only", action="store_true")
    arguments = parser.parse_args()

    spec_path = (
        arguments.spec
        if arguments.spec.is_absolute()
        else REPO_ROOT / arguments.spec
    )
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    preflight = validate_preflight(spec, spec_path)
    print(json.dumps(preflight, indent=2), flush=True)
    if not preflight["passed"]:
        return 2
    if arguments.preflight_only:
        return 0

    pilot_spec_sha256 = preflight["spec_sha256"]
    artifact_root = (
        REPO_ROOT
        / spec["artifact_layout"]["root"]
        / f"{spec['pilot_id']}_{pilot_spec_sha256[:12]}"
    )
    tracked_root = REPO_ROOT / spec["artifact_layout"]["tracked_summary_root"]
    if artifact_root.exists() or tracked_root.exists():
        raise FileExistsError(
            "Refusing to overwrite an existing pilot artifact root. "
            f"Remove or archive it explicitly first: {artifact_root}"
        )
    artifact_root.mkdir(parents=True)
    tracked_root.mkdir(parents=True)
    write_json_atomic(artifact_root / "pilot_spec.json", spec)
    write_bytes_atomic(
        artifact_root / "pilot_spec.sha256",
        f"{pilot_spec_sha256}  pilot_spec.json\n".encode("ascii"),
    )
    write_json_atomic(artifact_root / "preflight.json", preflight)

    provenance = {
        "pilot_id": spec["pilot_id"],
        "created_at_utc": utc_now(),
        "pilot_spec_sha256": pilot_spec_sha256,
        "git_commit": git_value("rev-parse", "HEAD"),
        "working_tree_status": git_value("status", "--short"),
        "engine_sha256": sha256_file(NOTEBOOK_DIR / "autosignal_engine.py"),
        "analysis_sha256": sha256_file(NOTEBOOK_DIR / "autosignal_analysis.py"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "requirements_sha256": sha256_file(
            NOTEBOOK_DIR / "requirements-autosignal.txt"
        ),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "total_memory_bytes": int(psutil.virtual_memory().total),
    }
    write_json_atomic(artifact_root / "provenance.json", provenance)

    selected_config = select_config(spec)
    dataset_path = REPO_ROOT / spec["dataset"]["path"]
    payloads: dict[str, dict[str, Any]] = {}
    executions = []
    validations = []
    for case in spec["cases"]:
        payload, execution, validation = run_case(
            spec=spec,
            case=case,
            selected_config=selected_config,
            dataset_path=dataset_path,
            artifact_root=artifact_root,
            pilot_spec_sha256=pilot_spec_sha256,
        )
        payloads[case["case_id"]] = payload
        executions.append(execution)
        validations.append(validation)

    groups: dict[str, list[str]] = {}
    for case in spec["cases"]:
        group = case.get("reproducibility_group")
        if group:
            groups.setdefault(group, []).append(case["case_id"])
    reproducibility_checks = []
    for group, case_ids in groups.items():
        if len(case_ids) != 2:
            raise ValueError(
                f"Reproducibility group {group!r} must contain exactly two cases."
            )
        comparison = compare_reproducibility(
            payloads[case_ids[0]],
            payloads[case_ids[1]],
            rtol=float(spec["technical_acceptance"]["same_seed_score_rtol"]),
            atol=float(spec["technical_acceptance"]["same_seed_score_atol"]),
        )
        reproducibility_checks.append(
            {"group": group, "case_ids": case_ids, **comparison}
        )
    reproducibility = {
        "passed": bool(reproducibility_checks)
        and all(item["passed"] for item in reproducibility_checks),
        "groups": reproducibility_checks,
    }
    summary = write_derived_artifacts(
        spec=spec,
        artifact_root=artifact_root,
        tracked_root=tracked_root,
        payloads=payloads,
        executions=executions,
        validations=validations,
        reproducibility=reproducibility,
    )
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
