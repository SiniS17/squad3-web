# Kế hoạch phát triển – Trang thông tin Đội 3 (A320/321)

## Tổng quan
Xây dựng trang thông tin nội bộ cho Đội Bảo dưỡng Số 3, chuyên dòng máy bay Airbus A320/321.
Dữ liệu Hot Spots lấy từ Google Sheets + ảnh từ Google Drive.
Phát triển theo từng giai đoạn (phase), mỗi phase có thể hoàn thành độc lập.

---

## Phase 1 – Rebranding + Skeleton Hot Spots (Google Sheets) ✅ HOÀN THÀNH

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

---

## Phase 2 – Kết nối Google Sheets + Google Drive thật ✅ HOÀN THÀNH

### Công việc:
- [x] Tạo Google Service Account, tải file credentials JSON
- [x] Lưu credentials vào Replit Secrets (biến môi trường)
- [x] Cấu hình: `GOOGLE_SHEET_ID`, `GOOGLE_DRIVE_FOLDER_ID` trong Secrets
- [x] Backend `fetch_hotspot_from_sheets()`:
  - Kết nối Google Sheets API, đọc 4 cột: NỘI DUNG, ĐÚNG, SAI, ZONE
  - Cache kết quả 5 phút để tránh quá nhiều API call
- [x] Backend `get_drive_image_url(filename)`:
  - Tìm file theo tên trong Google Drive folder
  - Trả về link xem ảnh trực tiếp (hoặc proxy qua server)
- [x] Test với dữ liệu thật từ sheet
- [x] Xử lý lỗi khi Sheet trống, ảnh không tìm thấy

---

## Phase 3 – Nội dung trang Tools (A320/321) ✅ HOÀN THÀNH

### Công việc:
- [x] Thu thập danh sách tool lẻ tàu A320/321 từ đội
- [x] Trang Tools kết nối Google Sheets (tab "Tool chuẩn bị"), đọc cột A–F (task, part_number, tool, so_luong, engine, zone)
- [x] Giao diện lọc nâng cao: tìm kiếm task có autocomplete, bộ lọc engine/zone qua panel riêng
- [x] Card hiển thị tag engine và zone, bố cục 2 cột desktop
- [x] "Google Sheets ↗" là link bấm được dẫn đến sheet thật

---

## Phase 4 – Quy định & Album Đội 3

### Công việc:
- [ ] Cập nhật nội dung các quy định trong `rules.html` cho Đội 3
  - Quy định mượn/trả tool (giữ nguyên nếu giống đội 1)
  - Bổ sung quy định đặc thù A320/321 (nếu có)
- [ ] Cập nhật thông tin liên hệ trong `index.html` (section Liên hệ)
  - Tên, số điện thoại leader Đội 3
- [ ] Album ảnh: upload ảnh đội 3 lên hệ thống
- [ ] (Tùy chọn) Đổi ảnh bìa trong trang chủ (`pic01.jpg`, `pic02.jpg`, `pic03.jpg`, `squad1.jpg`)

---

## Phase 5 – Tính năng mới

### Công việc:
- [x] Trang "Các link thông dụng" (`/links`) – lấy dữ liệu từ tab "Links" (cột Tên, Link)
- [ ] Responsive mobile: kiểm tra và cải thiện hiển thị trên điện thoại
- [ ] Loading state cho trang Hot Spots (hiển thị spinner khi chờ Google Sheets)
- [ ] (Tùy chọn) Trang Hot Spots: thêm cột hiển thị ngày cập nhật từ sheet
- [ ] Deploy lên production (Replit Deployments)
- [ ] Đặt custom domain (nếu cần)

---

## Ghi chú kỹ thuật

### Cấu trúc Google Sheet (4 cột bắt buộc – tab Hotspot):
| NỘI DUNG CẦN CHÚ Ý KIỂM TRA | ĐÚNG | SAI | ZONE |
|-------------------------------|------|-----|------|
| Kiểm tra... | ten_anh_dung.jpg | ten_anh_sai.jpg | 100 |

- Cột **ĐÚNG**: tên file ảnh "Good Condition" trong Google Drive folder
- Cột **SAI**: tên file ảnh "Defect Condition" trong Google Drive folder
- Cột **ZONE**: mã zone (dùng để lọc)

### Cấu trúc Google Sheet – tab "Tool chuẩn bị" (6 cột):
| task | part_number | tool | so_luong | engine | zone |

### Cấu trúc Google Sheet – tab "Links" (2 cột):
| Tên | Link |

### Biến môi trường cần thiết:
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
