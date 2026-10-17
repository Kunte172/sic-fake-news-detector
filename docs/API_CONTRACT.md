# Hợp đồng API v0

Base URL local: `http://localhost:8000`. JSON UTF-8.

## Đã triển khai

- `GET /health` → `{"status":"ok","model_loaded":false}`; chỉ phản ánh API và trạng thái artifact.
- `POST /api/v1/analyze` với `{"text":"English article..."}` → `{"label":"SUSPICIOUS","score":0.72,"model_version":"baseline-v0"}`. `score` là điểm lớp fake theo mô hình, không phải xác suất sự kiện sai sự thật. Giá trị trên chỉ là ví dụ.
- Nếu chưa nạp artifact, API trả HTTP 503. Nếu văn bản quá ngắn hoặc quá dài, trả HTTP 422.
- `POST /api/v1/auth/register` với `{"email":"...","password":"...","role":"USER"}` → trả HTTP 201 `{"email":"...","role":"USER"}`. Lỗi 400 nếu trùng email.
- `POST /api/v1/auth/login` với `{"email":"...","password":"..."}` → trả HTTP 200 `{"access_token":"...","token_type":"bearer","role":"USER"}`. Lỗi 401 nếu sai mật khẩu/email.
- `GET /api/v1/auth/me` với header `Authorization: Bearer <token>` → trả HTTP 200 `{"email":"...","role":"USER"}`. Lỗi 401 nếu token sai/hết hạn.

## Đề xuất cho các issue tiếp theo (chưa triển khai)

- `POST /api/v1/analyses` nhận **một trong hai** `text`/`url`, trả id, nguồn đầu vào, điểm, phiên bản model và giải thích. Cần đăng nhập.
- `GET /api/v1/analyses` trả lịch sử phân trang của chính người dùng.
- `POST /api/v1/analyses/{id}/feedback` nhận `{"agree":false,"comment":"..."}`.
- `GET /api/v1/admin/summary`, `GET /api/v1/admin/disputed` chỉ ADMIN.

Tài liệu này là nơi thống nhất hợp đồng trước khi code. Không gửi `user_id` từ client để quyết định quyền sở hữu; API lấy từ phiên đăng nhập. Không coi phản hồi đồng ý/không đồng ý là nhãn thật/giả.