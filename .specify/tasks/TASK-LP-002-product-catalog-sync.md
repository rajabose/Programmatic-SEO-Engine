# TASK-LP-002: Product Catalog Synchronization

**Derived from**: [Landing Page Generation Plan](../plans/landing-page-generation-plan.md) - Phase 2, Day 1-2  
**Branch**: `feature/landing-page-generation`  
**Assignee**: [Developer Name]  
**Priority**: High  
**Estimated Time**: 8 hours  
**Due Date**: Sprint 1, Day 3-4

## Task Description
Implement Python services to synchronize product catalogs from Wix D2C, Amazon, Myntra, and Nykaa platforms into a unified PostgreSQL database.

## Acceptance Criteria

### Must Have
- [ ] SQLAlchemy models for Product and Category
- [ ] Alembic migrations for database schema
- [ ] Wix Store API integration
- [ ] Amazon Product API integration
- [ ] Myntra product scraper
- [ ] Nykaa product API integration
- [ ] Product deduplication logic
- [ ] Catalog sync service with batch processing
- [ ] Pydantic schemas for API validation

### Should Have
- [ ] Async API clients (aiohttp/httpx)
- [ ] Product image download and storage
- [ ] Category mapping across platforms
- [ ] Inventory sync
- [ ] Price tracking

### Nice to Have
- [ ] Real-time sync via webhooks
- [ ] Product change notifications
- [ ] Competitor price monitoring
- [ ] Product image optimization

## Technical Implementation

### 1. Database Models

```python
# app/models/product.py
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True, nullable=False)
    slug = Column(String, unique=True, index=True)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    keywords = Column(ARRAY(String), default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    
    # Platform info
    platform = Column(String, index=True, nullable=False)  # wix, amazon, myntra, nykaa
    platform_id = Column(String, index=True, nullable=False)  # Original platform ID
    
    # Basic info
    name = Column(String, index=True, nullable=False)
    slug = Column(String, unique=True, index=True)
    description = Column(String)
    short_description = Column(String)
    
    # Categorization
    category_id = Column(String, ForeignKey("categories.id"))
    category = relationship("Category", backref="products")
    tags = Column(ARRAY(String), default=[])
    
    # Pricing
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float)
    currency = Column(String, default="INR")
    
    # Media
    images = Column(JSON, default=[])
    featured_image = Column(String)
    
    # Platform-specific URLs
    wix_url = Column(String)
    amazon_url = Column(String)
    myntra_url = Column(String)
    nykaa_url = Column(String)
    
    # Inventory
    in_stock = Column(Boolean, default=True)
    inventory_quantity = Column(Integer, default=0)
    
    # Reviews
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    
    # Attributes
    brand = Column(String, index=True)
    color = Column(String)
    size = Column(String)
    material = Column(String)
    ingredients = Column(ARRAY(String), default=[])
    
    # SEO
    meta_title = Column(String)
    meta_description = Column(String)
    keywords = Column(ARRAY(String), default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_product_platform', 'platform', 'platform_id', unique=True),
        Index('idx_product_category_price', 'category_id', 'price'),
    )

class PlatformSyncLog(Base):
    __tablename__ = "platform_sync_logs"
    
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    sync_type = Column(String)  # full, incremental, webhook
    products_added = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    products_deleted = Column(Integer, default=0)
    errors = Column(JSON, default=[])
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    status = Column(String, default="running")  # running, completed, failed
```

### 2. Pydantic Schemas

```python
# app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class Platform(str, Enum):
    WIX = "wix"
    AMAZON = "amazon"
    MYNTRA = "myntra"
    NYKAA = "nykaa"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    price: float = Field(..., gt=0)
    category: str
    brand: Optional[str] = None
    in_stock: bool = True

class ProductCreate(ProductBase):
    platform: Platform
    platform_id: str
    images: List[str] = []

class ProductResponse(ProductBase):
    id: str
    platform: Platform
    platform_id: str
    images: List[str]
    rating: Optional[float] = None
    review_count: int = 0
    wix_url: Optional[str] = None
    amazon_url: Optional[str] = None
    myntra_url: Optional[str] = None
    nykaa_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SyncStatus(BaseModel):
    platform: Platform
    last_synced: Optional[datetime]
    total_products: int
    active_products: int
    status: str  # synced, syncing, error
```

### 3. Wix API Client

```python
# app/services/platforms/wix_client.py
import httpx
from typing import List, Optional
from app.models.schemas import ProductCreate, Platform
from app.config import settings

class WixAPIClient:
    """Client for Wix Store API"""
    
    def __init__(self):
        self.api_key = settings.WIX_API_KEY
        self.site_id = settings.WIX_SITE_ID
        self.base_url = f"https://www.wixapis.com/stores/v1"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def fetch_products(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ProductCreate]:
        """Fetch products from Wix Store"""
        
        url = f"{self.base_url}/products"
        params = {"limit": limit, "offset": offset}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        products = []
        for item in data.get("products", []):
            product = self._parse_wix_product(item)
            products.append(product)
        
        return products
    
    def _parse_wix_product(self, data: dict) -> ProductCreate:
        """Convert Wix product format to our schema"""
        
        variants = data.get("variants", [])
        price_info = variants[0].get("price", {}) if variants else {}
        
        return ProductCreate(
            name=data.get("name", ""),
            description=data.get("description", ""),
            price=float(price_info.get("price", 0)),
            category=data.get("ribbon", "Uncategorized"),
            brand=data.get("brand", None),
            in_stock=data.get("inventory", {}).get("status", "IN_STOCK") == "IN_STOCK",
            platform=Platform.WIX,
            platform_id=data.get("id"),
            images=[img.get("url") for img in data.get("media", {}).get("items", [])]
        )
    
    async def get_product_count(self) -> int:
        """Get total product count for pagination"""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/products/query",
                headers=self.headers,
                params={"limit": 1},
                timeout=10.0
            )
            data = response.json()
            return data.get("totalResults", 0)
```

### 4. Amazon Product API Client

```python
# app/services/platforms/amazon_client.py
import boto3
from botocore.exceptions import ClientError
from typing import List

class AmazonProductAPIClient:
    """Client for Amazon Product Advertising API or Selling Partner API"""
    
    def __init__(self):
        self.access_key = settings.AMAZON_ACCESS_KEY
        self.secret_key = settings.AMAZON_SECRET_KEY
        self.partner_tag = settings.AMAZON_PARTNER_TAG
        self.region = settings.AMAZON_REGION
        
    async def fetch_products(
        self, 
        search_index: str = "All",
        keywords: Optional[str] = None
    ) -> List[ProductCreate]:
        """Fetch products from Amazon"""
        
        # Implementation depends on whether using PA-API or SP-API
        # This is a simplified example
        
        products = []
        # ... API implementation ...
        
        return products
```

### 5. Myntra Scraper

```python
# app/services/platforms/myntra_scraper.py
import httpx
from bs4 import BeautifulSoup
from typing import List
import json

class MyntraScraper:
    """Scraper for Myntra products"""
    
    def __init__(self):
        self.base_url = "https://www.myntra.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 50
    ) -> List[ProductCreate]:
        """Search and scrape products from Myntra"""
        
        search_url = f"{self.base_url}/search/{query.replace(' ', '%20')}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                search_url, 
                headers=self.headers,
                timeout=30.0
            )
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # Myntra stores data in script tags as JSON
        scripts = soup.find_all('script')
        products = []
        
        for script in scripts:
            if script.string and 'window.__myx' in script.string:
                try:
                    json_data = self._extract_json(script.string)
                    products.extend(self._parse_myntra_products(json_data))
                except:
                    continue
        
        return products[:limit]
    
    def _extract_json(self, script_content: str) -> dict:
        """Extract JSON data from Myntra script tag"""
        start = script_content.find('{')
        end = script_content.rfind('}') + 1
        return json.loads(script_content[start:end])
    
    def _parse_myntra_products(self, data: dict) -> List[ProductCreate]:
        """Parse Myntra JSON to our product format"""
        
        products = []
        search_data = data.get('searchData', {}).get('results', {}).get('products', [])
        
        for item in search_data:
            product = ProductCreate(
                name=item.get('productName', ''),
                description=item.get('description', ''),
                price=float(item.get('price', 0)),
                category=item.get('category', 'Fashion'),
                brand=item.get('brand', ''),
                in_stock=item.get('inStock', True),
                platform=Platform.MYNTRA,
                platform_id=str(item.get('styleId')),
                images=[item.get('searchImage', '')]
            )
            products.append(product)
        
        return products
```

### 6. Catalog Manager Service

```python
# app/services/catalog_manager.py
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product, Category, PlatformSyncLog
from app.models.schemas import ProductCreate, SyncStatus, Platform
from app.services.platforms.wix_client import WixAPIClient
from app.services.platforms.amazon_client import AmazonProductAPIClient
from app.services.platforms.myntra_scraper import MyntraScraper

class CatalogManager:
    """Manage product catalog synchronization from all platforms"""
    
    def __init__(self, db: Session):
        self.db = db
        self.clients = {
            Platform.WIX: WixAPIClient(),
            Platform.AMAZON: AmazonProductAPIClient(),
            Platform.MYNTRA: MyntraScraper(),
            # Platform.NYKAA: NykaaAPIClient(),
        }
    
    async def sync_all_platforms(self) -> Dict[Platform, SyncStatus]:
        """Synchronize all platform catalogs"""
        
        results = {}
        for platform in Platform:
            try:
                status = await self.sync_platform(platform)
                results[platform] = status
            except Exception as e:
                results[platform] = SyncStatus(
                    platform=platform,
                    status="error",
                    total_products=0,
                    active_products=0
                )
        
        return results
    
    async def sync_platform(self, platform: Platform) -> SyncStatus:
        """Synchronize single platform"""
        
        client = self.clients.get(platform)
        if not client:
            raise ValueError(f"No client configured for {platform}")
        
        # Start sync log
        sync_log = PlatformSyncLog(
            platform=platform.value,
            sync_type="incremental"
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            # Fetch products
            products = await client.fetch_products()
            
            # Process and save
            stats = await self._process_products(products, platform)
            
            # Update sync log
            sync_log.products_added = stats["added"]
            sync_log.products_updated = stats["updated"]
            sync_log.status = "completed"
            self.db.commit()
            
            # Get current stats
            total = self.db.query(Product).filter(Product.platform == platform.value).count()
            active = self.db.query(Product).filter(
                Product.platform == platform.value,
                Product.is_active == True
            ).count()
            
            return SyncStatus(
                platform=platform,
                status="synced",
                total_products=total,
                active_products=active
            )
            
        except Exception as e:
            sync_log.status = "failed"
            sync_log.errors = [{"error": str(e)}]
            self.db.commit()
            raise
    
    async def _process_products(
        self, 
        products: List[ProductCreate], 
        platform: Platform
    ) -> Dict[str, int]:
        """Process and save products to database"""
        
        added = 0
        updated = 0
        
        for product_data in products:
            # Check if product exists
            existing = self.db.query(Product).filter(
                Product.platform == platform.value,
                Product.platform_id == product_data.platform_id
            ).first()
            
            if existing:
                # Update existing
                self._update_product(existing, product_data)
                updated += 1
            else:
                # Create new
                new_product = Product(
                    id=f"{platform.value}_{product_data.platform_id}",
                    **product_data.dict()
                )
                self.db.add(new_product)
                added += 1
        
        self.db.commit()
        return {"added": added, "updated": updated}
    
    def _update_product(self, existing: Product, new_data: ProductCreate):
        """Update existing product with new data"""
        
        for field, value in new_data.dict().items():
            if field not in ['platform', 'platform_id', 'id']:
                setattr(existing, field, value)
        
        existing.last_synced_at = datetime.utcnow()
    
    def get_products_by_category(
        self, 
        category: str, 
        platform: Optional[Platform] = None,
        limit: int = 100
    ) -> List[Product]:
        """Get products by category"""
        
        query = self.db.query(Product).filter(
            Product.category == category,
            Product.is_active == True,
            Product.in_stock == True
        )
        
        if platform:
            query = query.filter(Product.platform == platform.value)
        
        return query.limit(limit).all()
    
    def get_product_stats(self) -> Dict:
        """Get overall product statistics"""
        
        total = self.db.query(Product).count()
        by_platform = self.db.query(
            Product.platform,
            func.count(Product.id)
        ).group_by(Product.platform).all()
        
        by_category = self.db.query(
            Product.category,
            func.count(Product.id)
        ).group_by(Product.category).all()
        
        return {
            "total_products": total,
            "by_platform": {p: c for p, c in by_platform},
            "by_category": {c: n for c, n in by_category}
        }
```

### 7. API Endpoints

```python
# app/api/v1/endpoints/catalog.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.catalog_manager import CatalogManager
from app.models.schemas import ProductResponse, SyncStatus, Platform

router = APIRouter()

@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    platform: Optional[Platform] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get products with optional filtering"""
    
    manager = CatalogManager(db)
    
    if category:
        products = manager.get_products_by_category(category, platform, limit)
    else:
        query = db.query(Product)
        if platform:
            query = query.filter(Product.platform == platform.value)
        products = query.offset(offset).limit(limit).all()
    
    return products

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get single product by ID"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.post("/sync/{platform}")
async def sync_platform(
    platform: Platform,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger platform synchronization"""
    
    manager = CatalogManager(db)
    
    # Run sync in background
    background_tasks.add_task(manager.sync_platform, platform)
    
    return {"message": f"Sync started for {platform.value}", "status": "processing"}

@router.post("/sync/all")
async def sync_all_platforms(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Synchronize all platforms"""
    
    manager = CatalogManager(db)
    
    background_tasks.add_task(manager.sync_all_platforms)
    
    return {"message": "Full catalog sync started", "status": "processing"}

@router.get("/stats")
async def get_catalog_stats(db: Session = Depends(get_db)):
    """Get catalog statistics"""
    
    manager = CatalogManager(db)
    return manager.get_product_stats()
```

## Testing Steps

### Unit Tests
```python
# tests/test_catalog_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.catalog_manager import CatalogManager

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_wix_client():
    client = AsyncMock()
    client.fetch_products.return_value = [
        ProductCreate(
            name="Test Product",
            price=999.0,
            category="Skincare",
            platform=Platform.WIX,
            platform_id="123"
        )
    ]
    return client

@pytest.mark.asyncio
async def test_sync_platform(mock_db, mock_wix_client):
    manager = CatalogManager(mock_db)
    manager.clients[Platform.WIX] = mock_wix_client
    
    status = await manager.sync_platform(Platform.WIX)
    
    assert status.platform == Platform.WIX
    mock_wix_client.fetch_products.assert_called_once()
```

### Integration Tests
- Test actual API calls with sandbox/test keys
- Verify database writes
- Test error handling

## Definition of Done
- [ ] All platform clients implemented
- [ ] Database models created with migrations
- [ ] Catalog sync working end-to-end
- [ ] API endpoints tested
- [ ] Deduplication logic working
- [ ] Error handling and logging complete
- [ ] Documentation updated

## Related Tasks
- TASK-003: Setup Celery for background sync
- TASK-004: Implement keyword generation

## Notes
- Use async/await for all I/O operations
- Implement rate limiting for scrapers
- Add retry logic for API failures
- Monitor API usage and costs
- Keep API keys secure (use environment variables)
