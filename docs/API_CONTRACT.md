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

Tài liệu này là nơi thống nhất hợp đồng trước khi code. Không gửi `user_id` từ client để quyết định quyền sở hữu; API lấy từ phiên đăng nhập. Không coi phản hồi đồng ý/không đồng ý là nhãn thật/giả.
