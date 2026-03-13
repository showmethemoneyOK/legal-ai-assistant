from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from legal_ai.core.database import get_db
from legal_ai.service.vector_service import rebuild_public_vector_db, update_single_file_in_public_db, search_public_law
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class SearchQuery(BaseModel):
    query: str
    n_results: int = 5

class FileUpdate(BaseModel):
    file_path: str

@router.post("/rebuild", summary="Rebuild Public Vector DB")
def rebuild_vector_db(db: Session = Depends(get_db)):
    try:
        result = rebuild_public_vector_db(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_single", summary="Update Single File in Public DB")
def update_single_file(file: FileUpdate, db: Session = Depends(get_db)):
    try:
        result = update_single_file_in_public_db(db, file.file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", summary="Search Public Law")
def search(query: SearchQuery):
    try:
        results = search_public_law(query.query, query.n_results)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
