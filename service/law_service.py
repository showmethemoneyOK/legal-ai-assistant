import os
import hashlib
import re
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

def chunk_legal_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Intelligently splits Chinese legal texts into chunks based on hierarchy (Part, Chapter, Section, Article).
    
    Structure:
    - Identifies '第X编', '第X章', '第X节', '第X条'.
    - Uses 'Article' (条) as the primary unit.
    - Prepends hierarchy context (e.g., "第一编 总则 第一章 ...") to each article chunk.
    - If an article + context exceeds chunk_size, it falls back to standard sliding window chunking.
    
    Args:
        text (str): The input legal text.
        chunk_size (int): Max chars per chunk.
        overlap (int): Overlap for large chunks.
        
    Returns:
        list[str]: List of semantically aware chunks.
    """
    if not text:
        return []

    lines = text.split('\n')
    chunks = []
    
    # Regex patterns for Chinese legal structure
    # Matches lines starting with "第...编/章/节/条" possibly followed by a title
    part_pattern = re.compile(r'^\s*第[零一二三四五六七八九十百]+编\s+.*$')
    chapter_pattern = re.compile(r'^\s*第[零一二三四五六七八九十百]+章\s+.*$')
    section_pattern = re.compile(r'^\s*第[零一二三四五六七八九十百]+节\s+.*$')
    # Article pattern: "第X条" at start of line
    article_pattern = re.compile(r'^\s*第[零一二三四五六七八九十百]+条\s*.*')
    
    current_part = ""
    current_chapter = ""
    current_section = ""
    
    current_article_content = []
    
    def flush_article():
        nonlocal current_article_content
        if current_article_content:
            content = "\n".join(current_article_content)
            
            # Construct context string
            context_parts = []
            if current_part: context_parts.append(current_part)
            if current_chapter: context_parts.append(current_chapter)
            if current_section: context_parts.append(current_section)
            
            context = " ".join(context_parts).strip()
            
            # Combine context and content
            full_text = f"{context}\n{content}".strip()
            
            # If the single article is too long, split it using standard chunking
            if len(full_text) > chunk_size:
                sub_chunks = chunk_text(full_text, chunk_size, overlap)
                chunks.extend(sub_chunks)
            else:
                chunks.append(full_text)
            
            # Clear buffer
            current_article_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for structural markers
        if part_pattern.match(line):
            flush_article() # Finish previous article
            current_part = line
            current_chapter = "" # Reset lower levels
            current_section = ""
        elif chapter_pattern.match(line):
            flush_article()
            current_chapter = line
            current_section = ""
        elif section_pattern.match(line):
            flush_article()
            current_section = line
        elif article_pattern.match(line):
            flush_article()
            # Start new article
            current_article_content.append(line)
        else:
            # Regular content line
            # If we haven't started an article yet (e.g. preamble text), we treat it as part of the current context block
            # Or if inside an article, append to it
            current_article_content.append(line)
            
    # Flush the last accumulating article
    flush_article()
    
    return chunks
