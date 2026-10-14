# Giao việc bằng GitHub Issues

Repository: https://github.com/Kunte172/sic-fake-news-detector

Issue là **một đầu việc có kết quả và tiêu chí nghiệm thu rõ ràng**. Người được giao chịu trách nhiệm cập nhật tiến độ, mở pull request (PR) và trả lời review. Một PR có thể được hỗ trợ bởi nhiều người, nhưng nên có một người chịu trách nhiệm chính cho mỗi issue.

## 1. Nhận các đầu việc đã tạo sẵn

Nhóm đã có **13 issue** tương ứng [bảng công việc](TASK_BOARD.md). Mở [danh sách Issues](https://github.com/Kunte172/sic-fake-news-detector/issues) và tìm theo mã; **đừng tạo bản sao** của những đầu việc này.

| Giai đoạn gợi ý | Issue | Có thể bắt đầu khi |
| --- | --- | --- |
| Khảo sát dữ liệu | [#1 DATA-01 — EDA](https://github.com/Kunte172/sic-fake-news-detector/issues/1) | Có dữ liệu CSV ở máy cá nhân |
| Kiểm toán dữ liệu | [#2 DATA-02 — rò rỉ và trùng](https://github.com/Kunte172/sic-fake-news-detector/issues/2) | Có kết luận EDA; có thể khảo sát song song |
| Thử nghiệm mô hình | [#3 ML-01 — NB/SVM](https://github.com/Kunte172/sic-fake-news-detector/issues/3), [#4 ML-02 — theo chủ đề](https://github.com/Kunte172/sic-fake-news-detector/issues/4), [#5 ML-03 — LSTM](https://github.com/Kunte172/sic-fake-news-detector/issues/5), [#6 ML-04 — giải thích](https://github.com/Kunte172/sic-fake-news-detector/issues/6) | Theo phụ thuộc ghi trong từng issue |
| API | [#7 API-01 — tài khoản](https://github.com/Kunte172/sic-fake-news-detector/issues/7), [#8 API-02 — lịch sử](https://github.com/Kunte172/sic-fake-news-detector/issues/8), [#9 API-03 — URL](https://github.com/Kunte172/sic-fake-news-detector/issues/9) | Thống nhất API contract trước khi làm UI phụ thuộc |
| Giao diện | [#10 UI-01 — người dùng](https://github.com/Kunte172/sic-fake-news-detector/issues/10), [#11 UI-02 — quản trị](https://github.com/Kunte172/sic-fake-news-detector/issues/11) | API liên quan đã thống nhất |
| Hoàn thiện | [#12 OPS-01 — cloud](https://github.com/Kunte172/sic-fake-news-detector/issues/12), [#13 DOC-01 — báo cáo](https://github.com/Kunte172/sic-fake-news-detector/issues/13) | Có kết quả để tích hợp; báo cáo có thể viết dần |

### Trưởng nhóm giao một issue có sẵn

1. Mở issue từ bảng trên; đọc **Mục tiêu**, **Hoàn thành khi** và phần phụ thuộc.
2. Ở cột bên phải, bấm **Assignees** → tìm tên GitHub của thành viên → chọn. Nếu không tìm thấy, kiểm tra thành viên đã được mời vào repository hoặc đã bình luận vào issue. Việc chỉ định người khác cần quyền phù hợp trên repository.
3. Bình luận phạm vi đợt này, người phối hợp, thời hạn nhóm thống nhất và link issue phụ thuộc, ví dụ `Blocked by #2`. Không ghi thời hạn chỉ trong tin nhắn riêng.
4. Có thể thêm issue vào GitHub Project với trạng thái `Backlog`, `In progress`, `Review`, `Done`. Project là tùy chọn; **Assignees + issue + PR** đã đủ để bắt đầu.

### Thành viên nhận việc

1. Bình luận `Mình nhận #1; dự kiến nộp notebook, biểu đồ và hướng dẫn chạy lại.`
2. Kiểm tra phụ thuộc và hỏi ngay trong issue nếu tiêu chí chưa rõ. Không đưa nguyên văn bài báo, dữ liệu CSV hay token vào bình luận.
3. Khi bắt đầu, cập nhật Project sang `In progress` (nếu có) hoặc bình luận tiến độ. Khi vướng, bình luận lý do và gắn issue liên quan bằng `#số`.

## 2. Tạo issue mới khi phát sinh việc

1. Trước hết tìm trong [Issues](https://github.com/Kunte172/sic-fake-news-detector/issues) bằng từ khóa hoặc mã để tránh trùng.
2. Bấm **New issue** → chọn mẫu **Tính năng / nghiên cứu**; với lỗi có thể tái hiện, chọn **Báo lỗi**.
3. Đặt tiêu đề ngắn theo dạng `[DATA-03] Tên kết quả cần làm`, `[ML-05] ...`, `[API-04] ...`, `[UI-03] ...`, `[OPS-02] ...`, hoặc `[DOC-02] ...`. Tăng số tiếp theo của đúng nhóm việc; mã trong tiêu đề khác số issue GitHub (`#14`, `#15`, ...).
4. Điền **Mục tiêu**, **Tiêu chí nghiệm thu** dưới dạng checklist, **File dự kiến sửa và phụ thuộc**. Nêu cách kiểm tra có thể lặp lại, không chỉ ghi “làm xong”.
5. Gán **Assignees** cho người chịu trách nhiệm; để trống khi chưa thống nhất. Bấm **Submit new issue**, rồi gửi link issue cho nhóm.

Ví dụ cho việc mới:

```md
Tiêu đề: [DATA-03] Báo cáo tỷ lệ bài gần trùng theo nhãn

Mục tiêu: Đo mức gần trùng để thiết kế cách chia train/test an toàn hơn.

Tiêu chí nghiệm thu:
- [ ] Có định nghĩa độ tương đồng, ngưỡng và số lượng cặp bài theo nhãn.
- [ ] Có bảng số liệu trước/sau và hướng dẫn chạy lại.
- [ ] Không đưa CSV hay nguyên văn bài báo vào Git.

File dự kiến sửa và phụ thuộc: ml/notebooks/; phụ thuộc #2.
```

Nếu đầu việc quá lớn, chia thành các issue có thể review riêng; liên kết chúng bằng `#số`. Với một thay đổi nhỏ trong phạm vi issue hiện có, bổ sung checklist hoặc bình luận vào issue đó.

## 3. Từ issue đến branch, PR và hoàn thành

Tại terminal ở thư mục gốc repo, ví dụ với issue `#1`:

```bash
git switch main
git pull origin main
git switch -c feat/1-eda
# Sửa code hoặc notebook, chạy kiểm tra liên quan
git add <cac-file-can-commit>
git commit -m "feat(data): add text EDA notebook"
git push -u origin feat/1-eda
```

Mở **Pull requests → New pull request**, chọn nhánh vừa push và điền mẫu PR. Thay `Closes #` bằng **`Closes #1`** trong phần mô tả; GitHub sẽ liên kết và đóng issue khi PR được merge vào nhánh mặc định. Ghi cách chạy thử, kết quả, ảnh giao diện nếu có, giới hạn và các file tài liệu cần cập nhật. Nhờ một thành viên khác review, sửa góp ý, chờ CI thành công rồi merge theo [quy trình cộng tác](COLLABORATION.md).

Sau khi merge, kiểm tra issue đã đóng và Project (nếu dùng) đã ở `Done`. Nếu PR chỉ giải quyết một phần, dùng `Refs #1` thay cho `Closes #1` và giữ issue mở; mô tả rõ phần còn lại trong checklist.

## Quy tắc chung

- Một issue có kết quả kiểm chứng được, một người chịu trách nhiệm chính, phụ thuộc rõ ràng.
- Cập nhật tiến độ trong issue để mọi thành viên nhìn thấy cùng một thông tin.
- Notebook phù hợp với EDA và thí nghiệm; phần huấn luyện/chạy API ổn định chuyển sang file `.py` để chạy lại được.
- Không commit `Fake.csv`, `True.csv`, model artifact, `.env`, thông tin đăng nhập hay dữ liệu người dùng.
