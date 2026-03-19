from legal_ai.core.llm import LLMFactory
from typing import Any

def get_llm_provider(state: dict[str, Any]):
    """
    Dynamically route to the appropriate LLM provider based on AgentState.
    """
    # 1. Get base model from DB or config
    from legal_ai.core.llm import LLMFactory
    db_configs = LLMFactory._get_db_configs()
    from legal_ai.core.config import DEFAULT_MODEL_NAME
    base_model = db_configs.get("DEFAULT_MODEL_NAME") or DEFAULT_MODEL_NAME
    
    target_model = base_model # Default to UI/Config choice
    
    loop_count = state.get("loop_count", 0)
    v_res = state.get("verifier_result", {})
    score = v_res.get("score", 10)
    goal = state.get("goal_consensus", {})
    priority = goal.get("priority", "Medium")
    
    # 2. Intelligent Routing: Force stronger model if needed
    # In a LiteLLM Proxy setup, you might want to route to a specific strong model alias
    # e.g., if base is a small local model, upgrade to 'gpt-4o' or 'claude' alias
    if "ollama" in base_model or "local" in base_model:
        if loop_count >= 2 or (v_res and score < 6) or priority == "High":
            # Assume 'gpt-4o' is a configured alias in your LiteLLM Proxy for hard tasks
            target_model = "gpt-4o" 
        
    # Log the decision in state for output transparency
    if "model_history" not in state:
        state["model_history"] = set()
    state["model_history"].add(target_model)
        
    return LLMFactory.create_provider(model=target_model)
