from fastapi import FastAPI
from legal_ai.core.database import engine, Base
from legal_ai.api.routes import auth, doc, vector, agent, config, proxy_models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Legal AI Assistant", version="1.0.0")

# Include routers
app.include_router(auth.router, prefix="/api/user", tags=["User"])
app.include_router(doc.router, prefix="/api/doc", tags=["Doc"])
app.include_router(vector.router, prefix="/api/vector", tags=["Vector"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(proxy_models.router, prefix="/api/proxy", tags=["Proxy Models"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Legal AI Assistant API"}
