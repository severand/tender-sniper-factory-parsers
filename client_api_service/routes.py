"""Client API routes (Sprint 34)"""

from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from factory_parsers.shared.database import get_db
from .search_service import SearchService
from .detail_service import DetailService

router = APIRouter(prefix="/api/v1", tags=["client-api"])


@router.get("/search")
def search_tenders(
    query: str = Query(..., description="Search query"),
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    budget_min: Optional[float] = Query(None),
    budget_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search tenders"""
    service = SearchService(db)
    return service.search(
        query=query,
        platform=platform,
        category=category,
        customer=customer,
        budget_min=budget_min,
        budget_max=budget_max,
        page=page,
        size=size,
    )


@router.get("/tenders/{tender_id}")
def get_tender(tender_id: str, db: Session = Depends(get_db)):
    """Get tender details"""
    service = DetailService(db)
    tender = service.get_tender(tender_id)
    if not tender:
        return {"error": "Tender not found"}
    return tender


@router.get("/tenders/platform/{platform_id}/external/{external_id}")
def get_tender_by_external(platform_id: str, external_id: str, db: Session = Depends(get_db)):
    """Get tender by external ID"""
    service = DetailService(db)
    tender = service.get_tender_by_external_id(external_id, platform_id)
    if not tender:
        return {"error": "Tender not found"}
    return tender
