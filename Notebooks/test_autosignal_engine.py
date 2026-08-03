import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autosignal_engine import (
    ConfigValidationError,
    apply_matched_amplification,
    build_session_knn_operator,
    compute_signal_diagnostic_channels,
    pick_signal_regime,
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
    def test_signal_channels_and_matched_amplifiers_match_formulas(self):
        propagation = sparse.csr_matrix(
            [
                [0.0, 1.0, 0.0],
                [0.5, 0.0, 0.5],
                [0.0, 1.0, 0.0],
            ]
        )
        intrinsic = np.asarray([1.0, 2.0, 4.0])
        channels = compute_signal_diagnostic_channels(
            propagation,
            intrinsic,
        )

        expected_neighbor_support = np.asarray([2.0, 2.5, 2.0])
        expected_second_hop = np.asarray([2.5, 2.0, 2.5])
        expected_local_contrast = np.asarray([-1.0, -0.5, 2.0])
        expected_pocket = np.asarray([-0.5, 0.5, -0.5])
        np.testing.assert_allclose(
            channels["intrinsic"],
            intrinsic,
        )
        np.testing.assert_allclose(
            channels["neighbor_support"],
            expected_neighbor_support,
        )
        np.testing.assert_allclose(
            channels["second_hop_support"],
            expected_second_hop,
        )
        np.testing.assert_allclose(
            channels["local_contrast"],
            expected_local_contrast,
        )
        np.testing.assert_allclose(
            channels["local_contrast_magnitude"],
            np.abs(expected_local_contrast),
        )
        np.testing.assert_allclose(
            channels["pocket"],
            expected_pocket,
        )
        np.testing.assert_allclose(
            channels["supported_candidate"],
            0.5 * intrinsic + 0.5 * expected_neighbor_support,
        )

        np.testing.assert_allclose(
            apply_matched_amplification(
                intrinsic,
                channels,
                "Neighborhood-supported",
                alpha=0.25,
            ),
            0.25 * intrinsic + 0.75 * expected_neighbor_support,
        )
        np.testing.assert_allclose(
            apply_matched_amplification(
                intrinsic,
                channels,
                "Locally Contrastive",
            ),
            expected_local_contrast,
        )
        np.testing.assert_allclose(
            apply_matched_amplification(
                intrinsic,
                channels,
                "Intermediate-scale",
            ),
            expected_pocket,
        )
        np.testing.assert_allclose(
            apply_matched_amplification(
                intrinsic,
                channels,
                "No useful organization",
            ),
            intrinsic,
        )
        with self.assertRaisesRegex(ValueError, "Unknown signal regime"):
            apply_matched_amplification(
                intrinsic,
                channels,
                "Unsupported regime",
            )

    def test_session_knn_operator_handles_duplicate_rows_without_isolates(self):
        representation = np.asarray(
            [
                [0.0, 0.0],
                [0.0, 0.0],
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 0.0],
                [2.0, 0.0],
            ],
            dtype=float,
        )
        adjacency, propagation = build_session_knn_operator(
            representation,
            k=2,
        )

        self.assertEqual(adjacency.shape, (len(representation),) * 2)
        self.assertEqual(propagation.shape, adjacency.shape)
        self.assertEqual(adjacency.diagonal().sum(), 0.0)
        self.assertEqual((adjacency != adjacency.T).nnz, 0)
        degrees = np.asarray(adjacency.sum(axis=1)).ravel()
        self.assertTrue(np.all(degrees > 0))
        np.testing.assert_allclose(
            np.asarray(propagation.sum(axis=1)).ravel(),
            np.ones(len(representation)),
            rtol=0,
            atol=1e-12,
        )

    def test_signal_regime_picker_is_deterministically_neighborhood_supported(
        self,
    ):
        high_group_size = 12
        low_group_size = 48

        def clique_operator(size):
            adjacency = np.ones((size, size), dtype=float)
            np.fill_diagonal(adjacency, 0.0)
            return sparse.csr_matrix(adjacency / (size - 1))

        propagation = sparse.block_diag(
            [
                clique_operator(high_group_size),
                clique_operator(low_group_size),
            ],
            format="csr",
        )
        scores = np.concatenate(
            [
                np.linspace(10.0, 11.0, high_group_size),
                np.linspace(0.0, 1.0, low_group_size),
            ]
        )

        first = pick_signal_regime(
            propagation,
            scores,
            n_permutations=99,
            random_state=17,
        )
        second = pick_signal_regime(
            propagation,
            scores,
            n_permutations=99,
            random_state=17,
        )

        self.assertEqual(first, second)
        self.assertEqual(first["regime"], "Neighborhood-supported")
        neighborhood_evidence = first["evidence"][0]
        self.assertTrue(neighborhood_evidence["passes"])
        self.assertLessEqual(neighborhood_evidence["familywise_p"], 0.05)

    def test_renamed_schema_runs_complete_battery_with_aligned_scores(self):
        df = renamed_telemetry()
        result = run_autosignal(
            df,
            renamed_config(),
            k=3,
            seeds=(42,),
            graph_epochs=1,
            signal_permutations=99,
        )

        method_results = pd.DataFrame(result["method_results"])
        self.assertTrue(method_results["status"].eq("completed").all())
        self.assertEqual(len(method_results), 12)

        session_count = result["run_manifest"]["sessions"]
        scores = pd.DataFrame(result["session_scores"])
        per_method_counts = scores.groupby("method_key")["session_id"].nunique()
        self.assertTrue((per_method_counts == session_count).all())
        self.assertEqual(result["graph_manifest"]["primary_id_column"], "process_key")

        non_random_method_keys = set(
            scores.loc[
                scores["method"].ne("random_baseline"),
                "method_key",
            ]
        )
        signal_results = pd.DataFrame(result["signal_results"])
        self.assertEqual(
            set(signal_results["method_key"]),
            non_random_method_keys,
        )
        self.assertEqual(
            len(signal_results),
            len(non_random_method_keys),
        )
        self.assertTrue(
            signal_results["status"].isin(
                ["completed", "unavailable"]
            ).all()
        )
        self.assertNotIn(
            "random_baseline::seed=42",
            set(signal_results["method_key"]),
        )

        signal_scores = pd.DataFrame(result["signal_scores"])
        self.assertFalse(
            signal_scores["method"].eq("random_baseline").any()
        )
        completed_signal_keys = set(
            signal_results.loc[
                signal_results["status"].eq("completed"),
                "method_key",
            ]
        )
        self.assertEqual(
            set(signal_scores["method_key"]),
            completed_signal_keys,
        )
        for method_key in completed_signal_keys:
            method_signal_scores = signal_scores[
                signal_scores["method_key"].eq(method_key)
            ]
            self.assertEqual(len(method_signal_scores), session_count)
            self.assertEqual(
                method_signal_scores["session_id"].nunique(),
                session_count,
            )
            aligned = (
                method_signal_scores[["session_id", "intrinsic"]]
                .merge(
                    scores[
                        scores["method_key"].eq(method_key)
                    ][["session_id", "score"]],
                    on="session_id",
                    how="inner",
                    validate="one_to_one",
                )
                .sort_values("session_id")
            )
            self.assertEqual(len(aligned), session_count)
            np.testing.assert_allclose(
                aligned["intrinsic"].to_numpy(),
                aligned["score"].to_numpy(),
                rtol=0,
                atol=0,
            )
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
            signal_permutations=99,
        )
        second = run_autosignal(
            changed_labels,
            config,
            k=3,
            seeds=(42,),
            graph_epochs=1,
            signal_permutations=99,
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

        def label_blind_signal_results(payload):
            return sorted(
                [
                    {
                        key: value
                        for key, value in record.items()
                        if key != "evaluation"
                    }
                    for record in payload["signal_results"]
                ],
                key=lambda record: record["method_key"],
            )

        self.assertEqual(
            label_blind_signal_results(first),
            label_blind_signal_results(second),
        )
        first_signal_scores = (
            pd.DataFrame(first["signal_scores"])
            .drop(columns=["label"])
            .sort_values(["method_key", "session_id"])
            .reset_index(drop=True)
        )
        second_signal_scores = (
            pd.DataFrame(second["signal_scores"])
            .drop(columns=["label"])
            .sort_values(["method_key", "session_id"])
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(
            first_signal_scores,
            second_signal_scores,
            check_exact=False,
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
