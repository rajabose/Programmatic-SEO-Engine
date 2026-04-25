# Plan: Landing Page Generation Implementation (Python Stack)

**Derived from**: [Landing Page Generation Spec](../specs/landing-page-generation-spec.md)  
**Assigned to**: Development Team  
**Sprint**: Sprint 1-6  
**Estimated Effort**: 6 weeks  
**Target**: 13,000 landing pages on discover.vanchai.in

## Phase 1: Foundation & Setup (Week 1)

### Sprint Goals
Set up Python project structure, FastAPI server, and core infrastructure.

### Day 1-2: Project Initialization
- [ ] Initialize Python project with Poetry/pipenv
- [ ] Set up FastAPI application structure
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching and task queue
- [ ] Configure environment variables (.env)
- [ ] Set up logging (structlog)

**Deliverables**:
```
vanchai_seo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   ├── api/                 # API endpoints
│   └── tasks/               # Celery tasks
├── tests/
├── templates/               # Jinja2 templates
├── scripts/                 # Utility scripts
├── pyproject.toml          # Poetry config
└── docker-compose.yml      # Local dev
```

**Code Snippets**:
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/vanchai"
    REDIS_URL: str = "redis://localhost:6379"
    OPENAI_API_KEY: str
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    S3_BUCKET: str = "vanchai-landing-pages"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Day 3-4: Database Models & Migrations
- [ ] Create SQLAlchemy models for Product, LandingPage, Job
- [ ] Set up Alembic migrations
- [ ] Create Pydantic schemas for API
- [ ] Add database indexes for performance
- [ ] Seed data for testing

**Models**:
```python
# app/models/product.py
from sqlalchemy import Column, String, Float, Integer, Boolean
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    platform = Column(String, index=True)  # wix, amazon, myntra, nykaa
    platform_id = Column(String)
    name = Column(String, index=True)
    category = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    images = Column(JSON)
    url = Column(String)
    in_stock = Column(Boolean, default=True)
    rating = Column(Float)
    review_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Day 5: API Structure & Health Checks
- [ ] Create FastAPI router structure
- [ ] Implement health check endpoints
- [ ] Add request/response middleware
- [ ] Set up API documentation (auto-generated)
- [ ] Add error handling middleware

**API Structure**:
```python
# app/api/v1/endpoints/generation.py
from fastapi import APIRouter, BackgroundTasks
from app.services.generation import GenerationService

router = APIRouter()

@router.post("/generate/bulk")
async def generate_bulk_pages(
    request: BulkGenerationRequest,
    background_tasks: BackgroundTasks
):
    service = GenerationService()
    job = await service.start_bulk_generation(request)
    return {"job_id": job.id, "status": "queued"}

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    service = GenerationService()
    return await service.get_job_status(job_id)
```

## Phase 2: Core Services (Week 2)

### Sprint Goals
Implement Python services for catalog, content generation, and page building.

### Day 1-2: Product Catalog Manager
- [ ] Implement Wix Store API client
- [ ] Implement Amazon Product API client
- [ ] Implement Myntra scraper
- [ ] Implement Nykaa API client
- [ ] Build catalog synchronization service
- [ ] Add product deduplication logic

**Service Implementation**:
```python
# app/services/catalog_manager.py
import requests
from typing import List
from app.models.product import Product

class CatalogManager:
    def __init__(self):
        self.wix_client = WixAPIClient()
        self.amazon_client = AmazonAPIClient()
        
    async def sync_all_platforms(self) -> SyncResult:
        """Synchronize product catalogs from all platforms"""
        
        wix_products = await self.wix_client.fetch_products()
        amazon_products = await self.amazon_client.fetch_products()
        myntra_products = await self._scrape_myntra()
        nykaa_products = await self._fetch_nykaa()
        
        all_products = self._deduplicate_products(
            wix_products + amazon_products + 
            myntra_products + nykaa_products
        )
        
        await self._upsert_to_database(all_products)
        
        return SyncResult(
            total_products=len(all_products),
            by_platform={
                "wix": len(wix_products),
                "amazon": len(amazon_products),
                "myntra": len(myntra_products),
                "nykaa": len(nykaa_products)
            }
        )
```

### Day 3-4: Keyword Engine
- [ ] Implement keyword research with OpenAI
- [ ] Build keyword clustering algorithm
- [ ] Create long-tail keyword generator
- [ ] Add category-based keyword mapping
- [ ] Implement keyword competition analysis

```python
# app/services/keyword_engine.py
from openai import OpenAI

class KeywordEngine:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
    async def generate_keywords(self, product: Product) -> List[KeywordCluster]:
        """Generate keyword clusters for product"""
        
        prompt = f"""
        Generate SEO keywords for:
        Product: {product.name}
        Category: {product.category}
        
        Provide:
        1. Primary keywords (3-5 high-volume)
        2. Secondary keywords (5-10 medium-volume)
        3. Long-tail keywords (10-15 specific)
        4. Category variations
        
        Format: JSON with keyword, volume, competition, intent
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return self._parse_keywords(response.choices[0].message.content)
```

### Day 5: Content Generator Setup
- [ ] Set up OpenAI API integration
- [ ] Create prompt templates
- [ ] Implement content generation service
- [ ] Add content caching (Redis)
- [ ] Set up content quality checks

## Phase 3: Template & Page Building (Week 3)

### Sprint Goals
Build Jinja2 templates and landing page generation system.

### Day 1-2: Jinja2 Template System
- [ ] Create base template structure
- [ ] Build platform-specific templates
- [ ] Implement template inheritance
- [ ] Add custom Jinja2 filters
- [ ] Create responsive CSS framework

**Templates**:
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="{{ meta_description }}">
    {{ schema_markup | tojson | safe }}
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <main>
        {% block content %}{% endblock %}
    </main>
    {% include 'components/cta.html' %}
</body>
</html>

<!-- templates/landing_page.html -->
{% extends "base.html" %}
{% block content %}
<article class="product-landing">
    <h1>{{ headline }}</h1>
    <div class="product-content">
        {{ body | safe }}
    </div>
    <div class="platform-links">
        {% for platform, link in platform_links.items() %}
        <a href="{{ link }}" class="btn btn-{{ platform }}">
            Buy on {{ platform | title }}
        </a>
        {% endfor %}
    </div>
</article>
{% endblock %}
```

### Day 3-4: Landing Page Builder
- [ ] Implement HTML generation from templates
- [ ] Add schema markup generation
- [ ] Optimize HTML for performance
- [ ] Implement image optimization
- [ ] Add lazy loading for images

```python
# app/services/page_builder.py
from jinja2 import Environment, FileSystemLoader

class LandingPageBuilder:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
    def build_page(self, content: LandingPageContent, template: str = "landing_page.html") -> str:
        """Generate optimized HTML landing page"""
        
        template = self.env.get_template(template)
        
        html = template.render(
            title=content.title,
            meta_description=content.meta_description,
            headline=content.headline,
            body=content.body,
            platform_links=content.platform_links,
            schema_markup=self._generate_schema_json_ld(content),
            product_images=content.images
        )
        
        # Optimize HTML
        html = self._minify_html(html)
        html = self._add_lazy_loading(html)
        html = self._optimize_images(html)
        
        return html
    
    def _generate_schema_json_ld(self, content: LandingPageContent) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": content.product_name,
            "description": content.meta_description,
            "image": content.images,
            "offers": {
                "@type": "Offer",
                "price": content.price,
                "availability": "https://schema.org/InStock"
            }
        }
```

### Day 5: SEO Optimization Service
- [ ] Implement on-page SEO analysis
- [ ] Build SEO scoring algorithm
- [ ] Add content optimization
- [ ] Create meta tag optimization
- [ ] Implement internal linking

## Phase 4: Task Queue & Automation (Week 4)

### Sprint Goals
Set up Celery for distributed task processing and automation.

### Day 1-2: Celery Setup
- [ ] Configure Celery with Redis broker
- [ ] Create task definitions
- [ ] Set up task routing
- [ ] Configure task retry policies
- [ ] Add task monitoring (Flower)

```python
# app/tasks/generation.py
from celery import Celery
from app.services.generation import GenerationService

app = Celery('vanchai_seo')
app.config_from_object('app.celeryconfig')

@app.task(bind=True, max_retries=3)
def generate_single_page(self, product_id: str, keywords: List[str], platform: str):
    """Generate single landing page"""
    try:
        service = GenerationService()
        result = await service.generate_page(product_id, keywords, platform)
        return result
    except Exception as exc:
        # Retry with exponential backoff
        self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)

@app.task
def bulk_generation_task(category: str, platforms: List[str]):
    """Orchestrate bulk page generation"""
    products = get_products_by_category(category)
    
    for product in products:
        keywords = generate_keywords_for_product(product)
        for platform in platforms:
            generate_single_page.delay(product.id, keywords, platform)
    
    return {"total_tasks": len(products) * len(platforms)}
```

### Day 3-4: Deployment Pipeline
- [ ] Set up S3 bucket for static hosting
- [ ] Configure CloudFront CDN
- [ ] Implement page upload to S3
- [ ] Add cache invalidation
- [ ] Set up domain mapping (discover.vanchai.in)

### Day 5: Monitoring & Analytics
- [ ] Add structured logging
- [ ] Set up Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Implement error tracking (Sentry)
- [ ] Add performance monitoring

## Phase 5: Integration & Testing (Week 5)

### Sprint Goals
Integrate all components and run comprehensive tests.

### Day 1-2: Platform Integration Testing
- [ ] Test Wix API integration
- [ ] Test Amazon API integration
- [ ] Test Myntra scraping
- [ ] Test Nykaa API integration
- [ ] Verify product data accuracy

### Day 3-4: Load Testing & Optimization
- [ ] Load test API endpoints (locust)
- [ ] Test concurrent generation (50+ parallel)
- [ ] Optimize database queries
- [ ] Tune Celery worker count
- [ ] Benchmark generation speed

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class LandingPageUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_bulk(self):
        self.client.post("/api/v1/generate/bulk", json={
            "category": "skincare",
            "keywords": ["best moisturizer", "face cream"],
            "platforms": ["wix", "amazon"]
        })
    
    @task
    def check_status(self):
        self.client.get("/api/v1/jobs/test-job-id/status")
```

### Day 5: Quality Assurance
- [ ] Run SEO quality checks on sample pages
- [ ] Check mobile responsiveness
- [ ] Verify page load times
- [ ] Test cross-browser compatibility
- [ ] Validate schema markup

## Phase 6: Deployment & Launch (Week 6)

### Sprint Goals
Deploy to production and launch 13,000 landing pages.

### Day 1-2: Staging Deployment
- [ ] Deploy API to staging
- [ ] Configure staging database
- [ ] Test end-to-end flow
- [ ] Run integration tests
- [ ] Performance validation

### Day 3-4: Production Deployment
- [ ] Set up production infrastructure (AWS)
- [ ] Deploy FastAPI application
- [ ] Configure production database
- [ ] Set up monitoring and alerting
- [ ] Configure SSL certificates

### Day 5: Bulk Generation & Launch
- [ ] Start bulk generation for all 13,000 pages
- [ ] Monitor generation progress
- [ ] Handle errors and retries
- [ ] Validate all pages are live
- [ ] Submit sitemap to Google
- [ ] Monitor analytics and SEO performance

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │   Admin Panel   │  │   Analytics     │  │   Monitoring    │        │
│  │   (React/Vue)   │  │   Dashboard     │  │   (Grafana)     │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer (FastAPI)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │  Generation     │  │    Jobs         │  │    Analytics    │        │
│  │  Endpoints      │  │    Endpoints    │  │    Endpoints    │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer (Python)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐│
│  │   Catalog    │  │   Keyword    │  │   Content    │  │   Page  ││
│  │   Manager    │  │   Engine     │  │   Generator  │  │  Builder││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │     SEO      │  │   Platform   │  │    Queue     │             │
│  │  Optimizer   │  │  Connectors  │  │   Manager    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐│
│  │  PostgreSQL  │  │    Redis     │  │  AWS S3      │  │OpenAI   ││
│  │  (Products)  │  │  (Queue +    │  │(Landing Pages│  │  API    ││
│  │              │  │   Cache)     │  │ + Static)    │  │         ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Python Dependencies

### Core
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.0
alembic==1.12.0
psycopg2-binary==2.9.0
```

### Services
```
celery==5.3.4
redis==5.0.0
openai==1.0.0
jinja2==3.1.0
boto3==1.34.0
requests==2.31.0
beautifulsoup4==4.12.0
```

### Dev & Testing
```
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.25.0
locust==2.18.0
black==23.0.0
isort==5.12.0
mypy==1.7.0
```

## Deployment Configuration

### Docker Compose (Development)
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vanchai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vanchai
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  celery:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/vanchai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  flower:
    image: mher/flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

volumes:
  postgres_data:
```

## Success Criteria

### Functional
- [ ] 13,000 landing pages generated and deployed
- [ ] Multi-platform support (Wix, Amazon, Myntra, Nykaa)
- [ ] Average generation time <30 seconds per page
- [ ] Bulk generation rate: 500+ pages/day
- [ ] API endpoints working and documented

### Performance
- [ ] API response time <2 seconds
- [ ] Page load time <3 seconds
- [ ] 99.9% uptime
- [ ] Handle 50+ concurrent generations
- [ ] Redis cache hit rate >80%

### Quality
- [ ] Average SEO score >80/100
- [ ] Content uniqueness >95%
- [ ] Mobile responsiveness 100%
- [ ] Zero critical bugs
- [ ] Python code coverage >85%

### Business
- [ ] discover.vanchai.in subdomain live
- [ ] Google indexing all pages
- [ ] Traffic increase to Wix D2C
- [ ] Cross-platform visibility improved

## Risk Management

### High Priority Risks
1. **OpenAI API rate limiting** - Multiple keys, request queue, caching
2. **13,000 page deployment** - Incremental deployment, CDN, pre-rendering
3. **Platform API changes** - Abstraction layer, monitoring
4. **Content quality variance** - SEO scoring, human review queue

### Mitigation Strategies
- Implement circuit breakers for external APIs
- Use Celery task retry with exponential backoff
- Monitor API usage and costs
- Maintain fallback content templates

## Review & Approval

**Plan Review Date**: [To be scheduled]  
**Tech Lead Approval**: Pending  
**Product Owner Approval**: Pending  
**Sprint Capacity**: 6 weeks (3 sprints)  
**Status**: Ready for Implementation

---

**Next Steps**:
1. Create Git branch: `feature/landing-page-generation`
2. Set up Python environment with Poetry
3. Start Phase 1: Foundation & Setup
4. Daily standups to track progress
5. Weekly demos with stakeholders
