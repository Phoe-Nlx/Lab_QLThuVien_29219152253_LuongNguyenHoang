# Hệ Thống Quản Lý Thư Viện Ứng Dụng Công Cụ AI (SmartLib AI)

> **BÀI THỰC HÀNH (LAB):** Phân tích, thiết kế và xây dựng hệ thống quản lý thư viện ứng dụng công cụ AI  
> **Công cụ & Môi trường:** Google AI Studio (Gemini 1.5/2.0 Flash), Antigravity IDE, Python 3, SQLite, HTML5/CSS3/JavaScript SPA.

---

## 🌟 Giới Thiệu & Điểm Nổi Bật

Dự án được xây dựng toàn diện từ khâu phân tích bài toán, thiết kế cơ sở dữ liệu đến triển khai ứng dụng thực tế với sự đồng hành của **Google AI Studio** và **Antigravity IDE**:
- **Không cần cài đặt phức tạp (Zero-Dependency):** Máy chủ backend viết bằng thư viện chuẩn của Python (`http.server`, `sqlite3`, `json`), chỉ cần máy tính có sẵn Python 3 là chạy ngay lập tức mà không cần `pip install` bất kỳ thư viện nào!
- **Hỗ trợ chế độ kép (Dual Mode):**
  - Chạy đầy đủ Client - Server với cơ sở dữ liệu SQLite qua `python app.py`.
  - Hoặc có thể mở trực tiếp file `src/static/index.html` trên bất kỳ trình duyệt web nào.
- **Trợ lý AI thông minh tích hợp Google AI Studio (Gemini):**
  - Trợ lý ảo tư vấn tài liệu theo ngữ cảnh danh mục sách thực tế trong kho thư viện.
  - Tự động sinh tóm tắt sách (Book Summarizer) cho thủ thư chỉ với 1 cú click.
  - Tự động chuyển đổi sang Local AI Rule Engine nếu người dùng chưa nhập API Key hoặc khi không có mạng.
- **Quản lý Mượn / Trả & Phạt trễ hạn tự động:** Kiểm tra số lượng sách thực tế còn trên kệ, tự động tính tiền phạt trễ hạn ($5.000\text{ VNĐ/ngày/cuốn}$).

---

## 📁 Cấu Trúc Dự Án

```
Lab_QLThuVien_[MSSV]_[HoTen]/
│
├── BaoCao_Lab.md             # Báo cáo phân tích & thiết kế hoàn chỉnh (Mermaid diagrams, Use case, ERD, Test cases)
├── README.md                 # Tài liệu hướng dẫn sử dụng và khởi chạy
├── start.bat                 # File thực thi 1-click để khởi chạy máy chủ trên Windows
├── package_zip.py            # Script tự động nén thư mục thành file zip nộp bài
│
├── data/
│   └── library.db            # Cơ sở dữ liệu SQLite (chứa sẵn 13 cuốn sách mẫu, 6 độc giả, 4 phiếu mượn)
│
└── src/
    ├── app.py                # Máy chủ REST API Server (Python standard library)
    ├── database.py           # Khởi tạo bảng dữ liệu và nạp dữ liệu mẫu
    ├── ai_service.py         # Module tích hợp Google AI Studio (Gemini API) & Fallback Engine
    │
    └── static/               # Giao diện người dùng Web SPA
        ├── index.html        # Giao diện chính (Dashboard, Sách, Độc giả, Mượn trả, Chat AI, Cài đặt)
        ├── css/
        │   └── style.css     # Tùy biến giao diện hiện đại, Responsive UI
        └── js/
            └── app.js        # Logic điều khiển, gọi API, Chart.js, SweetAlert2
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### Cách 1: Khởi chạy nhanh bằng file thực thi (Khuyên dùng trên Windows)
Chỉ cần nhấp đúp chuột vào file `start.bat` trong thư mục gốc của dự án. Trình duyệt web sẽ tự động mở trang quản lý thư viện tại địa chỉ:
`http://localhost:8080`

### Cách 2: Khởi chạy bằng dòng lệnh Terminal / PowerShell
1. Mở Terminal / PowerShell và chuyển vào thư mục `src`:
   ```bash
   cd src
   ```
2. Khởi chạy máy chủ:
   ```bash
   python app.py
   ```
3. Mở trình duyệt web và truy cập:
   ```
   http://localhost:8080
   ```

---

## 🔑 Hướng Dẫn Kích Hoạt Google AI Studio (Gemini API)

Mặc định hệ thống đã tích hợp sẵn **Bộ máy AI cục bộ (Local Rule Engine)** để bạn có thể trải nghiệm đầy đủ tính năng tra cứu và gợi ý sách ngay cả khi offline.

Nếu muốn trải nghiệm sức mạnh của mô hình ngôn ngữ lớn **Gemini 1.5 Flash**:
1. Truy cập [https://aistudio.google.com/](https://aistudio.google.com/) và đăng nhập bằng tài khoản Google.
2. Chọn **"Get API key"** -> **"Create API key"** để lấy mã khóa miễn phí.
3. Mở giao diện ứng dụng thư viện -> Chọn tab **"Cài Đặt"** trên thanh Menu -> Dán API Key vào và nhấn **"Lưu API Key"**.
4. Trợ lý AI sẽ chuyển sang nguồn **"Google AI Studio (Gemini 1.5 Flash)"** ngay lập tức!

---

## 📦 Hướng Dẫn Đóng Gói Sản Phẩm Nộp Bài

Theo yêu cầu của đề bài thực hành, sinh viên cần nộp file nén định dạng `[MSSV]_[HoTen]_LabQLThuVien.zip`.

Dự án đã tích hợp sẵn script tự động:
1. Chạy lệnh:
   ```bash
   python package_zip.py --mssv "20240001" --hoten "NguyenVanA"
   ```
   *(Thay thế `"20240001"` và `"NguyenVanA"` bằng MSSV và Họ tên thực tế của bạn)*
2. File zip hoàn chỉnh sẽ được tạo ra ngay trong thư mục:
   `20240001_NguyenVanA_LabQLThuVien.zip`

---

## 👥 Nhóm Tác Giả & Bản Quyền
- **Học phần:** Phát triển Ứng dụng & Kỹ nghệ Phần mềm với Công cụ AI
- **Công cụ hỗ trợ:** Antigravity IDE & Google AI Studio
