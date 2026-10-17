# Kết quả EDA văn bản (DATA-01)

Nguồn: [Fake and Real News Dataset](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset), hai file `Fake.csv` và `True.csv`. Kết quả dưới đây được đọc từ các bảng mà người phụ trách chạy bằng [notebook EDA](../ml/notebooks/01_eda.ipynb) trên dữ liệu thật ngày 16/10/2026. Notebook phân tích **văn bản thô** và không loại bài trùng trước khi đếm. CSV, nguyên văn bài báo và output notebook không được đưa vào Git.

## Quy mô và độ dài

| Nhãn trong dataset | Số bài | Trung vị số từ nội dung |
| --- | ---: | ---: |
| FAKE | 23.481 | 375 |
| REAL | 21.417 | 367 |
| Tổng | 44.898 | — |

Trung vị độ dài nội dung gần nhau (chênh 8 từ). Không thể dùng riêng độ dài để kết luận về độ tin cậy của một bài. Notebook có biểu đồ phân phối số từ trong tiêu đề và nội dung; phần hiển thị giới hạn trục ở bách phân vị 99, còn bảng thống kê dùng toàn bộ bài.

## `subject` là dấu hiệu rò rỉ nhãn

| subject | FAKE | REAL |
| --- | ---: | ---: |
| News | 9.050 | 0 |
| politics | 6.841 | 0 |
| left-news | 4.459 | 0 |
| Government News | 1.570 | 0 |
| US_News | 783 | 0 |
| Middle-east | 778 | 0 |
| politicsNews | 0 | 11.272 |
| worldnews | 0 | 10.145 |

Cả **8/8** giá trị `subject` chỉ thuộc một nhãn, bao phủ **100%** số bài. Đây là sự khác biệt trong cách gắn nhãn/thu thập dữ liệu; mô hình dùng cột này có thể suy ra nhãn mà không cần đọc nội dung. Không đưa `subject` gốc vào đặc trưng mô hình hoặc dùng trực tiếp làm nhóm đánh giá chéo theo chủ đề. Issue [#4](https://github.com/Kunte172/sic-fake-news-detector/issues/4) cần định nghĩa nhóm chủ đề chung từ nội dung và kiểm tra mỗi nhóm có cả hai nhãn.

## Từ vựng và dấu nguồn

Notebook so sánh **tỷ lệ bài chứa từ**, không so tần suất lặp lại của từ trong bài.

| Từ | FAKE | REAL | Diễn giải cần kiểm tra |
| --- | ---: | ---: | --- |
| `video` | 44,1% | 2,9% | Có thể liên quan định dạng nội dung |
| `image` | 38,4% | 1,4% | Có thể là thành phần của trang/bài |
| `featured` | 34,5% | 0,4% | Có thể là dấu template |
| `getty` | 17,3% | 0,0% | Có thể là credit ảnh |
| `reuters` | 1,3% | 99,8% | Tên hãng tin gắn rất mạnh với nhãn REAL |
| `said` | 54,6% | 93,7% | Có thể phản ánh phong cách dẫn nguồn |

Regex dò `(Reuters) -` trong **220 ký tự đầu nội dung** thấy 0/23.481 bài FAKE và 21.241/21.417 bài REAL (**99,2%**). Dò từ `Reuters` nói chung trong đoạn đầu thấy 26 bài FAKE (**0,1%**) và 21.353 bài REAL (**99,7%**). Regex có thể bỏ sót hoặc nhận nhầm; những tỷ lệ này đủ cho thấy khả năng mô hình học nguồn/định dạng mở đầu. Các từ `video`, `image`, `featured`, `getty` cũng cần rà xem là nội dung bài hay phần trang web bị đưa vào CSV.

## Phong cách viết

| Chỉ số | Trung vị FAKE | Trung vị REAL |
| --- | ---: | ---: |
| Từ trên câu (ước lượng) | 18,222 | 18,314 |
| Ký tự dấu câu trên 1.000 ký tự | 21,397 | 24,373 |
| `!` hoặc `?` trên 1.000 ký tự | 0,435 | 0,000 |
| Tỷ lệ chữ hoa trên chữ cái Latin | 0,046 | 0,047 |

Các số đo bề mặt này khác nhau ở một số chỉ số, nhưng còn chịu ảnh hưởng của nguồn, chủ đề và cách tách câu. Chúng chỉ mô tả tập dữ liệu này; không phải quy tắc nhận biết tin giả nói chung.

## Kết luận và chuyển giao

1. Ưu tiên [DATA-02](https://github.com/Kunte172/sic-fake-news-detector/issues/2): kiểm toán Reuters/dateline, tên nguồn, dấu template, bài trùng và gần trùng; đo lại tỷ lệ trước/sau làm sạch. Lưu ý việc bỏ đúng chuỗi `(Reuters) -` chưa chứng minh đã hết dấu nguồn ở phần còn lại.
2. So sánh baseline trước/sau làm sạch trên **cùng phép chia dữ liệu** và kiểm tra các từ trọng số lớn của mô hình. Vectorizer EDA fit trên toàn bộ dữ liệu chỉ để mô tả; không tái sử dụng nó trong thí nghiệm huấn luyện.
3. Ghi rõ giới hạn khi báo cáo: đây là bài báo tiếng Anh trong bộ dữ liệu có sai lệch nguồn rõ rệt; chưa có bằng chứng hiệu quả trên bài mạng xã hội hoặc tiếng Việt. Điểm phân loại không xác minh sự thật của sự kiện.

Các ảnh chụp được chia sẻ trong quá trình review cho biết các số liệu trên; chưa có số đếm bài rỗng, trùng chính xác hoặc trung bình độ dài trong các ảnh, dù notebook có tính những chỉ số đó. Người chạy có thể lấy thêm khi viết báo cáo đầy đủ. Không suy diễn các chỉ số chưa được ghi nhận.
