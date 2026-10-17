# Hợp đồng API v0

Base URL local: `http://localhost:8000`. JSON UTF-8.

## Đã triển khai

- `GET /health` → `{"status":"ok","model_loaded":false}`; chỉ phản ánh API và trạng thái artifact.
- `POST /api/v1/analyze` với `{"text":"English article..."}` → `{"id": 1, "label":"SUSPICIOUS","score":0.72,"model_version":"baseline-v0"}`. `score` là điểm lớp fake theo mô hình, không phải xác suất sự kiện sai sự thật. Giá trị trên chỉ là ví dụ. Hỗ trợ kèm token Bearer để tự động lưu kết quả vào lịch sử cá nhân.
- Nếu chưa nạp artifact, API trả HTTP 503. Nếu văn bản quá ngắn hoặc quá dài, trả HTTP 422.
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`: Đăng ký, đăng nhập cấp JWT Bearer token và lấy thông tin người dùng hiện tại.
- `GET /api/v1/analyses?limit=10&offset=0`: Trả lịch sử phân tích kèm phân trang của chính người dùng đăng nhập (`items`, `total`, `limit`, `offset`).
- `POST /api/v1/analyses/{analysis_id}/feedback`: Nhận `{"agree":false,"comment":"..."}` để lưu phản hồi của người dùng cho bài phân tích tương ứng.
- `GET /api/v1/admin/summary`: Trả số liệu tổng hợp người dùng, lượt phân tích và phản hồi. Chỉ dành cho vai trò ADMIN.
- `GET /api/v1/admin/disputed?limit=10&offset=0`: Danh sách các ca bị người dùng phản đối (`agree = false`) phục vụ kiểm duyệt thủ công. Chỉ dành cho vai trò ADMIN.

## Đề xuất cho các issue tiếp theo (chưa triển khai)

- `POST /api/v1/analyses` nhận **một trong hai** `text`/`url`, trả id, nguồn đầu vào, điểm, phiên bản model và giải thích. Cần đăng nhập.

Tài liệu này là nơi thống nhất hợp đồng trước khi code. Không gửi `user_id` từ client để quyết định quyền sở hữu; API lấy từ phiên đăng nhập. Không coi phản hồi đồng ý/không đồng ý là nhãn thật/giả.