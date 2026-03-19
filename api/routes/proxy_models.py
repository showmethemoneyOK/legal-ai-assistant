from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import os
from langchain_openai import ChatOpenAI

from legal_ai.core.database import get_db
from legal_ai.db.models import LLMModel
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    model_name: str
    litellm_params: Dict[str, Any]

class TestModelRequest(BaseModel):
    model_name: str

@router.get("/models")
async def get_models(db: Session = Depends(get_db)):
    """Fetch all configured models from the database (API keys are masked)."""
    try:
        models = db.query(LLMModel).all()
        result = []
        for model in models:
            result.append({
                "model_name": model.model_name,
                "litellm_params": {
                    "model": model.target_model,
                    "api_base": model.api_base,
                    "api_key": "***MASKED***"  # Never expose API keys
                }
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching models from DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models")
async def add_model(model_info: ModelInfo, db: Session = Depends(get_db)):
    """Add a new model to the database."""
    try:
        # Check if model already exists
        existing_model = db.query(LLMModel).filter(LLMModel.model_name == model_info.model_name).first()
        
        target_model = model_info.litellm_params.get("model")
        if not target_model:
            raise HTTPException(status_code=400, detail="Target model is required")
            
        api_base = model_info.litellm_params.get("api_base", "")
        api_key = model_info.litellm_params.get("api_key", "")
        
        if existing_model:
            existing_model.target_model = target_model
            existing_model.api_base = api_base
            existing_model.api_key = api_key
        else:
            new_model = LLMModel(
                model_name=model_info.model_name,
                target_model=target_model,
                api_base=api_base,
                api_key=api_key
            )
            db.add(new_model)
            
        db.commit()
        return {"status": "success", "message": "Model added to database successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating model in DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-model")
async def test_model(request: TestModelRequest, db: Session = Depends(get_db)):
    """Test connectivity to a specific model using LangChain."""
    import time
    from legal_ai.db.models import SystemConfig
    
    try:
        model = db.query(LLMModel).filter(LLMModel.model_name == request.model_name).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
            
        # Check global async execution mode
        async_config = db.query(SystemConfig).filter(SystemConfig.config_key == "ASYNC_MODEL_EXECUTION").first()
        is_async = async_config and async_config.config_value.lower() == "true"
            
        api_key = model.api_key or os.getenv("LLM_API_KEY", "") # Default for local models that might not need it
        base_url = model.api_base
        
        # Ensure base_url has no trailing slash, but ends with /v1 for openai client
        if base_url:
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"
                
        # Initialize LangChain client
        chat_client = ChatOpenAI(
            model=model.target_model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            max_tokens=50,
            timeout=15.0
        )
        
        start_time = time.time()
        
        # Send a simple test message based on execution mode
        if is_async:
            response = await chat_client.ainvoke("Hello, please reply with 'Connection successful'.")
            mode_used = "Asynchronous"
        else:
            response = chat_client.invoke("Hello, please reply with 'Connection successful'.")
            mode_used = "Synchronous"
            
        elapsed_time = time.time() - start_time
        
        return {
            "status": "success", 
            "message": "Connection successful", 
            "reply": response.content,
            "mode": mode_used,
            "time_ms": round(elapsed_time * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Error testing model {request.model_name}: {e}")
        return {"status": "error", "message": f"Connection failed: {str(e)}"}
