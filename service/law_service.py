import os
import hashlib
from docx import Document
import pdfplumber

def calculate_file_hash(file_path: str) -> str:
    """
    Calculates the SHA-256 hash of a file.
    
    This is used to uniquely identify file versions and detect changes.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        str: The SHA-256 hash digest string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from a .docx or .pdf file.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        str: The extracted text content, or an empty string if extraction failed.
    """
    _, ext = os.path.splitext(file_path)
    text = ""
    
    if ext.lower() == ".docx":
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error reading docx file {file_path}: {e}")
            return ""
    elif ext.lower() == ".pdf":
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading pdf file {file_path}: {e}")
            return ""
    else:
        print(f"Unsupported file type: {ext}")
        return ""
        
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text into chunks of a given size with overlap.
    
    Chunking is essential for embedding models which have a maximum token limit.
    Overlap helps maintain context between chunks.
    
    Args:
        text (str): The input text to be chunked.
        chunk_size (int): The maximum size of each chunk (in characters).
        overlap (int): The number of characters to overlap between chunks.
        
    Returns:
        list[str]: A list of text chunks.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move start position forward, but back by 'overlap' amount
        start += chunk_size - overlap
        
    return chunks
