import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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
from autosignal_analysis import (
    evaluate_representation,
    isolation_forest_anomaly_scores,
    rare_cluster_anomaly_scores,
    representation_stability,
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


def single_feature_config():
    config = renamed_config()
    retained = set(config["feature_sets"][0]["columns"])
    config["selected_columns"] = [
        item
        for item in config["selected_columns"]
        if item["column"] in retained
    ]
    config["feature_sets"] = [config["feature_sets"][0]]
    return config


class AutoSignalEngineTests(unittest.TestCase):
    def test_graph_construction_failure_declares_every_planned_outcome(self):
        df = renamed_telemetry(48)
        with patch(
            "autosignal_engine.build_typed_graph",
            side_effect=RuntimeError("forced graph failure"),
        ):
            result = run_autosignal(
                df,
                single_feature_config(),
                k=3,
                seeds=(42,),
                graph_epochs=1,
                signal_permutations=99,
            )

        methods = pd.DataFrame(result["method_results"])
        self.assertEqual(len(methods), 18)
        self.assertEqual(methods["method_key"].nunique(), 18)
        graph_dependent = methods.loc[
            ~methods["representation"].isin(["random_score", "raw_session"])
        ]
        self.assertEqual(len(graph_dependent), 14)
        self.assertTrue(graph_dependent["status"].eq("failed").all())
        self.assertTrue(
            graph_dependent["error"].str.contains("forced graph failure").all()
        )

        representations = pd.DataFrame(result["representation_results"])
        self.assertEqual(len(representations), 7)
        self.assertEqual(representations["representation_key"].nunique(), 7)
        self.assertEqual(int(representations["status"].eq("completed").sum()), 1)
        self.assertEqual(int(representations["status"].eq("failed").sum()), 6)
        json.dumps(result, allow_nan=False)

    def test_representation_evaluation_uses_full_space_and_is_deterministic(self):
        representation = np.asarray(
            [[0.0], [0.1], [10.0], [10.1]], dtype=float
        )
        labels = np.asarray(
            ["malicious", "malicious", "benign", "benign"]
        )
        first = evaluate_representation(
            representation,
            labels,
            k=1,
            n_permutations=99,
            random_state=17,
        )
        second = evaluate_representation(
            representation,
            labels,
            k=1,
            n_permutations=99,
            random_state=17,
        )

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "completed")
        self.assertEqual(first["effective_k"], 1)
        self.assertEqual(first["malicious_neighbor_purity"], 1.0)
        self.assertAlmostEqual(
            first["neighbor_purity_prevalence_reference"], 1 / 3
        )
        self.assertGreater(first["label_silhouette"], 0.9)
        self.assertGreaterEqual(first["linear_probe_average_precision"], 0.5)

        unavailable = evaluate_representation(
            representation,
            None,
            k=1,
            n_permutations=99,
        )
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertFalse(unavailable["labels_available"])
        self.assertIsNone(unavailable["malicious_neighbor_purity"])

    def test_isolation_forest_is_deterministic_and_scores_far_point_highest(self):
        rng = np.random.default_rng(9)
        representation = np.vstack(
            [rng.normal(0, 0.05, size=(32, 2)), np.asarray([[8.0, 8.0]])]
        )
        first, first_diagnostics = isolation_forest_anomaly_scores(
            representation,
            random_state=23,
            n_estimators=64,
        )
        second, second_diagnostics = isolation_forest_anomaly_scores(
            representation,
            random_state=23,
            n_estimators=64,
        )

        np.testing.assert_allclose(first, second, rtol=0, atol=0)
        self.assertEqual(first_diagnostics, second_diagnostics)
        self.assertEqual(int(np.argmax(first)), len(representation) - 1)
        self.assertTrue(np.isfinite(first).all())

    def test_rare_cluster_scorer_promotes_separated_coherent_population(self):
        rng = np.random.default_rng(11)
        dominant = rng.normal(0, 0.08, size=(50, 2))
        rare = rng.normal(7, 0.08, size=(10, 2))
        representation = np.vstack([dominant, rare])

        first, assignments, diagnostics = rare_cluster_anomaly_scores(
            representation,
            min_cluster_size=5,
            dominance_ratio=1.25,
        )
        second, second_assignments, second_diagnostics = (
            rare_cluster_anomaly_scores(
                representation,
                min_cluster_size=5,
                dominance_ratio=1.25,
            )
        )

        self.assertEqual(diagnostics["status"], "completed")
        self.assertEqual(diagnostics, second_diagnostics)
        np.testing.assert_array_equal(assignments, second_assignments)
        np.testing.assert_allclose(first, second, rtol=0, atol=0)
        self.assertGreater(first[50:].mean(), first[:50].mean())
        self.assertTrue(np.isfinite(first).all())

    def test_representation_stability_is_rotation_invariant(self):
        rng = np.random.default_rng(13)
        first = rng.normal(size=(24, 2))
        rotation = np.asarray([[0.0, -1.0], [1.0, 0.0]])
        second = first @ rotation
        stability = representation_stability(first, second, k=4)

        self.assertEqual(stability["status"], "completed")
        self.assertAlmostEqual(stability["distance_rank_correlation"], 1.0)
        self.assertAlmostEqual(stability["mean_neighbor_jaccard"], 1.0)

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

        environment = result["run_manifest"]["software_environment"]
        self.assertRegex(environment["python"], r"^\d+\.\d+\.\d+$")
        self.assertIsNotNone(environment["packages"]["scikit-learn"])

        method_results = pd.DataFrame(result["method_results"])
        self.assertFalse(method_results["status"].eq("failed").any())
        self.assertTrue(
            method_results["status"].isin(
                ["completed", "abstained", "degenerate", "unavailable"]
            ).all()
        )
        self.assertEqual(len(method_results), 40)
        self.assertEqual(method_results["method_key"].nunique(), 40)

        session_count = result["run_manifest"]["sessions"]
        scores = pd.DataFrame(result["session_scores"])
        per_method_counts = scores.groupby("method_key")["session_id"].nunique()
        self.assertTrue((per_method_counts == session_count).all())
        self.assertEqual(
            set(scores["method_key"]),
            set(
                method_results.loc[
                    method_results["status"].eq("completed"), "method_key"
                ]
            ),
        )
        self.assertFalse(
            scores.duplicated(["method_key", "session_id"]).any()
        )
        self.assertEqual(result["graph_manifest"]["primary_id_column"], "process_key")

        representation_results = pd.DataFrame(result["representation_results"])
        self.assertEqual(len(representation_results), 17)
        self.assertEqual(representation_results["representation_key"].nunique(), 17)
        self.assertTrue(representation_results["status"].eq("completed").all())
        for record in result["representation_results"]:
            self.assertEqual(record["n_sessions"], session_count)
            self.assertEqual(
                len(record["dimension_names"]), record["n_dimensions"]
            )

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
        components = pd.DataFrame(result["score_components"])
        dominant_components = components[
            components["scorer"].eq("dominant_joint_reconstruction")
        ].dropna(subset=["attribute_error"])
        self.assertFalse(dominant_components.empty)
        np.testing.assert_allclose(
            dominant_components["joint_score"].to_numpy(),
            0.5 * dominant_components["attribute_error"].to_numpy()
            + 0.5 * dominant_components["structure_error"].to_numpy(),
            rtol=1e-6,
            atol=1e-6,
        )
        json.dumps(result, allow_nan=False)

    def test_score_only_mode_is_label_isolated(self):
        df = renamed_telemetry()
        config = single_feature_config()
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
        self.assertTrue(
            all(
                record["status"] == "unavailable"
                and not record["labels_available"]
                for record in first["representation_results"]
            )
        )

    def test_configured_development_labels_do_not_change_label_free_outputs(self):
        df = renamed_telemetry(rows=48)
        config = single_feature_config()
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

        for table_name, value_columns in (
            ("session_scores", ["score"]),
            ("embeddings", ["x", "y"]),
        ):
            first_table = pd.DataFrame(first[table_name]).sort_values(
                ["method_key", "session_id"]
            )
            second_table = pd.DataFrame(second[table_name]).sort_values(
                ["method_key", "session_id"]
            )
            self.assertEqual(
                first_table[["method_key", "session_id"]].to_dict("records"),
                second_table[["method_key", "session_id"]].to_dict("records"),
            )
            np.testing.assert_allclose(
                first_table[value_columns].to_numpy(dtype=float),
                second_table[value_columns].to_numpy(dtype=float),
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
        first_components = pd.DataFrame(first["score_components"]).sort_values(
            ["method_key", "session_id"]
        ).reset_index(drop=True)
        second_components = pd.DataFrame(second["score_components"]).sort_values(
            ["method_key", "session_id"]
        ).reset_index(drop=True)
        pd.testing.assert_frame_equal(
            first_components,
            second_components,
            check_exact=False,
            rtol=1e-6,
            atol=1e-6,
        )

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

    def test_label_cannot_enter_session_or_graph_construction(self):
        df = renamed_telemetry()
        for mutate in (
            lambda cfg: cfg.update(timestamp_col="is_attack"),
            lambda cfg: cfg.update(existing_session_id_col="is_attack"),
            lambda cfg: cfg["session_group_cols"].append("is_attack"),
            lambda cfg: cfg["graph_relations"][0].update(
                source_column="is_attack"
            ),
        ):
            config = renamed_config()
            mutate(config)
            with self.assertRaises(ConfigValidationError):
                validate_config(config, df)


if __name__ == "__main__":
    unittest.main()
