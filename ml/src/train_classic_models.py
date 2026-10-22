"""Compare TF-IDF classifiers using the fixed DATA-02 train/validation/test split.

Run from the repository root. This script never downloads data or recreates splits.
"""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


LABELS = {0: "Fake", 1: "Real"}
SPLITS = ("train", "validation", "test")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_splits(path: Path) -> dict[str, pd.DataFrame]:
    frame = pd.read_csv(path, keep_default_na=False)
    required = {"text_clean", "label", "split", "_row_id", "group_id", "_clean_key"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing DATA-02 columns: {sorted(missing)}")
    if set(frame["split"]) != set(SPLITS):
        raise ValueError("Expected exactly train, validation and test splits")
    if frame["_row_id"].duplicated().any():
        raise ValueError("Duplicate article IDs")
    if frame["text_clean"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty cleaned article")
    if set(frame["label"]) != set(LABELS):
        raise ValueError("Expected DATA-02 labels 0=Fake, 1=Real")
    for column in ("_row_id", "group_id", "_clean_key"):
        if frame.groupby(column)["split"].nunique().gt(1).any():
            raise ValueError(f"Cross-split leakage in {column}")
    parts = {name: frame.loc[frame["split"].eq(name)].copy() for name in SPLITS}
    if any(set(part["label"]) != set(LABELS) for part in parts.values()):
        raise ValueError("Each split must contain both labels")
    return parts


def make_pipeline(classifier) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True, ngram_range=(1, 2), min_df=2,
            max_df=0.95, max_features=100_000, sublinear_tf=True,
        )),
        ("classifier", classifier),
    ])


def evaluate(model: Pipeline, part: pd.DataFrame) -> dict:
    truth = part["label"].to_numpy()
    predicted = model.predict(part["text_clean"])
    return {
        "articles": len(part),
        "accuracy": round(float(accuracy_score(truth, predicted)), 6),
        "f1_fake": round(float(f1_score(truth, predicted, pos_label=0)), 6),
        "f1_macro": round(float(f1_score(truth, predicted, average="macro")), 6),
        "confusion_matrix_rows_fake_real": confusion_matrix(
            truth, predicted, labels=[0, 1]
        ).tolist(),
    }


def train(input_path: Path, output_dir: Path) -> dict:
    parts = load_splits(input_path)
    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "multinomial_nb": MultinomialNB(),
        "linear_svm": LinearSVC(random_state=42),
    }
    results = {}
    models = {}
    for name, classifier in candidates.items():
        print(f"Training {name}...", flush=True)
        model = make_pipeline(classifier)
        model.fit(parts["train"]["text_clean"], parts["train"]["label"])
        models[name] = model
        results[name] = {"validation": evaluate(model, parts["validation"])}

    # Select with validation only. Do not tune parameters after reading test scores.
    winner = max(candidates, key=lambda name: (
        results[name]["validation"]["f1_macro"],
        results[name]["validation"]["f1_fake"],
    ))
    for name, model in models.items():
        results[name]["test"] = evaluate(model, parts["test"])

    report = {
        "experiment": "ml-01-audited-classic-models-v1",
        "input_sha256": sha256(input_path),
        "label_map": {"0": "Fake", "1": "Real"},
        "feature": "text_clean",
        "split_counts": {name: len(part) for name, part in parts.items()},
        "selection": "highest validation macro F1; Fake F1 breaks ties",
        "selected_model": winner,
        "results": results,
        "scikit_learn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "limitations": (
            "The dataset has source and topic confounding. Scores describe this dataset, "
            "not independent verification of news claims. LinearSVC margins are not probabilities."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(models[winner], output_dir / "ml01_selected.joblib")
    (output_dir / "ml01_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("ml/artifacts/data02/prepared_splits.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts/ml01"))
    args = parser.parse_args()
    print(json.dumps(train(args.input, args.output_dir), ensure_ascii=False, indent=2))
