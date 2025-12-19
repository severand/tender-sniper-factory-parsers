"""FastAPI routes for normalizer service"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from factory_parsers.shared.database import get_db
from factory_parsers.normalizer_service.repositories import (
    NormalizedTenderRepository,
    NormalizationLogRepository,
)

router = APIRouter(prefix="/normalized-tenders", tags=["normalized-tenders"])


class NormalizedTenderResponse(BaseModel):
    id: int
    tender_id: str
    title: str
    platform: str
    budget: Optional[float]
    currency: str
    status: str
    normalized_at: str
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    platform: Optional[str] = None
    customer: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None


@router.get("/", response_model=List[NormalizedTenderResponse])
def list_tenders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List normalized tenders"""
    repo = NormalizedTenderRepository(db)
    query = db.query(repo.__class__.__bases__[0])
    return query.offset(skip).limit(limit).all()


@router.get("/{tender_id}", response_model=NormalizedTenderResponse)
def get_tender(
    tender_id: str,
    db: Session = Depends(get_db)
):
    """Get normalized tender"""
    repo = NormalizedTenderRepository(db)
    tender = repo.get_by_id(tender_id)
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )
    return tender


@router.post("/search", response_model=List[NormalizedTenderResponse])
def search_tenders(
    criteria: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search tenders by criteria"""
    repo = NormalizedTenderRepository(db)
    results = repo.search(
        platform=criteria.platform,
        customer=criteria.customer,
        status=criteria.status,
        category=criteria.category,
    )
    return results


@router.get("/platform/{platform}/count")
def count_by_platform(
    platform: str,
    db: Session = Depends(get_db)
):
    """Count tenders from platform"""
    repo = NormalizedTenderRepository(db)
    tenders = repo.get_by_platform(platform)
    return {"platform": platform, "count": len(tenders)}


@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get normalization statistics"""
    repo = NormalizedTenderRepository(db)
    total = repo.count()
    
    # Get counts by status
    status_query = db.query(
        repo.__class__.__bases__[0].status,
        db.func.count()
    ).group_by(repo.__class__.__bases__[0].status)
    
    status_counts = {row[0]: row[1] for row in status_query.all()}
    
    return {
        "total_normalized": total,
        "by_status": status_counts,
    }


@router.get("/logs/{tender_id}")
def get_logs(
    tender_id: str,
    db: Session = Depends(get_db)
):
    """Get normalization logs for tender"""
    repo = NormalizationLogRepository(db)
    logs = repo.get_by_tender(tender_id)
    return {"tender_id": tender_id, "logs": logs}
