# Kế hoạch phát triển – Trang thông tin Đội 3 (A320/321)

## Tổng quan
Xây dựng trang thông tin nội bộ cho Đội Bảo dưỡng Số 3, chuyên dòng máy bay Airbus A320/321.
Dữ liệu Hot Spots lấy từ Google Sheets + ảnh từ Google Drive.
Phát triển theo từng giai đoạn (phase), mỗi phase có thể hoàn thành độc lập.

---

## Phase 1 – Rebranding + Skeleton Hot Spots (Google Sheets) ✅ ĐANG LÀM
**Mục tiêu:** Website chạy được, mang nhận diện Đội 3, trang Hot Spots có cấu trúc đúng nhưng
chưa cần kết nối Google thật.

### Công việc:
- [x] Đổi tất cả "đội 1" → "Đội 3" trong toàn bộ template
- [x] Đổi tất cả "B787" / "Boeing" → "A320/321" / "Airbus"
- [x] Thay đổi màu chủ đạo (accent color) để phân biệt với website gốc
- [x] Cập nhật `main.py`:
  - Route `/hotspot` trả về dữ liệu từ Google Sheets (fallback mock data khi chưa cấu hình)
  - Route `/api/hotspot-data` (JSON) để frontend có thể gọi
  - Route `/proxy-drive-image` để phục vụ ảnh từ Google Drive qua backend
- [x] Redesign `hotspot.html`: render card động từ dữ liệu JSON thay vì hardcode HTML
- [x] Cập nhật trang Tools → nội dung A320/321 (giữ cấu trúc bảng)
- [x] Cập nhật Rules, Memories, Index với tên Đội 3
- [x] Tạo file `planning.md`

### Kết quả mong đợi:
Website chạy, trang Hot Spots hiển thị dữ liệu mẫu (mock), sẵn sàng kết nối Google ở Phase 2.

---

## Phase 2 – Kết nối Google Sheets + Google Drive thật
**Mục tiêu:** Hot Spots đọc dữ liệu thật từ Google Sheets, ảnh thật từ Google Drive.

### Công việc:
- [ ] Tạo Google Service Account, tải file credentials JSON
- [ ] Lưu credentials vào Replit Secrets (biến môi trường)
- [ ] Cấu hình: `GOOGLE_SHEET_ID`, `GOOGLE_DRIVE_FOLDER_ID` trong Secrets
- [ ] Backend `fetch_hotspot_from_sheets()`:
  - Kết nối Google Sheets API, đọc 4 cột: NỘI DUNG, ĐÚNG, SAI, ZONE
  - Cache kết quả 5 phút để tránh quá nhiều API call
- [ ] Backend `get_drive_image_url(filename)`:
  - Tìm file theo tên trong Google Drive folder
  - Trả về link xem ảnh trực tiếp (hoặc proxy qua server)
- [ ] Test với dữ liệu thật từ sheet
- [ ] Xử lý lỗi khi Sheet trống, ảnh không tìm thấy

### Yêu cầu từ người dùng trước khi bắt đầu:
- Cung cấp Google Sheet ID (lấy từ URL của sheet)
- Cung cấp Google Drive Folder ID (chứa ảnh ĐÚNG/SAI)
- Chia sẻ Sheet và Folder cho Service Account email

---

## Phase 3 – Nội dung trang Tools (A320/321)
**Mục tiêu:** Thay thế toàn bộ danh sách tool B787 bằng tool thực tế cho A320/321.

### Công việc:
- [ ] Thu thập danh sách tool lẻ tàu A320/321 từ đội
- [ ] Cập nhật bảng "Danh mục tool lẻ" trong `a320_tools.html`
- [ ] Thêm bảng "Danh mục tool thay động cơ A320/321" (nếu có)
- [ ] Cân nhắc: có cần lấy từ Google Sheets không? (giống Hot Spots)

---

## Phase 4 – Quy định & Album Đội 3
**Mục tiêu:** Cập nhật nội dung quy định và album ảnh phù hợp Đội 3.

### Công việc:
- [ ] Cập nhật nội dung các quy định trong `rules.html` cho Đội 3
  - Quy định mượn/trả tool (giữ nguyên nếu giống đội 1)
  - Bổ sung quy định đặc thù A320/321 (nếu có)
- [ ] Cập nhật thông tin liên hệ trong `index.html` (section Liên hệ)
  - Tên, số điện thoại leader Đội 3
- [ ] Album ảnh: upload ảnh đội 3 lên hệ thống
- [ ] (Tùy chọn) Đổi ảnh bìa trong trang chủ (`pic01.jpg`, `pic02.jpg`, `pic03.jpg`, `squad1.jpg`)

---

## Phase 5 – Tối ưu & Hoàn thiện
**Mục tiêu:** Trau chuốt giao diện, cải thiện trải nghiệm người dùng.

### Công việc:
- [ ] Responsive mobile: kiểm tra và cải thiện hiển thị trên điện thoại
- [ ] Loading state cho trang Hot Spots (hiển thị spinner khi chờ Google Sheets)
- [ ] Bộ lọc Hot Spots: lọc theo Zone (dữ liệu động từ sheet)
- [ ] (Tùy chọn) Thêm tính năng tìm kiếm trong trang Rules
- [ ] (Tùy chọn) Trang Hot Spots: thêm cột hiển thị ngày cập nhật từ sheet
- [ ] Deploy lên production (Replit Deployments)
- [ ] Đặt custom domain (nếu cần)

---

## Ghi chú kỹ thuật

### Cấu trúc Google Sheet (4 cột bắt buộc):
| NỘI DUNG CẦN CHÚ Ý KIỂM TRA | ĐÚNG | SAI | ZONE |
|-------------------------------|------|-----|------|
| Kiểm tra... | ten_anh_dung.jpg | ten_anh_sai.jpg | 100 |

- Cột **ĐÚNG**: tên file ảnh "Good Condition" trong Google Drive folder
- Cột **SAI**: tên file ảnh "Defect Condition" trong Google Drive folder
- Cột **ZONE**: mã zone (dùng để lọc)

### Biến môi trường cần thiết (Phase 2):
```
GOOGLE_CREDENTIALS_JSON  → nội dung file service account JSON
GOOGLE_SHEET_ID          → ID của Google Sheet
GOOGLE_DRIVE_FOLDER_ID   → ID của folder chứa ảnh
```

### Stack:
- Backend: Python Flask
- Frontend: HTML/CSS/JS (Jinja2 template)
- Data: Google Sheets API v4
- Images: Google Drive API v3
- Hosting: Replit (dev) → Replit Deployments (prod)
