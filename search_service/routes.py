"""FastAPI routes for search service"""

from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from factory_parsers.shared.database import get_db
from factory_parsers.search_service.searcher import TenderSearcher
from factory_parsers.search_service.indexer import TenderIndexer

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    platform: Optional[str] = None
    category: Optional[str] = None
    customer: Optional[str] = None
    status: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    size: int = 20
    page: int = 1


class SearchResult(BaseModel):
    total: int
    items: list
    query_time_ms: int


@router.post("/query", response_model=SearchResult)
def search_tenders(request: SearchRequest):
    """Search tenders"""
    searcher = TenderSearcher()
    from_offset = (request.page - 1) * request.size
    
    return searcher.search(
        query=request.query,
        platform=request.platform,
        category=request.category,
        customer=request.customer,
        status=request.status,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        size=request.size,
        from_=from_offset,
    )


@router.get("/by-customer/{customer}", response_model=SearchResult)
def search_by_customer(customer: str, size: int = Query(50, le=100)):
    """Search tenders by customer"""
    searcher = TenderSearcher()
    items = searcher.search_by_customer(customer, size=size)
    return {"total": len(items), "items": items, "query_time_ms": 0}


@router.get("/by-category/{category}", response_model=SearchResult)
def search_by_category(category: str, size: int = Query(50, le=100)):
    """Search tenders by category"""
    searcher = TenderSearcher()
    items = searcher.search_by_category(category, size=size)
    return {"total": len(items), "items": items, "query_time_ms": 0}


@router.get("/trending", response_model=SearchResult)
def get_trending(days: int = Query(7, ge=1, le=90), size: int = Query(20, le=100)):
    """Get trending tenders"""
    searcher = TenderSearcher()
    items = searcher.get_trending(days=days, size=size)
    return {"total": len(items), "items": items, "query_time_ms": 0}


@router.post("/index/{tender_id}")
def index_tender(tender_id: str, db: Session = Depends(get_db)):
    """Index single tender"""
    indexer = TenderIndexer(db)
    success = indexer.index_tender(tender_id)
    return {"status": "success" if success else "failed", "tender_id": tender_id}


@router.post("/index-all")
def index_all_tenders(platform: Optional[str] = None, db: Session = Depends(get_db)):
    """Bulk index all tenders"""
    indexer = TenderIndexer(db)
    count = indexer.bulk_index(platform=platform)
    return {"status": "success", "indexed_count": count}


@router.post("/reindex")
def reindex_all(db: Session = Depends(get_db)):
    """Reindex all tenders"""
    indexer = TenderIndexer(db)
    count = indexer.reindex_all()
    return {"status": "success", "indexed_count": count}


@router.get("/stats")
def get_search_stats():
    """Get search engine statistics"""
    searcher = TenderSearcher()
    stats = searcher.es_client.get_stats()
    return stats
