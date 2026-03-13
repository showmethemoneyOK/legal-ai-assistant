# Legal AI Assistant - 项目技术文档

## 1. 项目简介 (Overview)

**Legal AI Assistant** 是一款专为法律专业人士设计的本地化智能辅助工具。它结合了先进的自然语言处理 (NLP)、向量检索 (RAG) 和多模型协作 (Multi-Agent) 技术，旨在提供高效、安全、准确的法律文书分析、生成和检索服务。

### 核心价值
*   **隐私安全**: 核心数据（文档、向量库）完全本地化存储，支持断网运行。
*   **多模型协作**: 支持同时接入 OpenAI 线上模型（用于复杂推理）和 Ollama 本地模型（用于隐私数据处理）。
*   **专业检索**: 基于 ChromaDB 构建法律法规专用知识库，提供语义级精准检索。
*   **智能工作流**: 通过 Orchestrator 协调多个专门 Agent（检索、分析、起草）完成复杂任务。

## 2. 系统架构 (System Architecture)

系统采用分层架构设计，各模块松耦合，易于扩展。

```mermaid
graph TD
    User[用户 (GUI/API)] --> API[FastAPI 接口层]
    API --> Orchestrator[Agent 协调器]
    
    subgraph "Agent Service (多 Agent 系统)"
        Orchestrator --> SearchAgent[检索 Agent]
        Orchestrator --> AnalysisAgent[分析 Agent]
        Orchestrator --> DraftingAgent[起草 Agent (待实现)]
    end
    
    subgraph "Core Services (核心服务)"
        SearchAgent --> VectorService[向量检索服务]
        AnalysisAgent --> LLMFactory[LLM 模型网关]
        VectorService --> ChromaDB[(Chroma 向量库)]
        VectorService --> LawParser[法条解析器]
    end
    
    subgraph "Infrastructure (基础设施)"
        LLMFactory --> OpenAI[OpenAI API]
        LLMFactory --> LocalLLM[Ollama/Local API]
        AuthService[认证服务] --> SQLite[(SQLite 数据库)]
    end
```

### 2.1 模块说明
*   **GUI (`legal_ai/gui`)**: 基于 PyQt6 的桌面客户端，提供登录、向量库管理、对话交互界面。
*   **API (`legal_ai/api`)**: 基于 FastAPI 的 RESTful 接口，处理前端请求。
*   **Service (`legal_ai/service`)**: 业务逻辑层，包括文档管理、认证、向量处理和 Agent 逻辑。
*   **Core (`legal_ai/core`)**: 核心配置、数据库连接、LLM 工厂等基础组件。
*   **DB (`legal_ai/db`)**: SQLAlchemy ORM 模型定义及 SQLite 数据库文件。

## 3. 核心功能详解 (Core Features)

### 3.1 多模型网关 (LLM Gateway)
*   **位置**: `legal_ai/core/llm.py`
*   **功能**: 统一管理不同 LLM 提供商的调用接口。
*   **实现**:
    *   `LLMProvider`: 抽象基类，定义 `chat` 和 `generate` 接口。
    *   `OpenAIProvider`: 对接官方 API。
    *   `LocalLLMProvider`: 对接本地兼容接口 (Ollama, vLLM)。
    *   `LLMFactory`: 工厂模式，支持通过配置 (`config.py`) 或动态参数创建实例。
*   **配置**: 支持 `LLM_PROVIDER` ("openai"/"local") 全局切换，也支持代码级动态指定。

### 3.2 向量检索系统 (Vector Search)
*   **位置**: `legal_ai/service/vector_service.py`
*   **功能**: 管理法律法规的向量索引。
*   **特性**:
    *   **全量重建**: 清空并重新扫描 `data/public_law` 目录。
    *   **增量更新**: 基于文件哈希 (SHA-256) 检测变更，仅更新变动文件。
    *   **文本分块**: 使用 `chunk_text` (500字符/块，50重叠) 优化检索粒度。
*   **存储**: ChromaDB (本地持久化)。

### 3.3 多 Agent 系统 (Multi-Agent System)
*   **位置**: `legal_ai/service/agent_service/`
*   **架构**:
    *   **BaseAgent**: 所有 Agent 的基类，集成 LLM 实例。
    *   **SearchAgent**:
        *   **工具**: `vector_service`
        *   **逻辑**: 接收自然语言 -> (可选: LLM 提炼关键词) -> 向量检索 -> 格式化输出。
    *   **AnalysisAgent**:
        *   **输入**: 待审文档 + 相关法条。
        *   **逻辑**: 使用预设 Prompt (`legal_ai/service/agent_service/analysis_agent.py`) 进行风险识别和合规性审查。
    *   **Orchestrator**:
        *   **职责**: 任务调度中枢。目前实现标准工作流：`Search -> (Document Review ? Analyze : QA)`。

### 3.4 用户认证与安全 (Authentication)
*   **位置**: `legal_ai/service/auth_service.py`
*   **机制**:
    *   密码存储: bcrypt 哈希 (使用 `passlib`)。
    *   参数校验: Pydantic 模型 (`legal_ai/api/routes/auth.py`) 严格限制用户名/密码长度，防止 DoS 攻击和后端异常。

## 4. 数据模型 (Data Models)

主要数据库表 (`legal_ai/db/models.py`):

1.  **User**: 用户信息 (id, username, hashed_password)。
2.  **LegalDoc**: 用户私有文档 (title, content, owner_id)。
3.  **DocVersion**: 文档版本历史 (doc_id, content, operator_id)。
4.  **PublicLawFile**: 公共法条文件索引状态 (file_path, file_hash, status)。
5.  **VectorLog**: 向量库操作审计日志。

## 5. 接口文档 (API Reference)

### Auth
*   `POST /api/user/register`: 用户注册 (校验密码长度 6-72)。
*   `POST /api/user/login`: 用户登录 (返回 Access Token)。

### Vector
*   `POST /api/vector/rebuild`: 重建公共向量库。
*   `POST /api/vector/update_single`: 更新单文件索引。
*   `POST /api/vector/search`: 语义检索测试。

### Doc (待完善)
*   `POST /api/doc/`: 创建文档。
*   `GET /api/doc/{id}`: 获取文档详情。

## 6. 部署与配置 (Deployment)

### 环境要求
*   Python 3.10+
*   依赖库: `requirements.txt` (含 `openai`, `fastapi`, `chromadb`, `pyqt6` 等)

### 配置文件
修改 `legal_ai/core/config.py` 或设置环境变量：

```python
# LLM 选择
LLM_PROVIDER = "local"  # 或 "openai"

# OpenAI 配置
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL_NAME = "gpt-4"

# 本地模型配置 (Ollama)
LOCAL_LLM_API_BASE = "http://localhost:11434/v1"
LOCAL_MODEL_NAME = "llama3"
```

### 启动方式
```bash
# 同时启动 API 服务和 GUI 客户端
python main.py
```

## 7. 未来规划 (Roadmap)
*   [ ] **Drafting Agent**: 实现基于模板和法条的文书自动生成。
*   [ ] **Review Agent**: 引入多轮审核机制。
*   [ ] **前端集成**: 在 PyQt6 界面中增加 "智能助手" 对话框，对接 Orchestrator。
