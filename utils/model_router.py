import time
from datetime import datetime, timedelta
from typing import Any
from legal_ai.core.llm import LLMFactory
from legal_ai.core.config import DEFAULT_MODEL_NAME
from legal_ai.core.database import SessionLocal
from legal_ai.db.models import LLMModel

# Global model metrics tracker
# Structure: { "model_name": {"failures": [datetime, ...], "latencies": [float, ...], "success_count": int, "total_count": int} }
MODEL_METRICS = {}

def update_model_metrics(model_name: str, success: bool, latency: float):
    """Update tracking metrics for a model."""
    if model_name not in MODEL_METRICS:
        MODEL_METRICS[model_name] = {"failures": [], "latencies": [], "success_count": 0, "total_count": 0}
        
    metrics = MODEL_METRICS[model_name]
    metrics["total_count"] += 1
    metrics["latencies"].append(latency)
    # Keep last 10 latencies
    if len(metrics["latencies"]) > 10:
        metrics["latencies"].pop(0)
        
    if success:
        metrics["success_count"] += 1
    else:
        metrics["failures"].append(datetime.now())
        
    # Clean up failures older than 24h
    cutoff = datetime.now() - timedelta(hours=24)
    metrics["failures"] = [f for f in metrics["failures"] if f > cutoff]

def get_best_fallback_model() -> str:
    """Get the best available online model from DB based on success rate and latency."""
    db = SessionLocal()
    try:
        models = db.query(LLMModel).all()
        available_models = []
        for m in models:
            m_name = m.model_name
            metrics = MODEL_METRICS.get(m_name, {"failures": [], "latencies": [], "success_count": 0, "total_count": 0})
            
            # Clean up old failures
            cutoff = datetime.now() - timedelta(hours=24)
            recent_failures = [f for f in metrics.get("failures", []) if f > cutoff]
            if m_name in MODEL_METRICS:
                MODEL_METRICS[m_name]["failures"] = recent_failures
            
            if len(recent_failures) >= 3:
                continue # Skip models with >= 3 failures in 24h
                
            avg_latency = sum(metrics["latencies"]) / len(metrics["latencies"]) if metrics["latencies"] else 0
            success_rate = metrics["success_count"] / metrics["total_count"] if metrics["total_count"] > 0 else 1.0
            
            # Penalize models with > 30s latency
            if avg_latency > 30:
                continue
                
            available_models.append({
                "name": m_name,
                "success_rate": success_rate,
                "latency": avg_latency
            })
            
        if not available_models:
            return "gpt-4o" # Ultimate fallback
            
        # Sort by success rate (desc) and latency (asc)
        available_models.sort(key=lambda x: (-x["success_rate"], x["latency"]))
        return available_models[0]["name"]
    except Exception as e:
        print(f"Error fetching fallback model: {e}")
        return "gpt-4o"
    finally:
        db.close()

def get_llm_provider(state: dict[str, Any]):
    """
    Dynamically route to the appropriate LLM provider based on AgentState.
    """
    # 1. Get base model from DB or config
    db_configs = LLMFactory._get_db_configs()
    base_model = db_configs.get("DEFAULT_MODEL_NAME") or DEFAULT_MODEL_NAME
    
    target_model = base_model # Default to UI/Config choice
    
    loop_count = state.get("loop_count", 0)
    v_res = state.get("verifier_result", {})
    score = v_res.get("score", 10)
    goal = state.get("goal_consensus", {})
    priority = goal.get("priority", "Medium")
    
    # 2. Intelligent Routing: Check latency and failure rules
    metrics = MODEL_METRICS.get(base_model, {})
    avg_latency = sum(metrics.get("latencies", [])) / len(metrics.get("latencies", [1])) if metrics.get("latencies") else 0
    recent_failures = len([f for f in metrics.get("failures", []) if f > datetime.now() - timedelta(hours=24)])
    
    needs_upgrade = False
    if "ollama" in base_model.lower() or "local" in base_model.lower():
        if loop_count >= 2 or (v_res and score < 6) or priority == "High":
            needs_upgrade = True
            
    if avg_latency > 30 or recent_failures >= 3 or needs_upgrade:
        target_model = get_best_fallback_model()
        
    # Log the decision in state for output transparency
    if "model_history" not in state:
        state["model_history"] = set()
    state["model_history"].add(target_model)
        
    return LLMFactory.create_provider(model=target_model)
