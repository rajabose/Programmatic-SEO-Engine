# TASK-LP-001: Initialize Python Project Structure

**Derived from**: [Landing Page Generation Plan](../plans/landing-page-generation-plan.md) - Phase 1, Day 1-2  
**Branch**: `feature/landing-page-generation`  
**Assignee**: [Developer Name]  
**Priority**: High  
**Estimated Time**: 6 hours  
**Due Date**: Sprint 1, Day 1-2

## Task Description
Set up the foundational Python project structure for the Landing Page Generation feature including FastAPI server, database setup, and core infrastructure.

## Acceptance Criteria

### Must Have
- [ ] Python 3.10+ project initialized with Poetry
- [ ] FastAPI application structure created
- [ ] PostgreSQL database configured with SQLAlchemy
- [ ] Redis configured for caching and task queue
- [ ] Environment configuration (.env) working
- [ ] Health check endpoint responding with status 200
- [ ] Docker Compose setup for local development
- [ ] Logging configured (structlog)

### Should Have
- [ ] Pre-commit hooks (black, isort, flake8)
- [ ] Basic test structure with pytest
- [ ] API documentation auto-generated (FastAPI default)
- [ ] Git ignore configured for Python

### Nice to Have
- [ ] Makefile with common commands
- [ ] VS Code settings for Python development
- [ ] Initial CI/CD pipeline (GitHub Actions)

## Technical Details

### Project Structure to Create
```
vanchai_seo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Pydantic settings
│   ├── database.py          # SQLAlchemy setup
│   ├── dependencies.py      # FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py       # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── base.py          # Base service class
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py
│   └── tasks/
│       └── __init__.py      # Celery tasks placeholder
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   └── test_health.py       # Health endpoint tests
├── templates/               # Jinja2 templates (empty for now)
├── scripts/                 # Utility scripts
├── migrations/              # Alembic migrations
├── pyproject.toml          # Poetry configuration
├── poetry.lock             # Locked dependencies
├── docker-compose.yml      # Local dev environment
├── Dockerfile              # Production Docker
├── .env.example            # Environment template
├── .env                    # Local environment (gitignored)
├── .gitignore              # Python gitignore
└── README.md               # Project documentation
```

### Implementation Steps

#### Step 1: Initialize Python Project with Poetry
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Create project directory
mkdir -p /Users/rajabose/projects/Vanchai-Programmatic-SEO-Engine

# Initialize Poetry project
cd /Users/rajabose/projects/Vanchai-Programmatic-SEO-Engine
poetry init --name "vanchai-seo" --description "Programmatic SEO Engine for D2C" --author "Vanchai Team" --python "^3.10" --no-interaction

# Add core dependencies
poetry add fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy alembic psycopg2-binary redis celery python-dotenv structlog

# Add development dependencies
poetry add --group dev pytest pytest-asyncio httpx black isort flake8 mypy pre-commit

# Activate virtual environment
poetry shell
```

#### Step 2: Create Configuration (Pydantic Settings)
File: `app/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Application
    APP_NAME: str = "Vanchai SEO Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/vanchai"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "vanchai-landing-pages"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_CONCURRENCY: int = 4
    
    # SEO
    MIN_SEO_SCORE: float = 80.0
    MAX_KEYWORDS_PER_PAGE: int = 15
    
    @property
    def database_async_url(self) -> str:
        """Convert sync database URL to async"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

settings = get_settings()
```

#### Step 3: Database Setup (SQLAlchemy)
File: `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)
```

#### Step 4: FastAPI Application
File: `app/main.py`
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.config import settings
from app.database import init_db
from app.api.v1.endpoints import health

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting up Vanchai SEO Engine")
    init_db()
    yield
    logger.info("Shutting down Vanchai SEO Engine")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Programmatic SEO Engine for D2C platforms",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
```

#### Step 5: Health Check Endpoint
File: `app/api/v1/endpoints/health.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import psutil

from app.database import get_db
from app.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float
    database: str
    redis: str
    memory_usage: dict

@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Redis (placeholder for now)
    redis_status = "not_implemented"
    
    # System metrics
    memory = psutil.virtual_memory()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.APP_VERSION,
        uptime=psutil.boot_time(),
        database=db_status,
        redis=redis_status,
        memory_usage={
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        }
    )

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"ready": True}

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"alive": True}
```

#### Step 6: Docker Compose Setup
File: `docker-compose.yml`
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vanchai
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DEBUG=true
    volumes:
      - ./app:/app/app
    depends_on:
      - db
      - redis
    command: poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vanchai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vanchai
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: poetry run celery -A app.tasks worker --loglevel=info

volumes:
  postgres_data:
  redis_data:
```

#### Step 7: Environment Template
File: `.env.example`
```bash
# Application
DEBUG=true
APP_NAME="Vanchai SEO Engine"
APP_VERSION="1.0.0"

# Database
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/vanchai"

# Redis
REDIS_URL="redis://localhost:6379/0"

# OpenAI
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4"

# AWS
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_REGION="ap-south-1"
S3_BUCKET="vanchai-landing-pages"

# Celery
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"
```

#### Step 8: Pre-commit Configuration
File: `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']
```

## Testing Steps

### Manual Testing
1. **Start services**:
   ```bash
   docker-compose up -d db redis
   ```

2. **Run application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

3. **Test health endpoint**:
   ```bash
   curl http://localhost:8000/api/v1/health/
   ```

4. **Verify response**:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-01T00:00:00",
     "version": "1.0.0",
     "uptime": 123456,
     "database": "connected",
     "redis": "not_implemented",
     "memory_usage": {
       "total_gb": 16.0,
       "used_gb": 8.5,
       "percent": 53.0
     }
   }
   ```

5. **Test API docs**:
   - Open http://localhost:8000/docs
   - Verify Swagger UI loads

### Automated Testing
File: `tests/test_health.py`
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_readiness_probe():
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True

def test_liveness_probe():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True
```

## Definition of Done
- [ ] All project files created
- [ ] Poetry dependencies installed
- [ ] Docker Compose services running
- [ ] Health check endpoint working
- [ ] API documentation accessible
- [ ] Tests passing
- [ ] Pre-commit hooks installed
- [ ] README updated with setup instructions
- [ ] Ready for code review

## Dependencies
- Python 3.10+ installed
- Poetry installed
- Docker and Docker Compose installed
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

## Notes
- Use `poetry shell` to enter virtual environment
- Use `poetry run <command>` to run commands in venv
- All dependencies managed by Poetry
- Follow PEP 8 style guidelines
- Add type hints to all functions

## Related Tasks
- TASK-LP-002: Create Product Catalog Models
- TASK-LP-003: Setup Celery Task Queue

## Review Checklist
- [ ] Code follows Python best practices
- [ ] FastAPI structure is correct
- [ ] Database connection working
- [ ] Docker Compose tested
- [ ] Documentation clear
- [ ] Ready to merge
