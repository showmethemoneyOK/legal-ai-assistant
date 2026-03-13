from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from legal_ai.core.database import Base

class User(Base):
    """
    Represents a user in the system.
    """
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    docs = relationship("LegalDoc", back_populates="owner")
    logs = relationship("OperationLog", back_populates="user")
    shared_to_me = relationship("DocPermission", back_populates="user")

class LegalDoc(Base):
    """
    Represents a legal document created by a user.
    """
    __tablename__ = "legal_doc"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"))
    title = Column(String)
    content = Column(Text)
    doc_type = Column(String) # e.g., "contract", "legal_opinion"
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="docs")
    versions = relationship("DocVersion", back_populates="doc")
    permissions = relationship("DocPermission", back_populates="doc")

class DocVersion(Base):
    """
    Stores version history for a legal document.
    Created automatically whenever a document is updated.
    """
    __tablename__ = "doc_version"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("legal_doc.id"))
    content = Column(Text)
    operator_id = Column(Integer) # ID of user who made changes
    create_time = Column(DateTime, default=datetime.utcnow)

    doc = relationship("LegalDoc", back_populates="versions")

class DocPermission(Base):
    """
    Manages file sharing permissions between users.
    """
    __tablename__ = "doc_permission"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("legal_doc.id"))
    owner_id = Column(Integer)
    to_user_id = Column(Integer, ForeignKey("sys_user.id"))
    permission = Column(Integer) # 1=read, 2=write
    create_time = Column(DateTime, default=datetime.utcnow)

    doc = relationship("LegalDoc", back_populates="permissions")
    user = relationship("User", back_populates="shared_to_me")

class PublicLawFile(Base):
    """
    Tracks the indexing status of public law files in the vector database.
    Used to manage updates and avoid re-indexing unchanged files.
    """
    __tablename__ = "public_law_files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_path = Column(String, unique=True)
    file_hash = Column(String) # SHA-256 hash for change detection
    law_name = Column(String)
    status = Column(String) # e.g., "indexed", "failed"
    chunk_count = Column(Integer)
    update_time = Column(DateTime, default=datetime.utcnow)

class VectorLog(Base):
    """
    Logs operations performed on the vector database (rebuild, update, delete).
    """
    __tablename__ = "vector_log"

    id = Column(Integer, primary_key=True, index=True)
    operate_type = Column(String) # rebuild/update/delete
    file_path = Column(String)
    operator = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)

class OperationLog(Base):
    """
    General audit log for user actions.
    """
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"))
    action = Column(String)
    target_type = Column(String)
    target_id = Column(Integer)
    create_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
