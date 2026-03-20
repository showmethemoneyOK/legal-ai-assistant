from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from legal_ai.core.database import get_db
from legal_ai.db.models import SystemConfig
from pydantic import BaseModel

router = APIRouter()

class ConfigUpdate(BaseModel):
    configs: Dict[str, str]

class ConfigDelete(BaseModel):
    key: str

@router.get("/")
def get_all_configs(db: Session = Depends(get_db)):
    """Retrieve all system configurations."""
    configs = db.query(SystemConfig).all()
    result = {c.config_key: c.config_value for c in configs}
    
    # Ensure default configs are returned even if not in DB
    from legal_ai.core.config import DEFAULT_MODEL_NAME
    if "DEFAULT_MODEL_NAME" not in result:
        result["DEFAULT_MODEL_NAME"] = DEFAULT_MODEL_NAME
        
    return result

@router.post("/")
def update_configs(data: ConfigUpdate, db: Session = Depends(get_db)):
    """Update or create system configurations."""
    for key, value in data.configs.items():
        if not value and value != "": # handle None gracefully, but keep empty strings if intentional
            continue
        config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if config:
            config.config_value = value
        else:
            config = SystemConfig(config_key=key, config_value=value)
            db.add(config)
    db.commit()
    return {"message": "Configs updated successfully"}

@router.delete("/{key}")
def delete_config(key: str, db: Session = Depends(get_db)):
    """Delete a system configuration."""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if config:
        db.delete(config)
        db.commit()
        return {"message": f"Config {key} deleted successfully"}
    raise HTTPException(status_code=404, detail="Config not found")
