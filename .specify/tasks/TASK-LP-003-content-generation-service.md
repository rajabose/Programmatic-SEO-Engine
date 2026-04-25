# TASK-LP-003: AI Content Generation Service

**Derived from**: [Landing Page Generation Plan](../plans/landing-page-generation-plan.md) - Phase 2, Day 3-5  
**Branch**: `feature/landing-page-generation`  
**Assignee**: [Developer Name]  
**Priority**: High  
**Estimated Time**: 10 hours  
**Due Date**: Sprint 1, Day 5 - Sprint 2, Day 1

## Task Description
Implement Python service for AI-powered content generation using OpenAI API to create SEO-optimized landing page content for products.

## Acceptance Criteria

### Must Have
- [ ] OpenAI API integration with GPT-4
- [ ] Prompt engineering for SEO content
- [ ] Content generation service with caching
- [ ] SEO-optimized title and meta description generation
- [ ] Product description generation
- [ ] Platform-specific CTA generation
- [ ] Content quality validation
- [ ] Redis caching for generated content

### Should Have
- [ ] A/B testing different prompts
- [ ] Content variation generation
- [ ] Multi-language support preparation
- [ ] Content templates library
- [ ] Batch generation support

### Nice to Have
- [ ] Fine-tuned model training
- [ ] Content sentiment analysis
- [ ] Competitor content analysis
- [ ] Auto-content refresh for stale pages

## Technical Implementation

### 1. OpenAI Client Setup

```python
# app/services/ai/openai_client.py
from openai import AsyncOpenAI
from typing import List, Dict, Optional
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIContentClient:
    """Client for OpenAI API content generation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_content(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> str:
        """Generate content with retry logic"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format=response_format
            )
            
            content = response.choices[0].message.content
            logger.info("Content generated successfully", 
                       tokens_used=response.usage.total_tokens)
            
            return content
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
```

### 2. Content Generation Service

```python
# app/services/content_generator.py
from typing import List, Optional
from datetime import datetime
import hashlib

from app.models.product import Product
from app.models.schemas import Platform, LandingPageContent, KeywordCluster
from app.services.ai.openai_client import OpenAIContentClient
from app.services.cache.redis_cache import RedisCache
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

class ContentGenerationService:
    """Service for generating SEO-optimized landing page content"""
    
    def __init__(self):
        self.openai = OpenAIContentClient()
        self.cache = RedisCache()
    
    async def generate_landing_page_content(
        self,
        product: Product,
        keywords: List[str],
        platform: Platform,
        use_cache: bool = True
    ) -> LandingPageContent:
        """Generate complete landing page content"""
        
        # Check cache
        cache_key = self._generate_cache_key(product.id, keywords, platform)
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info("Content retrieved from cache", product_id=product.id)
                return LandingPageContent(**cached)
        
        # Generate content components
        title = await self._generate_title(product, keywords)
        meta_description = await self._generate_meta_description(product, keywords)
        headline = await self._generate_headline(product, keywords)
        body = await self._generate_body_content(product, keywords, platform)
        cta = await self._generate_cta(product, platform)
        
        # Build content object
        content = LandingPageContent(
            title=title,
            meta_description=meta_description,
            headline=headline,
            body=body,
            cta=cta,
            product_name=product.name,
            platform_links=self._build_platform_links(product, platform),
            product_price=product.price,
            images=product.images
        )
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, content.dict(), ttl=86400)  # 24 hours
        
        return content
    
    def _generate_cache_key(self, product_id: str, keywords: List[str], platform: Platform) -> str:
        """Generate cache key for content"""
        key_data = f"{product_id}:{':'.join(sorted(keywords))}:{platform.value}"
        return f"content:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _generate_title(
        self, 
        product: Product, 
        keywords: List[str]
    ) -> str:
        """Generate SEO-optimized page title (50-60 chars)"""
        
        system_prompt = """
        You are an expert SEO copywriter. Generate compelling, SEO-optimized page titles.
        - Length: 50-60 characters
        - Include primary keyword near the beginning
        - Make it compelling and click-worthy
        - Include brand name if space permits
        """
        
        primary_keyword = keywords[0] if keywords else product.category
        
        prompt = f"""
        Generate a page title for:
        Product: {product.name}
        Brand: {product.brand or 'Vanchai'}
        Category: {product.category}
        Primary Keyword: {primary_keyword}
        
        Respond with ONLY the title, nothing else.
        """
        
        title = await self.openai.generate_content(prompt, system_prompt)
        
        # Ensure length constraints
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title.strip()
    
    async def _generate_meta_description(
        self, 
        product: Product, 
        keywords: List[str]
    ) -> str:
        """Generate meta description (150-160 chars)"""
        
        system_prompt = """
        You are an expert SEO copywriter. Generate compelling meta descriptions.
        - Length: 150-160 characters
        - Include primary keyword
        - Include call-to-action
        - Make it compelling for SERP clicks
        """
        
        primary_keyword = keywords[0] if keywords else product.category
        
        prompt = f"""
        Generate a meta description for:
        Product: {product.name}
        Description: {product.description[:200] if product.description else 'Beauty and wellness product'}
        Category: {product.category}
        Primary Keyword: {primary_keyword}
        Price: ₹{product.price}
        
        Respond with ONLY the meta description, nothing else.
        """
        
        meta = await self.openai.generate_content(prompt, system_prompt)
        
        # Ensure length constraints
        if len(meta) > 160:
            meta = meta[:157] + "..."
        
        return meta.strip()
    
    async def _generate_headline(
        self, 
        product: Product, 
        keywords: List[str]
    ) -> str:
        """Generate compelling headline for landing page"""
        
        system_prompt = """
        You are a conversion copywriter. Create compelling headlines for product pages.
        - Focus on benefits, not just features
        - Include power words
        - Create urgency or curiosity
        - Keep it under 10 words if possible
        """
        
        prompt = f"""
        Generate a compelling headline for:
        Product: {product.name}
        Brand: {product.brand}
        Category: {product.category}
        Price: ₹{product.price}
        Rating: {product.rating or 'N/A'}/5
        
        Keywords to consider: {', '.join(keywords[:3])}
        
        Respond with ONLY the headline, nothing else.
        """
        
        return await self.openai.generate_content(prompt, system_prompt)
    
    async def _generate_body_content(
        self, 
        product: Product, 
        keywords: List[str],
        platform: Platform
    ) -> str:
        """Generate main body content (300-500 words)"""
        
        system_prompt = """
        You are an expert SEO content writer for beauty and wellness products.
        Write compelling, SEO-optimized product descriptions.
        
        Guidelines:
        - Length: 300-500 words
        - Include primary keyword in first paragraph
        - Use secondary keywords naturally throughout
        - Write in HTML format with proper heading structure
        - Include benefits, features, and usage
        - Add social proof elements (ratings, reviews)
        - Include platform-specific trust signals
        """
        
        primary_keyword = keywords[0] if keywords else product.category
        secondary_keywords = keywords[1:4] if len(keywords) > 1 else []
        
        prompt = f"""
        Generate HTML content for a product landing page:
        
        Product: {product.name}
        Brand: {product.brand}
        Category: {product.category}
        Description: {product.description or ''}
        Price: ₹{product.price}
        Rating: {product.rating}/5 ({product.review_count} reviews)
        Key Features: {', '.join(product.tags[:5] if product.tags else [])}
        
        Primary Keyword: {primary_keyword}
        Secondary Keywords: {', '.join(secondary_keywords)}
        
        Target Platform: {platform.value.title()}
        
        Generate content in this HTML structure:
        <h2>Introduction with primary keyword</h2>
        <p>Compelling intro paragraph...</p>
        
        <h2>Key Benefits</h2>
        <ul>
          <li>Benefit 1</li>
          <li>Benefit 2</li>
        </ul>
        
        <h2>Why Choose This</h2>
        <p>With secondary keywords naturally included...</p>
        
        <h2>How to Use</h2>
        <p>Usage instructions...</p>
        
        <h2>What Customers Say</h2>
        <blockquote>Social proof...</blockquote>
        
        Respond with ONLY the HTML content, no markdown code blocks.
        """
        
        return await self.openai.generate_content(prompt, system_prompt)
    
    async def _generate_cta(
        self, 
        product: Product, 
        platform: Platform
    ) -> str:
        """Generate platform-specific call-to-action"""
        
        cta_templates = {
            Platform.WIX: f"Shop {product.name} now on our store - Free delivery & easy returns!",
            Platform.AMAZON: f"Buy {product.name} on Amazon - Prime eligible, fast delivery!",
            Platform.MYNTRA: f"Get {product.name} on Myntra - Trending now, style it your way!",
            Platform.NYKAA: f"Shop {product.name} on Nykaa - 100% authentic beauty products!"
        }
        
        return cta_templates.get(platform, f"Shop {product.name} now!")
    
    def _build_platform_links(
        self, 
        product: Product, 
        primary_platform: Platform
    ) -> Dict[str, str]:
        """Build links to all platforms for this product"""
        
        links = {}
        
        if product.wix_url:
            links[Platform.WIX.value] = product.wix_url
        if product.amazon_url:
            links[Platform.AMAZON.value] = product.amazon_url
        if product.myntra_url:
            links[Platform.MYNTRA.value] = product.myntra_url
        if product.nykaa_url:
            links[Platform.NYKAA.value] = product.nykaa_url
        
        # Ensure primary platform link is first
        if primary_platform.value in links:
            # Move to front by reinserting
            primary_link = links.pop(primary_platform.value)
            links = {primary_platform.value: primary_link, **links}
        
        return links
    
    async def generate_batch(
        self,
        products: List[Product],
        keywords_map: Dict[str, List[str]],
        platforms: List[Platform]
    ) -> List[LandingPageContent]:
        """Generate content for multiple products in batch"""
        
        import asyncio
        
        tasks = []
        for product in products:
            keywords = keywords_map.get(product.id, [product.category])
            for platform in platforms:
                task = self.generate_landing_page_content(
                    product, keywords, platform
                )
                tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        successful = [r for r in results if not isinstance(r, Exception)]
        
        logger.info(f"Batch generation complete: {len(successful)}/{len(tasks)} successful")
        
        return successful
```

### 3. Redis Cache Service

```python
# app/services/cache/redis_cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any

from app.config import settings

class RedisCache:
    """Redis caching service for content"""
    
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        await self.client.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.client.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
```

### 4. Content Validation

```python
# app/services/content_validator.py
from typing import Dict, List
import re

class ContentValidator:
    """Validate generated content quality"""
    
    def validate_landing_page_content(
        self, 
        content: LandingPageContent,
        keywords: List[str]
    ) -> Dict:
        """Validate landing page content meets standards"""
        
        issues = []
        score = 100
        
        # Check title length
        if len(content.title) < 30 or len(content.title) > 70:
            issues.append(f"Title length issue: {len(content.title)} chars")
            score -= 5
        
        # Check meta description length
        if len(content.meta_description) < 120 or len(content.meta_description) > 170:
            issues.append(f"Meta description length issue: {len(content.meta_description)} chars")
            score -= 5
        
        # Check primary keyword in title
        primary_keyword = keywords[0] if keywords else ""
        if primary_keyword.lower() not in content.title.lower():
            issues.append("Primary keyword not in title")
            score -= 10
        
        # Check primary keyword in meta
        if primary_keyword.lower() not in content.meta_description.lower():
            issues.append("Primary keyword not in meta description")
            score -= 5
        
        # Check keyword density in body
        body_lower = content.body.lower()
        keyword_count = sum(1 for kw in keywords if kw.lower() in body_lower)
        if keyword_count < len(keywords) * 0.5:
            issues.append("Insufficient keyword coverage in body")
            score -= 10
        
        # Check body length
        body_text = re.sub(r'<[^>]+>', '', content.body)
        word_count = len(body_text.split())
        if word_count < 200:
            issues.append(f"Body content too short: {word_count} words")
            score -= 15
        
        # Check for CTA
        if not content.cta or len(content.cta) < 10:
            issues.append("Weak or missing call-to-action")
            score -= 10
        
        return {
            "is_valid": score >= 70,
            "score": max(score, 0),
            "issues": issues,
            "word_count": word_count
        }
```

### 5. API Endpoints

```python
# app/api/v1/endpoints/generation.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.content_generator import ContentGenerationService
from app.services.catalog_manager import CatalogManager
from app.models.schemas import Platform, ContentGenerationRequest, LandingPageContent

router = APIRouter()

@router.post("/generate/{product_id}", response_model=LandingPageContent)
async def generate_content(
    product_id: str,
    request: ContentGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate landing page content for a product"""
    
    # Get product
    manager = CatalogManager(db)
    product = manager.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Generate content
    service = ContentGenerationService()
    content = await service.generate_landing_page_content(
        product=product,
        keywords=request.keywords,
        platform=request.platform
    )
    
    return content

@router.post("/generate/bulk")
async def generate_bulk_content(
    request: BulkContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start bulk content generation"""
    
    # Queue generation task
    # ... implementation
    
    return {"message": "Bulk generation started", "job_id": "xxx"}
```

## Testing Steps

### Unit Tests
```python
# tests/test_content_generator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.content_generator import ContentGenerationService

@pytest.fixture
def mock_openai():
    client = AsyncMock()
    client.generate_content.return_value = "Test generated content"
    return client

@pytest.mark.asyncio
async def test_generate_title(mock_openai):
    service = ContentGenerationService()
    service.openai = mock_openai
    
    product = MagicMock(name="Test Product", brand="Brand")
    title = await service._generate_title(product, ["test keyword"])
    
    assert len(title) <= 60
    assert "Test Product" in title or "test keyword" in title.lower()
```

### Integration Tests
- Test actual OpenAI API calls
- Verify content quality scores
- Test caching behavior
- Test error handling and retries

## Definition of Done
- [ ] OpenAI client with retry logic
- [ ] All content generation methods working
- [ ] Redis caching implemented
- [ ] Content validation service
- [ ] API endpoints tested
- [ ] Average generation time <10 seconds
- [ ] Content quality score >75/100
- [ ] Documentation complete

## Notes
- Monitor OpenAI API costs closely
- Implement request throttling for cost control
- Cache aggressively to reduce API calls
- Log all generations for analysis
- Test prompts thoroughly before production

## API Costs Estimate
- GPT-4: ~$0.03 per 1K tokens
- Average request: ~800 tokens
- 13,000 pages × ~5 requests each = 65,000 requests
- Estimated cost: $1,500 - $2,000 for full generation

## Related Tasks
- TASK-004: Setup Celery task queue for batch generation
- TASK-005: Implement SEO scoring service
