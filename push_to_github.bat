@echo off
chcp 65001 >nul
echo ========================================================
echo   DANG DAY MA NGUON LEN GITHUB: Phoe-Nlx
echo   Repo: Lab_QLThuVien_29211555052_NguyenTranVanManh
echo ========================================================
echo.
cd /d "%~dp0"

git branch -M main
git remote set-url origin https://github.com/Phoe-Nlx/Lab_QLThuVien_29211555052_NguyenTranVanManh.git
echo Dang day code len GitHub (neu co cua so trinh duyet hien len, hay bam 'Sign in with your browser')...
echo.
git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  CHUC MUNG! DA DAY TOAN BO DU AN LEN GITHUB THANH CONG!
    echo  Xem tai: https://github.com/Phoe-Nlx/Lab_QLThuVien_29211555052_NguyenTranVanManh
    echo ========================================================
) else (
    echo Co loi xay ra hoac chua xac thuc tai khoan.
)
pause
