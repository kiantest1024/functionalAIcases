# 功能测试用例生成器

## 项目简介

AI增强的功能测试用例生成器，支持多种测试方法和真实AI集成，能够自动生成高质量、全覆盖的功能测试用例。

## 核心功能

- 🤖 **AI增强生成** - 集成多种AI服务（OpenAI、Claude、通义千问等）
- 📊 **多种测试方法** - 支持10种测试类型（等价类、边界值、场景法等）
- 🌐 **Web界面操作** - 友好的Web界面，操作简单
- 📁 **多格式导出** - Excel/Markdown格式导出，包含完整标题
- ⚙️ **智能配置管理** - 支持多AI服务配置和自动降级
- 🎯 **100%标题覆盖** - 每个测试用例都有清晰的标题和描述

## 快速开始

### 1. 安装依赖

#### Windows用户
```bash
pip install -r requirements.txt
```

#### Linux / macOS
若遇到 numpy / pandas 版本冲突，可尝试：
```bash
pip uninstall numpy pandas -y
pip install "numpy>=1.21.0,<2.0.0" "pandas>=2.0.0"
pip install -r requirements.txt
```

### 2. 配置 MySQL（必需）

应用使用 MySQL 存储 AI 配置、智能模板与用例历史。请复制 `.env.example` 为 `.env` 并填写 `MYSQL_*`。启动 `run.py`、脚本或包内 Web 模块时会通过 `python-dotenv` 自动加载根目录 `.env`；亦可在系统中设置同名环境变量。

首次从旧版 JSON 迁移数据时（在仓库根目录执行）：
```bash
python scripts/migrate_to_mysql.py
```

验证数据库连接与统计：
```bash
python scripts/test_mysql_connection.py
```

### 3. 启动 Web 服务
```bash
python run.py
```

（亦兼容：`python ai_web_app.py` 或 `python -m functional_ai.ai_web_app`）

### 4. 访问界面
打开浏览器访问: http://localhost:5001

### 5. 配置AI服务（可选）
- 访问AI配置页面
- 输入API密钥
- 选择AI服务提供商

### 6. 生成测试用例
- 选择生成方式（专业生成/AI增强/智能模板）
- 输入需求文档
- 选择增强级别
- 点击生成并下载结果

## 核心文件说明

| 位置 | 功能 |
|------|------|
| `run.py` | 推荐启动入口 |
| `ai_web_app.py`（根目录） | 兼容旧习惯的启动入口，等价于 `run.py` |
| `functional_ai/ai_web_app.py` | Flask 应用、路由与生成流程 |
| `functional_ai/strict_ai_generator.py` | 严格 AI 用例生成（功能点 + JSON 校验） |
| `functional_ai/comprehensive_test_generator.py` | 全面测试生成器，10 种测试类型 |
| `functional_ai/ai_test_generator.py` | AI 增强分析与本地生成逻辑 |
| `functional_ai/real_ai_generator.py` | 真实 AI API 调用与多厂商适配 |
| `functional_ai/professional_test_generator.py` / `professional_ai_prompt.py` | 专业模式与提示词 |
| `functional_ai/test_case_generator.py` / `test_step_optimizer.py` | 用例模型、导出与步骤优化 |
| `functional_ai/ai_config_manager_mysql.py` | AI 配置读写（MySQL） |
| `functional_ai/mysql_db_manager.py` | MySQL 连接、表结构与业务数据 |
| `functional_ai/ai_config_manager.py` | 旧版 SQLite 配置管理（参考用） |
| `functional_ai/translations.py` | 中英界面文案 |
| `functional_ai/paths.py` | `PROJECT_ROOT`，统一解析模板/上传/输出等路径 |
| `scripts/migrate_to_mysql.py` | 从 `config/`、`data/` 下 JSON 迁移到 MySQL |
| `scripts/test_mysql_connection.py` | 检查 MySQL 与数据统计 |

## 目录结构

```
functionalAItest/
├── run.py                      # 启动 Web（推荐）
├── ai_web_app.py               # 启动 Web（兼容）
├── requirements.txt
├── .env.example
├── functional_ai/              # 应用 Python 包
│   ├── paths.py
│   ├── ai_web_app.py
│   ├── strict_ai_generator.py
│   ├── mysql_db_manager.py
│   └── ...                     # 其余生成器与配置模块
├── scripts/
│   ├── migrate_to_mysql.py
│   └── test_mysql_connection.py
├── config/                     # AI 配置 JSON/SQLite 等（见 .gitignore）
├── data/                       # 本地 JSON：智能模板、用例历史等（迁移源）
├── templates/                  # Jinja2 模板
├── static/                     # 静态资源（含 .gitkeep）
├── outputs/                    # 生成结果（运行期，默认忽略）
└── uploads/                    # 上传目录（运行期，已忽略）
```

## 功能特性

### 🆔 优化的用例编号格式
- **新格式**: `模块英文简写_子模块英文简写_数字编号`
- **示例**: `personal_info_001`, `user_login_002`, `func_core_003`
- **优势**: 简洁易读、便于国际化、格式统一

### 📝 智能测试步骤优化
- **详细步骤描述**: 自动生成具体、详细的测试步骤
- **备选流程说明**: 明确说明备选流程的触发条件和执行路径
- **具体操作指导**: 包含具体的点击、输入、验证等操作描述
- **功能类型适配**: 根据不同功能类型生成相应的测试步骤

### 🎓 专业测试用例生成器
- **专业标准**: 基于专业测试工程师要求的高质量生成
- **全面需求解析**: 逐字逐句分析，识别显式和隐式功能点
- **多维度测试策略**: 正向、边界、等价类、异常、组合测试
- **10个标准字段**: 完整的专业测试用例格式
- **质量保证**: 完整性、准确性、有效性、可执行性

#### 步骤优化示例
**优化前**:
```
1. 触发备选流程条件
2. 执行备选路径：个人信息
3. 检查响应结果
```

**优化后**:
```
1. 触发备选流程：直接从网址进入个人信息页面（跳过主页导航）
2. 执行备选路径：点击页面右上角用户头像，选择"个人信息"
3. 检查系统响应：验证HTTP状态码为200，响应时间在可接受范围内，返回数据格式正确，无JavaScript错误
```

#### 编号映射规则
| 中文模块 | 英文简写 | 示例 |
|----------|----------|------|
| 个人中心 | personal | personal_info_001 |
| 用户管理 | user | user_login_002 |
| 功能测试 | func | func_core_003 |
| 界面测试 | ui | ui_element_004 |
| 数据验证 | data | data_required_005 |
| 业务流程 | biz | biz_complete_006 |
| 异常处理 | error | error_network_007 |
| 性能测试 | perf | perf_response_008 |
| 安全测试 | sec | sec_auth_009 |
| 兼容性测试 | compat | compat_browser_010 |

### 测试类型支持
1. **功能测试** - 核心功能、边界功能、功能组合
2. **界面测试** - 界面元素、交互功能、响应式设计、可访问性
3. **数据验证** - 必填验证、格式验证、长度验证、特殊字符
4. **业务流程** - 完整流程、业务规则、流程恢复
5. **异常处理** - 网络异常、服务器异常、数据异常、并发异常
6. **性能测试** - 响应时间、并发性能、内存使用
7. **安全测试** - 权限验证、输入安全、会话安全
8. **兼容性测试** - 浏览器兼容、操作系统兼容
9. **易用性测试** - 用户体验、操作效率
10. **回归测试** - 历史缺陷验证

### AI服务支持
- **OpenAI** - GPT-3.5/GPT-4
- **Anthropic** - Claude系列
- **阿里云** - 通义千问
- **百度** - 文心一言
- **腾讯** - 混元大模型
- **智谱AI** - ChatGLM

### 输出格式
- **Excel格式** - 包含完整的测试用例信息和标题
- **Markdown格式** - 便于阅读和分享的报告格式
- **统计报告** - 测试覆盖度和方法分布统计

## 使用说明

### 基本使用
1. 启动 Web 服务：`python run.py`
2. 访问 http://localhost:5001
3. 在AI生成页面输入需求文档
4. 选择AI增强级别（基础/中等/高级）
5. 可选输入历史缺陷信息
6. 点击生成测试用例
7. 下载Excel和Markdown格式的结果

### AI配置
1. 访问AI配置页面
2. 选择AI服务提供商
3. 输入API密钥和相关配置
4. 测试连接并保存配置
5. 系统会自动使用配置的AI服务

### 高级功能
- **批量生成** - 支持多个需求文档批量处理
- **模板功能** - 预定义的需求模板
- **智能模板** - AI辅助的需求分析和模板生成

## 技术特性

- **智能降级** - AI服务不可用时自动切换到本地生成
- **错误恢复** - 完善的错误处理和恢复机制
- **配置管理** - 支持多种AI服务的配置和切换
- **文件管理** - 自动文件清理和备份机制
- **性能优化** - 高效的测试用例生成算法

## 系统要求

- **Python** 3.8+
- **依赖**：见 `requirements.txt`（Flask、pandas、requests、openpyxl、PyMySQL 等）

## 配置说明

### MySQL
连接参数通过环境变量提供（推荐复制 `.env.example` 为 `.env` 后按需填写）：

| 变量 | 说明 |
|------|------|
| `MYSQL_HOST` | 主机，默认 `localhost` |
| `MYSQL_PORT` | 端口，默认 `3306` |
| `MYSQL_USER` | 用户名，默认 `root` |
| `MYSQL_PASSWORD` | 密码 |
| `MYSQL_DATABASE` | 库名，默认 `test_case_generator` |

`*.svc.cluster.local` 等 Kubernetes 集群内域名**仅在集群 Pod 网络中可解析**。在 Windows/macOS 本机直接运行 `run.py` 时，请使用 `kubectl port-forward` 将 MySQL 服务转到本机，并把 `.env` 中的 `MYSQL_HOST` 设为 `127.0.0.1`、`MYSQL_PORT` 设为转发端口（详见 `.env.example` 注释）。

首次部署若仍有旧版 JSON，可运行 `python scripts/migrate_to_mysql.py` 导入后再通过 Web 管理配置。迁移脚本会优先读取 `data/test_config.json` 与 `data/test_case_history.json`，若不存在则回退到仓库根目录下的旧文件名。

### AI 服务配置
优先在 Web 端「AI 配置」页面保存（数据写入 MySQL）。迁移或离线场景下也可编辑 `config/ai_config.json` 后执行迁移脚本。

示例 JSON 字段：

```json
{
    "provider": "openai",
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo"
}
```

### 支持的 AI 服务
- **OpenAI**、**Claude**、**通义千问** 等：在界面中配置对应 API 密钥与模型即可（具体厂商以 `real_ai_generator.py` 中枚举为准）。

## 常见问题

### Q: 如何配置AI服务？
A: 访问Web界面的AI配置页面，输入相应的API密钥和配置信息。

### Q: AI服务不可用怎么办？
A: 系统会自动降级到本地生成器，确保功能正常使用。

### Q: 如何提高测试用例质量？
A: 1) 配置AI服务 2) 提供详细的需求文档 3) 输入历史缺陷信息

### Q: 支持哪些输出格式？
A: 支持Excel和Markdown两种格式，都包含完整的测试用例信息。

## 更新日志

### v2.0 (当前版本)
- ✅ 添加了完整的测试用例标题支持
- ✅ 实现了10种测试类型的全覆盖
- ✅ 集成了真实AI服务
- ✅ 优化了Web界面和用户体验
- ✅ 完善了错误处理和降级机制
- ✅ MySQL 存储配置与历史；连接信息改为环境变量，避免密钥写入代码库
- ✅ 清理调试脚本与临时 JSON/文本产物，文档与目录说明与仓库一致
- ✅ 应用代码归入 `functional_ai/` 包，脚本归入 `scripts/`，本地数据归入 `data/`，根目录保留 `run.py` 启动入口

### v1.0
- 基础测试用例生成功能
- 简单的Web界面
- Excel导出功能

## 许可证

MIT License

## 支持

说明与排错以本 README 为准；数据库与迁移细节见上文「配置说明」与 `migrate_to_mysql.py` 注释。
