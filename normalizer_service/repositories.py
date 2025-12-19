"""Repositories for normalized tender data"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import NormalizedTender, NormalizationLog


class NormalizedTenderRepository:
    """Repository for normalized tenders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, tender_data: dict) -> NormalizedTender:
        """Create normalized tender"""
        tender = NormalizedTender(**tender_data)
        self.db.add(tender)
        self.db.commit()
        self.db.refresh(tender)
        return tender
    
    def get_by_id(self, tender_id: str) -> Optional[NormalizedTender]:
        """Get tender by tender_id"""
        return self.db.query(NormalizedTender).filter(
            NormalizedTender.tender_id == tender_id
        ).first()
    
    def get_by_platform(self, platform: str) -> List[NormalizedTender]:
        """Get all tenders from platform"""
        return self.db.query(NormalizedTender).filter(
            NormalizedTender.platform == platform
        ).all()
    
    def search(
        self,
        platform: Optional[str] = None,
        customer: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[NormalizedTender]:
        """Search tenders by criteria"""
        query = self.db.query(NormalizedTender)
        
        if platform:
            query = query.filter(NormalizedTender.platform == platform)
        if customer:
            query = query.filter(NormalizedTender.customer.ilike(f"%{customer}%"))
        if status:
            query = query.filter(NormalizedTender.status == status)
        if category:
            query = query.filter(NormalizedTender.category == category)
        
        return query.all()
    
    def update(self, tender_id: str, **kwargs) -> Optional[NormalizedTender]:
        """Update tender"""
        tender = self.get_by_id(tender_id)
        if tender:
            for key, value in kwargs.items():
                if hasattr(tender, key):
                    setattr(tender, key, value)
            tender.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(tender)
        return tender
    
    def delete(self, tender_id: str) -> bool:
        """Delete tender"""
        tender = self.get_by_id(tender_id)
        if tender:
            self.db.delete(tender)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Total normalized tenders"""
        return self.db.query(NormalizedTender).count()


class NormalizationLogRepository:
    """Repository for normalization logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, log_data: dict) -> NormalizationLog:
        """Create normalization log"""
        log = NormalizationLog(**log_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_by_tender(self, tender_id: str) -> List[NormalizationLog]:
        """Get logs for tender"""
        return self.db.query(NormalizationLog).filter(
            NormalizationLog.tender_id == tender_id
        ).order_by(NormalizationLog.started_at.desc()).all()
    
    def get_failed(self) -> List[NormalizationLog]:
        """Get failed normalization attempts"""
        return self.db.query(NormalizationLog).filter(
            NormalizationLog.status.in_(['failed', 'partial'])
        ).all()
