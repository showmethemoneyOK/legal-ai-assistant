from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from legal_ai.core.llm import get_llm

class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    
    Attributes:
        name (str): The name of the agent.
        llm (BaseChatModel): The LangChain Chat Model instance this agent uses.
    """
    
    def __init__(self, name: str, llm: Optional[BaseChatModel] = None):
        """
        Initialize the agent.
        
        Args:
            name (str): Name of the agent.
            llm (Optional[BaseChatModel]): Specific LangChain Chat Model for this agent. 
                                         If None, uses the default provider from config.
        """
        self.name = name
        self.llm = llm if llm else get_llm()

    @abstractmethod
    def run(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        Args:
            input_text (str): The user's input or instruction.
            context (Dict[str, Any]): Shared context or previous conversation history.
            
        Returns:
            Dict[str, Any]: The result of the agent's execution.
        """
        pass

    def log(self, message: str):
        """Simple logging helper."""
        print(f"[{self.name}] {message}")
