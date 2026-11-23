"""
Script tự động đóng gói bài nộp: [MSSV]_[HoTen]_LabQLThuVien.zip
Theo quy định bài thực hành môn học.
"""

import os
import sys
import zipfile
import argparse

def create_submission_zip(mssv="29211555052", hoten="NguyenTranVanManh"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_filename = f"{mssv}_{hoten}_LabQLThuVien.zip"
    zip_filepath = os.path.join(base_dir, zip_filename)

    # Các thư mục và file cần đóng gói
    include_files = [
        "BaoCao_Lab.md",
        "README.md",
        "start.bat",
        "package_zip.py"
    ]
    include_dirs = [
        "src",
        "data"
    ]

    print("=" * 60)
    print(f"📦 BẮT ĐẦU ĐÓNG GÓI BÀI THỰC HÀNH:")
    print(f" - MSSV: {mssv}")
    print(f" - Họ tên: {hoten}")
    print(f" - Tên file nén: {zip_filename}")
    print("=" * 60)

    count = 0
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Thêm các file đơn lẻ
        for filename in include_files:
            file_path = os.path.join(base_dir, filename)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=filename)
                print(f" + Đã thêm: {filename}")
                count += 1

        # Thêm các thư mục
        for dir_name in include_dirs:
            dir_path = os.path.join(base_dir, dir_name)
            if os.path.exists(dir_path):
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, base_dir)
                        # Bỏ qua các file cache __pycache__
                        if "__pycache__" in rel_path or rel_path.endswith(".pyc"):
                            continue
                        zipf.write(full_path, arcname=rel_path)
                        print(f" + Đã thêm: {rel_path}")
                        count += 1

    file_size_kb = os.path.getsize(zip_filepath) / 1024
    print("=" * 60)
    print(f"🎉 ĐÓNG GÓI THÀNH CÔNG! (Tổng cộng {count} files)")
    print(f"📂 Vị trí file zip: {zip_filepath}")
    print(f"📊 Kích thước: {file_size_kb:.2f} KB")
    print("=" * 60)
    return zip_filepath

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đóng gói bài Lab Quản lý Thư viện")
    parser.add_argument("--mssv", default="29211555052", help="Mã số sinh viên của bạn")
    parser.add_argument("--hoten", default="NguyenTranVanManh", help="Họ và tên viết liền không dấu")
    args = parser.parse_args()

    create_submission_zip(args.mssv, args.hoten)
