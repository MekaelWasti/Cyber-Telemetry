from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import run_matrix as runner


class Phase4RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(
            (runner.REPO_ROOT / "experiments/phase3/matrix_v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_quota_allocation_is_exact_and_balanced(self):
        quotas = runner.allocate_quotas(25000, 3)
        self.assertEqual(quotas, [8334, 8333, 8333])
        self.assertEqual(sum(quotas), 25000)

    def test_session_sampling_preserves_whole_sessions_and_row_cap(self):
        sessions = [[index] * size for index, size in enumerate([2, 5, 7, 11])]
        selected = runner.lowest_hash_sessions_with_row_cap(
            sessions=sessions,
            session_quota=4,
            row_quota=13,
            digest_for_session=lambda session_id: bytes([session_id]) * 32,
        )
        self.assertLessEqual(sum(row_count for _, _, row_count in selected), 13)
        self.assertEqual(
            {session_id for session_id, _, _ in selected},
            {0, 1},
        )

    def test_graph_null_changes_targets_and_preserves_counts(self):
        frame = pd.DataFrame(
            {
                "source": ["a", "a", "b", "c", "c", "d"],
                "target": ["x", "y", "x", "z", "z", "y"],
            }
        )
        config = {
            "graph_relations": [
                {
                    "relation_name": "connects",
                    "source_column": "source",
                    "target_column": "target",
                }
            ]
        }
        shuffled, shuffled_config, diagnostics = runner.graph_null_frame(
            self.matrix,
            "test_dataset",
            "test_partition",
            frame,
            config,
        )
        control_column = shuffled_config["graph_relations"][0]["target_column"]
        self.assertNotEqual(control_column, "target")
        self.assertFalse(shuffled[control_column].equals(shuffled["target"]))
        self.assertEqual(
            shuffled[control_column].value_counts().sort_index().to_dict(),
            shuffled["target"].value_counts().sort_index().to_dict(),
        )
        self.assertEqual(len(diagnostics), 1)

    def test_confirmation_role_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "confirmation remains sealed"):
            runner.selected_cases(
                self.matrix,
                dataset_ids=None,
                roles=["sealed_confirmation"],
            )


if __name__ == "__main__":
    unittest.main()
