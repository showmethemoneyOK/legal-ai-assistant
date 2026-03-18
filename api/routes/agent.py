from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from legal_ai.service.agents.multi_agent_orchestrator import orchestrator

router = APIRouter()

class AgentRequest(BaseModel):
    question: str
    
class AgentResponse(BaseModel):
    final_answer: str
    parsed_info: Dict[str, Any]
    retrieved_docs: List[Dict[str, Any]]
    analysis_result: str

@router.post("/run", response_model=AgentResponse)
async def run_agent_workflow(request: AgentRequest):
    """
    Run the multi-agent workflow to analyze a legal question or document.
    """
    try:
        # Run the LangGraph workflow
        final_state = orchestrator.run(request.question)
        
        return AgentResponse(
            final_answer=final_state.get("final_answer", ""),
            parsed_info=final_state.get("parsed_info", {}),
            retrieved_docs=final_state.get("retrieved_docs", []),
            analysis_result=final_state.get("analysis_result", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
