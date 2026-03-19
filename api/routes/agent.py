from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from legal_ai.service.agents.multi_agent_orchestrator import orchestrator
from legal_ai.core.database import get_db
from sqlalchemy.orm import Session
from legal_ai.db.models import AgentExecutionLog
import uuid
import json

router = APIRouter()

class AgentRequest(BaseModel):
    question: str
    
class AgentResponse(BaseModel):
    final_answer: str
    parsed_info: Dict[str, Any]
    retrieved_docs: List[Dict[str, Any]]
    analysis_result: str
    execution_log: List[Dict[str, Any]]

@router.post("/run", response_model=AgentResponse)
async def run_agent_workflow(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Run the multi-agent workflow to analyze a legal question or document.
    """
    try:
        task_id = str(uuid.uuid4())
        # Run the LangGraph workflow
        final_state = orchestrator.run(request.question)
        
        # Persist Execution Log to DB
        execution_logs = final_state.get("execution_log", [])
        v_res = final_state.get("verifier_result", {})
        score = v_res.get("score", None)
        
        for log in execution_logs:
            db_log = AgentExecutionLog(
                task_id=task_id,
                question=request.question,
                node_name=log.get("node"),
                summary_json=json.dumps(log),
                verifier_score=score if log.get("node") == "verifier" else None
            )
            db.add(db_log)
        db.commit()
        
        # Note: model_history is a set, need to convert to list for JSON serialization if returned directly,
        # but report_generator already handles it in final_answer.
        
        return AgentResponse(
            final_answer=final_state.get("final_answer", ""),
            parsed_info=final_state.get("parsed_info", {}),
            retrieved_docs=final_state.get("retrieved_docs", []),
            analysis_result=final_state.get("analysis_result", ""),
            execution_log=execution_logs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
