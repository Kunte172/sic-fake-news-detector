"""Data-safety regression tests; synthetic fixtures, not fabricated dataset rows."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

MODULE_PATH = Path(__file__).resolve().parents[2] / "ml/src/prepare_liar.py"
spec = importlib.util.spec_from_file_location("data03_prepare", MODULE_PATH)
data03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data03)


def row(i, text, label="true", split="train"):
    return {"id": str(i), "text_clean": text, "text_sha256": data03.text_hash(text),
            "official_split": split, "label_original": label, "label_binary": data03.BINARY.get(label)}


class LiarAuditTests(unittest.TestCase):
    def test_strict_mapping_keeps_ambiguous_labels_out(self):
        self.assertEqual(data03.BINARY, {"true": 1, "false": 0, "pants-fire": 0})
        for label in ("half-true", "mostly-true", "barely-true"):
            kept, held = data03.select_binary([row(1, "some statement", label)], [], set())
            self.assertFalse(kept)
            self.assertIn("intermediate_label_not_mapped", held[0]["exclusion_reasons"])

    def test_entire_cross_split_component_quarantined(self):
        rows = [row(1,"one",split="train"), row(2,"two",split="train"),row(3,"three",split="test")]
        edges = [{"id_1":"1","id_2":"2"},{"id_1":"2","id_2":"3"}]
        kept, held = data03.select_binary(rows,edges,set())
        self.assertEqual(len(held),3)
        self.assertFalse(kept)
        self.assertTrue(all("group_crosses_official_splits" in r["exclusion_reasons"] for r in held))

    def test_conflict_detected_before_intermediate_filter(self):
        rows = [row(1,"same claim","true"),row(2,"same claim","half-true")]
        kept, held = data03.select_binary(rows,[{"id_1":"1","id_2":"2"}],set())
        self.assertFalse(kept)
        self.assertTrue(all("group_has_conflicting_six_way_labels" in r["exclusion_reasons"] for r in held))

    def test_old_dataset_overlap_quarantines_transitive_group(self):
        rows = [row(1,"first claim"),row(2,"related claim")]
        kept, held = data03.select_binary(rows,[{"id_1":"1","id_2":"2"}],{"1"})
        self.assertFalse(kept)
        self.assertEqual(len(held),2)

    def test_metadata_never_in_model_view(self):
        r = row(1,"clean input")
        r["metadata"] = {"speaker":"LABEL LEAK", "true_count": 400}
        kept, _ = data03.select_binary([r],[],set())
        self.assertEqual(set(kept[0]), {"id","text","label","split","group_id","language","content_type"})
        self.assertEqual(kept[0]["text"],"clean input")

    def test_unicode_and_whitespace_exact_duplicates(self):
        rows=[row(1,"Ａ claim  here"),row(2,"a CLAIM here",split="test")]
        edges=data03.near_edges(rows)
        self.assertTrue(any(e["kind"]=="exact" for e in edges))
        kept,held=data03.select_binary(rows,edges,set())
        self.assertFalse(kept)
        self.assertEqual(len(held),2)

    def test_same_split_duplicate_keep_one(self):
        rows=[row(1,"same input"),row(2,"same input")]
        kept,held=data03.select_binary(rows,data03.near_edges(rows),set())
        self.assertEqual(len(kept),1)
        self.assertEqual(len(held),1)

    def test_no_deleting_short_claims_by_article_length_rule(self):
        kept,_=data03.select_binary([row(1,"Taxes rose.")],[],set())
        self.assertEqual(len(kept),1)

    def test_empty_claim_excluded(self):
        kept,held=data03.select_binary([row(1,"  ")],[],set())
        self.assertFalse(kept)
        self.assertIn("empty_statement",held[0]["exclusion_reasons"])

    def test_split_validation_fails_on_shared_group(self):
        fixture=[]
        for split in ("train","validation","test"):
            for label in (0,1):
                fixture.append({"id":f"{split}-{label}","text":f"{split} {label}",
                                "label":label,"split":split,"group_id":"shared"})
        with self.assertRaisesRegex(ValueError,"Cross-split"):
            data03.validate_view(fixture)

    def archive_fixture(self, temp, train):
        target=Path(temp)/"fixture.zip"
        with zipfile.ZipFile(target,"w") as z:
            z.writestr("train.tsv",train)
            z.writestr("valid.tsv","2.json\tfalse\tValidation claim\n")
            z.writestr("test.tsv","3.json\ttrue\tTest claim\n")
            z.writestr("README","Synthetic fixture only")
            z.writestr("../../should_not_extract.txt","bad path")
        return target

    def test_missing_metadata_padded_without_losing_statement(self):
        with tempfile.TemporaryDirectory() as temp:
            rows,warnings,_=data03.read_zip(self.archive_fixture(temp,"1.json\ttrue\tTraining claim\n"),False)
            self.assertEqual(len(rows),3)
            self.assertEqual(len(warnings),3)
            self.assertEqual(rows[0]["text"],"Training claim")
            self.assertEqual(len(rows[0]["metadata"]),11)
            self.assertFalse((Path(temp)/"should_not_extract.txt").exists())

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"duplicate"):
                data03.read_zip(self.archive_fixture(temp,"2.json\ttrue\tClaim\n"),False)

    def test_unknown_label_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"Unknown label"):
                data03.read_zip(self.archive_fixture(temp,"1.json\tmostly-fake\tClaim\n"),False)

    def test_checksum_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"checksum"):
                data03.read_zip(self.archive_fixture(temp,"1.json\ttrue\tClaim\n"))


if __name__ == "__main__":
    unittest.main()
