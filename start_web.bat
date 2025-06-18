@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 🚀 功能测试用例生成器 - Web版本
echo ========================================
echo.

echo 📋 检查依赖包...
python -c "import flask, pandas, openpyxl" 2>nul
if errorlevel 1 (
    echo ❌ 缺少依赖包，正在安装...
    pip install -r requirements_web.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖包安装完成
) else (
    echo ✅ 依赖包检查通过
)

echo.
echo 📋 启动信息:
echo    - 访问地址: http://localhost:5000
echo    - 按 Ctrl+C 停止服务
echo    - 浏览器将自动打开
echo ========================================
echo.

:: 延迟3秒后打开浏览器
start "" timeout /t 3 /nobreak >nul && start http://localhost:5000

:: 启动Flask应用
python "%~dp0app.py"

pause
