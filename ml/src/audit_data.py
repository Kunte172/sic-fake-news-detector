"""DATA-02: deterministic audit, no model fitting, Colab labels 0=fake/1=real.

Run from the repository root. Large outputs belong under ignored ml/artifacts/.
The original checkpoint is optional and MUST be a trusted local joblib file.
"""
import argparse
from functools import lru_cache
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd
from datasketch import MinHash, MinHashLSH
from sklearn.model_selection import StratifiedGroupKFold

from backend.app.colab_preprocessing import clean_source_markers

SEED = 42
PATTERNS = {
    "reuters": r"\bReuters\b",
    "dateline": r"^\s*[^.!?\n]{0,120}?\(\s*Reuters\s*\)\s*[-–—:]",
    "web_link": r"https?://|www\.|pic\.twitter\.com/|youtu\.be/",
    "photo_credit": r"\b(?:featured\s+image\b|(?:image|photo)\s+credits?\b|(?:image|photo)\s+(?:via|courtesy\s+of)\b)",
    # A diagnostic flag, NOT a rule to delete prose mentioning a social platform.
    "social_reference": r"pic\.twitter\.com|twitter\.com/|youtu(?:be\.com|\.be)|instagram\.com/|facebook\.com/",
    "leading_uppercase": r"^\s*[A-Z][A-Z ,.'/-]{2,60}(?:\(|[-–—:])",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duplicate_key(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip().casefold()


def load_raw(data_dir):
    frames = []
    for name, label in (("Fake.csv", 0), ("True.csv", 1)):
        frame = pd.read_csv(Path(data_dir) / name)
        required = {"title", "text", "subject", "date"}
        if not required.issubset(frame):
            raise ValueError(f"{name} is missing columns: {required - set(frame)}")
        frame = frame[list(sorted(required))].copy()
        frame["label"] = label
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    raw["_row_id"] = range(len(raw))
    raw["text"] = raw["text"].fillna("").astype(str)
    return raw


def prepare(raw):
    """Preserve each exclusion separately; never silently relabel an article."""
    work = raw.copy()
    work["_dup_key"] = work.text.map(duplicate_key)
    excluded = {"empty_raw": work.loc[work._dup_key.eq("")].copy()}
    work = work.loc[~work._dup_key.eq("")].copy()
    mixed = work.groupby("_dup_key").label.nunique().loc[lambda s: s.gt(1)].index
    excluded["exact_label_conflicts_raw"] = work.loc[work._dup_key.isin(mixed)].copy()
    work = work.loc[~work._dup_key.isin(mixed)].copy()
    excluded["duplicates_raw"] = work.loc[work.duplicated("_dup_key")].copy()
    work = work.drop_duplicates("_dup_key").copy()
    before_clean = work.copy()
    work["text_clean"] = work.text.map(clean_source_markers)
    work["_clean_key"] = work.text_clean.map(duplicate_key)
    work["_removed_fraction"] = ((work.text.str.len() - work.text_clean.str.len()) / work.text.str.len().clip(lower=1)).clip(lower=0)
    work["_word_count_clean"] = work.text_clean.str.split().str.len()
    after_clean = work.copy()
    empty = work._clean_key.eq("")
    reasons = pd.DataFrame({
        "under_20_words": work._word_count_clean.lt(20) & ~empty,
        "photo_credit_remaining": work.text_clean.str.contains(PATTERNS["photo_credit"], case=False, regex=True, na=False) & ~empty,
        "over_30_percent_removed": work._removed_fraction.gt(.30) & ~empty,
    }, index=work.index)
    work["_review_reason"] = reasons.apply(lambda r: ";".join(r.index[r]), axis=1)
    excluded["empty_clean"] = work.loc[empty].copy()
    excluded["review"] = work.loc[reasons.any(axis=1)].copy()
    work = work.loc[~empty & ~reasons.any(axis=1)].copy()
    mixed = work.groupby("_clean_key").label.nunique().loc[lambda s: s.gt(1)].index
    excluded["exact_label_conflicts_clean"] = work.loc[work._clean_key.isin(mixed)].copy()
    work = work.loc[~work._clean_key.isin(mixed)].copy()
    excluded["duplicates_clean"] = work.loc[work.duplicated("_clean_key")].copy()
    work = work.drop_duplicates("_clean_key").copy()
    return work, excluded, before_clean, after_clean, reasons.sum().astype(int).to_dict()


def shingles(text, width=5):
    words = re.findall(r"\w+", text.casefold())
    if len(words) < width:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + width]) for i in range(len(words) - width + 1)}


def groups_from_edges(ids, edges):
    """Connected components; transitive neighbours stay in one split."""
    parent = {int(i): int(i) for i in ids}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for left, right in edges:
        a, b = root(int(left)), root(int(right))
        parent[max(a, b)] = min(a, b)
    return {i: root(i) for i in parent}


def group_near_duplicates(frame, candidate_threshold=.70, threshold=.85):
    """LSH candidates + exact Jaccard. Approximate retrieval can miss pairs."""
    if not 0 < candidate_threshold <= threshold <= 1:
        raise ValueError("Require 0 < candidate threshold <= exact threshold <= 1")
    frame = frame.sort_values("_row_id").copy()
    texts = frame.set_index("_row_id").text_clean.to_dict()

    @lru_cache(maxsize=256)
    def tokens(row_id):
        return shingles(texts[row_id])

    lsh = MinHashLSH(threshold=candidate_threshold, num_perm=128)
    edges = []
    for count, row_id in enumerate(texts, 1):
        token_set = tokens(row_id)
        signature = MinHash(num_perm=128, seed=SEED)
        encoded = [t.encode("utf-8") for t in sorted(token_set)]
        for offset in range(0, len(encoded), 128):
            signature.update_batch(encoded[offset:offset + 128])
        for other_id in sorted(lsh.query(signature)):
            other = tokens(other_id)
            union = token_set | other
            similarity = len(token_set & other) / len(union) if union else 0
            if similarity >= threshold:
                edges.append((other_id, row_id, similarity))
        lsh.insert(row_id, signature)
        if count % 5000 == 0:
            print(f"Near-duplicate audit: {count}/{len(frame)}", flush=True)
    groups = groups_from_edges(texts, [(a, b) for a, b, _ in edges])
    frame["group_id"] = frame._row_id.map(groups)
    return frame, pd.DataFrame(edges, columns=["id_1", "id_2", "jaccard"])


def quarantine_mixed_groups(frame):
    mixed = frame.groupby("group_id").label.nunique().loc[lambda s: s.gt(1)].index
    mask = frame.group_id.isin(mixed)
    return frame.loc[~mask].copy(), frame.loc[mask].copy()


def validate_splits(frame):
    required = {"_row_id", "group_id", "_clean_key", "label", "split"}
    if not required.issubset(frame):
        raise ValueError(f"Missing split columns: {required - set(frame)}")
    if frame[list(required)].isna().any().any() or frame._row_id.duplicated().any():
        raise ValueError("Missing values or duplicate row IDs in split")
    if frame._clean_key.eq("").any():
        raise ValueError("Empty content in split")
    if set(frame.split) != {"train", "validation", "test"}:
        raise ValueError("Expected train, validation and test")
    for column in ("_row_id", "group_id", "_clean_key"):
        if frame.groupby(column).split.nunique().gt(1).any():
            raise ValueError(f"Cross-split overlap: {column}")
    summary = {}
    for name, part in frame.groupby("split", sort=True):
        if set(part.label) != {0, 1}:
            raise ValueError(f"{name} must contain both labels")
        summary[name] = {"articles": len(part), "groups": int(part.group_id.nunique()),
                         "fake_0": int(part.label.eq(0).sum()), "real_1": int(part.label.eq(1).sum())}
    return summary


def new_split(frame):
    """Only for a new experiment; never replace an evaluated checkpoint split."""
    frame = frame.sort_values("_row_id").reset_index(drop=True).copy()
    frame["split"] = "train"
    splitter = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=SEED)
    for fold, (_, index) in enumerate(splitter.split(frame, frame.label, frame.group_id)):
        if fold in (0, 1):
            frame.loc[index, "split"] = "test" if fold == 0 else "validation"
    validate_splits(frame)
    return frame


def marker_rates(frame, column, stage):
    records = []
    for label, part in frame.groupby("label"):
        for name, pattern in PATTERNS.items():
            count = int(part[column].str.contains(pattern, case=(name == "leading_uppercase"), regex=True, na=False).sum())
            records.append({"stage": stage, "label": int(label), "marker": name,
                            "articles": len(part), "matched": count, "percent": round(100 * count / len(part), 4)})
    return records


def restore_checkpoint(path, raw, expected, review, conflicts):
    # joblib/pickle may execute code: the CLI requires explicit trusted-file opt-in.
    import joblib
    saved = joblib.load(path)
    parts = []
    for key, name in (("train_df", "train"), ("val_df", "validation"), ("test_df", "test")):
        part = saved[key].copy()
        if not part.split.eq(name).all():
            raise ValueError(f"Checkpoint split mismatch in {key}")
        parts.append(part)
    restored = pd.concat(parts, ignore_index=True)
    validate_splits(restored)
    if set(restored._row_id) != set(expected._row_id):
        raise ValueError("Reconstructed accepted IDs differ from checkpoint")
    for key, rebuilt in (("quarantine_review", review), ("quarantine_near_conflicts", conflicts)):
        if set(saved[key]._row_id) != set(rebuilt._row_id):
            raise ValueError(f"Reconstructed IDs differ: {key}")
    recovered = pd.concat([restored, saved["quarantine_review"], saved["quarantine_near_conflicts"]], ignore_index=True)
    if recovered._row_id.duplicated().any():
        raise ValueError("Duplicate IDs across checkpoint partitions")
    source = raw.set_index("_row_id")
    for column in ("text", "title", "subject", "date", "label"):
        actual = recovered.set_index("_row_id")[column].fillna("")
        if not actual.eq(source.loc[actual.index, column].fillna("")).all():
            raise ValueError(f"Kaggle input does not match checkpoint column: {column}")
    cleaned = recovered.text.map(clean_source_markers)
    mismatch = int(cleaned.ne(recovered.text_clean).sum())
    if mismatch:
        raise ValueError(f"Cleaner differs from checkpoint on {mismatch} articles")
    if not recovered._clean_key.eq(cleaned.map(duplicate_key)).all():
        raise ValueError("Checkpoint content keys differ from normalized cleaned text")
    manifest = saved["split_manifest"].set_index("_row_id").sort_index()
    current = restored.set_index("_row_id").sort_index()
    if not manifest.index.equals(current.index) or not manifest[["group_id", "label", "split"]].equals(current[["group_id", "label", "split"]]):
        raise ValueError("Checkpoint manifest differs from saved dataframes")
    # Also check the newly detected components against the old split. New cross-
    # split neighbours must fail the audit, not silently change the held-out test.
    recheck = expected.drop(columns=["split"], errors="ignore").merge(restored[["_row_id", "split"]], on="_row_id", validate="one_to_one")
    validate_splits(recheck)
    return restored, {"recovered_rows": len(recovered), "cleaning_mismatches": mismatch,
                      "original_fields_match": True, "saved_manifest_matches": True,
                      "new_groups_cross_split": False, "versions": saved.get("versions", {})}


def run(data_dir, output_dir, checkpoint=None):
    raw = load_raw(data_dir)
    prepared, excluded, before, after, reason_counts = prepare(raw)
    grouped, pairs = group_near_duplicates(prepared)
    accepted, excluded["near_label_conflicts"] = quarantine_mixed_groups(grouped)
    verification = None
    if checkpoint:
        split, verification = restore_checkpoint(checkpoint, raw, accepted, excluded["review"], excluded["near_label_conflicts"])
    else:
        split = new_split(accepted)
    summary = validate_splits(split)
    counts = {name: len(frame) for name, frame in excluded.items()}
    if sum(counts.values()) + len(split) != len(raw):
        raise ValueError("Row conservation failed")
    group_sizes = grouped.groupby("group_id").size()
    date_parsed = pd.to_datetime(raw.date, format="mixed", errors="coerce", utc=True)
    report = {
        "schema_version": 1, "preprocessing_version": "colab-source-markers-v1",
        "label_map": {"0": "Fake", "1": "Real"}, "features": ["text_clean"],
        "excluded_features": ["title", "subject", "date", "_row_id", "group_id"],
        "input_sha256": {n: sha256(Path(data_dir) / n) for n in ("Fake.csv", "True.csv")},
        "cleaner_sha256": sha256(Path(__file__).parents[2] / "backend/app/colab_preprocessing.py"),
        "checkpoint_sha256": sha256(checkpoint) if checkpoint else None,
        "split_origin": "restored_colab_unchanged" if checkpoint else "new_experiment",
        "raw_articles": len(raw), "before_cleaning": len(before), "exclusions": counts,
        "review_reasons_overlapping": reason_counts, "accepted_articles": len(split),
        "near_duplicates": {"shingle_words": 5, "num_perm": 128, "seed": SEED,
                            "candidate_threshold": .70, "exact_jaccard_threshold": .85,
                            "matched_pairs": len(pairs), "groups": len(group_sizes),
                            "multi_article_groups": int(group_sizes.gt(1).sum()),
                            "articles_in_multi_groups": int(group_sizes[group_sizes.gt(1)].sum()),
                            "largest_group": int(group_sizes.max())},
        "split": summary, "checkpoint_verification": verification,
        "date_parse": {"parsed": int(date_parsed.notna().sum()), "unparsed": int(date_parsed.isna().sum())},
        "versions": {n: version(n) for n in ("pandas", "numpy", "scikit-learn", "datasketch", "joblib")},
        "limitations": ["LSH candidates are approximate; no claim of complete semantic deduplication.",
                        "Removing markers does not remove source/style/topic confounding.",
                        "Review quarantine is a selection rule, not proof of incorrect labels.",
                        "Raw subject is label-confounded and is not a shared semantic topic taxonomy.",
                        "No model retraining, ablation, or new performance evaluation in this audit."],
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    # Outputs with article bodies and IDs are deliberately local, ignored artifacts.
    split.to_csv(output / "prepared_splits.csv", index=False)
    split[["_row_id", "group_id", "label", "split"]].to_csv(output / "split_manifest.csv", index=False)
    pairs.to_csv(output / "near_pairs.csv", index=False)
    for name, frame in excluded.items():
        frame.to_csv(output / f"excluded_{name}.csv", index=False)
    records = []
    for frame, column, stage in ((raw, "text", "raw"), (before, "text", "deduplicated_before_clean"),
                                 (after, "text_clean", "after_clean_before_quarantine"), (split, "text_clean", "accepted")):
        records.extend(marker_rates(frame, column, stage))
    pd.DataFrame(records).to_csv(output / "marker_rates.csv", index=False)
    pd.crosstab(raw.subject.fillna("(missing)"), raw.label).to_csv(output / "subject_by_label.csv")
    pd.crosstab(date_parsed.dt.strftime("%Y-%m").fillna("unparsed"), raw.label).to_csv(output / "month_by_label.csv")
    pd.DataFrame([{ "reason": name, "label": int(label), "articles": int(count)}
                  for name, frame in excluded.items() for label, count in frame.label.value_counts().items()]).to_csv(output / "exclusions_by_label.csv", index=False)
    (output / "audit_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--trust-local-checkpoint", action="store_true")
    args = parser.parse_args()
    if args.checkpoint and not args.trust_local_checkpoint:
        parser.error("joblib can execute code; use --trust-local-checkpoint only for your own checkpoint")
    print(json.dumps(run(args.data_dir, args.output_dir, args.checkpoint), indent=2, ensure_ascii=False))
