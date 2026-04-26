# TASK-LP-002: Product Catalog Synchronization

**Plan ref**: Phase 2, Day 1-2 | **Branch**: `feature/landing-page-generation`  
**Priority**: High | **Estimate**: 8h | **Sprint**: Day 3-4

## What to build
`CatalogManager` service that syncs products from Wix, Amazon, Myntra, Nykaa into a unified PostgreSQL `products` table.

## Models to create
- `Product` — platform, platform_id, name, slug, price, category, images, urls (wix/amazon/myntra/nykaa), in_stock, rating, brand, material
- `Category` — name, slug, parent_id, keywords
- `PlatformSyncLog` — platform, status, counts, errors, timestamps

## Platform clients
| Client | Method |
|--------|--------|
| `WixAPIClient` | Wix Store REST API (paginated) |
| `AmazonProductAPIClient` | PA-API or SP-API |
| `MyntraScraper` | httpx + BeautifulSoup / JSON from `window.__myx` |
| `NykaaAPIClient` | Nykaa REST API |

## Service interface
```python
CatalogManager.sync_all_platforms() -> Dict[Platform, SyncStatus]
CatalogManager.sync_platform(platform) -> SyncStatus
CatalogManager.get_products_by_category(category, platform?, limit) -> List[Product]
CatalogManager.get_product_stats() -> Dict
```

## API endpoints
```
POST /api/v1/catalog/sync/{platform}   # background task
POST /api/v1/catalog/sync/all
GET  /api/v1/catalog/products          # filter by category, platform
GET  /api/v1/catalog/products/{id}
GET  /api/v1/catalog/stats
```

## Acceptance criteria
- [ ] Alembic migration creates tables cleanly
- [ ] Wix sync fetches real products (or sandbox)
- [ ] Deduplication: re-running sync doesn't create duplicates
- [ ] `PlatformSyncLog` written for every run
- [ ] All endpoints return correct HTTP codes + schemas
- [ ] Async clients with timeout + retry

## Definition of done
End-to-end sync tested for at least one platform, unit tests with mocked clients passing.

## Blocked by
TASK-LP-001
