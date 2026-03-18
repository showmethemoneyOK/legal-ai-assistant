# Legal AI Assistant (本地法律文书AI助手)

这是一个基于 Python 的本地化法律文书 AI 助手，专为律师和律所设计。它集成了本地向量数据库（ChromaDB）、SQLite 数据库、FastAPI 后端服务和 PyQt6 桌面客户端，实现了法律文书的智能检索、生成和管理功能。

## 🌟 核心特性

*   **完全本地化**: 所有数据（包括向量库、数据库、文档）均存储在本地，确保数据安全和隐私。
*   **向量检索**: 基于 ChromaDB 构建法律条文和私有文档的向量索引，支持语义检索。
*   **智能更新**:
    *   **全量重建**: 支持一键重建整个公共法律向量库。
    *   **单文件增量更新**: 支持针对单个法律文件（如《民法典》修订）进行增量更新，无需重建整个库。
*   **多用户管理**: 内置用户系统和权限管理，支持文档的私有化存储和授权共享。
*   **多智能体工作流 (Multi-Agent Workflow)**:
    *   **Parser Agent**: 智能解析用户意图，提取关键词，支持文件路径输入
    *   **Search Agent**: 基于向量数据库进行语义检索，查找相关法律条款
    *   **Analysis Agent**: 风险审查与合规性分析，提供专业法律建议
    *   **Orchestrator**: 基于 LangGraph 的任务协调器，管理多智能体协作流程
*   **可视化界面**: 提供基于 PyQt6 的桌面客户端，操作便捷，包含专门的多智能体工作流界面。

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
*   **智能体框架**: LangGraph (工作流编排), LangChain (Agent基础)
*   **AI模型**: 支持本地/云端 LLM (通过 LLMFactory 统一接口)

## 📂 目录结构

```
legal_ai/
├── api/                 # FastAPI 接口层
│   ├── routes/          # 路由定义 (auth, doc, vector, agent)
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
│   ├── widgets/         # 自定义组件 (向量库管理, 智能体工作流)
│   ├── login_window.py  # 登录窗口
│   └── main_window.py   # 主窗口
├── service/             # 业务逻辑层
│   ├── auth_service.py  # 用户认证服务
│   ├── doc_service.py   # 文档管理服务
│   ├── law_service.py   # 法条解析与分块服务
│   ├── vector_service.py # 向量库核心服务 (重建/更新/检索)
│   ├── agent_service/   # 基础智能体实现
│   │   ├── base_agent.py    # 智能体基类
│   │   ├── search_agent.py  # 检索智能体
│   │   └── analysis_agent.py # 分析智能体
│   └── agents/          # 多智能体工作流
│       ├── __init__.py
│       └── multi_agent_orchestrator.py # LangGraph 协调器
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
3.  **多智能体工作流**:
    *   进入 "Agent Workflow" 标签页。
    *   输入法律问题或文档文件路径（支持 `.docx` 和 `.pdf` 格式）。
    *   点击 "Test Agent Flow" 启动多智能体分析流程。
    *   系统将自动执行：意图解析 → 法律检索 → 风险分析 → 综合建议。

## 📝 开发文档

### 多智能体架构设计

系统采用基于 **LangGraph** 的多智能体工作流，实现法律问题的端到端分析：

```
用户输入
    ↓
[Parser Agent] - 解析意图，提取关键词，支持文件输入
    ↓
[Search Agent] - 基于向量数据库检索相关法律条款
    ↓
[Analysis Agent] - 风险审查与合规性分析
    ↓
[Orchestrator] - 协调流程，生成综合建议
    ↓
最终答案
```

#### 智能体职责：
1.  **Parser Agent**: 
    - 识别用户意图（咨询、审查、起草等）
    - 提取关键法律概念和搜索关键词
    - 支持直接输入文件路径，自动解析文档内容

2.  **Search Agent**:
    - 基于 ChromaDB 向量数据库进行语义检索
    - 返回最相关的法律条款和案例
    - 支持多轮检索和结果精炼

3.  **Analysis Agent**:
    - 评估法律风险等级
    - 提供合规性建议
    - 生成结构化分析报告

4.  **Orchestrator**:
    - 基于 LangGraph 的工作流协调器
    - 管理智能体间的状态传递
    - 处理异常和重试逻辑

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

## 🔌 API 接口

### 多智能体工作流接口

**端点**: `POST /api/agent/run`

**请求体**:
```json
{
  "question": "劳动合同解除的经济补偿金计算标准是什么？"
}
```

**响应**:
```json
{
  "final_answer": "根据《劳动合同法》第四十六条、第四十七条规定...",
  "parsed_info": {
    "intent": "法律咨询",
    "keywords": ["劳动合同", "解除", "经济补偿金", "计算标准"],
    "file_path": null
  },
  "retrieved_docs": [
    {
      "content": "《劳动合同法》第四十六条...",
      "source": "劳动合同法.docx",
      "relevance_score": 0.92
    }
  ],
  "analysis_result": "风险等级：低。建议：..."
}
```

**支持文件输入**:
可以直接传入文件路径，系统会自动解析文档内容：
```json
{
  "question": "C:/path/to/legal_document.docx"
}
```

### 其他核心接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/vector/search` - 向量检索
- `POST /api/vector/rebuild` - 重建向量库
- `POST /api/vector/update-file` - 更新单个文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 📄 许可证

MIT License
