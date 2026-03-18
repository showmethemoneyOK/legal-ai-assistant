import os
from typing import Dict, List, Optional, TypedDict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from legal_ai.core.llm import LLMFactory
from legal_ai.service.vector_service import search_public_law
from legal_ai.service.law_service import extract_text_from_file

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

# --- 1. Parser Node (Existing) ---
def parser_node(state: AgentState):
    """
    Parser Node: Understands user intent and extracts search keywords.
    Also handles file input if the question is a file path.
    """
    print("--- Parser Node ---")
    question = state["question"]
    llm = LLMFactory.create_provider()
    
    # 1. Check if input is a file path
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
        print(f"File check warning: {e}")
        context_question = question

    # 2. Extract search keywords
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        """
        You are a legal assistant. Extract key legal concepts and search terms from the user query.
        If the query mentions a specific file or document, focus on the legal issues it might involve (e.g. lease, contract, risk, compliance).
        
        User Query: {question}
        
        Return a JSON object with:
        - "keywords": list of string search terms (3-5 key terms) for the vector database
        - "intent": brief description of user intent
        - "summary": brief summary of the query or document topic
        
        {format_instructions}
        """
    )
    chain = prompt | llm | parser
    try:
        parsed_info = chain.invoke({"question": context_question, "format_instructions": parser.get_format_instructions()})
        
        if is_file:
            parsed_info["is_file_analysis"] = True
            parsed_info["file_path"] = file_path
            parsed_info["file_content_snippet"] = file_content 
        else:
            parsed_info["is_file_analysis"] = False
            
    except Exception as e:
        print(f"Parser Error: {e}")
        parsed_info = {
            "keywords": [question[:50]], 
            "intent": "general", 
            "is_file_analysis": is_file,
            "file_path": file_path if is_file else None,
            "file_content_snippet": file_content if is_file else None
        }
        
    print(f"Parsed Info: {parsed_info}")
    return {"parsed_info": parsed_info}

# --- 2. Goal Voter Node (New) ---
def goal_voter_node(state: AgentState):
    """
    Goal Voter: 3 Roles (Senior Partner, Junior Associate, Compliance Specialist)
    vote on the understanding of the task.
    """
    print("--- Goal Voter Node ---")
    question = state["question"]
    parsed_info = state["parsed_info"]
    llm = LLMFactory.create_provider()
    
    roles = ["Senior Partner", "Junior Associate", "Compliance Specialist"]
    votes = []
    
    # 1. Collect Votes
    for role in roles:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a {role} in a law firm. 
            Review the User Query and Parsed Info.
            Define the core legal goal, priority (High/Medium/Low), and scope of analysis.
            
            User Query: {question}
            Parsed Info: {parsed_info}
            
            Return a concise analysis string.
            """
        )
        chain = prompt | llm
        try:
            res = chain.invoke({"role": role, "question": question, "parsed_info": str(parsed_info)})
            votes.append(f"Role: {role}\nAnalysis: {res.content}")
        except Exception as e:
            votes.append(f"Role: {role}\nError: {str(e)}")
            
    # 2. Aggregator
    agg_parser = JsonOutputParser()
    agg_prompt = ChatPromptTemplate.from_template(
        """
        You are the Managing Partner. Review the following 3 analyses from your team and synthesize a consensus goal.
        
        Team Analyses:
        {votes}
        
        Return a JSON object with:
        - "consensus_intent": The agreed core intent
        - "priority": Final priority level
        - "scope": Agreed scope of work
        
        {format_instructions}
        """
    )
    agg_chain = agg_prompt | llm | agg_parser
    try:
        consensus = agg_chain.invoke({"votes": "\n---\n".join(votes), "format_instructions": agg_parser.get_format_instructions()})
    except Exception as e:
        print(f"Goal Aggregation Error: {e}")
        consensus = {"consensus_intent": parsed_info.get("intent"), "priority": "Medium", "scope": "General Analysis"}

    print(f"Goal Consensus: {consensus}")
    return {"goal_consensus": consensus, "vote_records": votes}

# --- 3. Planner Node (New) ---
def planner_node(state: AgentState):
    """
    Planner: Decompose the consensus goal into execution steps.
    """
    print("--- Planner Node ---")
    goal = state["goal_consensus"]
    llm = LLMFactory.create_provider()
    
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        """
        Based on the legal goal, create a execution plan with 2-4 distinct steps.
        Each step should be a specific task for a sub-agent.
        
        Goal: {goal}
        
        Return a JSON list of objects, where each object has:
        - "step_name": Short name
        - "role": The agent role best for this step (e.g. Researcher, Analyst, Reviewer)
        - "description": Detailed instruction for the step
        - "search_keywords": Specific keywords for vector search for this step
        
        {format_instructions}
        """
    )
    chain = prompt | llm | parser
    try:
        plan = chain.invoke({"goal": str(goal), "format_instructions": parser.get_format_instructions()})
        # Ensure it's a list
        if isinstance(plan, dict): plan = [plan]
    except Exception as e:
        print(f"Planner Error: {e}")
        plan = [{"step_name": "General Analysis", "role": "Generalist", "description": "Analyze the query based on general legal principles.", "search_keywords": ["law"]}]
        
    print(f"Plan Generated: {len(plan)} steps")
    return {"node_plan": plan}

# --- 4. Node Voter Node (New - Simplified) ---
def node_voter_node(state: AgentState):
    """
    Node Voter: Reviews the plan and approves or refines it.
    """
    print("--- Node Voter Node ---")
    plan = state["node_plan"]
    # For this simplified version, we just pass through or doing a simple check.
    # In a full version, this would call LLM to critique the plan.
    print("Plan approved by Node Voter.")
    return {"node_plan": plan}

# --- 5. Executor Node (Fan-out simulation) ---
def executor_node(state: AgentState):
    """
    Executor: Runs the plan steps.
    Although LangGraph supports parallel nodes, for simplicity and stability in this script,
    we iterate through the plan here (simulating parallel workers).
    """
    print("--- Executor Node (Fan-out) ---")
    plan = state["node_plan"]
    parsed_info = state["parsed_info"]
    sub_results = []
    
    llm = LLMFactory.create_provider()
    
    for step in plan:
        print(f"Executing Step: {step.get('step_name')}")
        keywords = step.get("search_keywords", [])
        if isinstance(keywords, str): keywords = [keywords]
        
        # A. Retrieval (Reusing vector_service logic per step)
        step_docs = []
        seen_ids = set()
        for kw in keywords:
            try:
                results = search_public_law(kw, n_results=2) # Keep it focused
                if results and results.get('ids'):
                    ids = results['ids'][0]
                    docs = results['documents'][0]
                    metas = results['metadatas'][0]
                    for i, doc_id in enumerate(ids):
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            step_docs.append(f"Source: {metas[i].get('law_name')}\nContent: {docs[i]}")
            except Exception:
                pass
        
        context = "\n\n".join(step_docs) if step_docs else "No specific provisions found."
        
        # B. Analysis (Sub-task execution)
        # Check if we have file content to inject
        file_context = ""
        if parsed_info.get("is_file_analysis"):
            snippet = parsed_info.get("file_content_snippet", "")
            if len(snippet) > 5000: snippet = snippet[:5000] + "..."
            file_context = f"\nDocument Content:\n{snippet}"
            
        prompt = ChatPromptTemplate.from_template(
            """
            You are executing a sub-task: {step_name}
            Role: {role}
            Instruction: {description}
            
            Relevant Laws:
            {context}
            {file_context}
            
            Provide your analysis for this specific step.
            """
        )
        chain = prompt | llm
        try:
            res = chain.invoke({
                "step_name": step.get("step_name"), 
                "role": step.get("role"), 
                "description": step.get("description"),
                "context": context,
                "file_context": file_context
            })
            sub_results.append(f"### Step: {step.get('step_name')}\n{res.content}")
        except Exception as e:
            sub_results.append(f"### Step: {step.get('step_name')}\nFailed: {e}")

    return {"sub_results": sub_results}

# --- 6. Result Voter Node (New) ---
def result_voter_node(state: AgentState):
    """
    Result Voter: Synthesizes all sub-task results into a final answer.
    """
    print("--- Result Voter Node ---")
    sub_results = state["sub_results"]
    goal = state["goal_consensus"]
    llm = LLMFactory.create_provider()
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are the Lead Attorney. Synthesize the following sub-task analyses into a final, cohesive legal report.
        
        Goal: {goal}
        
        Sub-task Results:
        {sub_results}
        
        Ensure the final report is structured, professional, and directly addresses the client's goal.
        """
    )
    chain = prompt | llm
    try:
        final_res = chain.invoke({"goal": str(goal), "sub_results": "\n\n".join(sub_results)})
        analysis_result = final_res.content
    except Exception as e:
        analysis_result = "Error generating final report."
        
    return {"analysis_result": analysis_result}

# --- 7. Output Node (Enhanced) ---
def output_node(state: AgentState):
    """
    Output Node: Final formatting.
    """
    print("--- Output Node ---")
    analysis = state["analysis_result"]
    # We could collect references from sub_results if we parsed them, 
    # but for now we just present the synthesized analysis.
    
    final_answer = f"{analysis}\n\n---\n*Generated by Legal AI Multi-Agent System (Consensus & Voting Enabled)*"
    return {"final_answer": final_answer}

# Orchestrator Class
class MultiAgentOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("parser", parser_node)
        self.workflow.add_node("goal_voter", goal_voter_node)
        self.workflow.add_node("planner", planner_node)
        self.workflow.add_node("node_voter", node_voter_node)
        self.workflow.add_node("executor", executor_node)
        self.workflow.add_node("result_voter", result_voter_node)
        self.workflow.add_node("output", output_node)
        
        # Define edges
        self.workflow.set_entry_point("parser")
        self.workflow.add_edge("parser", "goal_voter")
        self.workflow.add_edge("goal_voter", "planner")
        self.workflow.add_edge("planner", "node_voter")
        self.workflow.add_edge("node_voter", "executor")
        self.workflow.add_edge("executor", "result_voter")
        self.workflow.add_edge("result_voter", "output")
        self.workflow.add_edge("output", END)
        
        # Compile graph
        self.app = self.workflow.compile()
        
    def run(self, question: str) -> Dict:
        """
        Run the agent workflow.
        """
        print(f"Starting Multi-Agent Workflow for: {question}")
        initial_state = {
            "question": question,
            "parsed_info": {},
            "goal_consensus": {},
            "node_plan": [],
            "sub_results": [],
            "vote_records": []
        }
        # invoke returns the final state
        final_state = self.app.invoke(initial_state)
        return final_state

# Singleton instance
orchestrator = MultiAgentOrchestrator()
