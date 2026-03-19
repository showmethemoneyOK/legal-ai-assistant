from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from legal_ai.core.database import Base

class User(Base):
    """
    Represents a user in the system.
    """
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="user") # e.g., 'admin', 'lawyer', 'user'
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
    """Metadata for files indexed in the public vector database."""
    __tablename__ = "public_law_files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    file_hash = Column(String(64), nullable=False) # SHA-256
    law_name = Column(String(255))
    status = Column(String(20), default="indexed") # indexed, error, updated
    chunk_count = Column(Integer, default=0)
    update_time = Column(DateTime, default=datetime.utcnow)

class VectorLog(Base):
    """Audit log for vector database operations."""
    __tablename__ = "vector_log"

    id = Column(Integer, primary_key=True, index=True)
    operate_type = Column(String(50)) # rebuild, update_single, delete
    file_path = Column(String(500))
    operator = Column(String(50))
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

class SystemConfig(Base):
    """
    Stores system-wide configurations, such as LLM settings.
    """
    __tablename__ = "sys_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(50), unique=True, index=True, nullable=False)
    config_value = Column(Text)
    description = Column(String(255))
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentExecutionLog(Base):
    """Audit log for multi-agent workflow executions."""
    __tablename__ = "agent_execution_log"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), index=True)
    question = Column(Text)
    node_name = Column(String(50))
    summary = Column(Text)
    verifier_score = Column(Float, nullable=True)
    model_used = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)

class LLMModel(Base):
    """
    Stores dynamically added LLM model configurations for direct connection.
    """
    __tablename__ = "llm_model"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), unique=True, index=True, nullable=False) # Alias/Frontend ID
    target_model = Column(String(100), nullable=False) # Actual model name, e.g., gpt-4, qwen2.5:7b, deepseek-chat
    api_base = Column(String(255)) # Base URL, e.g., http://127.0.0.1:11434/v1 or https://api.deepseek.com/v1
    api_key = Column(String(255)) # Optional for local models, required for online models
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
