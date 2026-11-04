"""ML-04 · Giải thích mô hình ML-01 bằng từ khóa toàn cục và LIME cục bộ.

Mô hình giải thích là artifact ML-01 (`ml01_selected.joblib`, hiện là Linear SVM,
nhãn 0 = Fake, 1 = Real). Chỉ nạp artifact tin cậy do chính nhóm tạo (joblib không an toàn
với file lạ).

Quy tắc đã chốt từ DATA-02/ML-01:
- Văn bản người dùng được làm sạch bằng `clean_source_markers` ĐÚNG MỘT LẦN trước khi
  dự đoán/giải thích (như lúc huấn luyện). Không làm sạch lại ở nơi khác.
- Linear SVM không có `predict_proba`. Điểm trả ra là điểm lớp Fake đã hiệu chỉnh
  (Platt scaling fit trên VALIDATION, xem calibrate_selected.py); không phải margin thô
  và không phải xác suất sự kiện sai sự thật.
- Nhãn lấy từ `label_map` trong ml01_report.json, không đoán từ số 0/1.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from backend.app.colab_preprocessing import clean_source_markers

SCHEMA_VERSION = "1.0"
LABEL_SUSPICIOUS = "SUSPICIOUS"          # khớp API_CONTRACT v0
LABEL_LESS_SUSPICIOUS = "LESS_SUSPICIOUS"  # khớp backend/app/inference.py
DISCLAIMER = (
    "Đây là lý do mô hình đưa ra dự đoán dựa trên từ ngữ trong văn bản, không phải "
    "bằng chứng sự kiện đúng hay sai. Hãy kiểm chứng với nguồn tin độc lập."
)
NGRAM_NOTE = (
    "Giải thích hiển thị theo từ đơn; mô hình còn dùng cặp từ liên tiếp nên một số "
    "ảnh hưởng không xuất hiện ở đây."
)

# Token nghi dấu nguồn/định dạng (DATA-02). Chỉ để RÀ BẰNG TAY: nhiều từ như
# "image", "via", "washington" cũng là từ thường gặp, không tự động coi là rò rỉ.
LEAK_TOKENS = {
    "reuters", "twitter", "pic", "http", "https", "www", "youtu", "youtube",
    "image", "photo", "credit", "credits", "featured", "getty", "via",
    "courtesy", "washington", "wire", "21st", "century",
    "tmsnrt", "rs",  # mảnh link rút gọn (vd tmsnrt.rs/...) còn sót sau WEB_LINK
}


def fake_label_from_report(report: dict) -> int:
    """Đọc mã nhãn của lớp Fake từ label_map (Colab: 0=Fake; baseline cũ: 1=FAKE_DATASET)."""
    for code, name in report.get("label_map", {}).items():
        if str(name).strip().lower().startswith("fake"):
            return int(code)
    raise ValueError("Không tìm thấy lớp Fake trong label_map của báo cáo.")


def fit_platt(margins, is_fake) -> dict:
    """Platt scaling: P(Fake) = sigmoid(slope * margin + intercept). Chỉ fit trên validation."""
    margins = np.asarray(margins, dtype=float).reshape(-1, 1)
    model = LogisticRegression(C=1e6, max_iter=1000).fit(margins, np.asarray(is_fake, dtype=int))
    return {
        "method": "platt_sigmoid",
        "slope": float(model.coef_[0, 0]),
        "intercept": float(model.intercept_[0]),
        "fit_on": "validation",
    }


def leakage_report(keywords: dict[str, list[dict]]) -> list[str]:
    """Từ khóa top chứa token nghi dấu nguồn, để người làm rà tay."""
    flagged = set()
    for side in keywords.values():
        for item in side:
            if LEAK_TOKENS & set(re.findall(r"\w+", item["term"].lower())):
                flagged.add(item["term"])
    return sorted(flagged)


@dataclass
class Explainer:
    pipeline: Any                      # sklearn Pipeline: TfidfVectorizer ... classifier
    fake_label: int                    # mã nhãn của lớp Fake (từ label_map)
    model_version: str = "ml01"
    calibration: dict | None = None    # kết quả fit_platt, cần khi classifier không có predict_proba
    cleaner: Callable[[str], str] = clean_source_markers

    def __post_init__(self):
        if len(getattr(self.pipeline, "steps", [])) < 2:
            raise TypeError("Cần sklearn Pipeline gồm vectorizer + classifier.")
        classes = list(self.pipeline.classes_)
        if len(classes) != 2 or self.fake_label not in classes:
            raise ValueError(f"classes_={classes} không khớp fake_label={self.fake_label}")
        self.fake_index = classes.index(self.fake_label)
        self.class_names = ["Fake" if c == self.fake_label else "Real" for c in classes]

    # ------------------------------------------------------------------ nạp
    @classmethod
    def from_artifacts(cls, model_path, report_path, calibration_path=None, model_version=None):
        """Điểm nạp duy nhất; sửa tại đây nếu đổi cách lưu artifact."""
        pipeline = joblib.load(model_path)
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        calibration = None
        if calibration_path and Path(calibration_path).is_file():
            calibration = json.loads(Path(calibration_path).read_text(encoding="utf-8"))
        version = model_version or f"{report.get('experiment', 'ml01')}:{report.get('selected_model', '?')}"
        return cls(pipeline, fake_label_from_report(report), version, calibration)

    # ------------------------------------------------------------ dự đoán
    @property
    def calibrated(self) -> bool:
        return not hasattr(self.pipeline, "predict_proba")

    def predict_proba(self, texts) -> np.ndarray:
        """Ma trận (n, 2) theo thứ tự classes_. Văn bản phải ĐÃ làm sạch."""
        texts = list(texts)
        if not self.calibrated:
            return self.pipeline.predict_proba(texts)
        if self.calibration is None:
            raise TypeError(
                "Mô hình không có predict_proba (Linear SVM). Chạy calibrate_selected.py để "
                "tạo hiệu chỉnh; không dùng decision_function làm xác suất."
            )
        margin = np.asarray(self.pipeline.decision_function(texts), dtype=float)
        z = np.clip(self.calibration["slope"] * margin + self.calibration["intercept"], -50, 50)
        p_fake = 1.0 / (1.0 + np.exp(-z))
        out = np.empty((len(texts), 2))
        out[:, self.fake_index] = p_fake
        out[:, 1 - self.fake_index] = 1.0 - p_fake
        return out

    # -------------------------------------------------- từ khóa toàn cục
    def _fake_weights(self) -> np.ndarray:
        """Trọng số từng đặc trưng; dương = nghiêng về Fake."""
        clf = self.pipeline.steps[-1][1]
        if hasattr(clf, "coef_") and clf.coef_.shape[0] == 1:
            return clf.coef_[0] * (1.0 if self.fake_index == 1 else -1.0)
        if hasattr(clf, "feature_log_prob_"):
            return clf.feature_log_prob_[self.fake_index] - clf.feature_log_prob_[1 - self.fake_index]
        raise TypeError(f"Không lấy được trọng số từ {type(clf).__name__}.")

    def global_keywords(self, top_k: int = 20) -> dict[str, list[dict]]:
        weights = self._fake_weights()
        terms = np.asarray(self.pipeline.steps[0][1].get_feature_names_out())
        order = np.argsort(weights)
        pick = lambda idx: [{"term": str(terms[i]), "weight": float(weights[i])} for i in idx]
        return {"fake": pick(order[::-1][:top_k]), "real": pick(order[:top_k])}

    # ------------------------------------------------------ LIME cục bộ
    def explain(self, text: str, already_clean: bool = False, **kwargs) -> dict:
        cleaned = text if already_clean else self.cleaner(text)
        return self._explain_cleaned(cleaned, **kwargs)

    def _explain_cleaned(self, cleaned: str, num_features: int = 10,
                         num_samples: int = 1000, seed: int = 42) -> dict:
        try:
            from lime.lime_text import LimeTextExplainer
        except ImportError as exc:
            raise ImportError("Cần cài lime: pip install -r ml/requirements-explain.txt") from exc
        if not cleaned.strip():
            raise ValueError("Văn bản rỗng sau khi loại dấu nguồn.")

        fi = self.fake_index
        lime = LimeTextExplainer(class_names=self.class_names, random_state=seed)
        exp = lime.explain_instance(
            cleaned, self.predict_proba, labels=(fi,),
            num_features=num_features, num_samples=num_samples,
        )
        vocab = getattr(self.pipeline.steps[0][1], "vocabulary_", {})
        gweights = self._fake_weights()
        terms = []
        for term, weight in sorted(exp.as_list(label=fi), key=lambda t: -abs(t[1])):
            idx = vocab.get(term.lower())
            terms.append({
                "term": term,
                "weight": round(float(weight), 5),   # > 0: đẩy về Fake; < 0: đẩy về Real
                "direction": "toward_fake" if weight > 0 else "toward_real",
                "global_weight": round(float(gweights[idx]), 5) if idx is not None else None,
            })
        fidelity = exp.score.get(fi) if isinstance(exp.score, dict) else exp.score
        return {
            "schema_version": SCHEMA_VERSION,
            "method": "lime",
            "model_version": self.model_version,
            "score_kind": "calibrated_fake_score" if self.calibrated else "model_probability",
            "terms": terms,
            "fidelity": None if fidelity is None else round(float(fidelity), 4),
            "num_samples": num_samples,
            "seed": seed,
            "note": NGRAM_NOTE,
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------ phản hồi đầy đủ cho API (/analyze)
    def analyze(self, text: str, already_clean: bool = False, **kwargs) -> dict:
        """Làm sạch một lần, rồi dự đoán + giải thích. Hình dạng khớp API_CONTRACT v0
        (label/score/model_version) cộng thêm `explanation`."""
        cleaned = text if already_clean else self.cleaner(text)
        if not cleaned.strip():
            raise ValueError("Văn bản rỗng sau khi loại dấu nguồn.")
        score = float(self.predict_proba([cleaned])[0][self.fake_index])
        is_fake = self.pipeline.predict([cleaned])[0] == self.fake_label  # khớp số liệu ML-01
        return {
            "label": LABEL_SUSPICIOUS if is_fake else LABEL_LESS_SUSPICIOUS,
            "score": round(score, 4),
            "model_version": self.model_version,
            "explanation": self._explain_cleaned(cleaned, **kwargs),
        }
