"""Train a reproducible first baseline. See docs/DATA_AND_EVALUATION.md for limits."""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from backend.app.preprocessing import article_text


def load_dataset(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    frames = []
    for filename, label in (("Fake.csv", 1), ("True.csv", 0)):
        path = data_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. See README.md for dataset download.")
        frame = pd.read_csv(path)
        if not {"title", "text"}.issubset(frame.columns):
            raise ValueError(f"{path} must contain title and text columns")
        frame = frame[["title", "text"]].fillna("")
        frame["label"] = label
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data["content"] = [article_text(str(t), str(b)) for t, b in zip(data.title, data.text)]
    data = data.loc[data.content.str.len() >= 80, ["content", "label"]].copy()
    before = len(data)
    conflicting = data.groupby("content").label.nunique()
    conflicts = set(conflicting[conflicting > 1].index)
    data = data.loc[~data.content.isin(conflicts)].drop_duplicates(subset=["content"])
    counts = {"usable_before_dedup": before, "conflicting_contents": len(conflicts),
              "usable_after_dedup": len(data), "fake": int(data.label.sum()),
              "real": int((data.label == 0).sum())}
    if data.label.nunique() != 2 or min(counts["fake"], counts["real"]) < 2:
        raise ValueError("Need at least two usable articles in each class")
    return data, counts


def train(data_dir: Path, output_dir: Path) -> dict:
    data, counts = load_dataset(data_dir)
    x_train, x_test, y_train, y_test = train_test_split(
        data.content, data.label, test_size=0.2, stratify=data.label, random_state=42
    )
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2,
                                  max_df=0.95, max_features=100_000, sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(x_train, y_train)
    predicted = pipeline.predict(x_test)
    report = {
        "model_version": "baseline-v0", "label_map": {"0": "REAL_DATASET", "1": "FAKE_DATASET"},
        "seed": 42, "test_size": len(x_test), "dataset": counts,
        "accuracy": accuracy_score(y_test, predicted),
        "f1_fake": f1_score(y_test, predicted, pos_label=1),
        "f1_macro": f1_score(y_test, predicted, average="macro"),
        "confusion_matrix_rows_real_fake": confusion_matrix(y_test, predicted, labels=[0, 1]).tolist(),
        "limitations": "Random split; exact dedup only; source confounding and topic CV unresolved.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_dir / "baseline.joblib")
    (output_dir / "baseline_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(train(arguments.data_dir, arguments.output_dir), indent=2))
