import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from legal_ai.core.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    OPENAI_API_BASE,
    LOCAL_LLM_API_BASE,
    LOCAL_LLM_API_KEY,
    LOCAL_MODEL_NAME
)

class LLMFactory:
    """
    Factory class to create LangChain Chat Models based on configuration or explicit parameters.
    Supports creating multiple distinct providers for multi-agent scenarios.
    """
    _default_instance = None

    @classmethod
    def create_provider(cls, 
                        provider: str = None, 
                        model: str = None, 
                        api_key: str = None, 
                        base_url: str = None,
                        temperature: float = 0.7) -> BaseChatModel:
        """
        Create a new instance of a LangChain Chat Model with specific settings.
        Useful for multi-agent systems where different agents need different models.
        
        Args:
            provider (str): "openai" or "local". Defaults to config.LLM_PROVIDER if None.
            model (str): Model name (e.g. "gpt-4", "llama3"). Defaults to config if None.
            api_key (str): API Key. Defaults to config if None.
            base_url (str): API Base URL. Defaults to config if None.
            temperature (float): Sampling temperature. Defaults to 0.7.
            
        Returns:
            BaseChatModel: An instance of the requested LangChain Chat Model (e.g., ChatOpenAI).
        """
        # 1. Resolve configuration (Priority: explicit arg > config > default)
        provider_type = (provider or LLM_PROVIDER).lower()
        
        if provider_type == "openai":
            api_key = api_key or OPENAI_API_KEY
            model = model or OPENAI_MODEL_NAME
            base_url = base_url or OPENAI_API_BASE
            
            if not api_key:
                print("Warning: OPENAI_API_KEY is not set.")
                
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            
        elif provider_type == "local":
            base_url = base_url or LOCAL_LLM_API_BASE
            model = model or LOCAL_MODEL_NAME
            api_key = api_key or LOCAL_LLM_API_KEY
            
            # For local models (Ollama/vLLM) that are OpenAI-compatible, we also use ChatOpenAI
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider_type}. Use 'openai' or 'local'.")

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

# Helper function to create a specific LLM (e.g., for a specific agent)
def create_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
    return LLMFactory.create_provider(provider=provider, model=model, **kwargs)
