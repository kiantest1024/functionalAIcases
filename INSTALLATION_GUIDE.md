# 功能测试用例生成器 - 安装指南

## 🚀 快速安装

### 1. 环境要求
- Python 3.8 或更高版本
- Windows/Linux/macOS 操作系统
- 网络连接（用于下载依赖包）

### 2. 安装步骤

#### 方法一：标准安装（推荐）
```bash
# 1. 进入项目目录
cd functionalAItest

# 2. 安装依赖包
pip install -r requirements.txt

# 3. 启动应用
python ai_web_app.py
```

#### 方法二：Windows批处理安装
```cmd
# 双击运行
start_web.bat
```

### 3. 验证安装

访问以下地址验证安装成功：
- 本地访问：http://127.0.0.1:5001
- 局域网访问：http://192.168.x.x:5001

## 🔧 依赖包说明

### 核心依赖
- **Flask>=2.3.0** - Web框架，提供用户界面
- **pandas>=2.0.0** - 数据处理，用于Excel文件操作
- **requests>=2.31.0** - HTTP请求，用于AI服务调用
- **openpyxl>=3.1.0** - Excel文件读写

### 可选依赖
- **openai>=1.0.0** - OpenAI API支持
- **anthropic>=0.3.0** - Claude API支持

## ❗ 常见问题解决

### 问题1：pandas安装失败
**错误信息**：`Microsoft Visual C++ 14.0 or greater is required`

**解决方案**：
```bash
# 方案1：使用预编译版本
pip install --only-binary=all pandas

# 方案2：使用conda
conda install pandas

# 方案3：安装Microsoft C++ Build Tools
# 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### 问题2：Flask启动失败
**错误信息**：`Address already in use`

**解决方案**：
```bash
# 检查端口占用
netstat -ano | findstr :5001

# 杀死占用进程
taskkill /PID <进程ID> /F

# 或者修改端口
# 在ai_web_app.py中修改：app.run(host='0.0.0.0', port=5002, debug=True)
```

### 问题3：模块导入错误
**错误信息**：`ModuleNotFoundError: No module named 'xxx'`

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 检查Python环境
python --version
pip list
```

### 问题4：权限错误
**错误信息**：`Permission denied`

**解决方案**：
```bash
# Windows：以管理员身份运行命令提示符
# Linux/macOS：使用sudo
sudo pip install -r requirements.txt
```

## 🌐 网络配置

### 防火墙设置
如需局域网访问，请确保防火墙允许5001端口：

**Windows防火墙**：
1. 控制面板 → 系统和安全 → Windows Defender防火墙
2. 高级设置 → 入站规则 → 新建规则
3. 选择"端口" → TCP → 特定本地端口：5001
4. 允许连接 → 应用到所有配置文件

**Linux防火墙**：
```bash
# Ubuntu/Debian
sudo ufw allow 5001

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

## 📋 系统要求

### 最低配置
- CPU：双核 1.5GHz
- 内存：2GB RAM
- 硬盘：500MB 可用空间
- 网络：宽带连接

### 推荐配置
- CPU：四核 2.0GHz 或更高
- 内存：4GB RAM 或更高
- 硬盘：1GB 可用空间
- 网络：稳定的宽带连接

## 🔍 安装验证

### 功能测试清单
- [ ] Web界面正常访问
- [ ] AI配置页面可用
- [ ] 测试用例生成功能正常
- [ ] Excel文件导出成功
- [ ] Markdown报告生成正常

### 测试命令
```bash
# 检查Python版本
python --version

# 检查依赖包
pip list | grep -E "(Flask|pandas|requests|openpyxl)"

# 测试导入
python -c "import flask, pandas, requests, openpyxl; print('所有依赖包导入成功')"
```

## 🆘 获取帮助

### 日志查看
应用运行时的日志信息会显示在终端中，包括：
- 启动信息
- 错误信息
- 请求日志

### 调试模式
应用默认以调试模式运行，提供详细的错误信息和自动重载功能。

### 联系支持
如遇到无法解决的问题，请提供以下信息：
- 操作系统版本
- Python版本
- 错误信息截图
- 完整的错误日志

## ✅ 安装成功标志

当看到以下信息时，表示安装成功：
```
✅ AI配置数据库初始化成功
 * Serving Flask app 'ai_web_app'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
 * Running on http://192.168.x.x:5001
```

现在可以通过浏览器访问应用，开始使用功能测试用例生成器！

---

**安装指南版本**: v1.0  
**最后更新**: 2025年6月19日  
**适用版本**: 功能测试用例生成器 v3.0 Professional Edition
