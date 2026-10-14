# Dữ liệu và đánh giá

## Bộ dữ liệu

Nguồn: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset. Hai file `Fake.csv`, `True.csv` có `title`, `text`, `subject`, `date`. Không commit CSV. Kiểm tra giấy phép bộ dữ liệu và quyền dùng bài báo trước khi phân phối artifact hoặc công bố nội dung bài.

## Giao thức thí nghiệm

1. Kiểm toán nhãn, bài rỗng, bài trùng và gần trùng. Giữ nhóm bài tương đương ở một phía phép chia; loại bài có cùng nội dung mà nhãn mâu thuẫn.
2. Chia test cố định một lần. Chỉ fit vectorizer, tokenizer và mô hình trên train; dùng validation/CV trên train để chọn tham số.
3. So sánh cùng test set, seed, quy tắc làm sạch. Báo cáo Accuracy, F1(fake), macro F1, confusion matrix; lưu số mẫu từng nhãn.
4. Chạy kiểm tra ablation: văn bản nguyên bản so với loại dấu nguồn. Xem từ khóa top của mô hình để phát hiện nguồn còn sót.
5. Đánh giá theo chủ đề: tạo nhóm chủ đề chung độc lập với nhãn CSV, kiểm tra từng fold có cả fake và real; giữ trọn nhóm ngoài train. Nếu không đủ mẫu, ghi rõ không đánh giá được, không báo F1 một lớp như kết quả tổng quát.
6. Nếu ứng dụng hỗ trợ mạng xã hội, bổ sung tập có nhãn từ miền mạng xã hội và đánh giá riêng, không suy diễn từ Kaggle.

## Trạng thái v0

`ml/src/train_baseline.py` chỉ thực hiện baseline Logistic Regression và split train/test có kiểm tra trùng **chính xác sau làm sạch**. Chưa giải quyết bài gần trùng, source confounding còn ẩn, topic CV, calibration và domain shift. Số liệu từ v0 là mốc kỹ thuật, không phải kết luận cuối cùng.
