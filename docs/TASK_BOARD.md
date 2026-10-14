# Bảng phân công khởi đầu

Tạo một GitHub Issue cho từng mã dưới đây. Người phụ trách do nhóm điền vào cột Owner trên GitHub.

| Mã | Luồng | Đầu việc | Điều kiện hoàn thành | Phụ thuộc |
| --- | --- | --- | --- | --- |
| DATA-01 | Dữ liệu | Notebook EDA | 4 nhóm phân tích, biểu đồ và kết luận nguồn | Dataset |
| DATA-02 | Dữ liệu | Audit dấu nguồn, trùng/gần trùng | Báo cáo tần suất và test cho phép làm sạch | DATA-01 |
| ML-01 | Baseline | Thêm NB và Linear SVM | Cùng split, bảng Accuracy/F1, artifact có version | DATA-02 |
| ML-02 | Đánh giá | Chủ đề chung và kiểm thử nhóm | Fold hợp lệ có hai nhãn, hoặc báo cáo không khả thi | DATA-02 |
| ML-03 | Deep learning | Embedding + LSTM | Tokenizer chỉ fit trên train; cùng test set, early stopping | DATA-02 |
| ML-04 | Giải thích | Trọng số từ và LIME | Ví dụ đúng/sai, không gọi lý do là bằng chứng thật/giả | ML-01 |
| API-01 | Tài khoản | Auth và phân quyền USER/ADMIN | DB migration, test quyền truy cập, tài khoản tách biệt | API contract |
| API-02 | Lịch sử | Lưu Analysis và Feedback | Người dùng chỉ xem dữ liệu của mình, admin xem thống kê | API-01 |
| API-03 | URL | Trích xuất bài viết | Giới hạn nguồn, chuyển hướng, timeout, kích thước | API-01 |
| UI-01 | Giao diện | Login, lịch sử và phản hồi | Kết nối API, loading/error rõ ràng | API-01/02 |
| UI-02 | Quản trị | Thống kê và ca tranh cãi | Chỉ ADMIN vào được, lọc và phân trang | API-02 |
| OPS-01 | Triển khai | Build, cấu hình cloud, demo | URL hoạt động, biến môi trường, test 2 tài khoản | API/UI |
| DOC-01 | Báo cáo | Phương pháp, đạo đức, giới hạn | Nguồn dữ liệu, thí nghiệm và bảng kết quả tái lập | ML-02/03 |

Mỗi luồng có thể bắt đầu độc lập từ scaffold này; API-01/02 và UI-01 cần thống nhất hợp đồng trước khi merge.
