"""ML-01 guards for audited split boundaries and Fake-positive metrics."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml.src.train_classic_models import evaluate, load_splits


class ConstantPredictions:
    def __init__(self, predictions):
        self.predictions = predictions

    def predict(self, texts):
        return self.predictions[:len(texts)]


class ClassicModelTests(unittest.TestCase):
    def fixture(self):
        rows = []
        for split, start in (("train", 0), ("validation", 2), ("test", 4)):
            for offset in range(2):
                row_id = start + offset
                rows.append({
                    "_row_id": row_id,
                    "group_id": row_id,
                    "_clean_key": f"unique body {row_id}",
                    "text_clean": f"article body number {row_id}",
                    "label": offset,
                    "split": split,
                })
        return pd.DataFrame(rows)

    def test_cross_split_group_is_rejected(self):
        frame = self.fixture()
        frame.loc[frame["_row_id"].eq(4), "group_id"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prepared_splits.csv"
            frame.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "group_id"):
                load_splits(path)

    def test_cross_split_content_is_rejected(self):
        frame = self.fixture()
        frame.loc[frame["_row_id"].eq(4), "_clean_key"] = "unique body 0"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prepared_splits.csv"
            frame.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "_clean_key"):
                load_splits(path)

    def test_fake_is_positive_class_and_matrix_order_is_explicit(self):
        part = pd.DataFrame({"text_clean": ["fake article", "real article"], "label": [0, 1]})
        result = evaluate(ConstantPredictions([1, 1]), part)
        self.assertEqual(result["f1_fake"], 0.0)
        self.assertEqual(result["confusion_matrix_rows_fake_real"], [[0, 1], [0, 1]])


if __name__ == "__main__":
    unittest.main()
