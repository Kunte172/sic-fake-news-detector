import tempfile
from pathlib import Path
import unittest

import pandas as pd

from backend.app.preprocessing import clean_colab_text
from ml.src.audit_data import (
    duplicate_key, group_near_duplicates, groups_from_edges, load_raw,
    marker_rates, new_split, prepare, quarantine_mixed_groups, restore_checkpoint,
    validate_splits,
)


def raw_frame(texts, labels=None):
    return pd.DataFrame({"_row_id": range(len(texts)), "text": texts,
                         "label": labels if labels is not None else [0] * len(texts),
                         "title": "Test", "date": "2017-01-01", "subject": "topic"})


class ColabCleaningTests(unittest.TestCase):
    def test_dateline_and_parenthesized_source_removed(self):
        self.assertEqual(clean_colab_text("WASHINGTON (Reuters) - A report."), "A report.")
        self.assertEqual(clean_colab_text("(Reuters) - A report."), "A report.")

    def test_unicode_html_and_whitespace(self):
        self.assertEqual(clean_colab_text("Ａ &amp; B\n  spoke."), "A & B spoke.")

    def test_url_punctuation_preserves_following_sentence(self):
        self.assertEqual(clean_colab_text('Read https://example.com/news. Next sentence.'), "Read . Next sentence.")

    def test_tail_credit_removed(self):
        self.assertEqual(clean_colab_text("A report. Featured image via Getty Images"), "A report.")
        self.assertEqual(clean_colab_text("A report. Image credit: John Doe"), "A report.")

    def test_inline_credit_far_from_tail_does_not_truncate_body(self):
        text = "Image credit: Alice. " + "This substantive paragraph is retained. " * 30
        self.assertEqual(clean_colab_text(text), text.strip())

    def test_social_platform_prose_retained(self):
        self.assertEqual(clean_colab_text("They posted on Twitter and youtube.com."), "They posted on Twitter and youtube.com.")

    def test_known_lossy_rule_is_explicit(self):
        # Faithfully replay the old cleaner: not a claim of grammatical preservation.
        self.assertEqual(clean_colab_text("A source told Reuters simply: hello."), "A source told simply: hello.")

    def test_only_url_becomes_empty(self):
        self.assertEqual(clean_colab_text("https://example.org/story"), "")


class AuditTests(unittest.TestCase):
    def test_duplicate_key_normalizes_unicode_case_spaces(self):
        self.assertEqual(duplicate_key("Ａ\n Report"), duplicate_key("a report"))

    def test_load_mapping_and_missing_text(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("Fake.csv", "True.csv"):
                raw_frame([None]).drop(columns=["label", "_row_id"]).to_csv(Path(directory) / name, index=False)
            frame = load_raw(directory)
            self.assertEqual(frame.label.tolist(), [0, 1])
            self.assertEqual(frame.text.tolist(), ["", ""])

    def test_exclusions_are_disjoint_and_conserve_rows(self):
        body = " ".join(f"word{i}" for i in range(40))
        texts = [" ", body, body.upper(), "https://example.org", "short prose",
                 "different " + body, "different " + body]
        frame, excluded, before, after, _ = prepare(raw_frame(texts, [0, 0, 0, 0, 0, 0, 1]))
        self.assertEqual(len(excluded["empty_raw"]), 1)
        self.assertEqual(len(excluded["duplicates_raw"]), 1)
        self.assertEqual(len(excluded["exact_label_conflicts_raw"]), 2)
        self.assertEqual(len(excluded["empty_clean"]), 1)
        self.assertEqual(len(excluded["review"]), 1)
        ids = frame._row_id.tolist() + [i for part in excluded.values() for i in part._row_id]
        self.assertEqual(sorted(ids), list(range(7)))
        self.assertEqual(len(before), len(after))

    def test_conflict_created_by_cleaning_is_quarantined(self):
        body = " ".join(f"word{i}" for i in range(40))
        frame, excluded, *_ = prepare(raw_frame([body, "(Reuters) - " + body], [0, 1]))
        self.assertEqual(len(frame), 0)
        self.assertEqual(len(excluded["exact_label_conflicts_clean"]), 2)

    def test_clean_duplicate_is_removed(self):
        body = " ".join(f"word{i}" for i in range(40))
        frame, excluded, *_ = prepare(raw_frame([body, "(Reuters) - " + body]))
        self.assertEqual(len(frame), 1)
        self.assertEqual(len(excluded["duplicates_clean"]), 1)

    def test_credit_in_middle_is_quarantined_not_deleted(self):
        body = "Image credit: Someone. " + "A meaningful sentence continues here. " * 40
        frame, excluded, *_ = prepare(raw_frame([body]))
        self.assertTrue(frame.empty)
        self.assertEqual(excluded["review"].iloc[0].text_clean, body.strip())

    def test_transitive_components(self):
        groups = groups_from_edges([8, 4, 2, 10], [(8, 4), (4, 2)])
        self.assertEqual(groups, {8: 2, 4: 2, 2: 2, 10: 10})

    def test_near_duplicates_and_distinct_article(self):
        body = " ".join(f"word{i}" for i in range(150))
        unrelated = " ".join(f"other{i}" for i in range(150))
        frame = raw_frame([body, body + " extra", unrelated])
        frame["text_clean"] = frame.text
        grouped, pairs = group_near_duplicates(frame)
        self.assertEqual(grouped.group_id.tolist(), [0, 0, 2])
        self.assertEqual(len(pairs), 1)
        self.assertGreaterEqual(pairs.iloc[0].jaccard, .85)

    def test_mixed_group_all_members_quarantined(self):
        frame = pd.DataFrame({"group_id": [1, 1, 1, 4], "label": [0, 1, 0, 1]})
        accepted, quarantined = quarantine_mixed_groups(frame)
        self.assertEqual(len(quarantined), 3)
        self.assertEqual(accepted.group_id.tolist(), [4])

    def test_marker_rates_use_same_denominator(self):
        records = marker_rates(raw_frame(["Reuters report", "other report"]), "text", "before")
        record = next(r for r in records if r["marker"] == "reuters")
        self.assertEqual((record["matched"], record["articles"], record["percent"]), (1, 2, 50.0))

    def split_fixture(self):
        rows = []
        for i in range(1000):
            rows.append({"_row_id": i, "group_id": i // 2, "_clean_key": f"article {i}", "label": ((i // 2) * 37 % 101) % 2})
        return new_split(pd.DataFrame(rows))

    def test_split_is_reproducible_and_group_safe(self):
        first, second = self.split_fixture(), self.split_fixture()
        self.assertTrue(first.equals(second))
        self.assertEqual(sum(x["articles"] for x in validate_splits(first).values()), 1000)

    def test_cross_split_group_fails(self):
        frame = self.split_fixture()
        a = frame.index[frame.split.eq("train")][0]
        b = frame.index[frame.split.eq("test")][0]
        frame.loc[b, "group_id"] = frame.loc[a, "group_id"]
        with self.assertRaisesRegex(ValueError, "group_id"):
            validate_splits(frame)

    def test_cross_split_content_fails(self):
        frame = self.split_fixture()
        a = frame.index[frame.split.eq("train")][0]
        b = frame.index[frame.split.eq("test")][0]
        frame.loc[b, "_clean_key"] = frame.loc[a, "_clean_key"]
        with self.assertRaisesRegex(ValueError, "_clean_key"):
            validate_splits(frame)

    def test_duplicate_id_fails(self):
        frame = self.split_fixture()
        frame.loc[1, "_row_id"] = frame.loc[0, "_row_id"]
        with self.assertRaisesRegex(ValueError, "duplicate row IDs"):
            validate_splits(frame)

    def test_checkpoint_manifest_and_cleaner_drift_fail(self):
        import joblib
        frame = self.split_fixture()
        frame["text"] = frame._clean_key
        frame["text_clean"] = frame.text
        frame["title"], frame["subject"], frame["date"] = "Title", "topic", "2017"
        empty = frame.iloc[:0].copy()
        saved = {"train_df": frame.loc[frame.split.eq("train")],
                 "val_df": frame.loc[frame.split.eq("validation")],
                 "test_df": frame.loc[frame.split.eq("test")],
                 "quarantine_review": empty, "quarantine_near_conflicts": empty,
                 "split_manifest": frame[["_row_id", "group_id", "label", "split"]].copy()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "own_test_checkpoint.joblib"
            joblib.dump(saved, path)
            recovered, report = restore_checkpoint(path, frame, frame, empty, empty)
            self.assertEqual(len(recovered), len(frame))
            self.assertEqual(report["cleaning_mismatches"], 0)
            saved["train_df"] = saved["train_df"].copy()
            saved["train_df"].loc[:, "text_clean"] = "changed"
            joblib.dump(saved, path)
            with self.assertRaisesRegex(ValueError, "Cleaner differs"):
                restore_checkpoint(path, frame, frame, empty, empty)


if __name__ == "__main__":
    unittest.main()
