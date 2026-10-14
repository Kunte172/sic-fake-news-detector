# Đưa repository lên GitHub

Repository của nhóm: https://github.com/Kunte172/sic-fake-news-detector. Đây là đích chính thức để push và mở pull request.

Nếu đã tải bản ZIP và giải nén, mở terminal ở thư mục `sic-fake-news`:

```bash
git init -b main
git add .
git commit -m "chore: scaffold SIC fake news group project"
git remote add origin https://github.com/Kunte172/sic-fake-news-detector.git
git push -u origin main
```

Nếu clone repository từ GitHub, không chạy lại các lệnh khởi tạo; tạo nhánh theo `docs/COLLABORATION.md`. Nếu đang làm trong repository Git có sẵn, bỏ ba lệnh `git init`, `git add`, `git commit`; kiểm tra `git status` và remote trước khi push.

Sau khi push: mời các thành viên có quyền phù hợp; tạo Issues từ `docs/TASK_BOARD.md`; bật branch protection cho `main` với PR, một review và CI; mỗi người nhận một issue trước khi mở nhánh. Giữ CSV, mô hình và `.env` ngoài Git.
