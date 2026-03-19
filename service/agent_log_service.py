from legal_ai.core.database import SessionLocal
from legal_ai.db.models import AgentExecutionLog
import json
from datetime import datetime

def save_execution_log(task_id: str, question: str, final_state: dict):
    """
    Saves the multi-agent execution path to the database.
    """
    db = SessionLocal()
    try:
        logs = final_state.get("execution_log", [])
        v_res = final_state.get("verifier_result", {})
        score = v_res.get("score") if v_res else None
        
        # models might be a set
        models_set = final_state.get("model_history", set())
        models_str = ", ".join(models_set) if models_set else "unknown"
        
        for log in logs:
            db_log = AgentExecutionLog(
                task_id=task_id,
                question=question,
                node_name=log.get("node", "unknown"),
                summary=log.get("summary", ""),
                verifier_score=score,
                model_used=models_str,
                timestamp=datetime.utcnow()
            )
            db.add(db_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to save execution log: {e}")
    finally:
        db.close()
