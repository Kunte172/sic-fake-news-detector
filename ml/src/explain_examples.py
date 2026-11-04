"""Sinh từ khóa toàn cục và ví dụ giải thích đúng/sai trên TẬP TEST của ML-01.

  python -m ml.src.explain_examples
Đầu ra ở ml/artifacts/explain/ (Git bỏ qua): global_keywords.json, examples.json.
Không ghi nguyên văn bài báo; chỉ id dòng, nhãn, điểm và từ khóa.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from ml.src.explain import Explainer, leakage_report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, default=Path("ml/artifacts/ml01"))
    ap.add_argument("--splits", type=Path, default=Path("ml/artifacts/data02/prepared_splits.csv"))
    ap.add_argument("--out", type=Path, default=Path("ml/artifacts/explain"))
    ap.add_argument("--per-cell", type=int, default=2, help="số ví dụ cho mỗi ô (thật, dự đoán)")
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--num-samples", type=int, default=1000)
    args = ap.parse_args()

    ex = Explainer.from_artifacts(
        args.model_dir / "ml01_selected.joblib", args.model_dir / "ml01_report.json",
        args.model_dir / "ml01_calibration.json",
    )
    args.out.mkdir(parents=True, exist_ok=True)

    keywords = ex.global_keywords(args.top_k)
    (args.out / "global_keywords.json").write_text(json.dumps(keywords, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Từ khóa top nghi dấu nguồn (cần rà tay):", leakage_report(keywords) or "không có")

    frame = pd.read_csv(args.splits, keep_default_na=False)
    test = frame[frame.split.eq("test")].copy()
    test["pred"] = ex.pipeline.predict(test.text_clean)
    name = lambda code: "Fake" if code == ex.fake_label else "Real"

    examples = []
    for true in (0, 1):
        for pred in (0, 1):
            cell = test[test.label.eq(true) & test.pred.eq(pred)]
            for _, row in cell.sample(min(args.per_cell, len(cell)), random_state=42).iterrows():
                result = ex.analyze(row.text_clean, already_clean=True, num_samples=args.num_samples)
                examples.append({
                    "row_id": row["_row_id"] if not hasattr(row["_row_id"], "item") else row["_row_id"].item(),
                    "group": "correct" if true == pred else "incorrect",
                    "true_label": name(true), "predicted": name(pred), **result,
                })
    (args.out / "examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {len(examples)} ví dụ vào {args.out}")


if __name__ == "__main__":
    main()
