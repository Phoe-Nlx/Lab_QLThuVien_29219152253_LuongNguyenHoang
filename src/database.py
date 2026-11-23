"""
Module Quản lý Cơ sở dữ liệu SQLite cho Hệ thống Quản lý Thư viện
Phục vụ Bài thực hành: Phân tích, Thiết kế và Xây dựng Hệ thống Quản lý Thư viện ứng dụng AI.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "library.db")

def get_connection(db_path=None):
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path=None):
    """Tạo các bảng cơ sở dữ liệu nếu chưa tồn tại"""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Bảng Thể loại sách
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT
    )
    """)

    # 2. Bảng Sách
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category_id INTEGER,
        publish_year INTEGER,
        publisher TEXT,
        total_copies INTEGER DEFAULT 1,
        available_copies INTEGER DEFAULT 1,
        location TEXT,
        summary TEXT,
        status TEXT DEFAULT 'AVAILABLE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    )
    """)

    # 3. Bảng Độc giả
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS readers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        gender TEXT DEFAULT 'Khác',
        dob TEXT,
        address TEXT,
        reader_type TEXT DEFAULT 'SINH_VIEN',
        status TEXT DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Bảng Phiếu mượn
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrow_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_code TEXT UNIQUE NOT NULL,
        reader_id INTEGER NOT NULL,
        borrow_date DATE NOT NULL,
        due_date DATE NOT NULL,
        status TEXT DEFAULT 'BORROWING',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE CASCADE
    )
    """)

    # 5. Bảng Chi tiết phiếu mượn
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrow_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        return_date DATE,
        status TEXT DEFAULT 'BORROWING',
        fine_amount REAL DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (record_id) REFERENCES borrow_records(id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
    )
    """)

    # 6. Bảng Nhật ký hệ thống
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Khởi tạo cấu trúc cơ sở dữ liệu thành công.")

def seed_sample_data(db_path=None, force=False):
    """Nạp dữ liệu mẫu phong phú và thực tế cho hệ thống quản lý thư viện"""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0 and not force:
        conn.close()
        return

    if force:
        cursor.execute("DELETE FROM borrow_details")
        cursor.execute("DELETE FROM borrow_records")
        cursor.execute("DELETE FROM readers")
        cursor.execute("DELETE FROM books")
        cursor.execute("DELETE FROM categories")
        cursor.execute("DELETE FROM system_logs")

    # 1. Thể loại sách
    categories = [
        ("CNTT", "Công nghệ thông tin & Trí tuệ nhân tạo", "Sách lập trình, thuật toán, AI, học máy và hệ điều hành"),
        ("KH_TN", "Khoa học Tự nhiên & Đời sống", "Toán học, Vật lý, Thiên văn học, Sinh học và Tiến hóa"),
        ("KINHTE", "Kinh tế & Quản trị Kinh doanh", "Tài chính, Marketing, Quản trị doanh nghiệp và Khởi nghiệp"),
        ("VANHOC", "Văn học & Nghệ thuật", "Tiểu thuyết kinh điển, văn học hiện đại và thơ ca"),
        ("KYNANG", "Kỹ năng sống & Phát triển bản thân", "Tâm lý học ứng dụng, tư duy logic và kỹ năng giao tiếp"),
        ("NGOAINGU", "Ngoại ngữ & Ngôn ngữ học", "Giáo trình IELTS, TOEIC, Ngữ pháp tiếng Anh và tiếng Nhật")
    ]
    cursor.executemany("INSERT OR IGNORE INTO categories (code, name, description) VALUES (?, ?, ?)", categories)

    # 2. Sách phong phú
    books = [
        ("978-604-01", "Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", 1, 2008, "Prentice Hall", 5, 3, "Kệ A1 - Ngăn 1", "Cuốn cẩm nang kinh điển về quy tắc viết mã sạch, dễ bảo trì và mở rộng cho lập trình viên chuyên nghiệp."),
        ("978-604-02", "Trí Tuệ Nhân Tạo: Cách Tiếp Cận Hiện Đại (AI: Modern Approach)", "Stuart Russell & Peter Norvig", 1, 2020, "Pearson", 4, 2, "Kệ A1 - Ngăn 2", "Giáo trình chuẩn toàn cầu về các phương pháp tìm kiếm, giải quyết vấn đề, tác tử thông minh và Deep Learning."),
        ("978-604-03", "Design Patterns: Elements of Reusable Object-Oriented Software", "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides", 1, 1994, "Addison-Wesley", 3, 2, "Kệ A1 - Ngăn 3", "23 mẫu thiết kế hướng đối tượng kinh điển giúp giải quyết các bài toán kiến trúc phần mềm."),
        ("978-604-04", "Machine Learning Cơ Bản", "Vũ Hữu Tiệp", 1, 2018, "NXB Thế Giới", 6, 4, "Kệ A1 - Ngăn 4", "Giới thiệu các thuật toán hồi quy, phân loại, mạng neural và ứng dụng thực tiễn với Python."),
        ("978-604-05", "Lược Sử Loài Người (Sapiens)", "Yuval Noah Harari", 2, 2014, "NXB Tri Thức", 6, 5, "Kệ B2 - Ngăn 1", "Khảo sát tiến trình phát triển của loài người từ thời kỳ đồ đá đến thế kỷ 21 qua các cuộc cách mạng nhận thức, nông nghiệp và khoa học."),
        ("978-604-06", "Vũ Trụ Trong Vỏ Hạt Dẻ (The Universe in a Nutshell)", "Stephen Hawking", 2, 2001, "NXB Trẻ", 4, 3, "Kệ B2 - Ngăn 2", "Khám phá thuyết tương đối, lỗ đen, lý thuyết dây và bản chất của thời gian qua lời giải thích dễ hiểu của Hawking."),
        ("978-604-07", "Kinh Tế Học Vi Mô Cơ Bản", "N. Gregory Mankiw", 3, 2021, "NXB Cengage", 5, 4, "Kệ C1 - Ngăn 1", "Giáo trình chuẩn mực cung cấp các nguyên lý kinh tế học, cung cầu, cấu trúc thị trường và chính sách công."),
        ("978-604-08", "Từ Tốt Đến Vĩ Đại (Good to Great)", "Jim Collins", 3, 2001, "NXB Trẻ", 5, 3, "Kệ C1 - Ngăn 2", "Nghiên cứu về các yếu tố giúp các công ty chuyển mình và duy trì sự phát triển xuất chúng qua nhiều thập kỷ."),
        ("978-604-09", "Nhà Giả Kim (The Alchemist)", "Paulo Coelho", 4, 1988, "NXB Hội Nhà Văn", 8, 6, "Kệ D3 - Ngăn 1", "Câu chuyện ngụ ngôn giàu triết lý về hành trình theo đuổi vận mệnh và tiếng gọi con tim của chàng chăn cừu Santiago."),
        ("978-604-10", "Không Gia Đình (Sans Famille)", "Hector Malot", 4, 1878, "NXB Kim Đồng", 4, 3, "Kệ D3 - Ngăn 2", "Tiểu thuyết cảm động về tình người và ý chí vượt qua nghịch cảnh của cậu bé mồ côi Rémi."),
        ("978-604-11", "Đắc Nhân Tâm (How to Win Friends and Influence People)", "Dale Carnegie", 5, 1936, "NXB Tổng Hợp TPHCM", 10, 7, "Kệ E2 - Ngăn 1", "Nghệ thuật giao tiếp, thấu hiểu và ứng xử giúp xây dựng các mối quan hệ thành công và bền vững."),
        ("978-604-12", "Tư Duy Nhanh Và Chậm (Thinking, Fast and Slow)", "Daniel Kahneman", 5, 2011, "NXB Thế Giới", 4, 2, "Kệ E2 - Ngăn 2", "Khám phá hai hệ thống tư duy chi phối nhận thức, các thiên kiến tâm lý và cách con người ra quyết định."),
        ("978-604-13", "English Grammar in Use (5th Edition)", "Raymond Murphy", 6, 2019, "Cambridge University Press", 6, 4, "Kệ F1 - Ngăn 1", "Cuốn sách ngữ pháp tiếng Anh tự học bán chạy nhất thế giới cho trình độ trung cấp.")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO books (isbn, title, author, category_id, publish_year, publisher, total_copies, available_copies, location, summary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, books)

    # 3. Độc giả mẫu
    readers = [
        ("DG001", "Nguyễn Văn An", "an.nv@university.edu.vn", "0912345678", "Nam", "2003-05-12", "Ký túc xá khu A, ĐHQG", "SINH_VIEN", "ACTIVE"),
        ("DG002", "Trần Thị Mai Hương", "huong.ttm@university.edu.vn", "0987654321", "Nữ", "2002-11-20", "128 Nguyễn Trãi, Thanh Xuân, Hà Nội", "SINH_VIEN", "ACTIVE"),
        ("DG003", "TS. Lê Hoàng Nam", "nam.lh@university.edu.vn", "0903112233", "Nam", "1980-04-15", "Tòa nhà Khoa CNTT, Phòng 402", "GIANG_VIEN", "ACTIVE"),
        ("DG004", "Phạm Quốc Bảo", "bao.pq@university.edu.vn", "0945678901", "Nam", "2004-01-30", "Ký túc xá khu B, ĐHQG", "SINH_VIEN", "ACTIVE"),
        ("DG005", "Đỗ Thị Kim Ngân", "ngan.dtk@university.edu.vn", "0971239874", "Nữ", "2003-09-08", "45 Cầu Giấy, Hà Nội", "SINH_VIEN", "ACTIVE"),
        ("DG006", "Vũ Đình Trọng", "trong.vd@research.edu.vn", "0966554433", "Nam", "1997-07-25", "Viện Công nghệ Thông tin", "NGHIEN_CUU_SINH", "ACTIVE")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO readers (card_number, full_name, email, phone, gender, dob, address, reader_type, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, readers)

    # 4. Phiếu mượn và chi tiết mượn
    today = datetime.now().date()
    records = [
        ("PM20261101", 1, (today - timedelta(days=20)).isoformat(), (today - timedelta(days=6)).isoformat(), "OVERDUE", "Mượn phục vụ làm đồ án môn học"),
        ("PM20261102", 2, (today - timedelta(days=10)).isoformat(), (today + timedelta(days=4)).isoformat(), "BORROWING", "Bạn đọc gia hạn lần 1"),
        ("PM20261103", 3, (today - timedelta(days=5)).isoformat(), (today + timedelta(days=25)).isoformat(), "BORROWING", "Giảng viên mượn nghiên cứu"),
        ("PM20261015", 4, (today - timedelta(days=40)).isoformat(), (today - timedelta(days=26)).isoformat(), "RETURNED", "Đã hoàn tất trả sách đúng hạn")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO borrow_records (record_code, reader_id, borrow_date, due_date, status, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, records)

    # Chi tiết phiếu mượn tương ứng
    # Record 1 (Overdue): reader 1 mượn sách 1 & 2
    # Record 2 (Borrowing): reader 2 mượn sách 5 & 11
    # Record 3 (Borrowing): reader 3 mượn sách 2 & 4
    # Record 4 (Returned): reader 4 mượn sách 9, đã trả
    details = [
        (1, 1, None, "BORROWING", 30000.0, "Quá hạn 6 ngày (phạt 5.000đ/ngày)"),
        (1, 2, None, "BORROWING", 30000.0, "Quá hạn 6 ngày (phạt 5.000đ/ngày)"),
        (2, 5, None, "BORROWING", 0.0, "Đang trong hạn mượn"),
        (2, 11, None, "BORROWING", 0.0, "Đang trong hạn mượn"),
        (3, 2, None, "BORROWING", 0.0, "Hạn mượn 30 ngày cho giảng viên"),
        (3, 4, None, "BORROWING", 0.0, "Hạn mượn 30 ngày cho giảng viên"),
        (4, 9, (today - timedelta(days=28)).isoformat(), "RETURNED", 0.0, "Trả sách đúng hạn, tình trạng tốt")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO borrow_details (record_id, book_id, return_date, status, fine_amount, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, details)

    # Cập nhật số lượng sách available_copies tương ứng
    cursor.execute("UPDATE books SET available_copies = total_copies")
    cursor.execute("""
    UPDATE books 
    SET available_copies = total_copies - (
        SELECT COUNT(*) FROM borrow_details 
        WHERE borrow_details.book_id = books.id AND borrow_details.status = 'BORROWING'
    )
    """)

    # Ghi log mẫu
    logs = [
        ("KHỞI TẠO HỆ THỐNG", "Khởi tạo thành công cơ sở dữ liệu và danh mục sách mẫu"),
        ("TẠO PHIẾU MƯỢN", "Tạo phiếu mượn PM20261101 cho độc giả Nguyễn Văn An"),
        ("GIA HẠN", "Độc giả Trần Thị Mai Hương gia hạn phiếu mượn PM20261102"),
        ("TRẢ SÁCH", "Độc giả Phạm Quốc Bảo đã trả sách phiếu PM20261015")
    ]
    cursor.executemany("INSERT INTO system_logs (action, details) VALUES (?, ?)", logs)

    conn.commit()
    conn.close()
    print("Nạp dữ liệu mẫu thành công!")

if __name__ == "__main__":
    init_db()
    seed_sample_data(force=True)
