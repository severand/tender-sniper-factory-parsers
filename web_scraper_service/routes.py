"""FastAPI routes for web scraper service"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from shared.database import get_db
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