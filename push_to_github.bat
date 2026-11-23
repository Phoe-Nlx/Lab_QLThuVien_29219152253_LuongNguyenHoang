@echo off
chcp 65001 >nul
echo ========================================================
echo   DAY MA NGUON LEN GITHUB: Phoe-Nlx
echo   Sinh vien: Nguyen Tran Van Manh - MSSV: 29211555052
echo ========================================================
echo.
cd /d "%~dp0"
git branch -M main

echo Chon repository tren GitHub cua ban:
echo  [1] https://github.com/Phoe-Nlx/Lab_QLThuVien_29211555052_NguyenTranVanManh.git (Chuan theo MSSV moi)
echo  [2] https://github.com/Phoe-Nlx/Lab_QLThuVien_29219152253_LuongNguyenHoang.git (Repo ban da tao tren GitHub)
echo  [3] Nhap link GitHub Repository khac
echo.
set /p choice="Nhap lua chon (1, 2 hoac 3) [Mac dinh: 1]: "

if "%choice%"=="2" (
    git remote set-url origin https://github.com/Phoe-Nlx/Lab_QLThuVien_29219152253_LuongNguyenHoang.git
) else if "%choice%"=="3" (
    set /p custom_url="Nhap link GitHub .git cua ban: "
    git remote set-url origin %custom_url%
) else (
    git remote set-url origin https://github.com/Phoe-Nlx/Lab_QLThuVien_29211555052_NguyenTranVanManh.git
)

echo.
echo Dang day code len GitHub (neu co cua so xac thuc hien len, hay bam 'Sign in with your browser')...
echo.
git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  CHUC MUNG! DA DAY TOAN BO DU AN LEN GITHUB THANH CONG!
    echo ========================================================
) else (
    echo Co loi xay ra hoac chua xac thuc tai khoan tren trinh duyet.
)
pause
