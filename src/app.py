"""
Hệ thống Quản lý Thư viện Ứng dụng AI (Library Management System with AI)
Tác giả: Nhóm Thực hành Lab AI / Google AI Studio & Antigravity IDE
Môi trường: Python 3 Standard Library (Zero-Dependency) + SQLite3 + Gemini AI API
"""

import os
import sys
import json
import sqlite3
import mimetypes
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import local modules
from database import get_connection, init_db, seed_sample_data, DEFAULT_DB_PATH
from ai_service import LibraryAIService

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ai_service = LibraryAIService(db_path=DEFAULT_DB_PATH)

class LibraryAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length).decode("utf-8")
                return json.loads(raw_data)
        except Exception as e:
            print("Lỗi parse JSON:", e)
        return {}

    def _send_json(self, data, status=200):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error(self, message, status=400):
        self._send_json({"success": False, "error": message}, status)

    def log_action(self, action, details):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO system_logs (action, details) VALUES (?, ?)", (action, details))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Lỗi ghi log:", e)

    # ==========================
    # GET REQUESTS ROUTING
    # ==========================
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. API: Thống kê tổng quan
        if path == "/api/stats":
            conn = get_connection()
            c = conn.cursor()

            # Thống kê sách
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_copies), 0), COALESCE(SUM(available_copies), 0) FROM books")
            books_row = c.fetchone()
            total_titles = books_row[0]
            total_copies = books_row[1]
            available_copies = books_row[2]
            borrowed_copies = total_copies - available_copies

            # Thống kê độc giả
            c.execute("SELECT COUNT(*) FROM readers")
            total_readers = c.fetchone()[0]

            # Thống kê phiếu mượn
            c.execute("SELECT COUNT(*) FROM borrow_records WHERE status = 'BORROWING'")
            active_borrows = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM borrow_records WHERE status = 'OVERDUE' OR (status = 'BORROWING' AND due_date < date('now'))")
            overdue_borrows = c.fetchone()[0]

            # Thống kê sách theo thể loại
            c.execute("""
                SELECT c.name, COUNT(b.id) as book_count 
                FROM categories c 
                LEFT JOIN books b ON c.id = b.category_id 
                GROUP BY c.id
            """)
            category_stats = [{"category": row["name"], "count": row["book_count"]} for row in c.fetchall()]

            # 5 hoạt động gần nhất
            c.execute("SELECT id, action, details, created_at FROM system_logs ORDER BY id DESC LIMIT 6")
            recent_logs = [dict(row) for row in c.fetchall()]

            conn.close()
            return self._send_json({
                "success": True,
                "data": {
                    "total_titles": total_titles,
                    "total_copies": total_copies,
                    "available_copies": available_copies,
                    "borrowed_copies": borrowed_copies,
                    "total_readers": total_readers,
                    "active_borrows": active_borrows,
                    "overdue_borrows": overdue_borrows,
                    "category_stats": category_stats,
                    "recent_logs": recent_logs
                }
            })

        # 2. API: Danh mục Thể loại
        if path == "/api/categories":
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM categories ORDER BY id ASC")
            categories = [dict(row) for row in c.fetchall()]
            conn.close()
            return self._send_json({"success": True, "data": categories})

        # 3. API: Danh sách Sách (kèm tìm kiếm và lọc)
        if path == "/api/books":
            conn = get_connection()
            c = conn.cursor()
            q = query.get("q", [""])[0].strip()
            cat_id = query.get("category_id", [""])[0].strip()

            sql = """
                SELECT b.*, c.name as category_name 
                FROM books b 
                LEFT JOIN categories c ON b.category_id = c.id 
                WHERE 1=1
            """
            params = []
            if q:
                sql += " AND (b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)"
                kw = f"%{q}%"
                params.extend([kw, kw, kw])
            if cat_id:
                sql += " AND b.category_id = ?"
                params.append(cat_id)

            sql += " ORDER BY b.id DESC"
            c.execute(sql, params)
            books = [dict(row) for row in c.fetchall()]
            conn.close()
            return self._send_json({"success": True, "data": books})

        # 4. API: Chi tiết 1 cuốn sách
        if path.startswith("/api/books/"):
            book_id = path.split("/")[-1]
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                SELECT b.*, c.name as category_name 
                FROM books b 
                LEFT JOIN categories c ON b.category_id = c.id 
                WHERE b.id = ?
            """, (book_id,))
            row = c.fetchone()
            conn.close()
            if row:
                return self._send_json({"success": True, "data": dict(row)})
            return self._send_error("Không tìm thấy sách", 404)

        # 5. API: Danh sách Độc giả
        if path == "/api/readers":
            conn = get_connection()
            c = conn.cursor()
            q = query.get("q", [""])[0].strip()
            sql = "SELECT * FROM readers WHERE 1=1"
            params = []
            if q:
                sql += " AND (full_name LIKE ? OR card_number LIKE ? OR phone LIKE ? OR email LIKE ?)"
                kw = f"%{q}%"
                params.extend([kw, kw, kw, kw])
            sql += " ORDER BY id DESC"
            c.execute(sql, params)
            readers = [dict(row) for row in c.fetchall()]
            conn.close()
            return self._send_json({"success": True, "data": readers})

        # 6. API: Danh sách Phiếu mượn
        if path == "/api/borrows":
            conn = get_connection()
            c = conn.cursor()
            status_filter = query.get("status", [""])[0].strip()
            sql = """
                SELECT br.id, br.record_code, br.reader_id, br.borrow_date, br.due_date, br.status, br.notes, br.created_at,
                       r.card_number, r.full_name as reader_name, r.phone as reader_phone, r.reader_type
                FROM borrow_records br
                JOIN readers r ON br.reader_id = r.id
                WHERE 1=1
            """
            params = []
            if status_filter:
                sql += " AND br.status = ?"
                params.append(status_filter)
            sql += " ORDER BY br.id DESC"
            c.execute(sql, params)
            records = [dict(row) for row in c.fetchall()]

            today_str = datetime.now().date().isoformat()
            # Lấy chi tiết các sách được mượn trong từng phiếu
            for rec in records:
                c.execute("""
                    SELECT bd.id, bd.book_id, bd.return_date, bd.status, bd.fine_amount, bd.notes,
                           b.title as book_title, b.isbn, b.location
                    FROM borrow_details bd
                    JOIN books b ON bd.book_id = b.id
                    WHERE bd.record_id = ?
                """, (rec["id"],))
                rec["books"] = [dict(r) for r in c.fetchall()]

                # Tự động tính trạng thái quá hạn
                if rec["status"] == "BORROWING" and rec["due_date"] < today_str:
                    rec["is_overdue"] = True
                    days_over = (datetime.now().date() - datetime.fromisoformat(rec["due_date"]).date()).days
                    rec["days_overdue"] = days_over
                    rec["estimated_fine"] = days_over * 5000 * len(rec["books"])
                else:
                    rec["is_overdue"] = False
                    rec["days_overdue"] = 0
                    rec["estimated_fine"] = 0

            conn.close()
            return self._send_json({"success": True, "data": records})

        # 7. API: Lịch sử logs
        if path == "/api/logs":
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 50")
            logs = [dict(r) for r in c.fetchall()]
            conn.close()
            return self._send_json({"success": True, "data": logs})

        # Static Files Serving
        return self._serve_static_file(path)

    # ==========================
    # POST / PUT / DELETE ROUTING
    # ==========================
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 1. API: Thêm sách mới
        if path == "/api/books":
            isbn = body.get("isbn", "").strip()
            title = body.get("title", "").strip()
            author = body.get("author", "").strip()
            cat_id = body.get("category_id")
            pub_year = body.get("publish_year") or 2024
            publisher = body.get("publisher", "").strip()
            copies = int(body.get("total_copies") or 1)
            location = body.get("location", "").strip()
            summary = body.get("summary", "").strip()

            if not title or not author:
                return self._send_error("Tiêu đề và Tác giả không được để trống!")

            if not isbn:
                isbn = f"ISBN-{int(datetime.now().timestamp())}"

            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO books (isbn, title, author, category_id, publish_year, publisher, total_copies, available_copies, location, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (isbn, title, author, cat_id, pub_year, publisher, copies, copies, location, summary))
                new_id = c.lastrowid
                conn.commit()
                self.log_action("THÊM SÁCH", f"Thêm sách mới: '{title}' (Mã ISBN: {isbn})")
                conn.close()
                return self._send_json({"success": True, "id": new_id, "message": "Thêm sách thành công!"})
            except sqlite3.IntegrityError:
                conn.close()
                return self._send_error("Mã ISBN đã tồn tại trong hệ thống!")
            except Exception as e:
                conn.close()
                return self._send_error(str(e))

        # 2. API: Thêm độc giả mới
        if path == "/api/readers":
            card_number = body.get("card_number", "").strip()
            full_name = body.get("full_name", "").strip()
            email = body.get("email", "").strip()
            phone = body.get("phone", "").strip()
            gender = body.get("gender", "Nam")
            dob = body.get("dob", "")
            address = body.get("address", "").strip()
            reader_type = body.get("reader_type", "SINH_VIEN")

            if not full_name:
                return self._send_error("Họ và tên độc giả không được để trống!")

            if not card_number:
                card_number = f"DG{int(datetime.now().timestamp()) % 100000:05d}"

            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO readers (card_number, full_name, email, phone, gender, dob, address, reader_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (card_number, full_name, email, phone, gender, dob, address, reader_type))
                new_id = c.lastrowid
                conn.commit()
                self.log_action("THÊM ĐỘC GIẢ", f"Đăng ký thẻ độc giả: {full_name} ({card_number})")
                conn.close()
                return self._send_json({"success": True, "id": new_id, "message": "Thêm độc giả thành công!"})
            except sqlite3.IntegrityError:
                conn.close()
                return self._send_error("Số thẻ độc giả đã tồn tại!")
            except Exception as e:
                conn.close()
                return self._send_error(str(e))

        # 3. API: Tạo phiếu mượn sách mới
        if path == "/api/borrows":
            reader_id = body.get("reader_id")
            book_ids = body.get("book_ids", [])
            due_days = int(body.get("due_days") or 14)
            notes = body.get("notes", "")

            if not reader_id or not book_ids:
                return self._send_error("Vui lòng chọn độc giả và ít nhất 1 cuốn sách để mượn!")

            conn = get_connection()
            c = conn.cursor()

            # Kiểm tra độc giả
            c.execute("SELECT card_number, full_name, status FROM readers WHERE id = ?", (reader_id,))
            reader = c.fetchone()
            if not reader:
                conn.close()
                return self._send_error("Độc giả không tồn tại!")
            if reader["status"] != "ACTIVE":
                conn.close()
                return self._send_error("Thẻ độc giả đang bị khóa hoặc hết hạn!")

            # Kiểm tra số sách đang mượn
            c.execute("""
                SELECT COUNT(*) FROM borrow_details bd
                JOIN borrow_records br ON bd.record_id = br.id
                WHERE br.reader_id = ? AND bd.status = 'BORROWING'
            """, (reader_id,))
            currently_borrowed = c.fetchone()[0]
            if currently_borrowed + len(book_ids) > 5:
                conn.close()
                return self._send_error(f"Độc giả đang mượn {currently_borrowed} cuốn. Không được mượn vượt quá hạn mức tối đa (5 cuốn)!")

            # Kiểm tra số lượng tồn kho từng cuốn sách
            for b_id in book_ids:
                c.execute("SELECT title, available_copies FROM books WHERE id = ?", (b_id,))
                book = c.fetchone()
                if not book or book["available_copies"] <= 0:
                    conn.close()
                    return self._send_error(f"Sách '{book['title'] if book else b_id}' hiện đã hết bản sao có sẵn!")

            # Tạo mã phiếu mượn
            record_code = f"PM{datetime.now().strftime('%Y%m%d%H%M%S')}"
            today = datetime.now().date()
            due_date = today + timedelta(days=due_days)

            c.execute("""
                INSERT INTO borrow_records (record_code, reader_id, borrow_date, due_date, status, notes)
                VALUES (?, ?, ?, ?, 'BORROWING', ?)
            """, (record_code, reader_id, today.isoformat(), due_date.isoformat(), notes))
            record_id = c.lastrowid

            for b_id in book_ids:
                c.execute("""
                    INSERT INTO borrow_details (record_id, book_id, status)
                    VALUES (?, ?, 'BORROWING')
                """, (record_id, b_id))
                # Trừ số lượng sách có sẵn
                c.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (b_id,))

            conn.commit()
            self.log_action("MƯỢN SÁCH", f"Lập phiếu mượn {record_code} cho độc giả {reader['full_name']} ({len(book_ids)} cuốn)")
            conn.close()
            return self._send_json({"success": True, "record_code": record_code, "message": "Tạo phiếu mượn thành công!"})

        # 4. API: Trả sách
        if path.startswith("/api/borrows/") and path.endswith("/return"):
            record_id = path.split("/")[3]
            conn = get_connection()
            c = conn.cursor()

            c.execute("SELECT * FROM borrow_records WHERE id = ?", (record_id,))
            record = c.fetchone()
            if not record:
                conn.close()
                return self._send_error("Không tìm thấy phiếu mượn!", 404)

            today = datetime.now().date()
            due_date = datetime.fromisoformat(record["due_date"]).date()
            days_over = max(0, (today - due_date).days)
            fine_per_book = days_over * 5000

            # Lấy các sách trong phiếu đang mượn
            c.execute("SELECT book_id FROM borrow_details WHERE record_id = ? AND status = 'BORROWING'", (record_id,))
            items = c.fetchall()

            total_fine = fine_per_book * len(items)

            # Cập nhật chi tiết
            c.execute("""
                UPDATE borrow_details 
                SET return_date = ?, status = 'RETURNED', fine_amount = ?
                WHERE record_id = ? AND status = 'BORROWING'
            """, (today.isoformat(), fine_per_book, record_id))

            # Hoàn trả lại số lượng bản sao có sẵn
            for item in items:
                c.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (item["book_id"],))

            # Cập nhật trạng thái phiếu
            c.execute("UPDATE borrow_records SET status = 'RETURNED' WHERE id = ?", (record_id,))
            conn.commit()

            self.log_action("TRẢ SÁCH", f"Hoàn tất trả sách phiếu mượn {record['record_code']} (Phạt trễ hạn: {total_fine:,} VNĐ)")
            conn.close()
            return self._send_json({
                "success": True,
                "days_overdue": days_over,
                "fine_amount": total_fine,
                "message": f"Trả sách thành công! {f'Phạt trễ hạn: {total_fine:,} VNĐ' if total_fine > 0 else 'Đúng hạn.'}"
            })

        # 5. API: Gia hạn phiếu mượn (+7 ngày)
        if path.startswith("/api/borrows/") and path.endswith("/renew"):
            record_id = path.split("/")[3]
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM borrow_records WHERE id = ?", (record_id,))
            record = c.fetchone()
            if not record:
                conn.close()
                return self._send_error("Không tìm thấy phiếu mượn", 404)

            current_due = datetime.fromisoformat(record["due_date"]).date()
            new_due = current_due + timedelta(days=7)
            c.execute("UPDATE borrow_records SET due_date = ?, status = 'BORROWING' WHERE id = ?", (new_due.isoformat(), record_id))
            conn.commit()
            self.log_action("GIA HẠN", f"Gia hạn phiếu mượn {record['record_code']} đến ngày {new_due.strftime('%d/%m/%Y')}")
            conn.close()
            return self._send_json({"success": True, "new_due_date": new_due.isoformat(), "message": "Gia hạn mượn thêm 7 ngày thành công!"})

        # 6. API: AI Chat Assistant (Google AI Studio / Gemini)
        if path == "/api/ai/chat":
            msg = body.get("message", "").strip()
            if not msg:
                return self._send_error("Nội dung tin nhắn không được rỗng!")
            res = ai_service.ask_assistant(msg)
            return self._send_json({"success": True, "data": res})

        # 7. API: Cấu hình Gemini API Key
        if path == "/api/ai/config":
            api_key = body.get("api_key", "").strip()
            ai_service.set_api_key(api_key)
            return self._send_json({"success": True, "message": "Đã lưu API Key thành công!"})

        # 8. API: Tóm tắt sách bằng AI
        if path == "/api/ai/summarize":
            title = body.get("title", "")
            author = body.get("author", "")
            cat = body.get("category", "")
            summary = ai_service.generate_book_summary(title, author, cat)
            return self._send_json({"success": True, "summary": summary})

        return self._send_error("Endpoint không tồn tại", 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 1. Cập nhật sách
        if path.startswith("/api/books/"):
            book_id = path.split("/")[-1]
            title = body.get("title")
            author = body.get("author")
            cat_id = body.get("category_id")
            pub_year = body.get("publish_year")
            publisher = body.get("publisher")
            total_copies = body.get("total_copies")
            location = body.get("location")
            summary = body.get("summary")

            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                UPDATE books SET
                    title = COALESCE(?, title),
                    author = COALESCE(?, author),
                    category_id = COALESCE(?, category_id),
                    publish_year = COALESCE(?, publish_year),
                    publisher = COALESCE(?, publisher),
                    total_copies = COALESCE(?, total_copies),
                    location = COALESCE(?, location),
                    summary = COALESCE(?, summary)
                WHERE id = ?
            """, (title, author, cat_id, pub_year, publisher, total_copies, location, summary, book_id))
            conn.commit()
            conn.close()
            self.log_action("CẬP NHẬT SÁCH", f"Cập nhật thông tin sách ID: {book_id}")
            return self._send_json({"success": True, "message": "Cập nhật sách thành công!"})

        # 2. Cập nhật độc giả
        if path.startswith("/api/readers/"):
            reader_id = path.split("/")[-1]
            full_name = body.get("full_name")
            email = body.get("email")
            phone = body.get("phone")
            gender = body.get("gender")
            dob = body.get("dob")
            address = body.get("address")
            reader_type = body.get("reader_type")
            status = body.get("status")

            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                UPDATE readers SET
                    full_name = COALESCE(?, full_name),
                    email = COALESCE(?, email),
                    phone = COALESCE(?, phone),
                    gender = COALESCE(?, gender),
                    dob = COALESCE(?, dob),
                    address = COALESCE(?, address),
                    reader_type = COALESCE(?, reader_type),
                    status = COALESCE(?, status)
                WHERE id = ?
            """, (full_name, email, phone, gender, dob, address, reader_type, status, reader_id))
            conn.commit()
            conn.close()
            self.log_action("CẬP NHẬT ĐỘC GIẢ", f"Cập nhật thông tin độc giả ID: {reader_id}")
            return self._send_json({"success": True, "message": "Cập nhật độc giả thành công!"})

        return self._send_error("Endpoint không tồn tại", 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Xóa sách
        if path.startswith("/api/books/"):
            book_id = path.split("/")[-1]
            conn = get_connection()
            c = conn.cursor()
            # Kiểm tra xem có ai đang mượn sách này không
            c.execute("SELECT COUNT(*) FROM borrow_details WHERE book_id = ? AND status = 'BORROWING'", (book_id,))
            if c.fetchone()[0] > 0:
                conn.close()
                return self._send_error("Không thể xóa sách đang có độc giả mượn!")

            c.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            self.log_action("XÓA SÁCH", f"Đã xóa sách ID {book_id}")
            return self._send_json({"success": True, "message": "Đã xóa sách thành công!"})

        # 2. Xóa độc giả
        if path.startswith("/api/readers/"):
            reader_id = path.split("/")[-1]
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) FROM borrow_records br
                JOIN borrow_details bd ON br.id = bd.record_id
                WHERE br.reader_id = ? AND bd.status = 'BORROWING'
            """, (reader_id,))
            if c.fetchone()[0] > 0:
                conn.close()
                return self._send_error("Không thể xóa độc giả đang chưa hoàn trả sách!")

            c.execute("DELETE FROM readers WHERE id = ?", (reader_id,))
            conn.commit()
            conn.close()
            self.log_action("XÓA ĐỘC GIẢ", f"Đã xóa hồ sơ độc giả ID {reader_id}")
            return self._send_json({"success": True, "message": "Đã xóa độc giả thành công!"})

        return self._send_error("Endpoint không tồn tại", 404)

    def _serve_static_file(self, req_path):
        """Phục vụ file giao diện HTML, CSS, JS tĩnh"""
        if req_path in ("/", ""):
            req_path = "/index.html"

        # Sanitize path
        req_path = req_path.lstrip("/").replace("\\", "/")
        file_path = os.path.join(STATIC_DIR, req_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(STATIC_DIR, "index.html")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Lỗi đọc file tĩnh: {e}")

def run_server(port=PORT):
    # Khởi tạo và nạp dữ liệu SQLite nếu chưa có
    init_db()
    seed_sample_data()

    server_address = ("", port)
    httpd = HTTPServer(server_address, LibraryAPIHandler)
    print("=" * 60)
    print(" 🚀 HỆ THỐNG QUẢN LÝ THƯ VIỆN ỨNG DỤNG CÔNG CỤ AI")
    print(f" 🌐 Địa chỉ truy cập: http://localhost:{port}")
    print(f" 📂 Thư mục mã nguồn: {os.path.dirname(os.path.abspath(__file__))}")
    print(" 💡 Nhấn Ctrl + C để dừng máy chủ.")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng máy chủ thư viện.")

if __name__ == "__main__":
    p = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        p = int(sys.argv[1])
    run_server(p)
