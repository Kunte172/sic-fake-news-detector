# DATA-03: LIAR — quy tắc dữ liệu và tích hợp

## Phạm vi

Bổ sung một nguồn **phát biểu tiếng Anh**, có nhãn do LIAR công bố, để nghiên cứu khả năng tổng quát hóa của mô hình. Đây là dữ liệu lịch sử năm 2017; ngày tải 02/11/2026 không phải ngày xuất bản phát biểu. Không có dữ liệu tiếng Việt trong đợt này.

Tác giả: William Yang Wang, ACL 2017, [bài báo](https://aclanthology.org/P17-2067/).
Nguồn ZIP: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip

LIAR được chọn trước vì có sẵn văn bản và nhãn. Bản tối thiểu của [FakeNewsNet/GossipCop](https://github.com/KaiDMML/FakeNewsNet) chủ yếu có ID, URL, tiêu đề và tweet IDs; muốn dùng nội dung toàn bài cần tải lại các nguồn. Đợt này chưa thực hiện GossipCop.

## Hai dạng dữ liệu

1. `liar_original_six_labels.jsonl`: giữ tất cả phát biểu, nhãn gốc, phép chia gốc, metadata và nguồn gốc từng dòng. Đây là bản nhập để kiểm tra; không phải bản được tuyên bố hết trùng lặp.
2. `liar_binary_strict.jsonl`: tập con hai nhãn theo **quy ước riêng của dự án**: `true → 1 (Real)`, `false` và `pants-fire → 0 (Fake)`. Giữ riêng `mostly-true`, `half-true`, `barely-true`; không suy đoán chúng hoàn toàn đúng hoặc sai.

Không báo điểm trên tập con này như kết quả benchmark LIAR sáu lớp. Việc giữ ba mức cực trị tạo thiên lệch chọn mẫu; báo cáo phải công khai số mẫu bị loại. Mô hình đọc được tiếng Anh không đồng nghĩa sẽ phân loại phát biểu ngắn chính xác.

## Tương thích DATA-01/02

- Quy ước số của luồng Colab/DATA-02: Fake=0, Real=1. Baseline cũ có thể đảo số; đọc metadata mô hình trước khi đánh giá.
- Dùng lại `backend.app.colab_preprocessing.clean_source_markers`, đúng một lần trên văn bản gốc. Bản xuất model-view đã được làm sạch; không làm sạch lần thứ hai.
- Giữ dấu câu/Unicode; không bổ sung nhãn hay kết luận vào nội dung.
- Chỉ `text` là đặc trưng mô hình. Không dùng `label_original`, metadata, tên người nói, đảng, chủ đề, ngữ cảnh, ID, nguồn, hay lịch sử đúng/sai. Lịch sử trong LIAR **bao gồm cả phát biểu hiện tại** nên có nguy cơ rò rỉ nhãn.
- Không áp dụng quy tắc bài dưới 20 từ của DATA-02 vào LIAR: phát biểu ngắn là đơn vị dữ liệu hợp lệ. Giữ riêng `content_type=claim`.
- Giữ nguyên train/validation/test của tác giả ở từng dòng. Khi phát hiện nhóm trùng/gần trùng chồng tập hoặc mâu thuẫn nhãn, cách ly **cả nhóm**, không chuyển test sang train.
- LSH 128 permutations, seed=42, ngưỡng truy hồi 0,70; xác minh Jaccard shingle 5 từ ≥0,85, giống DATA-02. Chuẩn hóa NFKC/casefold/khoảng trắng để bắt trùng chính xác độc lập với LSH.
- So sánh cả nội dung và tiêu đề của snapshot DATA-02 được cung cấp với LIAR; cách ly nhóm LIAR có cặp khớp. DATA-02 không bị chỉnh sửa.
- Những kiểm tra này không chứng minh không còn phát biểu được diễn đạt lại, trích dẫn nằm trong bài dài, hay chung sự kiện. Cần kiểm tra ngữ nghĩa/sự kiện trước thí nghiệm gộp nguồn lớn.

## Trường dữ liệu và dấu vết

Mỗi dòng gốc có `id=liar:<source_id>`, nội dung gốc/sạch, `label_original`, `label_binary` (null với nhãn trung gian), `official_split`, metadata, ngôn ngữ, loại nội dung, file/dòng nguồn và SHA256 ZIP.

`publication_date=null` vì TSV không cung cấp ngày từng phát biểu. Không tạo URL kiểm chứng giả từ ID. API cũ được nhắc trong README gốc chưa được kiểm tra hoạt động và không được coi là bằng chứng đã tải.

`excluded_review.jsonl` có các lý do loại không loại trừ nhau; số lý do có thể lớn hơn số dòng. `near_pairs.jsonl`, `data02_overlap.jsonl` và `split_manifest.jsonl` phục vụ kiểm tra cục bộ. Các bảng này chứa dữ liệu/ID, không tự đưa lên Git.

Hai dòng có 3 cột trong bản tải được giữ lại nếu ID/nhãn/nội dung hợp lệ; phần metadata thiếu để trống và ghi cảnh báo. Nếu ID trùng, nhãn lạ, checksum khác hoặc cấu trúc không hợp lệ thì dừng.

## Thí nghiệm ML tiếp theo

Đợt DATA-03 này chỉ chuẩn bị và kiểm tra dữ liệu, **chưa huấn luyện lại mô hình**.

1. Chốt chính sách nhãn và phiên bản dữ liệu trong báo cáo trước khi xem điểm test.
2. Nếu đo SVM hiện tại: dùng đúng pipeline và mapping nhãn của mô hình đó, đánh giá riêng LIAR. Điểm này là kiểm tra khác nguồn, không thay điểm test cũ.
3. Nếu huấn luyện V2: chỉ dùng train của LIAR và train DATA-02; validation giữ riêng để chọn cấu hình. Vectorizer/tokenizer chỉ fit trên train. Cân nhắc trọng số vì bài báo và phát biểu khác độ dài, chủ đề và nguồn.
4. Báo cáo riêng test DATA-02 và test LIAR đã khóa, cùng Accuracy, macro-F1, support mỗi nhãn, baseline đa số và sai số. Không tối ưu theo test hoặc gộp hai test thành một điểm che khuất sự suy giảm.
5. Lưu mô hình V2 sang tên mới. Chỉ thay mô hình ứng dụng sau khi so sánh và được nhóm chấp nhận. Không cần chạy lại LSTM chỉ để kiểm tra gói dữ liệu.

## Quyền sử dụng và giới hạn

README gốc quy định **dùng cho nghiên cứu**; bản quyền nguồn gốc vẫn thuộc bên cung cấp. Gói dữ liệu cục bộ kèm README nguyên gốc. Gói mã bàn giao không chứa văn bản phát biểu hay mô hình. Không mặc định việc dữ liệu tải được đồng nghĩa có giấy phép triển khai thương mại.

Nhãn thừa hưởng từ dataset, chưa kiểm chứng lại từng phát biểu. Người nói có thể xuất hiện ở nhiều tập; không tuyên bố đánh giá độc lập theo người nói. Chưa kiểm tra dữ liệu tiếng Việt, chưa crawl tin năm 2026, chưa chứng minh Accuracy/F1 tăng.