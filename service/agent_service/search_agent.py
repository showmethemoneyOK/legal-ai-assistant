from typing import Dict, Any, List
from langchain_core.language_models.chat_models import BaseChatModel
from legal_ai.service.agent_service.base_agent import BaseAgent
from legal_ai.service.vector_service import search_public_law

class SearchAgent(BaseAgent):
    """
    Search Agent responsible for retrieving relevant legal information.
    
    Capabilities:
    1. Refine user queries into better search terms.
    2. Search the vector database.
    3. Summarize search results.
    """
    
    def __init__(self, llm: BaseChatModel = None):
        super().__init__(name="SearchAgent", llm=llm)

    def run(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log(f"Processing query: {input_text}")
        
        # 1. Refine Query (Optional: use LLM to extract keywords)
        # For now, we use the input directly or a simple LLM call if needed
        search_query = self._refine_query(input_text)
        
        # 2. Execute Search
        self.log(f"Searching vector DB for: {search_query}")
        search_results = search_public_law(search_query, n_results=5)
        
        # 3. Process Results
        docs = search_results.get('documents', [[]])[0]
        metadatas = search_results.get('metadatas', [[]])[0]
        
        relevant_info = []
        for i, doc in enumerate(docs):
            if i < len(metadatas):
                meta = metadatas[i]
                source = f"《{meta.get('law_name', 'Unknown')}》"
                relevant_info.append(f"Source: {source}\nContent: {doc}")
        
        combined_text = "\n\n".join(relevant_info)
        
        if not combined_text:
            return {
                "status": "no_results",
                "answer": "未找到相关法律条款。",
                "raw_results": []
            }
        
        return {
            "status": "success",
            "query": search_query,
            "relevant_docs": relevant_info,
            "combined_text": combined_text
        }

    def _refine_query(self, input_text: str) -> str:
        """
        Use LLM to extract key legal search terms from natural language.
        """
        prompt = f"""
        Extract the key legal search terms from the following user query. 
        Return ONLY the keywords separated by spaces.
        
        User Query: {input_text}
        Keywords:
        """
        try:
            # LangChain specific: invoke() returns an AIMessage object, use .content to get text
            response = self.llm.invoke(prompt)
            keywords = response.content.strip()
            self.log(f"Refined query: {keywords}")
            return keywords
        except Exception as e:
            self.log(f"LLM refinement failed: {e}. Using original text.")
            return input_text
