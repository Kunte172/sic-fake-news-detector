# Quy trình làm việc nhóm

## Nhánh và PR

- `main`: bản tích hợp, luôn chạy được. Không push trực tiếp sau khi bật branch protection.
- Tên nhánh: `feat/<issue>-<mota>`, `fix/<issue>-<mota>`, `docs/<issue>-<mota>`.
- Mỗi issue có một người chịu trách nhiệm, tiêu chí nghiệm thu và các file dự kiến sửa.
- PR nhỏ, liên kết issue, nêu cách chạy thử và ảnh giao diện nếu có. Một thành viên khác review trước khi merge.
- Cập nhật nhánh từ `main` trước khi merge. Nếu có xung đột, người mở PR giải quyết và chạy lại kiểm tra.
- Khi thay đổi request/response API, sửa `docs/API_CONTRACT.md` trong cùng PR và báo nhóm frontend/backend.
- Khi thay đổi cách tiền xử lý, sửa `backend/app/preprocessing.py`, chương trình huấn luyện, và thêm test để bảo đảm train/inference giống nhau.

## Lệnh thường dùng

```bash
git switch main
git pull origin main
git switch -c feat/12-lstm
git add <cac-file-da-sua>
git commit -m "feat(ml): add LSTM comparison"
git push -u origin feat/12-lstm
```

Trên GitHub, bật branch protection cho `main`: yêu cầu PR, ít nhất một review và CI thành công; chặn force push. Có thể dùng Issues hoặc Project board với các cột `Backlog`, `In progress`, `Review`, `Done`.

## Quy tắc tránh xung đột

- Nhóm ML sở hữu notebook/huấn luyện; backend sở hữu API và DB; frontend sở hữu giao diện. Tài liệu và hợp đồng API được sửa qua PR.
- Không lưu dữ liệu Kaggle, model nặng, credential hay dữ liệu người dùng trong Git. Lưu hướng dẫn lấy dữ liệu và checksum/phiên bản artifact khi phát hành.
- Mỗi PR chạy: `python -m unittest discover -s backend/tests`, `python -m compileall -q backend ml`, và `npm run build` trong `frontend`.
