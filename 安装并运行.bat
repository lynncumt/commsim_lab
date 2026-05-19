@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  通信原理仿真软件 — 一键启动 / 首次自动安装
::  双击此文件即可运行，无需手动安装 Python 或任何依赖。
:: ─────────────────────────────────────────────────────────────────────────────
title 通信原理仿真软件
chcp 65001 >nul 2>&1

echo.
echo  ┌─────────────────────────────────────────────┐
echo  │     通信原理仿真软件  v1.0                  │
echo  │   Communications Simulation Lab             │
echo  └─────────────────────────────────────────────┘
echo.

:: 检查 PowerShell 可用性
where powershell >nul 2>&1
if errorlevel 1 (
    echo  [错误] 未找到 PowerShell，请确保 Windows 7+ 系统。
    pause
    exit /b 1
)

:: 获取本脚本所在目录（支持从任意位置双击）
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%安装并运行.ps1"

if not exist "%PS_SCRIPT%" (
    echo  [错误] 未找到安装脚本：%PS_SCRIPT%
    echo  请确保 "安装并运行.bat" 与 "安装并运行.ps1" 在同一目录。
    pause
    exit /b 1
)

:: 以绕过执行策略的方式运行 PS1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

if errorlevel 1 (
    echo.
    echo  [错误] 程序异常退出，请查看日志：
    echo  %%LOCALAPPDATA%%\CommSimLab\setup.log
    pause
)
