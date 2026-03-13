import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sqlalchemy.orm import Session
from datetime import datetime
from legal_ai.core.config import CHROMA_PERSIST_DIRECTORY, PUBLIC_LAW_DIR
from legal_ai.db.models import PublicLawFile, VectorLog
from legal_ai.service.law_service import extract_text_from_file, chunk_text, calculate_file_hash

# Global variable to store the ChromaDB client instance
_chroma_client = None
_embedding_function = None

def get_embedding_function():
    """
    Get the embedding function. Uses SentenceTransformer by default for better compatibility.
    """
    global _embedding_function
    if _embedding_function is None:
        try:
            # Use 'all-MiniLM-L6-v2' which is small and effective
            _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Failed to load SentenceTransformer: {e}")
            # Fallback or raise error? For now let it crash if we can't load embeddings
            raise e
    return _embedding_function

def get_chroma_client():
    """
    Get or create a persistent ChromaDB client.
    
    Returns:
        chromadb.PersistentClient: The initialized ChromaDB client.
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
    return _chroma_client

def get_public_collection():
    """
    Get or create the 'public_law' collection in ChromaDB.
    
    Returns:
        chromadb.Collection: The 'public_law' collection object.
    """
    client = get_chroma_client()
    ef = get_embedding_function()
    # get_or_create_collection is idempotent
    return client.get_or_create_collection(name="public_law", embedding_function=ef)

def rebuild_public_vector_db(db: Session, operator: str = "system"):
    """
    Rebuilds the entire public law vector database from scratch.
    
    WARNING: This operation is destructive. It deletes all existing data in the 'public_law' collection
    and clears the 'public_law_files' table in the database before reprocessing all files.
    
    Args:
        db (Session): The database session.
        operator (str): The name of the user or system triggering the rebuild.
        
    Returns:
        dict: A dictionary containing the status and the number of files processed.
    """
    client = get_chroma_client()
    ef = get_embedding_function()
    
    # 1. Delete existing collection if it exists and create a new one to start fresh
    try:
        client.delete_collection("public_law")
    except ValueError:
        pass # Collection might not exist, which is fine
    
    collection = client.create_collection("public_law", embedding_function=ef)
    
    # Clear database records for public files to sync with vector DB
    db.query(PublicLawFile).delete()
    db.commit()

    # 2. Iterate through files in PUBLIC_LAW_DIR and process them
    files_processed = 0
    for root, dirs, files in os.walk(PUBLIC_LAW_DIR):
        for file in files:
            if file.lower().endswith(('.docx', '.pdf')):
                file_path = os.path.join(root, file)
                process_file(db, collection, file_path)
                files_processed += 1
    
    # Log the operation for audit purposes
    log_entry = VectorLog(
        operate_type="rebuild",
        file_path="ALL",
        operator=operator,
        create_time=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    
    return {"status": "success", "files_processed": files_processed}

def update_single_file_in_public_db(db: Session, file_path: str, operator: str = "system"):
    """
    Updates a single file in the public vector database.
    
    This function handles both updating existing files and adding new files.
    It first removes any existing vectors associated with the file path, then re-indexes the file.
    
    Args:
        db (Session): The database session.
        file_path (str): The absolute path to the file to be updated.
        operator (str): The name of the user or system triggering the update.
        
    Returns:
        dict: A dictionary containing the status ('updated' or 'deleted') and the file path.
    """
    collection = get_public_collection()
    
    # 1. Check if file exists in DB and delete old vectors
    existing_file = db.query(PublicLawFile).filter(PublicLawFile.file_path == file_path).first()
    if existing_file:
        # Delete old vectors using metadata filter 'file_path'
        # This ensures we only remove vectors belonging to this specific file
        collection.delete(where={"file_path": file_path})
        # Remove DB record
        db.delete(existing_file)
        db.commit()
    
    # 2. Process the new file content if it still exists on disk
    if os.path.exists(file_path):
        process_file(db, collection, file_path)
        status = "updated"
    else:
        status = "deleted" # File was removed from disk, so we just removed it from DB/VectorDB

    # Log the operation
    log_entry = VectorLog(
        operate_type="update_single",
        file_path=file_path,
        operator=operator,
        create_time=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    
    return {"status": status, "file_path": file_path}

def process_file(db: Session, collection, file_path: str):
    """
    Helper function to process a single file: extract text, chunk, embed, and store in vector DB.
    
    Args:
        db (Session): The database session.
        collection (chromadb.Collection): The ChromaDB collection to store vectors in.
        file_path (str): The path to the file to process.
    """
    try:
        # Extract text from file (docx or pdf)
        text = extract_text_from_file(file_path)
        if not text:
            print(f"Skipping empty or unreadable file: {file_path}")
            return

        # Calculate file hash for version control
        file_hash = calculate_file_hash(file_path)
        file_name = os.path.basename(file_path)
        law_name = os.path.splitext(file_name)[0]
        
        # Split text into manageable chunks
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Create a unique ID for each chunk: hash_index
            chunk_id = f"{file_hash}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            # Metadata is crucial for filtering and retrieval
            metadatas.append({
                "library": "public",
                "file_path": file_path,
                "law_name": law_name,
                "file_hash": file_hash,
                "chunk_index": i
            })
            
        if ids:
            # Add vectors to ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            # Save file metadata to SQLite for tracking
            db_file = PublicLawFile(
                file_name=file_name,
                file_path=file_path,
                file_hash=file_hash,
                law_name=law_name,
                status="indexed",
                chunk_count=len(chunks),
                update_time=datetime.utcnow()
            )
            db.add(db_file)
            db.commit()
            print(f"Successfully indexed: {file_path}")
            
    except Exception as e:
        error_msg = f"Error processing file {file_path}: {e}"
        print(error_msg)
        # Re-raise the exception so the API layer can catch it and report to the user
        raise Exception(error_msg)


def search_public_law(query_text: str, n_results: int = 5):
    """
    Searches the public law vector database for relevant chunks.
    
    Args:
        query_text (str): The query string (e.g., a legal question).
        n_results (int): The number of top results to return.
        
    Returns:
        dict: The search results from ChromaDB, containing ids, documents, metadatas, and distances.
    """
    collection = get_public_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results
