"""Hiệu chỉnh điểm Linear SVM (Platt scaling) CHỈ trên validation để LIME có xác suất.

Không huấn luyện lại SVM, không dùng test để fit. Test chỉ để báo cáo Brier và số ca
nhãn SVM khác nhãn theo ngưỡng 0,5 của điểm đã hiệu chỉnh.

  python -m ml.src.calibrate_selected
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

from ml.src.explain import fake_label_from_report, fit_platt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--splits", type=Path, default=Path("ml/artifacts/data02/prepared_splits.csv"))
    ap.add_argument("--model-dir", type=Path, default=Path("ml/artifacts/ml01"))
    args = ap.parse_args()

    pipeline = joblib.load(args.model_dir / "ml01_selected.joblib")
    report = json.loads((args.model_dir / "ml01_report.json").read_text(encoding="utf-8"))
    if hasattr(pipeline, "predict_proba"):
        print("Mô hình đã có predict_proba, không cần hiệu chỉnh.")
        return
    fake = fake_label_from_report(report)

    frame = pd.read_csv(args.splits, keep_default_na=False)
    val, test = (frame[frame.split.eq(s)] for s in ("validation", "test"))
    cal = fit_platt(pipeline.decision_function(val.text_clean), val.label.eq(fake))

    margin = pipeline.decision_function(test.text_clean)
    z = np.clip(cal["slope"] * margin + cal["intercept"], -50, 50)
    p_fake = 1 / (1 + np.exp(-z))
    svm_fake = pipeline.predict(test.text_clean) == fake
    cal.update({
        "n_validation": len(val),
        "test_brier": round(float(brier_score_loss(test.label.eq(fake), p_fake)), 6),
        "test_rows_where_threshold_0.5_disagrees_with_svm": int(((p_fake >= 0.5) != svm_fake).sum()),
        "note": "Điểm đã hiệu chỉnh, không phải xác suất sự kiện sai sự thật. Nhãn công bố vẫn theo SVM.",
    })
    out = args.model_dir / "ml01_calibration.json"
    out.write_text(json.dumps(cal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(cal, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
