from sqlalchemy.orm import Session
from legal_ai.db.models import LegalDoc, DocVersion
from datetime import datetime

def create_doc(db: Session, doc: LegalDoc, user_id: int):
    db_doc = LegalDoc(
        title=doc.title,
        content=doc.content,
        doc_type=doc.doc_type,
        user_id=user_id,
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow()
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Create first version
    db_version = DocVersion(
        doc_id=db_doc.id,
        content=doc.content,
        operator_id=user_id,
        create_time=datetime.utcnow()
    )
    db.add(db_version)
    db.commit()
    
    return db_doc

def get_doc(db: Session, doc_id: int):
    return db.query(LegalDoc).filter(LegalDoc.id == doc_id).first()

def get_user_docs(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(LegalDoc).filter(LegalDoc.user_id == user_id).offset(skip).limit(limit).all()

def update_doc(db: Session, doc_id: int, content: str, user_id: int):
    db_doc = db.query(LegalDoc).filter(LegalDoc.id == doc_id).first()
    if not db_doc:
        return None
    
    db_doc.content = content
    db_doc.update_time = datetime.utcnow()
    
    # Create new version
    db_version = DocVersion(
        doc_id=doc_id,
        content=content,
        operator_id=user_id,
        create_time=datetime.utcnow()
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_doc)
    
    return db_doc
