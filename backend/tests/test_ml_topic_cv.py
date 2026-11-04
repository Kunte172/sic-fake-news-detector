"""ML-02 guards: label-free topics, grouped articles, held-out topics, one-label topics."""

import unittest
import warnings

import numpy as np
import pandas as pd

from ml.src.topic_cv import (
    assert_no_leakage, discover_topics, evaluate_topics, leave_one_topic_out,
    summarize_topics,
)

TOPIC_WORDS = {
    0: "senate budget tax committee ballot governor policy election",
    1: "market shares inflation bank earnings dollar trade economy",
    2: "storm rainfall flood coast wildfire drought climate rescue",
    3: "tournament league coach stadium season playoff striker referee",
}


def corpus(single_label_topic=None, per_label=30):
    rng = np.random.default_rng(7)
    rows = []
    for topic, words in TOPIC_WORDS.items():
        vocabulary = words.split()
        for label in (0, 1):
            if single_label_topic == topic and label == 1:
                continue
            for _ in range(per_label):
                body = " ".join(rng.choice(vocabulary, size=24))
                rows.append({"text_clean": body, "label": label, "true_topic": topic})
    frame = pd.DataFrame(rows)
    frame["_row_id"] = range(len(frame))
    frame["group_id"] = frame["_row_id"]
    frame["_clean_key"] = [f"key-{i}" for i in frame["_row_id"]]
    return frame


class AlternatingModel:
    """Records what it was trained on; predicts alternating labels without sklearn."""

    seen = []

    def fit(self, texts, labels):
        AlternatingModel.seen.append(set(texts.index))

    def predict(self, texts):
        return np.arange(len(texts)) % 2


class TopicCvTests(unittest.TestCase):
    def test_topics_are_label_free_and_groups_stay_together(self):
        frame = corpus()
        # One group spans two different true topics; it must still get a single topic.
        frame.loc[frame.index[0], "group_id"] = 999
        frame.loc[frame.index[-1], "group_id"] = 999
        flipped = frame.assign(label=1 - frame["label"])
        topics, _ = discover_topics(frame["text_clean"], frame["group_id"], 4, min_df=1)
        topics_flipped, _ = discover_topics(flipped["text_clean"], flipped["group_id"], 4, min_df=1)
        self.assertTrue((topics == topics_flipped).all())
        self.assertEqual(len(set(topics[frame["group_id"].eq(999).to_numpy()])), 1)

    def test_single_label_topic_is_not_evaluated(self):
        frame = corpus(single_label_topic=3)
        topics, terms = discover_topics(frame["text_clean"], frame["group_id"], 4, min_df=1)
        frame["topic"] = topics
        table = summarize_topics(frame, "topic", 10, terms)
        self.assertEqual(int(table["eligible"].sum()), 3)
        self.assertEqual(int((~table["eligible"]).sum()), 1)
        self.assertTrue(table.loc[~table["eligible"], "reason"].iloc[0])

    def test_held_out_topic_never_appears_in_training(self):
        frame = corpus()
        frame["topic"] = frame["true_topic"]
        AlternatingModel.seen = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            folds = leave_one_topic_out(frame, "topic", [0, 1, 2, 3], AlternatingModel, {})
        self.assertEqual(len(folds), 4)
        for fold, trained_on in zip(folds, AlternatingModel.seen):
            held_out = set(fold["_index"])
            self.assertFalse(held_out & trained_on)
            self.assertEqual(held_out | trained_on, set(frame.index))
            self.assertGreater(fold["fake"], 0)
            self.assertGreater(fold["real"], 0)

    def test_leakage_guard_rejects_shared_content_key(self):
        frame = corpus()
        frame.loc[1, "_clean_key"] = frame.loc[0, "_clean_key"]
        with self.assertRaisesRegex(ValueError, "_clean_key"):
            assert_no_leakage(frame.loc[[0]], frame.loc[[1]])

    def test_infeasible_when_no_topic_has_both_labels(self):
        frame = corpus()
        frame["label"] = (frame["true_topic"] % 2).astype(int)  # every topic is one label
        report, _ = evaluate_topics(frame, 4, 10, AlternatingModel, random_baseline=False, min_df=1)
        self.assertFalse(report["feasible"])
        self.assertNotIn("folds", report)
        self.assertIn("Not feasible", report["conclusion"])

    def test_report_uses_fake_as_positive_and_compares_with_random_groups(self):
        frame = corpus()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            report, _ = evaluate_topics(frame, 4, 10, AlternatingModel, random_baseline=True, min_df=1)
        self.assertTrue(report["feasible"])
        self.assertEqual(len(report["folds"]), 4)
        for fold in report["folds"]:
            self.assertEqual(len(fold["confusion_matrix_rows_fake_real"]), 2)
            self.assertIn("f1_fake", fold)
        self.assertIn("random_group_baseline_same_articles", report)
        self.assertEqual(report["pooled_topic_holdout"]["articles"], len(frame))


if __name__ == "__main__":
    unittest.main()
