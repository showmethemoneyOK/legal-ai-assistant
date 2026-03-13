from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from legal_ai.core.database import get_db
from legal_ai.service.doc_service import create_doc, get_doc, get_user_docs, update_doc
from legal_ai.db.models import LegalDoc
from pydantic import BaseModel

router = APIRouter()

class DocCreate(BaseModel):
    title: str
    content: str
    doc_type: str
    user_id: int

class DocUpdate(BaseModel):
    content: str
    user_id: int

class DocResponse(BaseModel):
    id: int
    title: str
    content: str
    doc_type: str
    user_id: int

    class Config:
        orm_mode = True

@router.post("/", response_model=DocResponse)
def create_legal_doc(doc: DocCreate, db: Session = Depends(get_db)):
    return create_doc(db=db, doc=doc, user_id=doc.user_id)

@router.get("/{doc_id}", response_model=DocResponse)
def read_doc(doc_id: int, db: Session = Depends(get_db)):
    db_doc = get_doc(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Doc not found")
    return db_doc

@router.get("/user/{user_id}", response_model=List[DocResponse])
def read_user_docs(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_user_docs(db, user_id=user_id, skip=skip, limit=limit)

@router.put("/{doc_id}", response_model=DocResponse)
def update_legal_doc(doc_id: int, doc: DocUpdate, db: Session = Depends(get_db)):
    db_doc = update_doc(db, doc_id=doc_id, content=doc.content, user_id=doc.user_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Doc not found")
    return db_doc
