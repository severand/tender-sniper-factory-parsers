"""Detail service for full tender information"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from factory_parsers.normalizer_service.repositories import NormalizedTenderRepository


class DetailService:
    """Get detailed tender information"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tender_repo = NormalizedTenderRepository(db)
    
    def get_tender(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Get tender details
        
        Args:
            tender_id: Tender ID
        
        Returns:
            Tender data or None
        """
        tender = self.tender_repo.get_by_id(tender_id)
        if not tender:
            logger.warning(f"Tender not found: {tender_id}")
            return None
        
        return self._tender_to_dict(tender)
    
    def get_tender_by_external_id(self, external_id: str, platform_id: str) -> Optional[Dict[str, Any]]:
        """Get tender by external ID
        
        Args:
            external_id: External platform ID
            platform_id: Platform ID
        
        Returns:
            Tender data or None
        """
        tender = self.db.query(__import__('factory_parsers.normalizer_service.models', fromlist=['NormalizedTender']).NormalizedTender).filter(
            __import__('factory_parsers.normalizer_service.models', fromlist=['NormalizedTender']).NormalizedTender.external_id == external_id,
            __import__('factory_parsers.normalizer_service.models', fromlist=['NormalizedTender']).NormalizedTender.platform_id == platform_id
        ).first()
        
        if not tender:
            return None
        
        return self._tender_to_dict(tender)
    
    @staticmethod
    def _tender_to_dict(tender) -> Dict[str, Any]:
        """Convert ORM object to dict"""
        return {
            'id': tender.id,
            'tender_id': tender.tender_id,
            'platform_id': tender.platform_id,
            'external_id': tender.external_id,
            'title': tender.title,
            'description': tender.description,
            'summary': tender.summary or tender.ai_summary,
            'category': tender.category,
            'customer': {
                'name': tender.customer_name,
                'contact': tender.customer_contact,
            },
            'budget': {
                'amount': tender.budget_amount,
                'currency': tender.budget_currency,
                'min': tender.budget_min,
                'max': tender.budget_max,
            },
            'dates': {
                'published': tender.published_date.isoformat() if tender.published_date else None,
                'deadline': tender.deadline_date.isoformat() if tender.deadline_date else None,
                'start': tender.start_date.isoformat() if tender.start_date else None,
                'end': tender.end_date.isoformat() if tender.end_date else None,
            },
            'status': tender.status,
            'source_url': tender.source_url,
            'requirements': tender.requirements or [],
            'criteria': tender.criteria or [],
            'restrictions': tender.restrictions or [],
            'ai_extracted': tender.ai_extracted or {},
            'ai_keywords': tender.ai_keywords or [],
            'attachments': tender.attachments or [],
            'quality_score': tender.data_quality_score,
            'created_at': tender.normalized_at.isoformat(),
        }
