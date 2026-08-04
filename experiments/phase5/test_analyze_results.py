import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from experiments.phase5.analyze_results import (
    bootstrap_config_metrics,
    holm_adjust,
    order_and_ties,
)


class Phase5AnalysisTests(unittest.TestCase):
    def test_weighted_bootstrap_matches_unweighted_metrics(self):
        labels = np.asarray([1, 0, 1, 0, 0], dtype=np.int8)
        scores = np.asarray([0.7, 0.7, 0.2, 0.1, 0.0], dtype=np.float64)
        order, ties = order_and_ties(scores)
        ap, recall = bootstrap_config_metrics(
            order[None, :],
            ties[None, :],
            labels,
            np.arange(len(labels), dtype=np.int32),
            np.ones((1, len(labels)), dtype=np.int16),
            3,
        )
        self.assertAlmostEqual(ap[0], average_precision_score(labels, scores))
        expected_order = np.argsort(-scores, kind="mergesort")
        self.assertAlmostEqual(recall[0], labels[expected_order[:3]].sum() / labels.sum())

    def test_holm_adjustment_is_monotone_in_sorted_order(self):
        raw = pd.Series([0.01, 0.04, 0.03], index=["a", "b", "c"])
        adjusted = holm_adjust(raw)
        self.assertAlmostEqual(adjusted["a"], 0.03)
        self.assertAlmostEqual(adjusted["c"], 0.06)
        self.assertAlmostEqual(adjusted["b"], 0.06)


if __name__ == "__main__":
    unittest.main()
