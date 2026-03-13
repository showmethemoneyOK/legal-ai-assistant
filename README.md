# Legal AI Assistant (本地法律文书AI助手)

这是一个基于 Python 的本地化法律文书 AI 助手，专为律师和律所设计。它集成了本地向量数据库（ChromaDB）、SQLite 数据库、FastAPI 后端服务和 PyQt6 桌面客户端，实现了法律文书的智能检索、生成和管理功能。

## 🌟 核心特性

*   **完全本地化**: 所有数据（包括向量库、数据库、文档）均存储在本地，确保数据安全和隐私。
*   **向量检索**: 基于 ChromaDB 构建法律条文和私有文档的向量索引，支持语义检索。
*   **智能更新**:
    *   **全量重建**: 支持一键重建整个公共法律向量库。
    *   **单文件增量更新**: 支持针对单个法律文件（如《民法典》修订）进行增量更新，无需重建整个库。
*   **多用户管理**: 内置用户系统和权限管理，支持文档的私有化存储和授权共享。
*   **多模型协作 (Multi-Agent)**:
    *   **Search Agent**: 智能检索法律条款。
    *   **Analysis Agent**: 风险审查与合规性分析。
    *   **Orchestrator**: 协调任务流，支持本地/线上模型切换。
*   **可视化界面**: 提供基于 PyQt6 的桌面客户端，操作便捷。

## 📚 详细文档

请参阅 [项目技术文档](docs/project_documentation.md) 获取更详细的架构说明和开发指南。
也可以查看 [多 Agent 设计文档](docs/multi_agent_design.md) 了解系统演进方向。

## 🛠 技术栈

*   **语言**: Python 3.10+
*   **GUI 框架**: PyQt6
*   **后端框架**: FastAPI
*   **数据库**: SQLite (关系型数据), ChromaDB (向量数据)
*   **文档解析**: python-docx, pdfplumber
*   **ORM**: SQLAlchemy

## 📂 目录结构

```
legal_ai/
├── api/                 # FastAPI 接口层
│   ├── routes/          # 路由定义 (auth, doc, vector)
│   └── server.py        # 服务启动入口
├── core/                # 核心配置
│   ├── config.py        # 路径与环境配置
│   └── database.py      # 数据库连接会话
├── data/                # 数据存储目录
│   └── public_law/      # 公共法律法规文件 (.docx, .pdf)
├── db/                  # 数据库模型与存储
│   ├── models.py        # SQLAlchemy 模型定义
│   └── app.db           # SQLite 数据库文件 (自动生成)
├── gui/                 # PyQt6 界面层
│   ├── widgets/         # 自定义组件 (如向量库管理)
│   ├── login_window.py  # 登录窗口
│   └── main_window.py   # 主窗口
├── service/             # 业务逻辑层
│   ├── auth_service.py  # 用户认证服务
│   ├── doc_service.py   # 文档管理服务
│   ├── law_service.py   # 法条解析与分块服务
│   └── vector_service.py # 向量库核心服务 (重建/更新/检索)
├── vector_db/           # 向量数据库存储目录
│   └── chroma_db/       # ChromaDB 持久化文件
├── main.py              # 项目启动入口
└── requirements.txt     # 项目依赖
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.10 或更高版本。

```bash
# 克隆或下载本项目到本地
cd legal_ai

# 创建虚拟环境 (可选但推荐)
python -m venv venv
# Windows 激活虚拟环境
venv\Scripts\activate
# Linux/Mac 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备数据

将您的法律法规文件（支持 `.docx` 和 `.pdf` 格式）放入 `legal_ai/data/public_law/` 目录中。系统会自动扫描该目录下的文件构建向量库。

### 3. 运行程序

在项目根目录下运行启动脚本：

```bash
python main.py
```

该命令将同时启动：
1.  **FastAPI 后端服务**: 运行在 `http://127.0.0.1:8000`
2.  **桌面客户端**: 自动弹出登录窗口

### 4. 使用说明

1.  **注册/登录**: 首次使用请在登录窗口点击 "Register" 注册新用户，然后登录。
2.  **向量库管理**:
    *   进入 "Vector DB Manager" 标签页。
    *   点击 **"Rebuild Public Vector DB (Full)"** 初始化或重建整个公共法律库。
    *   若需更新单个文件，在 "Single File Update" 区域选择文件路径并点击 "Update File"。
    *   在 "Search Test" 区域输入法律问题进行语义检索测试。

## 📝 开发文档

### 向量库更新机制

*   **全量重建 (`rebuild_public_vector_db`)**:
    1.  清空 ChromaDB 中的 `public_law` 集合。
    2.  清空 SQLite 中的 `public_law_files` 表。
    3.  遍历 `data/public_law` 目录，逐个解析文件。
    4.  计算文件哈希，文本分块，生成向量并存入 ChromaDB。
    5.  记录文件元数据到 SQLite。

*   **单文件更新 (`update_single_file_in_public_db`)**:
    1.  根据文件路径查询 SQLite，获取旧文件的元数据。
    2.  在 ChromaDB 中根据 `file_path` 删除旧向量。
    3.  重新解析目标文件，生成新向量并插入 ChromaDB。
    4.  更新 SQLite 中的文件记录和哈希值。

### 数据库设计

主要数据表包括：
*   `sys_user`: 用户表
*   `legal_doc`: 文书表
*   `doc_version`: 文书版本历史
*   `public_law_files`: 公共法律文件索引状态
*   `vector_log`: 向量库操作日志

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 📄 许可证

MIT License
