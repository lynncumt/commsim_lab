@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  通信原理仿真软件 - Windows EXE 构建脚本
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未找到，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/4] 安装依赖包...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)
echo       完成！

echo.
echo [2/4] 清理旧构建目录...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
echo       完成！

echo.
echo [3/4] 运行 PyInstaller 打包...
python -m PyInstaller commsim.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller 打包失败
    pause
    exit /b 1
)
echo       完成！

echo.
echo [4/4] 构建结果:
if exist "dist\通信原理仿真软件.exe" (
    echo       SUCCESS: dist\通信原理仿真软件.exe
    for %%F in ("dist\通信原理仿真软件.exe") do echo       文件大小: %%~zF 字节
) else (
    echo [ERROR] 未找到输出 EXE 文件
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  打包完成！双击运行:
echo  dist\通信原理仿真软件.exe
echo ============================================================
echo.
pause
