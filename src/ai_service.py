"""
Module AI Service - Tích hợp Google AI Studio (Gemini API) và Bộ máy Trí tuệ Nhân tạo Thư viện
Phục vụ Bài thực hành: Phân tích, Thiết kế và Xây dựng Hệ thống Quản lý Thư viện ứng dụng AI.
"""

import os
import json
import sqlite3
import requests
from datetime import datetime

class LibraryAIService:
    def __init__(self, api_key=None, db_path=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.db_path = db_path
        self.model = "gemini-1.5-flash"

    def set_api_key(self, api_key):
        self.api_key = api_key.strip() if api_key else ""

    def _get_books_context(self):
        """Lấy danh mục sách từ SQLite để đưa vào Context cho AI"""
        try:
            from database import get_connection
            conn = get_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, b.isbn, b.title, b.author, c.name as category, 
                       b.available_copies, b.location, b.summary
                FROM books b
                LEFT JOIN categories c ON b.category_id = c.id
            """)
            rows = cursor.fetchall()
            books = []
            for r in rows:
                books.append({
                    "id": r["id"],
                    "isbn": r["isbn"],
                    "title": r["title"],
                    "author": r["author"],
                    "category": r["category"],
                    "available": r["available_copies"],
                    "location": r["location"],
                    "summary": r["summary"]
                })
            conn.close()
            return books
        except Exception as e:
            print("Lỗi đọc sách cho AI Context:", e)
            return []

    def call_gemini(self, prompt, system_instruction=None):
        """Gọi API Google AI Studio / Gemini API bằng requests REST"""
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                print(f"Gemini API returned status {response.status_code}: {response.text}")
                return None
        except Exception as ex:
            print(f"Lỗi kết nối Gemini API: {ex}")
            return None

    def ask_assistant(self, user_message):
        """Trợ lý ảo thư viện giải đáp thắc mắc, gợi ý sách, tra cứu nội quy mượn trả"""
        books = self._get_books_context()
        books_str = json.dumps(books, ensure_ascii=False, indent=2)

        system_instruction = f"""
Bạn là Trợ lý AI Thông minh của Hệ thống Quản lý Thư viện trường Đại học.
Nhiệm vụ của bạn:
1. Tư vấn, giải đáp thắc mắc của độc giả về sách, thể loại, tác giả, vị trí kệ sách.
2. Hướng dẫn quy chế thư viện:
   - Thời hạn mượn: Sinh viên tối đa 14 ngày, Giảng viên tối đa 30 ngày.
   - Số sách mượn tối đa: 3 cuốn/lần đối với Sinh viên, 5 cuốn/lần đối với Giảng viên.
   - Phí trễ hạn: 5.000 VNĐ / ngày / cuốn sách.
3. Khi gợi ý sách, ưu tiên các đầu sách đang có sẵn trong kho thư viện dưới đây:
{books_str}
Hãy trả lời bằng tiếng Việt thân thiện, rõ ràng, định dạng markdown đẹp mắt (in đậm tên sách, tác giả, vị trí kệ sách).
"""

        if self.api_key:
            ai_reply = self.call_gemini(user_message, system_instruction)
            if ai_reply:
                return {
                    "source": "Google AI Studio (Gemini 1.5 Flash)",
                    "message": ai_reply
                }

        # Bộ máy quy tắc suy diễn Fallback cục bộ khi không có API Key
        msg_lower = user_message.lower()
        matched_books = []
        for b in books:
            if (any(word in b["title"].lower() for word in msg_lower.split()) or
                any(word in b["author"].lower() for word in msg_lower.split()) or
                (b["category"] and any(word in b["category"].lower() for word in msg_lower.split()))):
                matched_books.append(b)

        if "mượn" in msg_lower or "quy định" in msg_lower or "thời hạn" in msg_lower or "hạn" in msg_lower:
            reply = (
                "📚 **Quy định Mượn - Trả sách của Thư viện:**\n\n"
                "- **Đối tượng Sinh viên:** Mượn tối đa **3 cuốn/lần**, thời hạn mượn tối đa **14 ngày** (được gia hạn 1 lần thêm 7 ngày nếu không ai đặt trước).\n"
                "- **Đối tượng Giảng viên/NCS:** Mượn tối đa **5 cuốn/lần**, thời hạn **30 ngày**.\n"
                "- **Phí phạt quá hạn:** **5.000 VNĐ / cuốn / ngày trễ**.\n"
                "- **Lưu ý:** Độc giả vui lòng giữ gìn sách cẩn thận, không làm rách hoặc viết vẽ lên sách."
            )
        elif "phạt" in msg_lower or "tiền" in msg_lower:
            reply = (
                "⚠️ **Chính sách Phí phạt & Bồi hoàn:**\n\n"
                "- **Trễ hạn:** 5.000 VNĐ / cuốn / ngày quá hạn.\n"
                "- **Hư hỏng nhẹ (rách trang, viết bẩn):** Phạt 20.000 VNĐ / cuốn.\n"
                "- **Làm mất sách hoặc hư hỏng nặng:** Độc giả phải đền cuốn sách mới tương đương hoặc bồi thường 150% giá bìa sách."
            )
        elif matched_books:
            reply = "📖 **Dưới đây là một số đầu sách phù hợp trong kho thư viện:**\n\n"
            for b in matched_books[:3]:
                avail = f"✅ Còn {b['available']} cuốn" if b['available'] > 0 else "❌ Tạm hết (đang có người mượn)"
                reply += f"- **{b['title']}** - Tác giả: *{b['author']}*\n"
                reply += f"  - Thể loại: `{b['category']}` | Tình trạng: {avail}\n"
                reply += f"  - Vị trí: 📍 **{b['location']}**\n"
                reply += f"  - Tóm tắt: _{b['summary']}_\n\n"
            reply += "Bạn có thể đến trực tiếp kệ sách để lấy hoặc đăng ký mượn tại quầy thủ thư!"
        else:
            reply = (
                f"Xin chào bạn! Mình là Trợ lý Thư viện AI. Mình có thể giúp bạn:\n\n"
                f"1. 🔍 **Tra cứu sách**: Tìm kiếm theo tên sách, tác giả hoặc chủ đề (ví dụ: *Clean Code*, *Machine Learning*, *Kinh tế*, *Văn học*).\n"
                f"2. 💡 **Gợi ý học tập**: Gợi ý sách theo chuyên ngành Công nghệ thông tin, Kinh tế, Ngoại ngữ, Kỹ năng sống...\n"
                f"3. 📋 **Quy định thư viện**: Hướng dẫn thủ tục mượn/trả, thời hạn và phí phạt trễ hạn.\n\n"
                f"*(Mẹo: Bạn có thể nhập Google AI Studio API Key tại phần Cài đặt để kích hoạt mô hình Gemini mạnh mẽ nhất!)*"
            )

        return {
            "source": "Smart Library AI (Offline / Local Rule Engine)",
            "message": reply
        }

    def generate_book_summary(self, title, author, category=""):
        """Tự động tóm tắt nội dung sách cho thủ thư khi thêm sách mới"""
        prompt = f"Hãy viết một đoạn tóm tắt ngắn (khoảng 3-4 câu) bằng tiếng Việt cho cuốn sách '{title}' của tác giả '{author}' (Thể loại: {category}). Nêu bật giá trị cốt lõi và đối tượng bạn đọc nên đọc cuốn sách này."
        if self.api_key:
            res = self.call_gemini(prompt)
            if res:
                return res.strip()
        return f"Cuốn sách '{title}' của tác giả {author} là tài liệu giá trị thuộc thể loại {category}, cung cấp góc nhìn sâu sắc và kiến thức hữu ích cho bạn đọc và sinh viên."
