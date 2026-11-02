"""DATA-03: reproducible LIAR import/audit. Never train or modify DATA-02.

Binary policy is a project choice: true=1, false/pants-fire=0; defer middle labels.
Original six-way labels and official splits are always retained in separate files.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import zipfile

from datasketch import MinHash, MinHashLSH

from backend.app.colab_preprocessing import clean_source_markers

SOURCE_URL = "https://www.cs.ucsb.edu/~william/data/liar_dataset.zip"
PINNED_SHA256 = "611c1addad919743dde15822b87a60bfb760d8f85597f25289e34621800654c7"
LABELS = {"true", "mostly-true", "half-true", "barely-true", "false", "pants-fire"}
BINARY = {"true": 1, "false": 0, "pants-fire": 0}
SPLITS = {"train.tsv": "train", "valid.tsv": "validation", "test.tsv": "test"}
META = ["subject", "speaker", "speaker_job", "state", "party", "barely_true_count",
        "false_count", "half_true_count", "mostly_true_count", "pants_fire_count", "context"]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


def text_hash(text):
    return hashlib.sha256(norm(text).encode("utf8")).hexdigest()


def read_zip(path, enforce_pin=True):
    digest = sha256(path)
    if enforce_pin and digest != PINNED_SHA256:
        raise ValueError("LIAR archive checksum differs from reviewed release. Inspect before using it.")
    rows, warnings, seen = [], [], set()
    with zipfile.ZipFile(path) as z:
        for name, split in SPLITS.items():
            if name not in z.namelist():
                raise ValueError(f"Missing {name}")
            # Read only known members. Never extract paths supplied by an archive.
            reader = csv.reader(io.StringIO(z.read(name).decode("utf-8-sig")), delimiter="\t")
            for line, cells in enumerate(reader, 1):
                if len(cells) < 3 or len(cells) > 14:
                    raise ValueError(f"{name}:{line}: expected 3..14 columns, got {len(cells)}")
                missing = len(cells) != 14
                if missing:
                    warnings.append({"file": name, "row": line, "columns": len(cells), "id": cells[0],
                                     "action": "pad_missing_metadata_only"})
                cells += [""] * (14 - len(cells))
                sid, label, statement = cells[:3]
                if not re.fullmatch(r"\d+\.json", sid) or sid in seen:
                    raise ValueError(f"Bad or duplicate statement ID: {sid}")
                if label not in LABELS:
                    raise ValueError(f"Unknown label: {label}")
                seen.add(sid)
                clean = clean_source_markers(statement)
                rows.append({
                    "id": "liar:" + sid.removesuffix(".json"), "source_id": sid,
                    "dataset": "LIAR-v1.0", "language": "en", "content_type": "claim",
                    "official_split": split, "label_original": label,
                    "label_binary": BINARY.get(label), "text": statement, "text_clean": clean,
                    "text_sha256": text_hash(clean), "publication_date": None,
                    "source_archive_url": SOURCE_URL, "source_archive_sha256": digest,
                    "source_file": name, "source_line": line, "metadata_incomplete": missing,
                    "metadata": dict(zip(META, cells[3:])),
                })
        upstream_readme = z.read("README").decode("utf8")
    return rows, warnings, upstream_readme


def token_shingles(text):
    words = re.findall(r"\w+", text.casefold())
    return {" ".join(words[i:i+5]) for i in range(len(words)-4)} if len(words) >= 5 else ({" ".join(words)} if words else set())


def signature(text):
    m = MinHash(num_perm=128, seed=42)
    parts = sorted(token_shingles(text))
    for start in range(0, len(parts), 128):
        m.update_batch([p.encode("utf8") for p in parts[start:start+128]])
    return m


def similar(a, b):
    x, y = token_shingles(a), token_shingles(b)
    return len(x & y)/len(x | y) if x | y else 0.0


def near_edges(rows):
    """Same LSH parameters as DATA-02; exact verification of candidates only."""
    index = MinHashLSH(threshold=.70, num_perm=128)
    by_id = {r["id"]: r for r in rows}
    edges = []
    for i, row in enumerate(rows, 1):
        if not norm(row["text_clean"]):
            continue
        sig = signature(row["text_clean"])
        for other in sorted(index.query(sig)):
            score = similar(row["text_clean"], by_id[other]["text_clean"])
            if score >= .85:
                edges.append({"id_1": other, "id_2": row["id"], "jaccard": score, "kind": "near"})
        index.insert(row["id"], sig)
        if i % 2000 == 0:
            print(f"LIAR near-duplicate audit {i}/{len(rows)}", flush=True)
    # Normalized exact matches must not depend on approximate candidate retrieval.
    first = {}
    for row in rows:
        key = norm(row["text_clean"])
        if key and key in first:
            edges.append({"id_1": first[key], "id_2": row["id"], "jaccard": 1.0, "kind": "exact"})
        else:
            first[key] = row["id"]
    return edges


def groups(rows, edges):
    parent = {r["id"]: r["id"] for r in rows}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for edge in edges:
        a, b = find(edge["id_1"]), find(edge["id_2"])
        parent[max(a,b)] = min(a,b)
    result = defaultdict(list)
    for row in rows:
        result[find(row["id"])].append(row)
    return result


def select_binary(rows, edges, v1_matches):
    """Quarantine complete cross-split/conflicting groups; never move test to train."""
    kept, held = [], []
    for gid, members in sorted(groups(rows, edges).items()):
        shared = []
        if len({r["official_split"] for r in members}) > 1:
            shared.append("group_crosses_official_splits")
        if len({r["label_original"] for r in members}) > 1:
            shared.append("group_has_conflicting_six_way_labels")
        if any(r["id"] in v1_matches for r in members):
            shared.append("group_overlaps_data02")
        seen_content = set()
        for row in sorted(members, key=lambda r:r["id"]):
            reasons = list(shared)
            if row["label_binary"] is None:
                reasons.append("intermediate_label_not_mapped")
            if not norm(row["text_clean"]):
                reasons.append("empty_statement")
            if row["text_sha256"] in seen_content:
                reasons.append("exact_duplicate_within_group")
            seen_content.add(row["text_sha256"])
            if reasons:
                held.append({**row, "group_id": gid, "exclusion_reasons": reasons})
            else:
                # Model view is deliberately text-only: metadata and verdict label names stay out.
                kept.append({"id": row["id"], "text": row["text_clean"],
                             "label": row["label_binary"], "split": row["official_split"],
                             "group_id": gid, "language": "en", "content_type": "claim"})
    return kept, held


def compare_v1(rows, prepared_csv):
    """Audit original/cleaned bodies and titles in the provided DATA-02 snapshot.

    Near checks compare whole texts, not claim containment or semantic paraphrase.
    No V1 label/split is used for choosing any LIAR configuration.
    """
    csv.field_size_limit(2**30)
    lookup = defaultdict(set)
    index = MinHashLSH(threshold=.70, num_perm=128)
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        if norm(r["text_clean"]):
            lookup[norm(r["text_clean"])].add(r["id"])
            index.insert(r["id"], signature(r["text_clean"]))
    matches, count = [], 0
    with Path(prepared_csv).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"text_clean", "split", "_row_id"}.issubset(reader.fieldnames or []):
            raise ValueError("DATA-02 input must be prepared_splits.csv with text_clean, split, _row_id")
        for v1 in reader:
            count += 1
            texts = {"body": v1["text_clean"]}
            if v1.get("title"):
                texts["title"] = clean_source_markers(v1["title"])
            for field, value in texts.items():
                if not norm(value):
                    continue
                exact = lookup.get(norm(value), set())
                candidates = set(index.query(signature(value))) | exact
                for rid in sorted(candidates):
                    score = 1.0 if rid in exact else similar(value, by_id[rid]["text_clean"])
                    if score >= .85:
                        matches.append({"liar_id": rid, "data02_row_id": v1["_row_id"],
                                        "data02_split": v1["split"], "field": field,
                                        "kind": "exact" if rid in exact else "near", "jaccard": score})
            if count % 5000 == 0:
                print(f"DATA-02 overlap audit {count} articles", flush=True)
    return matches, count


def validate_view(rows):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate IDs in model view")
    for field in ("group_id", "text"):
        seen = defaultdict(set)
        for row in rows:
            seen[norm(row[field])].add(row["split"])
        if any(len(v) > 1 for v in seen.values()):
            raise ValueError(f"Cross-split {field} leakage")
    for split in ("train", "validation", "test"):
        part = [r for r in rows if r["split"] == split]
        if {r["label"] for r in part} != {0,1}:
            raise ValueError(f"{split} does not have both binary labels")


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counts(rows, label_field, split_field):
    return {s: dict(sorted(Counter(str(r[label_field]) for r in rows if r[split_field]==s).items()))
            for s in ("train", "validation", "test")}


def run(archive, output, v1_csv=None):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be new or empty; previous runs are immutable")
    output.mkdir(parents=True, exist_ok=True)
    rows, warnings, readme = read_zip(archive)
    edges = near_edges(rows)
    matches, v1_count = compare_v1(rows, v1_csv) if v1_csv else ([], 0)
    model_rows, excluded = select_binary(rows, edges, {r["liar_id"] for r in matches})
    validate_view(model_rows)
    write_jsonl(output / "liar_original_six_labels.jsonl", rows)
    write_jsonl(output / "liar_binary_strict.jsonl", model_rows)
    write_jsonl(output / "excluded_review.jsonl", excluded)
    write_jsonl(output / "near_pairs.jsonl", edges)
    write_jsonl(output / "data02_overlap.jsonl", matches)
    write_jsonl(output / "format_warnings.jsonl", warnings)
    write_jsonl(output / "split_manifest.jsonl", [
        {k:r[k] for k in ("id", "split", "group_id", "label")} | {"text_sha256": text_hash(r["text"])}
        for r in model_rows])
    (output / "UPSTREAM_README.txt").write_text(readme, encoding="utf8")
    group_list = list(groups(rows, edges).values())
    reason_counts = Counter(reason for r in excluded for reason in r["exclusion_reasons"])
    summary = {
        "dataset": "DATA03-LIAR-v1", "source_url": SOURCE_URL, "upstream_release": "2017-04-23",
        "archive_sha256": sha256(archive), "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "original_rows": len(rows), "original_label_counts": counts(rows,"label_original","official_split"),
        "format_warnings": warnings, "empty_statements": sum(not norm(r["text_clean"]) for r in rows),
        "binary_mapping": BINARY, "deferred_labels": sorted(LABELS-set(BINARY)),
        "binary_rows": len(model_rows), "binary_counts": counts(model_rows,"label","split"),
        "excluded_rows": len(excluded), "exclusion_reasons_nonexclusive": dict(sorted(reason_counts.items())),
        "duplicate_group_count": sum(len(g)>1 for g in group_list),
        "cross_split_group_count": sum(len({r['official_split'] for r in g})>1 for g in group_list),
        "six_label_conflict_group_count": sum(len({r['label_original'] for r in g})>1 for g in group_list),
        "near_duplicate_parameters": {"shingle_words":5,"lsh_threshold":.70,"jaccard_threshold":.85,"num_perm":128,"seed":42},
        "data02_overlap_checked": v1_csv is not None, "data02_rows": v1_count,
        "data02_sha256": sha256(v1_csv) if v1_csv else None,
        "data02_matching_liar_ids": len({r['liar_id'] for r in matches}),
        "data02_overlap_pairs": len(matches), "model_view_cross_split_check": "passed",
        "model_feature_columns": ["text"], "training_performed": False,
        "limitations": [
            "2017 historical claim dataset; not current news and not full articles.",
            "Strict binary subset is a new project protocol, not the official six-way LIAR benchmark.",
            "Labels inherited from LIAR; original fact-check evidence has not been reverified per row.",
            "No per-row publication date or verified live evidence URL in the original archive.",
            "LSH retrieval is approximate; whole-text Jaccard does not detect semantic overlap or claim containment.",
            "DATA-02 comparison covers the supplied prepared snapshot only, not every prior training artifact.",
            "Speaker overlap and political-domain bias remain; no speaker-disjoint evaluation claimed.",
            "Research use only per upstream README; original publishers retain copyright."
        ],
    }
    summary["output_sha256"] = {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}
    (output/"audit_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data02-prepared", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.archive,args.output_dir,args.data02_prepared),ensure_ascii=False,indent=2))
