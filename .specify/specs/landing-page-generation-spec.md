# Spec: Landing Page Generation for D2C Platforms

## Feature Overview
**Name**: Landing Page Generation  
**Branch**: `feature/landing-page-generation`  
**Status**: In Progress  
**Priority**: High  
**Owner**: Development Team

## Purpose
Generate 13,000+ SEO-optimized landing pages on discover.vanchai.in to drive traffic to Wix D2C, Amazon, Myntra, and Nykaa platforms.

## Target Platforms & Requirements

### Wix D2C Store
- Product catalog integration
- Direct checkout links
- Inventory sync
- Price matching

### Amazon Marketplace
- Product ASIN mapping
- Affiliate link generation
- Review integration
- Prime eligibility badges

### Myntra
- Product code mapping
- Fashion category optimization
- Size guide integration
- Trending tags

### Nykaa
- Beauty product mapping
- Ingredient highlights
- Skin type recommendations
- Rating integration

## User Stories

### Story 1: Bulk Landing Page Generation
As a marketing manager, I want to generate 500+ landing pages per day so that we can reach 13,000 pages in 30 days.

**Acceptance Criteria:**
- Input: Product category + keyword clusters
- Output: Static HTML landing pages
- Rate: 500+ pages/day
- Quality: SEO score >80
- Multi-platform: Wix, Amazon, Myntra, Nykaa

### Story 2: Platform-Specific Optimization
As a SEO specialist, I want platform-specific landing pages so that each platform gets optimized traffic.

**Acceptance Criteria:**
- Platform-specific CTAs
- Unique content per platform (95%+ uniqueness)
- Platform badge integration
- Deep linking to product pages

### Story 3: SEO Performance
As a growth manager, I want high-ranking landing pages so that organic traffic increases by 200%.

**Acceptance Criteria:**
- SEO score >80/100
- Page load <3 seconds
- Mobile-first responsive
- Schema markup for products

## Technical Specification

### Architecture (Python-Based)

```python
# Core Stack
- Python 3.10+
- FastAPI (API framework)
- Celery + Redis (Task queue)
- Jinja2 (Template engine)
- OpenAI API (Content generation)
- BeautifulSoup/Scrapy (Scraping)
- SQLAlchemy/PostgreSQL (Database)
- boto3 (AWS deployment)
```

### Python Services

#### 1. Product Catalog Service
```python
# services/catalog_manager.py
class ProductCatalogManager:
    """Manage unified product catalog from all platforms"""
    
    def fetch_wix_products(self) -> List[Product]:
        """Fetch products from Wix Store API"""
        pass
    
    def fetch_amazon_products(self) -> List[Product]:
        """Fetch products from Amazon Product API"""
        pass
    
    def fetch_myntra_products(self) -> List[Product]:
        """Scrape/scrape Myntra products"""
        pass
    
    def fetch_nykaa_products(self) -> List[Product]:
        """Fetch products from Nykaa"""
        pass
    
    def sync_catalog(self) -> CatalogSyncResult:
        """Synchronize all platform catalogs"""
        pass
```

#### 2. Keyword Engine
```python
# services/keyword_engine.py
class KeywordEngine:
    """Generate keywords from product categories"""
    
    def analyze_category(self, category: str) -> KeywordCluster:
        """Generate keyword clusters for category"""
        pass
    
    def generate_long_tail_keywords(self, seed: str) -> List[str]:
        """Generate long-tail variations"""
        pass
    
    def cluster_keywords(self, keywords: List[str]) -> List[KeywordCluster]:
        """Group keywords by intent"""
        pass
```

#### 3. Content Generation Service
```python
# services/content_generator.py
class ContentGenerator:
    """Generate SEO content using OpenAI"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
    
    def generate_landing_page_content(
        self, 
        product: Product,
        keywords: List[str],
        platform: Platform
    ) -> LandingPageContent:
        """Generate complete landing page content"""
        
        prompt = self._build_prompt(product, keywords, platform)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return self._parse_response(response)
    
    def _build_prompt(self, product, keywords, platform) -> str:
        return f"""
        Generate SEO-optimized landing page content for:
        Product: {product.name}
        Category: {product.category}
        Keywords: {', '.join(keywords)}
        Platform: {platform.value}
        
        Include:
        - Compelling headline
        - SEO meta description (150-160 chars)
        - Product description (300-500 words)
        - Key features/benefits
        - Platform-specific CTA
        """
```

#### 4. Landing Page Builder
```python
# services/page_builder.py
class LandingPageBuilder:
    """Build static HTML landing pages"""
    
    def __init__(self, template_dir: str):
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir)
        )
    
    def build_page(
        self, 
        content: LandingPageContent,
        template: str = "landing_page.html"
    ) -> str:
        """Generate HTML from content and template"""
        
        template = self.jinja_env.get_template(template)
        
        html = template.render(
            title=content.title,
            meta_description=content.meta_description,
            content=content.body,
            cta=content.cta,
            platform_links=content.platform_links,
            schema_markup=self._generate_schema(content)
        )
        
        return self._optimize_html(html)
    
    def _generate_schema(self, content: LandingPageContent) -> dict:
        """Generate JSON-LD schema markup"""
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": content.product_name,
            "description": content.meta_description,
            # ... more schema fields
        }
```

#### 5. SEO Optimization Service
```python
# services/seo_optimizer.py
class SEOOptimizer:
    """Optimize landing pages for search engines"""
    
    def analyze_page(self, html: str, keywords: List[str]) -> SEOScore:
        """Analyze SEO quality of page"""
        
        checks = {
            'title_optimization': self._check_title(html, keywords),
            'meta_description': self._check_meta(html, keywords),
            'header_structure': self._check_headers(html),
            'keyword_density': self._check_density(html, keywords),
            'image_alt_text': self._check_images(html),
            'internal_links': self._check_links(html),
            'mobile_responsive': self._check_mobile(html),
            'page_speed': self._check_speed(html)
        }
        
        return SEOScore(
            overall_score=sum(checks.values()) / len(checks),
            breakdown=checks,
            recommendations=self._generate_recommendations(checks)
        )
    
    def optimize_page(self, html: str, keywords: List[str]) -> str:
        """Apply SEO optimizations"""
        pass
```

### API Endpoints (FastAPI)

```python
# main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Vanchai SEO Engine")

class BulkGenerationRequest(BaseModel):
    category: str
    keywords: List[str]
    platforms: List[Platform]
    template: str = "default"

class GenerationResponse(BaseModel):
    job_id: str
    status: str
    estimated_pages: int
    estimated_time: str

@app.post("/api/v1/generate/bulk", response_model=GenerationResponse)
async def generate_bulk_pages(
    request: BulkGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Start bulk landing page generation"""
    
    job_id = await queue_bulk_generation(request)
    
    return GenerationResponse(
        job_id=job_id,
        status="queued",
        estimated_pages=len(request.keywords) * len(request.platforms),
        estimated_time="2-4 hours"
    )

@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get generation job status"""
    return await get_generation_status(job_id)

@app.get("/api/v1/pages/{page_id}/seo-score")
async def get_page_seo_score(page_id: str):
    """Get SEO score for generated page"""
    return await analyze_page_seo(page_id)
```

### Data Models (Pydantic)

```python
# models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Platform(str, Enum):
    WIX = "wix"
    AMAZON = "amazon"
    MYNTRA = "myntra"
    NYKAA = "nykaa"

class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    images: List[str]
    platform: Platform
    platform_id: str
    url: str
    in_stock: bool
    rating: Optional[float]
    review_count: Optional[int]

class LandingPageContent(BaseModel):
    title: str = Field(..., min_length=30, max_length=70)
    meta_description: str = Field(..., min_length=150, max_length=160)
    headline: str
    body: str
    cta: str
    product_name: str
    platform_links: dict
    schema_markup: dict

class SEOScore(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    breakdown: dict
    recommendations: List[str]
    analyzed_at: datetime

class GenerationJob(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    total_pages: int
    completed_pages: int
    failed_pages: int
    platform_breakdown: dict
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
```

### Workflow (Celery Tasks)

```python
# tasks.py
from celery import Celery

app = Celery('vanchai_seo')

@app.task(bind=True, max_retries=3)
def generate_landing_page_task(self, product_id: str, keywords: List[str]):
    """Celery task to generate single landing page"""
    try:
        product = fetch_product(product_id)
        content = content_generator.generate(product, keywords)
        html = page_builder.build(content)
        optimized = seo_optimizer.optimize(html, keywords)
        
        page_url = upload_to_s3(optimized, f"{product.category}/{product.slug}.html")
        
        return {
            'status': 'success',
            'url': page_url,
            'seo_score': seo_optimizer.analyze(optimized, keywords).overall_score
        }
    
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

@app.task
def bulk_generation_task(category: str, platforms: List[Platform]):
    """Orchestrate bulk generation"""
    products = catalog_manager.get_products_by_category(category)
    
    for product in products:
        keywords = keyword_engine.generate_for_product(product)
        
        for platform in platforms:
            generate_landing_page_task.delay(
                product.id, 
                keywords,
                platform=platform
            )
```

## Implementation Notes

### Content Generation Strategy
- Use GPT-4 for high-quality content
- Prompt engineering for SEO optimization
- Temperature 0.7 for creativity
- Max 2000 tokens per generation
- Caching for similar products

### Performance Optimization
- Celery + Redis for task queue
- Batch processing (50 concurrent)
- Async I/O for API calls
- Connection pooling
- Result caching with Redis

### Error Handling
- Retry with exponential backoff (3 retries)
- Dead letter queue for failures
- Manual review queue for low-quality content
- Comprehensive logging

## Dependencies

### Python Libraries
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
celery==5.3.0
redis==5.0.0
openai==1.0.0
jinja2==3.1.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
boto3==1.34.0
beautifulsoup4==4.12.0
requests==2.31.0
python-multipart==0.0.6
pytest==7.4.0
black==23.0.0
isort==5.12.0
```

### Infrastructure
- AWS EC2 (API servers)
- AWS S3 (Static hosting for discover.vanchai.in)
- AWS CloudFront (CDN)
- Redis (Task queue + caching)
- PostgreSQL (Product database)

## Risks & Mitigation

### Risk: OpenAI API rate limits
**Mitigation**: Request queue, batch processing, multiple API keys

### Risk: Content quality variance
**Mitigation**: SEO scoring threshold, human review queue, A/B testing

### Risk: Platform API changes
**Mitigation**: Abstraction layer, monitoring, fallback strategies

### Risk: 13,000 pages deployment
**Mitigation**: Incremental deployment, CDN caching, pre-rendering

## Testing Strategy

### Unit Tests (pytest)
```python
# tests/test_content_generator.py
def test_generate_landing_page_content():
    generator = ContentGenerator(mock_openai)
    content = generator.generate(mock_product, ["test keyword"])
    
    assert len(content.title) <= 70
    assert len(content.meta_description) <= 160
    assert content.seo_score > 75
```

### Integration Tests
- End-to-end generation flow
- Platform API integrations
- Database operations
- File uploads

### Load Tests (locust)
- 500+ concurrent generations
- API response times
- Queue processing rates
- Database performance

## Definition of Done
- [ ] All 13,000 pages generated and deployed
- [ ] Average SEO score >80/100
- [ ] API endpoints tested and documented
- [ ] Python code coverage >85%
- [ ] Performance benchmarks met (500 pages/day)
- [ ] Platform integrations working
- [ ] Monitoring and alerting configured
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Staging and production deployment successful

## Related Specs
- Product Catalog Sync Spec
- SEO Optimization Spec
- Deployment Pipeline Spec
- Analytics Tracking Spec
