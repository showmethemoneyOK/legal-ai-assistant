import os
from typing import Dict, List, Optional, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from legal_ai.core.llm import LLMFactory
from legal_ai.service.vector_service import search_public_law
from legal_ai.service.law_service import extract_text_from_file

# Define State
class AgentState(TypedDict):
    question: str
    parsed_info: Dict[str, any]
    retrieved_docs: List[Dict]
    analysis_result: str
    final_answer: str

# Define Nodes

def parser_node(state: AgentState):
    """
    Parser Node: Understands user intent and extracts search keywords.
    Also handles file input if the question is a file path.
    """
    print("--- Parser Node ---")
    question = state["question"]
    llm = LLMFactory.create_provider()
    
    # 1. Check if input is a file path
    file_content = ""
    file_path = ""
    is_file = False
    
    try:
        # Check if the question string is a valid file path that exists
        if len(question) < 260 and os.path.exists(question):
            file_path = question
            file_content = extract_text_from_file(file_path)
            is_file = True
            # Update question context for the LLM
            # We keep the original question as the file path, but give context to LLM
            context_question = f"Analyze the legal document at path: {question}"
        else:
            context_question = question
    except Exception as e:
        print(f"File check warning: {e}")
        context_question = question

    # 2. Extract search keywords
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        """
        You are a legal assistant. Extract key legal concepts and search terms from the user query.
        If the query mentions a specific file or document, focus on the legal issues it might involve (e.g. lease, contract, risk, compliance).
        
        User Query: {question}
        
        Return a JSON object with:
        - "keywords": list of string search terms (3-5 key terms) for the vector database
        - "intent": brief description of user intent
        - "summary": brief summary of the query or document topic
        
        {format_instructions}
        """
    )
    chain = prompt | llm | parser
    try:
        parsed_info = chain.invoke({"question": context_question, "format_instructions": parser.get_format_instructions()})
        
        # Inject file info if detected
        if is_file:
            parsed_info["is_file_analysis"] = True
            parsed_info["file_path"] = file_path
            # Store snippet for downstream use
            parsed_info["file_content_snippet"] = file_content 
        else:
            parsed_info["is_file_analysis"] = False
            
    except Exception as e:
        print(f"Parser Error: {e}")
        # Fallback
        parsed_info = {
            "keywords": [question[:50]], 
            "intent": "general", 
            "is_file_analysis": is_file,
            "file_path": file_path if is_file else None,
            "file_content_snippet": file_content if is_file else None
        }
        
    print(f"Parsed Info: {parsed_info}")
    return {"parsed_info": parsed_info}

def retriever_node(state: AgentState):
    """
    Retriever Node: Searches the vector database for relevant legal provisions.
    """
    print("--- Retriever Node ---")
    parsed_info = state["parsed_info"]
    keywords = parsed_info.get("keywords", [])
    
    if isinstance(keywords, str):
        keywords = [keywords]
        
    all_docs = []
    seen_ids = set()
    
    # Search for each keyword
    for kw in keywords:
        try:
            results = search_public_law(kw, n_results=3)
            if results and results.get('ids'):
                ids = results['ids'][0]
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                
                for i, doc_id in enumerate(ids):
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        all_docs.append({
                            "content": docs[i],
                            "metadata": metas[i],
                            "id": doc_id
                        })
        except Exception as e:
            print(f"Search error for keyword '{kw}': {e}")
    
    print(f"Retrieved {len(all_docs)} documents.")
    return {"retrieved_docs": all_docs}

def analysis_node(state: AgentState):
    """
    Analysis Node: Generates the final analysis using LLM and retrieved docs.
    """
    print("--- Analysis Node ---")
    question = state["question"]
    parsed_info = state["parsed_info"]
    docs = state["retrieved_docs"]
    llm = LLMFactory.create_provider()
    
    # Prepare context from retrieved docs
    context_text = ""
    for d in docs:
        law_name = d['metadata'].get('law_name', 'Unknown')
        content = d['content']
        context_text += f"Source: {law_name}\nContent: {content}\n\n"
    
    if not context_text:
        context_text = "No specific legal provisions found in the database."

    # Determine prompt based on whether we are analyzing a file or just a question
    if parsed_info.get("is_file_analysis"):
        file_content = parsed_info.get("file_content_snippet", "")
        # Truncate if too long (simple handling)
        if len(file_content) > 10000:
            file_content = file_content[:10000] + "...(truncated)"
            
        prompt = ChatPromptTemplate.from_template(
            """
            You are a senior legal consultant. Your task is to analyze the provided document content against the relevant legal provisions.
            
            # Relevant Legal Provisions (from Vector DB):
            {context}
            
            # Document Content to Analyze:
            {file_content}
            
            # User Instruction:
            Analyze the risks, compliance issues, and provide recommendations based on the laws above.
            
            Output a structured markdown report.
            """
        )
        chain = prompt | llm
        result = chain.invoke({"context": context_text, "file_content": file_content})
    else:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a senior legal consultant. Answer the user's legal question based strictly on the provided legal provisions.
            
            # Relevant Legal Provisions:
            {context}
            
            # User Question:
            {question}
            
            If the answer is not found in the provisions, state that based on the available database, but provide general legal knowledge if helpful (clearly distinguishing it).
            Output a clear, professional response.
            """
        )
        chain = prompt | llm
        result = chain.invoke({"context": context_text, "question": question})
        
    return {"analysis_result": result.content}

def output_node(state: AgentState):
    """
    Output Node: Formats the final response with references.
    """
    print("--- Output Node ---")
    analysis = state["analysis_result"]
    docs = state["retrieved_docs"]
    
    # Extract unique sources for citation
    sources = set()
    for d in docs:
        law_name = d['metadata'].get('law_name', 'Unknown')
        sources.add(law_name)
    
    sources_text = "\n".join([f"- {s}" for s in sources])
    
    final_answer = f"{analysis}\n\n---\n**Reference Sources:**\n{sources_text}"
    return {"final_answer": final_answer}

# Orchestrator Class
class MultiAgentOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("parser", parser_node)
        self.workflow.add_node("retriever", retriever_node)
        self.workflow.add_node("analysis", analysis_node)
        self.workflow.add_node("output", output_node)
        
        # Define edges
        self.workflow.set_entry_point("parser")
        self.workflow.add_edge("parser", "retriever")
        self.workflow.add_edge("retriever", "analysis")
        self.workflow.add_edge("analysis", "output")
        self.workflow.add_edge("output", END)
        
        # Compile graph
        self.app = self.workflow.compile()
        
    def run(self, question: str) -> Dict:
        """
        Run the agent workflow.
        """
        print(f"Starting Agent Workflow for: {question}")
        initial_state = {"question": question}
        # invoke returns the final state
        final_state = self.app.invoke(initial_state)
        return final_state

# Singleton instance
orchestrator = MultiAgentOrchestrator()
