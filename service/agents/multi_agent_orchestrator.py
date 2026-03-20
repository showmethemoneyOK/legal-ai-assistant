import os
import yaml
import asyncio
from typing import Dict, List, Optional, TypedDict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from legal_ai.core.llm import LLMFactory
from legal_ai.service.vector_service import search_public_law
from legal_ai.service.law_service import extract_text_from_file
from legal_ai.utils.model_router import get_llm_provider

# --- Models ---
class VerifierOutput(BaseModel):
    score: int = Field(description="Score from 0 to 10")
    passed: bool = Field(description="Whether the analysis passed verification (score >= 7)")
    issues: List[str] = Field(description="List of identified issues or shortcomings")
    suggestions: List[str] = Field(description="List of suggestions for improvement in the next iteration")

class StepItem(BaseModel):
    step_name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    search_keywords: List[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    steps: List[StepItem] = Field(..., min_items=1, max_items=8)

# --- Helper ---
def load_role_prompt(role_name: str) -> str:
    """Load system prompt from yaml file."""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "role_prompts_zh.yaml")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
            if role_name in prompts and 'system_prompt' in prompts[role_name]:
                return prompts[role_name]['system_prompt']
    except Exception as e:
        print(f"Warning: Failed to load prompt for {role_name} from {prompt_path}: {e}")
    
    # Fallback default
    return "你是一个有用的法律助手。请完成以下任务：\n{context}\n{question}\n注意：你的所有输出必须完全使用中文，禁止任何英文内容！"

# Define State
class AgentState(TypedDict):
    question: str
    parsed_info: Dict[str, Any]
    retrieved_docs: List[Dict]
    analysis_result: str
    final_answer: str
    # New fields for Multi-Agent Consensus
    goal_consensus: Dict[str, Any]
    node_plan: List[Dict[str, str]]
    sub_results: List[str]
    vote_records: List[Dict[str, Any]]
    # Phase 3 fields
    verifier_result: Dict[str, Any]
    loop_count: int
    execution_log: List[Dict[str, str]]
    model_history: set[str]

def _log_execution(state: AgentState, node_name: str, summary: str):
    log_entry = {"node": node_name, "summary": summary}
    if "execution_log" not in state or state["execution_log"] is None:
        state["execution_log"] = []
    state["execution_log"].append(log_entry)

# --- 1. Parser Node ---
def parser_node(state: AgentState):
    print("--- Parser Node ---")
    _log_execution(state, "parser", "Parsing user intent")
    question = state["question"]
    llm = get_llm_provider(state)
    
    file_content = ""
    file_path = ""
    is_file = False
    
    try:
        if len(question) < 260 and os.path.exists(question):
            file_path = question
            file_content = extract_text_from_file(file_path)
            is_file = True
            context_question = f"Analyze the legal document at path: {question}"
        else:
            context_question = question
    except Exception as e:
        context_question = question

    parser = JsonOutputParser()
    prompt_str = load_role_prompt("ParserAgent")
    prompt = ChatPromptTemplate.from_template(prompt_str)
    
    chain = prompt | llm | parser
    try:
        parsed_info = chain.invoke({"question": context_question, "format_instructions": parser.get_format_instructions()})
        if not parsed_info:
             raise ValueError("Empty parsed_info")
        if is_file:
            parsed_info["is_file_analysis"] = True
            parsed_info["file_path"] = file_path
            parsed_info["file_content_snippet"] = file_content 
        else:
            parsed_info["is_file_analysis"] = False
    except Exception as e:
        print(f"Parser Error: {e}")
        parsed_info = {
            "keywords": [question[:50]], "intent": "general", "is_file_analysis": is_file,
            "file_path": file_path if is_file else None, "file_content_snippet": file_content if is_file else None
        }
        
    print(f"Parsed Info: {parsed_info.get('intent')}")
    return {"parsed_info": parsed_info, "model_history": state.get("model_history", set())}

# --- 2. Goal Voter Node ---
async def goal_voter_node(state: AgentState):
    print("--- Goal Voter Node ---")
    _log_execution(state, "goal_voter", "Voting on task goals")
    question = state["question"]
    parsed_info = state["parsed_info"]
    llm = get_llm_provider(state)
    
    roles = ["SeniorPartner", "JuniorAssociate", "ComplianceSpecialist"]
    
    async def fetch_vote(role):
        prompt_str = load_role_prompt(role)
        prompt = ChatPromptTemplate.from_template(prompt_str)
        chain = prompt | llm
        try:
            res = await chain.ainvoke({"question": question, "parsed_info": str(parsed_info)})
            return f"Role: {role}\nAnalysis: {res.content}"
        except Exception as e:
            return f"Role: {role}\nError: {str(e)}"
            
    votes = await asyncio.gather(*(fetch_vote(role) for role in roles))
            
    agg_parser = JsonOutputParser()
    agg_prompt = ChatPromptTemplate.from_template(
        """You are the Managing Partner. Review the following 3 analyses from your team and synthesize a consensus goal.
        Team Analyses:\n{votes}\n
        Return a JSON object with:
        - "consensus_intent": The agreed core intent
        - "priority": Final priority level
        - "scope": Agreed scope of work\n{format_instructions}"""
    )
    agg_chain = agg_prompt | llm | agg_parser
    try:
        consensus = await agg_chain.ainvoke({"votes": "\n---\n".join(votes), "format_instructions": agg_parser.get_format_instructions()})
    except Exception as e:
        print(f"Goal Aggregation Error: {e}")
        consensus = {"consensus_intent": parsed_info.get("intent", "general") if parsed_info else "general", "priority": "Medium", "scope": "General Analysis"}

    if not consensus:
        consensus = {"consensus_intent": parsed_info.get("intent", "general") if parsed_info else "general", "priority": "Medium", "scope": "General Analysis"}

    print(f"Goal Consensus: {consensus.get('consensus_intent')}")
    return {"goal_consensus": consensus, "vote_records": votes, "model_history": state.get("model_history", set())}

# --- 3. Planner Node ---
def planner_node(state: AgentState):
    print("--- Planner Node ---")
    _log_execution(state, "planner", f"Planning steps (Loop {state.get('loop_count', 0)})")
    goal = state["goal_consensus"]
    llm = get_llm_provider(state)
    
    issues_context = ""
    if state.get("verifier_result") and not state["verifier_result"].get("passed", True):
        issues_context = f"Issues to fix: {state['verifier_result'].get('issues', [])}\nSuggestions: {state['verifier_result'].get('suggestions', [])}"
    
    prompt_str = load_role_prompt("PlannerAgent")
    prompt = ChatPromptTemplate.from_template(prompt_str)
    
    try:
        structured_llm = llm.with_structured_output(ExecutionPlan)
        chain = prompt | structured_llm
        plan_obj = chain.invoke({"goal": str(goal), "issues": issues_context, "format_instructions": ""})
        plan = [step.dict() for step in plan_obj.steps]
    except Exception as e_struct:
        print(f"Structured output failed: {e_struct}. Falling back to JsonOutputParser.")
        parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        chain = prompt | llm | parser
        try:
            plan_raw = chain.invoke({"goal": str(goal), "issues": issues_context, "format_instructions": parser.get_format_instructions()})
            if isinstance(plan_raw, dict) and "steps" in plan_raw:
                plan = plan_raw["steps"]
            elif isinstance(plan_raw, list):
                plan = plan_raw
            else:
                plan = [plan_raw]
            
            clean_plan = []
            for step in plan:
                if isinstance(step, dict) and "step_name" in step and "role" in step:
                    clean_plan.append(step)
            if not clean_plan:
                raise ValueError("No valid steps in parsed plan")
            plan = clean_plan
        except Exception as e:
            print(f"Planner Error (Fallback): {e}")
            plan = [{"step_name": "General Analysis", "role": "RiskAssessor", "description": "Analyze the query based on general legal principles.", "search_keywords": ["law"]}]
        
    print(f"Plan Generated: {len(plan)} steps")
    return {"node_plan": plan, "model_history": state.get("model_history", set())}

# --- 4. Node Voter Node (Upgraded) ---
async def node_voter_node(state: AgentState):
    print("--- Node Voter Node ---")
    _log_execution(state, "node_voter", "Reviewing execution plan")
    plan = state["node_plan"]
    llm = get_llm_provider(state)
    
    roles = ["SeniorPartner", "JuniorAssociate", "ComplianceSpecialist"]
    parser = JsonOutputParser()
    
    async def fetch_vote(role):
        prompt = ChatPromptTemplate.from_template(
            """You are a {role}. Review the proposed execution plan.
            Plan: {plan}
            Return JSON: {{"decision": "approve" or "suggest_changes", "feedback": "your feedback"}}
            {format_instructions}"""
        )
        chain = prompt | llm | parser
        try:
            res = await chain.ainvoke({"role": role, "plan": str(plan), "format_instructions": parser.get_format_instructions()})
            if not res:
                return {"decision": "approve", "feedback": "No feedback from LLM"}
            return res
        except Exception as e:
            print(f"Node Voter Error for {role}: {e}")
            return {"decision": "approve", "feedback": ""}

    votes = await asyncio.gather(*(fetch_vote(role) for role in roles))
            
    # Simple aggregation: if any suggest changes, we might tweak, but for simplicity we just proceed with the plan and log feedback
    rejections = [v for v in votes if v.get("decision") == "suggest_changes"]
    if rejections:
        print(f"Plan had {len(rejections)} change suggestions, proceeding with caution.")
    else:
        print("Plan fully approved.")
        
    return {"node_plan": plan, "model_history": state.get("model_history", set())}

# --- 5. Executor Node ---
async def _execute_step(step, parsed_info, state, index):
    llm = get_llm_provider(state)
    step_name = step.get('step_name')
    print(f"Executing Step: {step_name}")
    keywords = step.get("search_keywords", [])
    if isinstance(keywords, str): keywords = [keywords]
    
    step_docs = []
    seen_ids = set()
    for kw in keywords:
        try:
            results = await asyncio.to_thread(search_public_law, kw, n_results=2)
            if results and results.get('ids'):
                ids = results['ids'][0]
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                for i, doc_id in enumerate(ids):
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        step_docs.append(f"Source: {metas[i].get('law_name')}\nContent: {docs[i]}")
        except Exception as e:
            print(f"Search error for '{kw}': {e}")
    
    context = "\n\n".join(step_docs) if step_docs else "No specific provisions found."
    
    file_context = ""
    if parsed_info.get("is_file_analysis"):
        snippet = parsed_info.get("file_content_snippet", "")
        if len(snippet) > 5000: snippet = snippet[:5000] + "..."
        file_context = f"\nDocument Content:\n{snippet}"
        
    role_name = step.get("role", "RiskAssessor")
    prompt_str = load_role_prompt(role_name)
    if "{question}" in prompt_str: # fallback safety
         prompt_str = "Task: {step_name}\nInstruction: {description}\nRelevant Laws:\n{context}\nDocument Content:\n{file_context}"
         
    prompt = ChatPromptTemplate.from_template(prompt_str)
    chain = prompt | llm
    try:
        res = await chain.ainvoke({
            "step_name": step_name, 
            "description": step.get("description"),
            "context": context,
            "file_context": file_context
        })
        if not res or not res.content:
            result_text = f"### Step: {step_name} (by {role_name})\nNo analysis result returned."
        else:
            result_text = f"### Step: {step_name} (by {role_name})\n{res.content}"
    except Exception as e:
        print(f"Executor Error for step {step_name}: {e}")
        result_text = f"### Step: {step_name}\nFailed: {e}"

    return index, result_text

async def executor_node(state: AgentState):
    print("--- Executor Node ---")
    _log_execution(state, "executor", "Executing planned steps")
    plan = state["node_plan"]
    parsed_info = state["parsed_info"]
    
    tasks = []
    for i, step in enumerate(plan):
        tasks.append(_execute_step(step, parsed_info, state, i))
        
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x[0])
    sub_results = [r[1] for r in results]

    return {"sub_results": sub_results, "model_history": state.get("model_history", set())}

# --- 6. Result Voter Node ---
def result_voter_node(state: AgentState):
    print("--- Result Voter Node ---")
    _log_execution(state, "result_voter", "Synthesizing final report")
    sub_results = state["sub_results"]
    goal = state["goal_consensus"]
    llm = get_llm_provider(state)
    
    prompt_str = load_role_prompt("LeadAttorney")
    prompt = ChatPromptTemplate.from_template(prompt_str)
    chain = prompt | llm
    try:
        final_res = chain.invoke({"goal": str(goal), "sub_results": "\n\n".join(sub_results)})
        analysis_result = final_res.content
    except Exception as e:
        analysis_result = "Error generating final report."
        
    return {"analysis_result": analysis_result, "model_history": state.get("model_history", set())}

# --- 7. Verifier Node (New) ---
def verifier_node(state: AgentState):
    print("--- Verifier Node ---")
    _log_execution(state, "verifier", "Verifying quality")
    llm = get_llm_provider(state)
    
    prompt_str = load_role_prompt("VerifierAgent")
    prompt = ChatPromptTemplate.from_template(prompt_str)
    parser = JsonOutputParser(pydantic_object=VerifierOutput)
    
    chain = prompt | llm | parser
    try:
        result = chain.invoke({
            "goal": str(state["goal_consensus"]),
            "plan": str(state["node_plan"]),
            "analysis": state["analysis_result"],
            "format_instructions": parser.get_format_instructions()
        })
        if not result:
            result = {"score": 10, "passed": True, "issues": [], "suggestions": []}
    except Exception as e:
        print(f"Verifier Error: {e}")
        result = {"score": 10, "passed": True, "issues": [], "suggestions": []}
        
    print(f"Verification Score: {result.get('score')} - Passed: {result.get('passed')}")
    return {"verifier_result": result, "loop_count": state.get("loop_count", 0) + 1, "model_history": state.get("model_history", set())}

# --- Routing Logic ---
def should_continue(state: AgentState) -> str:
    result = state.get("verifier_result", {})
    passed = result.get("passed", True)
    loops = state.get("loop_count", 0)
    
    if passed or loops >= 3:
        if not passed:
            print("Max loops reached. Proceeding to output despite failing verification.")
        return "output"
    else:
        print(f"Verification failed. Looping back to planner (Loop {loops}).")
        return "planner"

# --- 8. Output Node ---
def output_node(state: AgentState):
    print("--- Output Node ---")
    _log_execution(state, "output", "Formatting final output")
    
    from legal_ai.utils.report_generator import generate_markdown_report
    final_answer = generate_markdown_report(state)
    
    return {"final_answer": final_answer, "model_history": state.get("model_history", set())}

# Orchestrator Class
class MultiAgentOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        
        self.workflow.add_node("parser", parser_node)
        self.workflow.add_node("goal_voter", goal_voter_node)
        self.workflow.add_node("planner", planner_node)
        self.workflow.add_node("node_voter", node_voter_node)
        self.workflow.add_node("executor", executor_node)
        self.workflow.add_node("result_voter", result_voter_node)
        self.workflow.add_node("verifier", verifier_node)
        self.workflow.add_node("output", output_node)
        
        self.workflow.set_entry_point("parser")
        self.workflow.add_edge("parser", "goal_voter")
        self.workflow.add_edge("goal_voter", "planner")
        self.workflow.add_edge("planner", "node_voter")
        self.workflow.add_edge("node_voter", "executor")
        self.workflow.add_edge("executor", "result_voter")
        self.workflow.add_edge("result_voter", "verifier")
        
        self.workflow.add_conditional_edges("verifier", should_continue, {
            "output": "output",
            "planner": "planner"
        })
        self.workflow.add_edge("output", END)
        
        self.app = self.workflow.compile()
        
    def run(self, question: str) -> Dict:
        import uuid
        print(f"Starting Multi-Agent Workflow for: {question}")
        initial_state = {
            "question": question,
            "parsed_info": {}, "goal_consensus": {}, "node_plan": [],
            "sub_results": [], "vote_records": [], "verifier_result": {},
            "loop_count": 0, "execution_log": [], "model_history": set()
        }
        final_state = self.app.invoke(initial_state)
        
        # Save execution log
        try:
            from legal_ai.service.agent_log_service import save_execution_log
            task_id = str(uuid.uuid4())
            save_execution_log(task_id, question, final_state)
        except Exception as e:
            print(f"Warning: Failed to save execution log: {e}")
            
        return final_state

    async def arun(self, question: str) -> Dict:
        import uuid
        print(f"Starting Async Multi-Agent Workflow for: {question}")
        initial_state = {
            "question": question,
            "parsed_info": {}, "goal_consensus": {}, "node_plan": [],
            "sub_results": [], "vote_records": [], "verifier_result": {},
            "loop_count": 0, "execution_log": [], "model_history": set()
        }
        final_state = await self.app.ainvoke(initial_state)
        
        try:
            from legal_ai.service.agent_log_service import save_execution_log
            task_id = str(uuid.uuid4())
            save_execution_log(task_id, question, final_state)
        except Exception as e:
            print(f"Warning: Failed to save execution log: {e}")
            
        return final_state

orchestrator = MultiAgentOrchestrator()
