"""ML-02: leave-one-topic-out evaluation with topics derived from article text.

Topics come from unsupervised clustering of `text_clean` only. Labels, `subject`,
`date`, titles and IDs never define a topic. Every near-duplicate group (`group_id`)
stays inside one topic. For each topic with enough Fake and Real articles, a model
is trained on all other articles and scored on the held-out topic. Topics without
both labels are reported as not evaluated; a one-label score is never reported.

Run from the repository root after DATA-02 has produced prepared_splits.csv.
This script never downloads data and never recreates the DATA-02 split.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import normalize
from sklearn.svm import LinearSVC

from ml.src.train_classic_models import SPLITS, evaluate, load_splits, make_pipeline, sha256

SEED = 42
LEAKAGE_COLUMNS = ("_row_id", "group_id", "_clean_key")
LIMITATIONS = (
    "Topics are unsupervised clusters of cleaned article text, not editorial categories; "
    "results depend on the number of topics and the random seed. Topic definition fits "
    "TF-IDF, SVD and KMeans on all articles without labels; classifiers never see the "
    "held-out topic. Source and style confounding can remain inside a topic. Scores describe "
    "this English-language dataset only and do not verify the truth of any article."
)


def say(message: str) -> None:
    """Progress goes to stderr so the JSON report on stdout stays clean."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def _quiet(message: str) -> None:
    return None


class StoredPredictions:
    """Adapter so ML-01's `evaluate` can score predictions collected across folds."""

    def __init__(self, values):
        self.values = np.asarray(values)

    def predict(self, texts):
        return self.values


def default_model():
    return make_pipeline(LinearSVC(random_state=SEED))


def load_articles(path: Path) -> pd.DataFrame:
    """Load every accepted DATA-02 article, re-using ML-01's boundary checks."""
    parts = load_splits(path)
    return pd.concat([parts[name] for name in SPLITS], ignore_index=True)


def keep_groups_together(clusters, group_ids, n_topics: int) -> np.ndarray:
    """Give every article of a near-duplicate group the group's majority topic."""
    frame = pd.DataFrame({"group": np.asarray(group_ids), "cluster": np.asarray(clusters)})
    chosen = frame.groupby("group")["cluster"].agg(
        lambda values: int(np.bincount(values, minlength=n_topics).argmax())
    )
    return frame["group"].map(chosen).to_numpy()


def top_terms(matrix, topics: np.ndarray, terms, count: int = 10) -> dict:
    result = {}
    for topic in sorted(set(topics.tolist())):
        rows = np.flatnonzero(topics == topic)
        centroid = np.asarray(matrix[rows].mean(axis=0)).ravel()
        result[int(topic)] = [str(terms[i]) for i in np.argsort(centroid)[::-1][:count]]
    return result


def discover_topics(texts, group_ids, n_topics: int, seed: int = SEED, min_df: int = 5):
    """Return (topic per article, top terms per topic). Uses text only, never labels."""
    vectorizer = TfidfVectorizer(
        lowercase=True, stop_words="english", min_df=min_df,
        max_df=0.5, max_features=20_000, sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)
    components = max(2, min(100, matrix.shape[1] - 1, matrix.shape[0] - 1))
    reduced = normalize(TruncatedSVD(n_components=components, random_state=seed).fit_transform(matrix))
    clusters = KMeans(n_clusters=n_topics, n_init=10, random_state=seed).fit_predict(reduced)
    topics = keep_groups_together(clusters, group_ids, n_topics)
    return topics, top_terms(matrix, topics, vectorizer.get_feature_names_out())


def summarize_topics(frame: pd.DataFrame, topic_column: str, min_per_label: int, terms: dict) -> pd.DataFrame:
    rows = []
    for topic, part in frame.groupby(topic_column, sort=True):
        fake = int(part["label"].eq(0).sum())
        real = int(part["label"].eq(1).sum())
        eligible = min(fake, real) >= min_per_label
        rows.append({
            "topic": int(topic), "articles": len(part), "fake": fake, "real": real,
            "eligible": bool(eligible),
            "reason": "" if eligible else f"fewer than {min_per_label} articles in at least one label",
            "top_terms": " ".join(terms.get(int(topic), [])),
        })
    return pd.DataFrame(rows)


def assert_no_leakage(train: pd.DataFrame, test: pd.DataFrame) -> None:
    for column in LEAKAGE_COLUMNS:
        if set(train[column]) & set(test[column]):
            raise ValueError(f"Leakage between train and held-out data in {column}")


def pooled_metrics(truth, predicted) -> dict:
    part = pd.DataFrame({"text_clean": [""] * len(truth), "label": list(truth)})
    return evaluate(StoredPredictions(predicted), part)


def leave_one_topic_out(frame, topic_column, eligible_topics, model_factory, topic_terms,
                        progress=_quiet) -> list:
    folds = []
    for number, topic in enumerate(eligible_topics, start=1):
        held_out = frame[topic_column].eq(topic)
        train, test = frame.loc[~held_out], frame.loc[held_out]
        assert_no_leakage(train, test)
        progress(f"Topic {topic} ({number}/{len(eligible_topics)}): training on "
                 f"{len(train)} articles, testing on {len(test)} unseen-topic articles...")
        started = time.time()
        model = model_factory()
        model.fit(train["text_clean"], train["label"])
        result = evaluate(model, test)
        progress(f"  finished in {time.time() - started:.0f}s: accuracy {result['accuracy']:.4f}, "
                 f"macro F1 {result['f1_macro']:.4f}")
        result.update({
            "topic": int(topic),
            "top_terms": topic_terms.get(int(topic), []),
            "fake": int(test["label"].eq(0).sum()),
            "real": int(test["label"].eq(1).sum()),
            "predictions": model.predict(test["text_clean"]).tolist(),
            "_index": test.index.tolist(),
        })
        folds.append(result)
    return folds


def random_group_baseline(frame, topic_column, eligible_topics, n_splits, model_factory,
                          progress=_quiet) -> dict:
    """Same data, grouped random folds; scored on the same articles the topic test covers."""
    predicted = pd.Series(index=frame.index, dtype="float64")
    splitter = GroupKFold(n_splits=n_splits)
    for number, (train_index, test_index) in enumerate(
            splitter.split(frame, frame["label"], frame["group_id"]), start=1):
        progress(f"Random-group baseline fold {number}/{n_splits}...")
        train, test = frame.iloc[train_index], frame.iloc[test_index]
        assert_no_leakage(train, test)
        model = model_factory()
        model.fit(train["text_clean"], train["label"])
        predicted.iloc[test_index] = model.predict(test["text_clean"])
    covered = frame[topic_column].isin(eligible_topics)
    return pooled_metrics(frame.loc[covered, "label"], predicted[covered].astype(int))


def evaluate_topics(frame, n_topics=10, min_per_label=100, model_factory=default_model,
                    random_baseline=True, min_df=5, progress=_quiet):
    frame = frame.reset_index(drop=True).copy()
    progress(f"Finding {n_topics} topics from article text (TF-IDF, SVD, KMeans)...")
    topics, terms = discover_topics(frame["text_clean"], frame["group_id"], n_topics, min_df=min_df)
    frame["topic"] = topics
    table = summarize_topics(frame, "topic", min_per_label, terms)
    eligible = table.loc[table["eligible"], "topic"].tolist()
    progress(f"Topics found. {len(eligible)} of {len(table)} have at least {min_per_label} Fake and "
             f"{min_per_label} Real articles and will be evaluated:")
    for row in table.itertuples():
        progress(f"  topic {row.topic}: {row.articles} articles (Fake {row.fake}, Real {row.real}) "
                 f"{'EVALUATED' if row.eligible else 'skipped'} | {row.top_terms}")
    report = {
        "topic_method": (
            f"TF-IDF(text_clean) -> TruncatedSVD -> KMeans(k={n_topics}, seed={SEED}); "
            "near-duplicate groups kept in one topic"
        ),
        "n_topics": n_topics,
        "min_per_label": min_per_label,
        "topics": table.to_dict(orient="records"),
        "evaluated_topics": eligible,
        "not_evaluated_topics": table.loc[~table["eligible"], "topic"].tolist(),
        "feasible": bool(eligible),
    }
    if not eligible:
        report["conclusion"] = (
            "Not feasible: no topic has at least "
            f"{min_per_label} Fake and {min_per_label} Real articles. No topic score is reported."
        )
        return report, table
    folds = leave_one_topic_out(frame, "topic", eligible, model_factory, terms, progress)
    order = [i for fold in folds for i in fold["_index"]]
    truth = frame.loc[order, "label"].tolist()
    predicted = [p for fold in folds for p in fold["predictions"]]
    for fold in folds:
        del fold["predictions"], fold["_index"]
    worst = min(folds, key=lambda fold: fold["f1_macro"])
    report.update({
        "folds": folds,
        "pooled_topic_holdout": pooled_metrics(truth, predicted),
        "mean_fold_accuracy": round(float(np.mean([f["accuracy"] for f in folds])), 6),
        "mean_fold_f1_macro": round(float(np.mean([f["f1_macro"] for f in folds])), 6),
        "worst_topic": {"topic": worst["topic"], "f1_macro": worst["f1_macro"]},
        "conclusion": (
            f"Evaluated {len(folds)} of {len(table)} topics; the others lack one label. "
            "Compare pooled topic hold-out with the grouped random baseline on the same articles."
        ),
    })
    if random_baseline:
        report["random_group_baseline_same_articles"] = random_group_baseline(
            frame, "topic", eligible, max(2, len(eligible)), model_factory, progress
        )
    return report, table


def run(input_path: Path, output_dir: Path, n_topics: int, min_per_label: int, random_baseline: bool) -> dict:
    say(f"Loading {input_path} (a large file, this can take a minute)...")
    frame = load_articles(input_path)
    say(f"Loaded {len(frame)} articles.")
    report, table = evaluate_topics(frame, n_topics, min_per_label, default_model,
                                    random_baseline, progress=say)
    say("Writing report files...")
    report = {
        "experiment": "ml-02-topic-holdout-v1",
        "input_sha256": sha256(input_path),
        "label_map": {"0": "Fake", "1": "Real"},
        "feature": "text_clean",
        "classifier": "TF-IDF + LinearSVC (same configuration as ML-01, no tuning)",
        "articles": len(frame),
        **report,
        "scikit_learn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "limitations": LIMITATIONS,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_dir / "ml02_topics.csv", index=False)
    (output_dir / "ml02_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    say(f"Done. Report saved to {output_dir / 'ml02_report.json'}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("ml/artifacts/data02/prepared_splits.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts/ml02"))
    parser.add_argument("--topics", type=int, default=10, help="number of text clusters (default 10)")
    parser.add_argument("--min-per-label", type=int, default=100,
                        help="minimum Fake and Real articles for a topic to be evaluated")
    parser.add_argument("--skip-random-baseline", action="store_true")
    args = parser.parse_args()
    print(json.dumps(
        run(args.input, args.output_dir, args.topics, args.min_per_label, not args.skip_random_baseline),
        ensure_ascii=False, indent=2,
    ))