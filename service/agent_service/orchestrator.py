from typing import Dict, Any, List
from legal_ai.core.llm import get_llm
from legal_ai.service.agent_service.search_agent import SearchAgent
from legal_ai.service.agent_service.analysis_agent import AnalysisAgent

class Orchestrator:
    """
    The main coordinator for the multi-agent system.
    Receives user requests and routes them to appropriate agents.
    """
    
    def __init__(self):
        # Initialize default LLM for orchestration
        self.llm = get_llm()
        
        # Initialize specialized agents
        # In a real system, we might use dependency injection or a registry
        self.search_agent = SearchAgent(llm=self.llm)
        self.analysis_agent = AnalysisAgent(llm=self.llm)

    def run_workflow(self, user_query: str, doc_content: str = None) -> Dict[str, Any]:
        """
        Execute a standard workflow: Search -> Analyze -> Respond
        
        Args:
            user_query (str): The user's question or instruction.
            doc_content (str): Optional document content to analyze.
        """
        print("[Orchestrator] Received request:", user_query)
        
        # Step 1: Search for relevant laws
        print("[Orchestrator] Step 1: Searching relevant laws...")
        search_result = self.search_agent.run(user_query)
        
        relevant_laws = search_result.get("combined_text", "")
        if not relevant_laws:
            return {
                "status": "partial_success",
                "message": "未找到相关法律条款，无法进行深入分析。",
                "search_results": []
            }

        # Step 2: Analyze based on search results
        print("[Orchestrator] Step 2: Analyzing...")
        
        # If user provided a document, analyze it against the laws
        # If not, just answer the question based on laws
        if doc_content:
            analysis_input = doc_content
            task_context = {"relevant_laws": relevant_laws}
            analysis_result = self.analysis_agent.run(analysis_input, task_context)
            
            return {
                "status": "success",
                "type": "document_review",
                "search_results": search_result.get("relevant_docs"),
                "analysis_report": analysis_result.get("report")
            }
        else:
            # Simple Q&A based on laws
            prompt = f"""
            Answer the user's question based on the following laws.
            
            [Relevant Laws]
            {relevant_laws}
            
            [User Question]
            {user_query}
            """
            # LangChain specific: invoke() returns an AIMessage object
            response = self.llm.invoke(prompt)
            answer = response.content
            return {
                "status": "success",
                "type": "legal_qa",
                "search_results": search_result.get("relevant_docs"),
                "answer": answer
            }
