param (
    [string]$mssv = "29211555052",
    [string]$hoten = "NguyenTranVanManh"
)

$baseDir = $PSScriptRoot
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " TỰ ĐỘNG ĐỔI TÊN DỰ ÁN & ĐÓNG GÓI BÀI THỰC HÀNH" -ForegroundColor Yellow
Write-Host " MSSV mới: $mssv" -ForegroundColor Green
Write-Host " Họ tên mới: $hoten" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# Cập nhật thông tin trong BaoCao_Lab.md
$baoCaoPath = Join-Path $baseDir "BaoCao_Lab.md"
if (Test-Path $baoCaoPath) {
    (Get-Content -Path $baoCaoPath -Raw -Encoding UTF8) -replace '29211555052', $mssv -replace 'Nguyễn Trần Văn Mạnh', $hoten | Set-Content -Path $baoCaoPath -Encoding UTF8
    Write-Host " + Đã cập nhật BaoCao_Lab.md" -ForegroundColor Green
}

# Chạy package_zip.py
python "$baseDir\package_zip.py" --mssv $mssv --hoten $hoten

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " HOÀN TẤT! File zip sẵn sàng để nộp: ${mssv}_${hoten}_LabQLThuVien.zip" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
