"""FastAPI routes for web scraper service"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from shared.database import get_db
from admin_service.models import Tender
from web_scraper_service.scraper_manager import ScraperManager
from web_scraper_service.dynamic_spider_generator import DynamicSpiderGenerator

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


class ScraperRunRequest(BaseModel):
    platform_id: int
    search_rule_id: int


class SpiderListResponse(BaseModel):
    name: str
    platform_id: int
    rule_id: int
    platform: str
    rule: str


class TenderResponse(BaseModel):
    id: int
    platform_id: int
    title: str
    url: str
    price: float = None
    published_date: datetime = None
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/run")
def run_scraper(
    request: ScraperRunRequest,
    db: Session = Depends(get_db)
):
    """Run scraper for specific platform and rule"""
    manager = ScraperManager(db)
    try:
        success = manager.run_spider(request.platform_id, request.search_rule_id)
        return {
            "status": "success" if success else "failed",
            "platform_id": request.platform_id,
            "rule_id": request.search_rule_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraper failed: {str(e)}"
        )


@router.post("/run-all")
def run_all_scrapers(db: Session = Depends(get_db)):
    """Run scrapers for all active platforms"""
    manager = ScraperManager(db)
    try:
        stats = manager.run_all_platforms()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraper failed: {str(e)}"
        )


@router.get("/results", response_model=List[TenderResponse])
def get_scraper_results(
    platform_id: Optional[int] = Query(None, description="Filter by platform ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get scraped tender results"""
    query = db.query(Tender).order_by(Tender.created_at.desc())
    
    if platform_id:
        query = query.filter(Tender.platform_id == platform_id)
    
    tenders = query.offset(offset).limit(limit).all()
    
    return tenders


@router.get("/available-spiders")
def list_available_spiders(db: Session = Depends(get_db)):
    """List all available spider configurations"""
    generator = DynamicSpiderGenerator(db)
    spiders = generator.get_available_spiders()
    return {"spiders": spiders, "total": len(spiders)}


@router.get("/platform-status/{platform_id}")
def get_platform_status(
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Get scraper status for platform"""
    manager = ScraperManager(db)
    status_info = manager.get_spider_status(platform_id)
    if 'error' in status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=status_info['error']
        )
    return status_info