import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autosignal_engine import (
    ConfigValidationError,
    run_autosignal,
    validate_config,
)


def renamed_telemetry(rows=80):
    rng = np.random.default_rng(7)
    timestamps = pd.date_range(
        "2026-01-01T00:00:00Z",
        periods=rows,
        freq="2min",
    )
    process_ids = [f"proc-{index}" for index in range(rows)]
    return pd.DataFrame(
        {
            "event_ts": timestamps.astype(str),
            "device_key": [f"device-{index % 5}" for index in range(rows)],
            "account_key": [f"user-{index % 3}" for index in range(rows)],
            "process_key": process_ids,
            "parent_key": [
                process_ids[index - 1] if index and index % 8 else None
                for index in range(rows)
            ],
            "image_key": [f"image-{index % 9}" for index in range(rows)],
            "compute_measure": rng.lognormal(3, 1, rows),
            "memory_measure": rng.lognormal(4, 0.7, rows),
            "local_read_count": rng.poisson(4, rows),
            "local_write_count": rng.poisson(2, rows),
            "connection_count": rng.poisson(1, rows),
            "bytes_out": rng.lognormal(5, 1.2, rows),
            "is_attack": [1 if index in {17, 61} else 0 for index in range(rows)],
        }
    )


def renamed_config():
    return {
        "timestamp_col": "event_ts",
        "existing_session_id_col": None,
        "session_group_cols": ["device_key", "account_key"],
        "graph_relations": [
            {
                "relation_name": "parent_of",
                "source_node_type": "process",
                "source_column": "parent_key",
                "target_node_type": "process",
                "target_column": "process_key",
                "directed": True,
                "meaning": "Observed process lineage.",
            },
            {
                "relation_name": "executes",
                "source_node_type": "process",
                "source_column": "process_key",
                "target_node_type": "executable",
                "target_column": "image_key",
                "directed": True,
                "meaning": "Observed executable identity.",
            },
            {
                "relation_name": "runs_on",
                "source_node_type": "process",
                "source_column": "process_key",
                "target_node_type": "host",
                "target_column": "device_key",
                "directed": True,
                "meaning": "Observed execution endpoint.",
            },
        ],
        "label_col": "is_attack",
        "malicious_label_values": [1],
        "selected_columns": [
            {
                "column": "compute_measure",
                "type": "numeric",
                "reason": "Compute intensity.",
            },
            {
                "column": "memory_measure",
                "type": "numeric",
                "reason": "Memory intensity.",
            },
            {
                "column": "local_read_count",
                "type": "numeric",
                "reason": "Local reads.",
            },
            {
                "column": "local_write_count",
                "type": "numeric",
                "reason": "Local writes.",
            },
            {
                "column": "connection_count",
                "type": "numeric",
                "reason": "Connection volume.",
            },
            {
                "column": "bytes_out",
                "type": "numeric",
                "reason": "Outbound volume.",
            },
        ],
        "feature_sets": [
            {
                "name": "Resource profile",
                "columns": ["compute_measure", "memory_measure"],
                "rationale": "Resource behavior.",
            },
            {
                "name": "Local I/O profile",
                "columns": ["local_read_count", "local_write_count"],
                "rationale": "Local state behavior.",
            },
            {
                "name": "Network profile",
                "columns": ["connection_count", "bytes_out"],
                "rationale": "Network behavior.",
            },
        ],
    }


class AutoSignalEngineTests(unittest.TestCase):
    def test_renamed_schema_runs_complete_battery_with_aligned_scores(self):
        df = renamed_telemetry()
        result = run_autosignal(
            df,
            renamed_config(),
            k=3,
            seeds=(42,),
            graph_epochs=1,
        )

        method_results = pd.DataFrame(result["method_results"])
        self.assertTrue(method_results["status"].eq("completed").all())
        self.assertEqual(len(method_results), 12)

        session_count = result["run_manifest"]["sessions"]
        scores = pd.DataFrame(result["session_scores"])
        per_method_counts = scores.groupby("method_key")["session_id"].nunique()
        self.assertTrue((per_method_counts == session_count).all())
        self.assertEqual(result["graph_manifest"]["primary_id_column"], "process_key")
        json.dumps(result)

    def test_score_only_mode_is_label_isolated(self):
        df = renamed_telemetry()
        config = renamed_config()
        config["label_col"] = None

        changed_labels = df.copy()
        changed_labels["is_attack"] = 1 - changed_labels["is_attack"]

        first = run_autosignal(
            df,
            config,
            k=3,
            seeds=(42,),
            graph_epochs=1,
        )
        second = run_autosignal(
            changed_labels,
            config,
            k=3,
            seeds=(42,),
            graph_epochs=1,
        )
        first_scores = pd.DataFrame(first["session_scores"]).sort_values(
            ["method_key", "session_id"]
        )
        second_scores = pd.DataFrame(second["session_scores"]).sort_values(
            ["method_key", "session_id"]
        )
        np.testing.assert_allclose(
            first_scores["score"].to_numpy(),
            second_scores["score"].to_numpy(),
            rtol=1e-6,
            atol=1e-6,
        )
        self.assertEqual(first["run_manifest"]["mode"], "score_only")

    def test_label_cannot_be_selected_as_a_feature(self):
        df = renamed_telemetry()
        config = renamed_config()
        config["selected_columns"].append(
            {
                "column": "is_attack",
                "type": "numeric",
                "reason": "Invalid leakage.",
            }
        )
        config["feature_sets"][0]["columns"].append("is_attack")
        with self.assertRaises(ConfigValidationError):
            validate_config(config, df)


if __name__ == "__main__":
    unittest.main()
