from __future__ import annotations

import json
import unittest

import numpy as np
import pandas as pd

from autosignal import EngineConfig, SignalLocalizationEngine
from autosignal.config import ConfigurationError


def make_events() -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    for user_index in range(8):
        previous = None
        for event_index in range(5):
            process_id = f"p{user_index}_{event_index}"
            rows.append(
                {
                    "process": process_id,
                    "parent": previous,
                    "timestamp": start
                    + pd.Timedelta(
                        minutes=10 * user_index,
                        seconds=20 * event_index,
                    ),
                    "executable": f"exe_{(user_index + event_index) % 4}",
                    "user": f"user_{user_index}",
                    "host": f"host_{user_index % 2}",
                    "process_name": f"process_{event_index}",
                    "feature_a": float(user_index + event_index / 10),
                    "feature_b": float((user_index * event_index) % 5),
                    "label": int(user_index == 7),
                }
            )
            previous = process_id
    return pd.DataFrame(rows)


def make_config(
    *,
    mode: str = "score_only",
    methods: list[str] | None = None,
    renamed: bool = False,
) -> EngineConfig:
    names = (
        {
            "process_id": "event_id",
            "parent_process_id": "ancestor_id",
            "timestamp": "event_time",
            "executable": "image",
            "user": "principal",
            "host": "asset",
            "process_name": "image_name",
            "label": "target",
        }
        if renamed
        else {
            "process_id": "process",
            "parent_process_id": "parent",
            "timestamp": "timestamp",
            "executable": "executable",
            "user": "user",
            "host": "host",
            "process_name": "process_name",
            "label": "label",
        }
    )
    features = ["signal_one", "signal_two"] if renamed else [
        "feature_a",
        "feature_b",
    ]
    return EngineConfig.from_dict(
        {
            "schema": names,
            "features": {"numeric": features},
            "evaluation": {"mode": mode},
            "methods": methods or ["raw", "m1"],
            "scoring": {"k": 2, "budgets": [2, 4]},
            "seeds": [42],
            "device": "cpu",
            "fail_fast": True,
        }
    )


class ConfigurationTests(unittest.TestCase):
    def test_unknown_and_label_feature_fields_are_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            EngineConfig.from_dict(
                {
                    "schema": {
                        "process_id": "p",
                        "parent_process_id": "pp",
                        "timestamp": "t",
                        "executable": "x",
                        "user": "u",
                    },
                    "features": {"numeric": ["f"], "python": "print(1)"},
                }
            )

    def test_configuration_json_round_trip_is_strict(self) -> None:
        config = make_config()
        self.assertEqual(
            EngineConfig.from_json(config.to_json()).to_dict(),
            config.to_dict(),
        )
        with self.assertRaises(ConfigurationError):
            EngineConfig.from_json('{"schema":')
        with self.assertRaises(ConfigurationError):
            EngineConfig.from_dict(
                {
                    **config.to_dict(),
                    "contract_version": "999",
                }
            )
        with self.assertRaises(ConfigurationError):
            EngineConfig.from_dict(
                {
                    "schema": {
                        "process_id": "p",
                        "parent_process_id": "pp",
                        "timestamp": "t",
                        "executable": "x",
                        "user": "u",
                        "label": "truth",
                    },
                    "features": {"numeric": ["truth"]},
                }
            )


class EngineContractTests(unittest.TestCase):
    def test_dynamic_schema_mapping_preserves_scores(self) -> None:
        original = make_events()
        renamed = original.rename(
            columns={
                "process": "event_id",
                "parent": "ancestor_id",
                "timestamp": "event_time",
                "executable": "image",
                "user": "principal",
                "host": "asset",
                "process_name": "image_name",
                "feature_a": "signal_one",
                "feature_b": "signal_two",
                "label": "target",
            }
        )
        left = SignalLocalizationEngine(make_config()).run(original).to_dict()
        right = SignalLocalizationEngine(
            make_config(renamed=True)
        ).run(renamed).to_dict()

        self.assertEqual(left["session_manifest"], right["session_manifest"])
        self.assertEqual(left["graph_manifest"], right["graph_manifest"])
        for method in ("raw", "m1"):
            np.testing.assert_allclose(
                left["methods"][method]["runs"][0]["scores"],
                right["methods"][method]["runs"][0]["scores"],
                rtol=0,
                atol=1e-12,
            )

    def test_score_only_does_not_read_or_hash_labels(self) -> None:
        frame = make_events()
        changed = frame.copy()
        changed["label"] = 1 - changed["label"]
        engine = SignalLocalizationEngine(make_config(mode="score_only"))
        left = engine.run(frame).to_dict()
        right = engine.run(changed).to_dict()

        self.assertFalse(left["run_policy"]["labels_read"])
        self.assertIsNone(left["session_manifest"]["malicious_sessions"])
        self.assertEqual(left["data_manifest"], right["data_manifest"])
        self.assertEqual(left["methods"], right["methods"])
        self.assertEqual(left["payload_sha256"], right["payload_sha256"])

    def test_development_selects_but_locked_evaluation_does_not(self) -> None:
        frame = make_events()
        development = SignalLocalizationEngine(
            make_config(mode="development")
        ).run(frame).to_dict()
        locked = SignalLocalizationEngine(
            make_config(mode="locked_evaluation")
        ).run(frame).to_dict()

        self.assertTrue(development["selection"]["eligible"])
        self.assertIsNotNone(development["selection"]["winner"])
        self.assertFalse(locked["selection"]["eligible"])
        self.assertIsNone(locked["selection"]["winner"])
        self.assertEqual(locked["session_manifest"]["malicious_sessions"], 1)

    def test_full_battery_smoke_and_json_payload(self) -> None:
        base = make_config(mode="development", methods=["raw", "m1", "m2", "m3"])
        raw = base.to_dict()
        raw.pop("contract_version")
        raw["node2vec"] = {
            "embedding_dim": 8,
            "walk_length": 4,
            "context_size": 2,
            "walks_per_node": 1,
            "epochs": 1,
            "batch_size": 32,
        }
        raw["graphsage"] = {
            "hidden_dim": 8,
            "output_dim": 8,
            "epochs": 1,
            "max_positive_edges_per_relation": 50,
        }
        result = SignalLocalizationEngine(
            EngineConfig.from_dict(raw)
        ).run(make_events()).to_dict()

        self.assertEqual(result["session_manifest"]["sessions"], 8)
        for method in ("raw", "m1", "m2", "m3", "m3_random_init"):
            self.assertEqual(result["methods"][method]["status"], "ok")
        self.assertEqual(result["methods"]["m2"]["representation_dimension"], 9)
        self.assertEqual(result["methods"]["m3"]["representation_dimension"], 9)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
