# Legal AI Assistant - Multi-Agent Integration Strategy

本文档详细描述了如何将多 Agent 架构集成到现有的 `legal_ai` 系统中，以增强法律文书分析、生成和审查的智能化水平。

## 1. 架构概览

我们将采用 **分层协作 (Hierarchical Collaboration)** 模式，引入一个中央协调器 (Coordinator) 来管理多个专业 Agent。

### 1.1 核心组件

1.  **Orchestrator (协调器 Agent)**:
    *   **职责**: 接收用户请求，理解意图，分解任务，调度子 Agent，汇总结果。
    *   **实现**: 基于 LLM (如 GPT-4, Claude 3 或本地大模型) 的核心控制单元。

2.  **Specialized Agents (专业 Agent)**:
    *   **Search Agent (检索专家)**:
        *   **工具**: `vector_service.search_public_law`
        *   **任务**: 根据自然语言问题，构建高效的检索策略，从向量库中提取相关法条和案例。
    *   **Analysis Agent (法律分析师)**:
        *   **输入**: 用户文书 + Search Agent 提供的法条。
        *   **任务**: 识别文书中的风险点，引用法条进行论证，提供修改建议。
    *   **Drafting Agent (文书起草专家)**:
        *   **输入**: 用户需求 + 法条/模板。
        *   **任务**: 生成结构严谨、用词专业的法律文书草稿。
    *   **Review Agent (审核专家)**:
        *   **输入**: Drafting Agent 的产出。
        *   **任务**: 进行二次校验，确保无逻辑漏洞和格式错误。

3.  **Shared Context (共享上下文)**:
    *   使用 Redis 或内存数据库存储当前会话的状态、中间结果和 Agent 间的消息历史。

## 2. 集成路径 (Roadmap)

### Phase 1: 基础架构搭建 (Infrastructure)
*   [x] **Agent Base Class**: 定义 Agent 的通用接口 (输入、输出、状态管理)。
*   [x] **LLM Gateway**: 统一管理 LLM 调用接口 (支持 OpenAI API 格式及本地模型)。
    *   **Configuration**: `legal_ai/core/config.py` 支持 `LLM_PROVIDER` ("openai", "local")。
    *   **Implementation**: `legal_ai/core/llm.py` 提供 `LLMProvider` 抽象类和 `OpenAIProvider`/`LocalLLMProvider` 实现。
*   [ ] **Tool Interface**: 将现有的 `vector_service` 封装为标准的 Agent Tool。

### Phase 2: 核心 Agent 实现 (Core Implementation)
*   [ ] **Search Agent**: 实现智能检索，支持多轮追问以澄清检索意图。
*   [ ] **Analysis Agent**: 集成 Prompt Engineering，专注于合同审查场景。

### Phase 3: 协调与工作流 (Orchestration)
*   [ ] **Router**: 实现简单的路由逻辑，根据用户输入判断调用哪个 Agent。
*   [ ] **Workflow Engine**: 定义标准的 "检索 -> 分析 -> 生成" 工作流。

## 3. 技术方案细节

### 3.1 Agent 定义示例 (Python)

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseAgent(ABC):
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    async def run(self, input_text: str, context: Dict) -> str:
        pass

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("SearchAgent", "gpt-4")
        
    async def run(self, input_text: str, context: Dict) -> str:
        # 1. 分析查询意图
        # 2. 调用 vector_service.search_public_law
        # 3. 总结检索结果
        pass
```

### 3.2 交互流程示例 (Sequence)

1.  **User**: "帮我看看这份劳动合同有没有风险，特别是关于试用期的条款。"
2.  **Orchestrator**: 识别意图 -> 任务类型: `Risk Review`。
3.  **Orchestrator** -> **Search Agent**: "检索关于劳动合同试用期的相关法律规定。"
4.  **Search Agent**: 返回《劳动合同法》第十九条等内容。
5.  **Orchestrator** -> **Analysis Agent**: "结合上述法条，审查用户上传的合同文本中的试用期条款。"
6.  **Analysis Agent**: 输出风险报告："合同中约定试用期为 1 年，违反《劳动合同法》第十九条（最长不超过 6 个月），建议修改为..."
7.  **Orchestrator**: 将最终报告返回给用户。

## 4. 推荐工具库

*   **LangChain**: 最成熟的 Agent 编排框架，拥有丰富的 Tool 生态。
*   **AutoGen (Microsoft)**: 擅长多 Agent 对话协作，适合复杂任务解决。
*   **LlamaIndex**: 在 RAG (检索增强生成) 方面表现优异，适合 Search Agent 的构建。

## 5. 下一步行动建议

1.  在 `legal_ai/service/` 下创建 `agent_service` 目录。
2.  引入 `langchain` 或 `openai` SDK。
3.  实现第一个 MVP: **智能法条检索助手** (Orchestrator + Search Agent)。
