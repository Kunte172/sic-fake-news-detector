# Phạm vi đề tài

## Mục tiêu

Xây dựng và đánh giá bộ phân loại văn bản tiếng Anh, sau đó cung cấp công cụ sàng lọc trên cloud cho nhiều tài khoản. Giao diện đưa ra điểm nghi ngờ, lý do mô hình dự đoán và cơ chế phản hồi. Không trình bày dự đoán như kết luận xác minh sự thật.

## Yêu cầu hoàn thành

1. EDA: độ dài, chủ đề, từ vựng đặc trưng và phong cách viết giữa hai nhãn.
2. Kiểm tra dấu nguồn, cách mở đầu, định dạng ngày, nhãn `subject`; tài liệu hóa tác động trước và sau khi xử lý.
3. So sánh TF-IDF + Logistic Regression, Linear SVM, Multinomial Naive Bayes và Embedding + LSTM trên cùng phép chia hợp lệ.
4. Accuracy, F1 lớp fake và macro F1, confusion matrix, đánh giá theo chủ đề có cả hai nhãn; ghi giới hạn nếu không lập được fold hợp lệ.
5. Giải thích hệ số mô hình tuyến tính và từng ca bằng LIME.
6. Người dùng đăng nhập, nhập văn bản/URL, xem lịch sử, gửi phản hồi; admin xem thống kê và ca tranh cãi.
7. Triển khai cloud, thử ít nhất hai tài khoản độc lập và ghi kết quả demo.

## Giới hạn cần trình bày

- True.csv và Fake.csv đến từ các nguồn khác nhau. Loại một vài chuỗi nguồn không bảo đảm hết sai lệch phong cách.
- `subject` gốc không phải tập nhóm chủ đề chung cho hai nhãn. Không dùng trực tiếp làm đặc trưng hay các fold đánh giá theo chủ đề.
- Tập dữ liệu chính không đại diện cho bài đăng mạng xã hội hoặc tiếng Việt. Để bảo vệ kết luận cho hai miền này, cần tập kiểm thử độc lập có nhãn.
- Phản hồi người dùng không tự động trở thành nhãn huấn luyện; cần quy trình rà soát.
