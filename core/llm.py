import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from legal_ai.core.config import (
    LLM_PROXY_BASE,
    LLM_MASTER_KEY,
    DEFAULT_MODEL_NAME
)
from legal_ai.core.database import SessionLocal
from legal_ai.db.models import SystemConfig, LLMModel

class LLMFactory:
    """
    Factory class to create LangChain Chat Models directly connecting to providers
    (like OpenAI, DeepSeek, or local Ollama) based on database configurations.
    """
    _default_instance = None

    @classmethod
    def _get_db_configs(cls) -> Dict[str, str]:
        """Fetch all configurations from the database."""
        db = SessionLocal()
        try:
            configs = db.query(SystemConfig).all()
            return {c.config_key: c.config_value for c in configs}
        except Exception as e:
            print(f"Warning: Could not fetch configs from DB: {e}")
            return {}
        finally:
            db.close()
            
    @classmethod
    def _get_model_config(cls, model_name: str) -> Optional[LLMModel]:
        """Fetch a specific model configuration from the database."""
        db = SessionLocal()
        try:
            return db.query(LLMModel).filter(LLMModel.model_name == model_name).first()
        except Exception as e:
            print(f"Warning: Could not fetch model config from DB: {e}")
            return None
        finally:
            db.close()

    @classmethod
    def create_provider(cls, 
                        model: str = None, 
                        temperature: float = 0.7,
                        max_tokens: int = None,
                        streaming: bool = False) -> BaseChatModel:
        """
        Create a new instance of a LangChain Chat Model directly connecting to the provider.
        Supports both synchronous and asynchronous usage depending on how the returned object is called
        (e.g., .invoke() vs .ainvoke(), .stream() vs .astream()).
        """
        # 1. Load DB configs to get default model name if not provided
        db_configs = cls._get_db_configs()
        target_model_name = model or db_configs.get("DEFAULT_MODEL_NAME") or DEFAULT_MODEL_NAME

        if not target_model_name:
            print("Warning: DEFAULT_MODEL_NAME is not set. Using fallback.")
            target_model_name = "default-model"

        # 2. Fetch specific model configuration
        model_config = cls._get_model_config(target_model_name)
        
        if model_config:
            api_key = model_config.api_key or os.getenv("LLM_API_KEY", "")
            base_url = model_config.api_base
            actual_model = model_config.target_model
        else:
            # Fallback to old behavior if model not found in DB
            print(f"Warning: Model {target_model_name} not found in DB. Falling back to default proxy settings.")
            api_key = db_configs.get("LLM_MASTER_KEY") or os.getenv("LLM_MASTER_KEY", "")
            base_url = db_configs.get("LLM_PROXY_BASE") or LLM_PROXY_BASE
            actual_model = target_model_name

        # Ensure base_url has no trailing slash, but ends with /v1 for openai client
        if base_url:
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"

        # Initialize the ChatOpenAI client which can handle sync/async/streaming natively
        kwargs = {
            "model": actual_model,
            "api_key": api_key,
            "temperature": temperature,
            "streaming": streaming
        }
        
        if base_url:
            kwargs["base_url"] = base_url
            
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        return ChatOpenAI(**kwargs)

    @classmethod
    def get_default_provider(cls) -> BaseChatModel:
        """
        Returns a singleton instance of the DEFAULT configured LLM provider.
        Use this for general purpose tasks.
        """
        if cls._default_instance is None:
            cls._default_instance = cls.create_provider()
        return cls._default_instance

# Helper function for easy access to the default provider
def get_llm() -> BaseChatModel:
    return LLMFactory.get_default_provider()

# Helper function to create a specific LLM
def create_llm(model: str, **kwargs) -> BaseChatModel:
    return LLMFactory.create_provider(model=model, **kwargs)
