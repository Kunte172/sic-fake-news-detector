import importlib.util
import json
import sys
import types
import unittest
from unittest import mock

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression

from ml.src import explain as ex

FAKE = ["shocking secret they hide truth outrage", "you won't believe shocking hoax outrage"] * 15
REAL = ["officials said the committee approved the budget", "the minister told reporters the policy"] * 15
TEXTS = FAKE + REAL
LABELS = [0] * len(FAKE) + [1] * len(REAL)  # quy ước DATA-02: 0=Fake, 1=Real
COLAB_REPORT = {"label_map": {"0": "Fake", "1": "Real"}}


def pipe(clf):
    return Pipeline([("tfidf", TfidfVectorizer()), ("classifier", clf)]).fit(TEXTS, LABELS)


def svm_explainer():
    p = pipe(LinearSVC(random_state=42))
    cal = ex.fit_platt(p.decision_function(TEXTS), [y == 0 for y in LABELS])
    return ex.Explainer(p, fake_label=0, calibration=cal)


class FakeExp:
    score = {0: 0.91}
    def as_list(self, label):
        return [("minister", -0.1), ("shocking", 0.2)]


class FakeLime:
    captured = None
    def __init__(self, **kwargs): pass
    def explain_instance(self, text, fn, labels, num_features, num_samples):
        FakeLime.captured = text
        fn([text])
        return FakeExp()


def stub_lime():
    pkg, mod = types.ModuleType("lime"), types.ModuleType("lime.lime_text")
    mod.LimeTextExplainer = FakeLime
    return mock.patch.dict(sys.modules, {"lime": pkg, "lime.lime_text": mod})


class ExplainTests(unittest.TestCase):
    def test_fake_label_follows_report(self):
        self.assertEqual(ex.fake_label_from_report(COLAB_REPORT), 0)
        self.assertEqual(ex.fake_label_from_report({"label_map": {"0": "REAL_DATASET", "1": "FAKE_DATASET"}}), 1)
        with self.assertRaises(ValueError):
            ex.fake_label_from_report({"label_map": {"0": "A", "1": "B"}})

    def test_global_keywords_direction_for_svm(self):
        kw = svm_explainer().global_keywords(top_k=10)
        self.assertIn("shocking", {k["term"] for k in kw["fake"]})
        self.assertTrue(all(k["weight"] > 0 for k in kw["fake"][:3]))  # dương = về Fake
        self.assertTrue(all(k["weight"] < 0 for k in kw["real"][:3]))

    def test_svm_needs_calibration(self):
        e = ex.Explainer(pipe(LinearSVC(random_state=42)), fake_label=0)
        with self.assertRaises(TypeError):
            e.predict_proba(["shocking"])

    def test_platt_scores(self):
        e = svm_explainer()
        proba = e.predict_proba(["shocking hoax outrage", "the minister said officials approved"])
        self.assertTrue(((proba.sum(axis=1) - 1).__abs__() < 1e-9).all())
        self.assertGreater(proba[0][e.fake_index], 0.5)
        self.assertLess(proba[1][e.fake_index], 0.5)

    def test_native_proba_model_needs_no_calibration(self):
        e = ex.Explainer(pipe(LogisticRegression()), fake_label=0)
        self.assertFalse(e.calibrated)
        self.assertEqual(e.predict_proba(["shocking"]).shape, (1, 2))

    def test_analyze_cleans_once_and_payload_shape(self):
        e = svm_explainer()
        raw = "WASHINGTON (Reuters) - the minister said officials approved https://x.co/a"
        with stub_lime():
            out = e.analyze(raw)
        self.assertNotIn("Reuters", FakeLime.captured)
        self.assertNotIn("https", FakeLime.captured)
        json.dumps(out)
        self.assertEqual(out["label"], ex.LABEL_LESS_SUSPICIOUS)
        self.assertLess(out["score"], 0.5)
        exp = out["explanation"]
        self.assertEqual(exp["terms"][0]["term"], "shocking")  # sắp theo |weight|
        self.assertEqual(exp["terms"][0]["direction"], "toward_fake")
        self.assertEqual(exp["terms"][1]["direction"], "toward_real")
        self.assertEqual(exp["score_kind"], "calibrated_fake_score")
        self.assertEqual(exp["fidelity"], 0.91)
        self.assertEqual(exp["disclaimer"], ex.DISCLAIMER)

    def test_already_clean_is_not_cleaned_again(self):
        e = svm_explainer()
        e.cleaner = mock.Mock(side_effect=AssertionError("không được làm sạch lại"))
        with stub_lime():
            e.analyze("the minister said officials approved", already_clean=True)

    def test_empty_after_cleaning_rejected(self):
        with stub_lime(), self.assertRaises(ValueError):
            svm_explainer().analyze("(Reuters) -")

    def test_leakage_report(self):
        kw = {"fake": [{"term": "pic twitter", "weight": 1}, {"term": "outrage", "weight": 1}], "real": []}
        self.assertEqual(ex.leakage_report(kw), ["pic twitter"])

    @unittest.skipUnless(importlib.util.find_spec("lime"), "cần cài lime")
    def test_real_lime_is_deterministic(self):
        e = svm_explainer()
        a = e.analyze("shocking hoax outrage the minister", num_samples=200)
        b = e.analyze("shocking hoax outrage the minister", num_samples=200)
        self.assertEqual(a, b)
        self.assertEqual(a["label"], ex.LABEL_SUSPICIOUS)


if __name__ == "__main__":
    unittest.main()
