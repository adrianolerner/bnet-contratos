import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from database import engine, Base
import models
from auth import limiter

from routers import api, backups
from scheduler import start_scheduler

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BNET Contratos API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def startup_event():
    start_scheduler()
    import create_admin

# CORS config
cors_origin = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(api.router, prefix="/api")
app.include_router(backups.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "BNET Contratos API is running"}


