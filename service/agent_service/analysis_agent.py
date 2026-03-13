from typing import Dict, Any, List
from langchain_core.language_models.chat_models import BaseChatModel
from legal_ai.service.agent_service.base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    """
    Analysis Agent responsible for reviewing legal documents and providing risk assessments.
    
    Inputs:
    - User document content
    - Relevant laws retrieved by SearchAgent
    """
    
    def __init__(self, llm: BaseChatModel = None):
        super().__init__(name="AnalysisAgent", llm=llm)

    def run(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze the document based on the context (laws).
        
        Args:
            input_text (str): The document content or specific clause to review.
            context (Dict): Should contain 'relevant_laws' from SearchAgent.
        """
        self.log("Starting analysis...")
        
        relevant_laws = context.get('relevant_laws', "No specific laws provided.")
        
        prompt = f"""
        You are a professional legal assistant. Your task is to review the following document content 
        based on the provided relevant laws. identify potential risks and provide suggestions.

        [Relevant Laws]
        {relevant_laws}

        [Document Content]
        {input_text}

        [Instructions]
        1. Identify clauses that conflict with the relevant laws.
        2. Point out missing necessary clauses.
        3. Provide specific modification suggestions.
        4. Output format: Markdown.

        [Analysis Report]
        """
        
        try:
            # LangChain specific: invoke() returns an AIMessage object
            response = self.llm.invoke(prompt)
            report = response.content
            return {
                "status": "success",
                "report": report
            }
        except Exception as e:
            self.log(f"Analysis failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
