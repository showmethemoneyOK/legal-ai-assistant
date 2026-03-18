# Legal AI Assistant (本地法律文书AI助手)

这是一个基于 Python 的本地化法律文书 AI 助手，专为律师和律所设计。它集成了本地向量数据库（ChromaDB）、SQLite 数据库、FastAPI 后端服务和 PyQt6 桌面客户端，实现了法律文书的智能检索、生成和管理功能。

## 🌟 核心特性

*   **完全本地化**: 所有数据（包括向量库、数据库、文档）均存储在本地，确保数据安全和隐私。
*   **向量检索**: 基于 ChromaDB 构建法律条文和私有文档的向量索引，支持语义检索。
*   **智能更新**:
    *   **全量重建**: 支持一键重建整个公共法律向量库。
    *   **单文件增量更新**: 支持针对单个法律文件（如《民法典》修订）进行增量更新，无需重建整个库。
*   **多用户管理**: 内置用户系统和权限管理，支持文档的私有化存储和授权共享。
*   **专业级多智能体工作流 (Professional Multi-Agent Workflow)**:
    *   **文件上传界面**: 支持 `.docx` 和 `.pdf` 文件直接上传
    *   **角色提示词系统**: 为每个智能体角色定义专业的系统提示词
    *   **三方投票机制**: 资深合伙人、初级律师、合规专家协同决策
    *   **质量验证循环**: 自动验证分析质量，支持迭代改进
    *   **执行日志系统**: 完整记录工作流执行过程
*   **可视化界面**: 提供基于 PyQt6 的桌面客户端，包含文件上传和多智能体工作流界面。

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
*   **配置管理**: YAML (角色提示词配置)
*   **数据验证**: Pydantic (结构化输出验证)
*   **AI模型**: 支持 OpenAI API 兼容接口，默认使用 GLM-4 模型，可通过 LLMFactory 切换其他模型
*   **工作流引擎**: 基于 LangGraph 的状态机，支持条件分支和循环

## 📂 目录结构

```
legal_ai/
├── api/                 # FastAPI 接口层
│   ├── routes/          # 路由定义 (auth, doc, vector, agent)
│   └── server.py        # 服务启动入口
├── core/                # 核心配置
│   ├── config.py        # 路径与环境配置 (支持GLM-4等模型)
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
│   └── agents/          # 专业级多智能体工作流
│       ├── __init__.py
│       ├── multi_agent_orchestrator.py # LangGraph 协调器 (支持质量验证循环)
│       └── prompts/     # 角色提示词配置
│           └── role_prompts.yaml # 专业角色系统提示词
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

### 2. 配置 AI 模型

系统默认使用 GLM-4 模型，通过 OpenAI API 兼容接口调用。确保您的本地或远程模型服务正常运行：

```bash
# 默认配置使用 http://localhost:11434/v1 (Ollama 兼容接口)
# 如需修改模型配置，编辑 core/config.py:
# LLM_PROVIDER = "openai"  # 使用OpenAI兼容接口
# OPENAI_MODEL_NAME = "glm4:latest"  # 使用GLM-4模型
# OPENAI_API_BASE = "http://localhost:11434/v1"  # Ollama API地址
```

### 3. 准备数据

将您的法律法规文件（支持 `.docx` 和 `.pdf` 格式）放入 `legal_ai/data/public_law/` 目录中。系统会自动扫描该目录下的文件构建向量库。

### 4. 运行程序

在项目根目录下运行启动脚本：

```bash
python main.py
```

该命令将同时启动：
1.  **FastAPI 后端服务**: 运行在 `http://127.0.0.1:8000`
2.  **桌面客户端**: 自动弹出登录窗口

### 5. 使用说明

1.  **注册/登录**: 首次使用请在登录窗口点击 "Register" 注册新用户，然后登录。
2.  **向量库管理**:
    *   进入 "Vector DB Manager" 标签页。
    *   点击 **"Rebuild Public Vector DB (Full)"** 初始化或重建整个公共法律库。
    *   若需更新单个文件，在 "Single File Update" 区域选择文件路径并点击 "Update File"。
    *   在 "Search Test" 区域输入法律问题进行语义检索测试。
3.  **专业多智能体工作流**:
    *   进入 "Agent Workflow" 标签页。
    *   输入法律问题或点击 "Upload File" 按钮选择 `.docx`/`.pdf` 文档。
    *   点击 "Test Agent Flow" 启动专业多智能体分析流程。
    *   系统将自动执行完整工作流，包含质量验证和迭代改进。

## 📝 开发文档

### 专业多智能体架构设计

系统采用基于 **LangGraph** 的专业级多智能体工作流，实现法律问题的端到端智能分析，支持质量验证和迭代改进：

```
用户输入 (文本或文件)
    ↓
[Parser Node] - 解析意图，提取关键词，支持文件内容解析
    ↓
[Goal Voter Node] - 三方专业投票 (资深合伙人、初级律师、合规专家)
    ↓
[Planner Node] - 专业任务分解，生成执行计划
    ↓
[Node Voter Node] - 计划评审与优化
    ↓
[Executor Node] - 并行执行子任务，调用专业角色
    ↓
[Result Voter Node] - 首席律师综合报告
    ↓
[Verifier Node] - 质量验证 (评分<7则循环改进)
    ↻ (最多3次循环)
    ↓
[Output Node] - 格式化最终输出
    ↓
专业法律建议报告
```

#### 专业智能体角色系统：

系统定义了 8 个专业角色，每个角色都有专门的任务和系统提示词：

1.  **ParserAgent** (解析员):
    - 提取关键法律概念和搜索关键词
    - 识别用户意图和文档类型
    - 生成结构化解析信息

2.  **SeniorPartner** (资深合伙人):
    - 从战略和商业角度分析
    - 关注重大商业风险和法律策略
    - 确定分析优先级和范围

3.  **JuniorAssociate** (初级律师):
    - 从法律细节和程序角度分析
    - 关注具体法律条文和合规要求
    - 提供详细的法律研究视角

4.  **ComplianceSpecialist** (合规专家):
    - 从监管合规角度分析
    - 识别合规风险和监管要求
    - 提供合规性评估和建议

5.  **PlannerAgent** (规划员):
    - 基于共识目标制定执行计划
    - 将复杂任务分解为 2-4 个子任务
    - 为每个子任务分配合适的专业角色

6.  **RiskAssessor** (风险评估师):
    - 识别和评估法律与商业风险
    - 基于相关法律条文进行风险评估
    - 提供风险等级和建议

7.  **ContractReviewer** (合同审查员):
    - 细致审查合同文档内容
    - 对照法律条文确保有效性
    - 保护客户利益，识别潜在问题

8.  **LeadAttorney** (首席律师):
    - 综合各子任务分析结果
    - 生成结构化、专业的法律报告
    - 确保报告直接回应客户目标

9.  **VerifierAgent** (质量验证员):
    - 严格验证分析结果质量
    - 评分标准：法律准确性(40%)、风险覆盖(30%)、引用可靠性(20%)、逻辑完整性(10%)
    - 决定是否需要迭代改进

### 质量验证与迭代改进机制

系统引入了专业的质量验证循环，确保分析结果的高质量：

#### 验证标准：
- **法律准确性 (40%)**: 结论是否合法合理，是否有法律依据支持
- **风险覆盖 (30%)**: 是否覆盖了目标中隐含的所有主要风险
- **引用可靠性 (20%)**: 法律引用是否恰当、相关、准确
- **逻辑完整性 (10%)**: 报告结构是否清晰，逻辑是否连贯

#### 迭代流程：
1.  **首次执行**: 完整执行工作流，生成初步分析
2.  **质量验证**: VerifierAgent 对结果进行评分（0-10分）
3.  **决策判断**: 
    - 评分 ≥ 7: 通过验证，输出最终结果
    - 评分 < 7: 未通过验证，记录问题和建议
4.  **迭代改进**: 将问题和建议反馈给 Planner，重新规划执行
5.  **循环限制**: 最多循环 3 次，避免无限循环
6.  **最终输出**: 即使未通过验证，第3次循环后也会输出结果（标注"强制输出"）

### 角色提示词系统

系统使用 YAML 文件管理所有角色的专业提示词：

```yaml
ParserAgent:
  system_prompt: |
    You are a legal assistant (Parser Agent). Extract key legal concepts...
    
SeniorPartner:
  system_prompt: |
    You are a Senior Partner in a top-tier law firm. You focus on strategic goals...
    
# ... 其他角色提示词
```

**优势**:
- **集中管理**: 所有提示词在单一文件中管理
- **易于修改**: 无需修改代码即可调整角色行为
- **专业定制**: 每个角色都有针对性的专业提示词
- **错误恢复**: 如果文件加载失败，有默认提示词备用

### 执行日志系统

系统记录完整的执行过程，便于调试和分析：

```python
def _log_execution(state: AgentState, node_name: str, summary: str):
    log_entry = {"node": node_name, "summary": summary}
    state["execution_log"].append(log_entry)
```

**日志包含**:
- 每个节点的执行时间点
- 执行摘要和关键信息
- 错误和异常记录
- 循环次数和验证结果

### 技术实现特点

1.  **状态管理**: 使用 `AgentState` TypedDict 管理整个工作流状态，包含解析信息、投票记录、执行计划、子结果、验证结果、循环计数、执行日志等
2.  **条件分支**: 基于 LangGraph 的条件边实现质量验证循环
3.  **错误处理**: 每个节点都有完善的异常处理机制，确保工作流稳定性
4.  **可扩展性**: 模块化设计，方便添加新的智能体节点或修改现有逻辑
5.  **配置灵活**: 支持多种 AI 模型，可通过环境变量轻松切换

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

### 专业多智能体工作流接口

**端点**: `POST /api/agent/run`

**请求体**:
```json
{
  "question": "劳动合同解除的经济补偿金计算标准是什么？"
}
```

或直接传入文件路径：
```json
{
  "question": "C:/path/to/employment_contract.docx"
}
```

**响应**:
```json
{
  "final_answer": "根据《劳动合同法》第四十六条、第四十七条规定...\n\n---\n**质量保证报告:**\n- 评分: 8/10\n- 状态: 通过\n- 迭代次数: 1\n*由法律AI多智能体系统生成*",
  "parsed_info": {
    "intent": "法律咨询",
    "keywords": ["劳动合同", "解除", "经济补偿金", "计算标准"],
    "file_path": null,
    "is_file_analysis": false
  },
  "goal_consensus": {
    "consensus_intent": "劳动合同解除补偿计算",
    "priority": "High",
    "scope": "Compensation calculation and legal compliance"
  },
  "node_plan": [
    {
      "step_name": "法律条文检索",
      "role": "RiskAssessor",
      "description": "检索劳动合同法相关条款",
      "search_keywords": ["劳动合同法", "解除", "经济补偿"]
    },
    {
      "step_name": "计算标准分析", 
      "role": "ContractReviewer",
      "description": "分析补偿金计算方法和标准",
      "search_keywords": ["补偿金计算", "工资标准", "工作年限"]
    }
  ],
  "retrieved_docs": [
    {
      "content": "《劳动合同法》第四十六条...",
      "source": "劳动合同法.docx",
      "relevance_score": 0.92
    }
  ],
  "analysis_result": "风险等级：低。建议：依法计算，注意保留相关证据。",
  "verifier_result": {
    "score": 8,
    "passed": true,
    "issues": [],
    "suggestions": ["可补充相关司法解释的引用"]
  },
  "vote_records": [
    "Role: SeniorPartner\nAnalysis: 从商业角度...",
    "Role: JuniorAssociate\nAnalysis: 从法律细节角度...", 
    "Role: ComplianceSpecialist\nAnalysis: 从合规风险角度..."
  ],
  "loop_count": 1,
  "execution_log": [
    {"node": "parser", "summary": "Parsing user intent"},
    {"node": "goal_voter", "summary": "Voting on task goals"},
    {"node": "planner", "summary": "Planning execution steps"},
    {"node": "executor", "summary": "Executing planned steps"},
    {"node": "result_voter", "summary": "Synthesizing final report"},
    {"node": "verifier", "summary": "Verifying quality"}
  ]
}
```

### 其他核心接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/vector/search` - 向量检索
- `POST /api/vector/rebuild` - 重建向量库
- `POST /api/vector/update-file` - 更新单个文件

## 🎯 应用场景

### 1. 专业法律咨询
- 快速回答复杂法律问题
- 提供多角度专业分析
- 生成结构化法律意见书

### 2. 合同智能审查
- 自动解析合同文件内容
- 多角色协同识别风险点
- 提供专业修改建议和合规指导

### 3. 合规性深度检查
- 全面检查业务操作的法律合规性
- 识别潜在违规风险点
- 提供风险防控和整改建议

### 4. 法律研究支持
- 快速检索相关法律条文和案例
- 多角度分析法律适用性
- 生成专业研究摘要和报告

### 5. 法律文书起草辅助
- 基于模板生成法律文书
- 智能填充法律条款
- 确保文书合规性和完整性

## 🔧 配置说明

### AI 模型配置
编辑 `core/config.py` 文件：

```python
# LLM 提供商配置
LLM_PROVIDER = "openai"  # 或 "local"
OPENAI_API_KEY = "ollama"  # 使用Ollama时设为"ollama"
OPENAI_MODEL_NAME = "glm4:latest"  # 模型名称
OPENAI_API_BASE = "http://localhost:11434/v1"  # API地址
```

### 角色提示词配置
编辑 `service/agents/prompts/role_prompts.yaml` 文件：

```yaml
# 为每个角色定义专业的系统提示词
ParserAgent:
  system_prompt: |
    You are a legal assistant (Parser Agent)...
    
SeniorPartner:
  system_prompt: |
    You are a Senior Partner in a top-tier law firm...
    
# ... 其他角色配置
```

### 工作流配置
可通过修改 `service/agents/multi_agent_orchestrator.py` 调整：
- 验证评分阈值（默认7分）
- 最大循环次数（默认3次）
- 角色分配逻辑
- 执行日志详细程度

## 📊 性能优化建议

### 1. 向量检索优化
- 确保法律条文分块合理（建议300-500字）
- 定期更新向量库，保持法律时效性
- 优化检索关键词提取算法

### 2. 工作流性能
- 监控各节点执行时间
- 优化提示词长度，减少token消耗
- 考虑并行执行独立子任务

### 3. 质量保证
- 定期审核验证评分标准
- 收集用户反馈优化角色提示词
- 建立测试用例库，确保系统稳定性

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进本项目。贡献前请阅读：

### 代码规范
1. 遵循 PEP 8 代码风格
2. 新增功能需包含单元测试
3. 更新文档以反映代码变更
4. 保持向后兼容性

### 新功能开发
1. **新增智能体角色**:
   - 在 `role_prompts.yaml` 中添加系统提示词
   - 在 `multi_agent_orchestrator.py` 中实现节点逻辑
   - 更新 README.md 文档

2. **修改工作流逻辑**:
   - 确保不影响现有功能
   - 添加相应的测试用例
   - 更新架构图和工作流说明

3. **优化性能**:
   - 提供性能测试数据
   - 说明优化原理和效果
   - 确保不降低分析质量

### 问题反馈
1. 提供详细的问题描述
2. 附上相关日志和错误信息
3. 说明复现步骤和环境信息

## 📄 许可证

MIT License

## 📞 支持与联系

如有问题或建议，请：
1. 查看项目文档和 FAQ
2. 提交 GitHub Issue
3. 联系项目维护者

---

*最后更新: 2026-03-18*  
*版本: 3.0.0 (专业多智能体版本)*  
*特性: 文件上传界面、角色提示词系统、质量验证循环、执行日志*