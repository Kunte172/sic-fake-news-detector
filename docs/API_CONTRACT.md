# Hợp đồng API v0

Base URL local: `http://localhost:8000`. JSON UTF-8.

## Đã triển khai

- `GET /health` → `{"status":"ok","model_loaded":false}`; chỉ phản ánh API và trạng thái artifact.
- `POST /api/v1/analyze` với `{"text":"English article..."}` → `{"id":1,"label":"SUSPICIOUS","score":0.72,"model_version":"baseline-v0"}`. Có Bearer token hợp lệ thì lưu lượt phân tích vào lịch sử cá nhân và trả `id`; không gửi token thì `id:null` và không lưu. Gửi token sai/hết hạn trả HTTP 401. `score` là điểm lớp fake theo mô hình, không phải xác suất sự kiện sai sự thật. Giá trị trên chỉ là ví dụ.
- Nếu chưa nạp artifact, API trả HTTP 503. Nếu văn bản quá ngắn hoặc quá dài, trả HTTP 422.
- `POST /api/v1/auth/register` với `{"email":"...","password":"..."}` → trả HTTP 201 `{"email":"...","role":"USER"}`. Server tự gán quyền USER; client không chọn role. Lỗi 400 nếu trùng email.
- `POST /api/v1/auth/login` với `{"email":"...","password":"..."}` → trả HTTP 200 `{"access_token":"...","token_type":"bearer","role":"USER"}`. Lỗi 401 nếu sai mật khẩu/email.
- `GET /api/v1/auth/me` với header `Authorization: Bearer <token>` → trả HTTP 200 `{"email":"...","role":"USER"}`. Lỗi 401 nếu token sai/hết hạn.
- `GET /api/v1/analyses?limit=10&offset=0` cần Bearer token → `{"total":1,"limit":10,"offset":0,"items":[...]}`. Chỉ trả lịch sử của tài khoản hiện tại; mỗi mục gồm `id`, `input_type`, `content_preview`, `label`, `score`, `model_version`, `created_at`, `feedback`. Giới hạn `limit` 1–50, `offset` từ 0.
- `POST /api/v1/analyses/{id}/feedback` cần Bearer token, body `{"agree":false,"comment":"..."}` → HTTP 201 với `id`, `analysis_id`, `agree`, `comment`. Chỉ chủ sở hữu được phản hồi; không có bài hoặc không thuộc sở hữu trả 404, gửi lần hai trả 409. `comment` tối đa 1000 ký tự. Phản hồi không trở thành nhãn huấn luyện.
- `GET /api/v1/admin/summary` cần quyền ADMIN → `total_users`, `total_analyses`, `total_feedbacks`, `disputed_feedbacks`.
- `GET /api/v1/admin/disputed?limit=10&offset=0` cần quyền ADMIN → `total`, `limit`, `offset`, `items` cho phản hồi `agree:false`, gồm thông tin tóm tắt bài và phiên bản mô hình. USER nhận 403.

## Đề xuất cho các issue tiếp theo (chưa triển khai)

- `POST /api/v1/analyses` nhận **một trong hai** `text`/`url`, trả id, nguồn đầu vào, điểm, phiên bản model và giải thích. Cần đăng nhập.

## Giải thích dự đoán — ML-04 (đề xuất, chưa nối vào API)

Module `ml/src/explain.py` (`Explainer.analyze`) trả đúng hình dạng dưới đây. Khi `/api/v1/analyze` chuyển sang artifact ML-01, phản hồi giữ các trường hiện có (`id`, `label`, `score`, `model_version`) và **thêm** object `explanation`:

```json
{
  "id": 1,
  "label": "SUSPICIOUS",
  "score": 0.9312,
  "model_version": "ml-01-audited-classic-models-v1:linear_svm",
  "explanation": {
    "schema_version": "1.0",
    "method": "lime",
    "model_version": "ml-01-audited-classic-models-v1:linear_svm",
    "score_kind": "calibrated_fake_score",
    "terms": [
      {"term": "hoax", "weight": 0.0412, "direction": "toward_fake", "global_weight": 1.8231},
      {"term": "minister", "weight": -0.0275, "direction": "toward_real", "global_weight": -1.2044}
    ],
    "fidelity": 0.83,
    "num_samples": 1000,
    "seed": 42,
    "note": "Giải thích hiển thị theo từ đơn; mô hình còn dùng cặp từ liên tiếp ...",
    "disclaimer": "Đây là lý do mô hình đưa ra dự đoán ... không phải bằng chứng sự kiện đúng hay sai ..."
  }
}
```

- `label`: `SUSPICIOUS` khi mô hình dự đoán lớp Fake, ngược lại `LESS_SUSPICIOUS` (khớp `backend/app/inference.py`). Nhãn lấy từ `predict` của mô hình, khớp số liệu ML-01.
- `score`: điểm lớp Fake. Với Linear SVM là điểm **đã hiệu chỉnh** (Platt scaling fit trên validation, `score_kind = calibrated_fake_score`); không phải `decision_function` thô và không phải xác suất sự kiện sai sự thật. Điểm hiệu chỉnh và nhãn có thể lệch ở vùng gần 0,5 (ví dụ điểm 0,55 vẫn đi với `LESS_SUSPICIOUS`; 8/3.803 bài test): **nhãn là kết quả chính thức**, UI/API không tự suy nhãn từ điểm.
- `terms[].weight` > 0: từ đẩy dự đoán về Fake; < 0: về Real (ảnh hưởng **cục bộ** của LIME quanh bài này). `global_weight`: hệ số của từ trong mô hình (dương = nghiêng Fake), `null` nếu từ ngoài từ vựng.
- `fidelity`: R² của xấp xỉ cục bộ. Giá trị thấp nghĩa là giải thích kém tin cậy (thường gặp khi điểm gần 0 hoặc 1); UI phải cảnh báo, không trình bày danh sách từ như lý do chắc chắn.
- Văn bản được loại dấu nguồn bằng `clean_colab_text` **một lần** trước khi dự đoán; API không làm sạch thêm. Luồng ML-01 dùng nhãn **0 = Fake, 1 = Real**; mã nhãn Fake đọc từ `label_map` trong `ml01_report.json`, không suy ra từ số.
- Không lưu hay trả nguyên văn bài trong `explanation`. Văn bản rỗng sau làm sạch → HTTP 422; chưa nạp artifact hoặc hiệu chỉnh → HTTP 503.
- **Lưu ý khi nối vào API:** `backend/app/inference.py` (`Predictor`) hiện cố định lớp Fake = 1, gọi `predict_proba` và đặt nhãn theo `score >= 0.5`. Vì vậy **không đặt `MODEL_PATH` trỏ tới artifact ML-01** (Linear SVM, Fake = 0, không có `predict_proba`). Khi chuyển `/analyze` sang ML-01, dùng `Explainer.analyze()`: nhãn lấy từ `predict` của mô hình (khớp số liệu ML-01), điểm là điểm đã hiệu chỉnh.
- UI **bắt buộc** hiển thị `disclaimer` cạnh phần giải thích và dùng cách nói "lý do mô hình dự đoán", không dùng "bằng chứng".
- Lịch sử `GET /api/v1/analyses` hiện chỉ lưu `label`, `score`, `model_version` và `content_preview`, **chưa** có `explanation`. Muốn xem lại giải thích trong lịch sử thì cần lưu object này (chỉ từ khóa, không nguyên văn bài) hoặc tính lại theo yêu cầu; quyết định ở issue tiếp theo.

Tài liệu này là nơi thống nhất hợp đồng trước khi code. Không gửi `user_id` từ client để quyết định quyền sở hữu; API lấy từ phiên đăng nhập. Không coi phản hồi đồng ý/không đồng ý là nhãn thật/giả.
