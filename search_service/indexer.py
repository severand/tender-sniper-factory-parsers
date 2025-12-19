"""Tender indexer for Elasticsearch"""

from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from factory_parsers.normalizer_service.repositories import NormalizedTenderRepository
from factory_parsers.search_service.elasticsearch_client import ElasticsearchClient


class TenderIndexer:
    """Index normalized tenders to Elasticsearch"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tender_repo = NormalizedTenderRepository(db)
        self.es_client = ElasticsearchClient()
    
    def index_tender(self, tender_id: str) -> bool:
        """Index single tender
        
        Args:
            tender_id: Tender ID
        
        Returns:
            Success status
        """
        tender = self.tender_repo.get_by_id(tender_id)
        if not tender:
            logger.warning(f"Tender not found: {tender_id}")
            return False
        
        doc = self._prepare_document(tender)
        return self.es_client.index_document(tender_id, doc)
    
    def bulk_index(self, tender_ids: List[str] = None, platform: str = None) -> int:
        """Bulk index tenders
        
        Args:
            tender_ids: List of specific tender IDs (optional)
            platform: Filter by platform (optional)
        
        Returns:
            Number of indexed documents
        """
        # Get tenders to index
        if tender_ids:
            tenders = [self.tender_repo.get_by_id(tid) for tid in tender_ids]
            tenders = [t for t in tenders if t]
        elif platform:
            tenders = self.tender_repo.get_by_platform(platform)
        else:
            # Index all
            query = self.db.query(self.tender_repo.__class__.__bases__[0])
            tenders = query.all()
        
        if not tenders:
            logger.warning("No tenders to index")
            return 0
        
        # Prepare documents
        documents = [self._prepare_document(t) for t in tenders]
        
        # Index
        count = self.es_client.bulk_index(documents)
        logger.info(f"Indexed {count} tenders")
        return count
    
    def reindex_all(self) -> int:
        """Reindex all tenders
        
        Returns:
            Number of indexed documents
        """
        logger.info("Starting full reindex...")
        
        # Clear old index
        self.es_client.clear_index()
        
        # Bulk index all
        return self.bulk_index()
    
    def _prepare_document(self, tender) -> Dict[str, Any]:
        """Prepare tender document for indexing
        
        Args:
            tender: NormalizedTender object
        
        Returns:
            Elasticsearch document
        """
        return {
            "tender_id": tender.tender_id,
            "title": tender.title,
            "description": tender.description or "",
            "extracted_text": tender.extracted_text or "",
            "platform": tender.platform,
            "customer": tender.customer or "",
            "category": tender.category or "",
            "status": tender.status,
            "budget": tender.budget,
            "currency": tender.currency,
            "start_date": tender.start_date.isoformat() if tender.start_date else None,
            "end_date": tender.end_date.isoformat() if tender.end_date else None,
            "normalized_at": tender.normalized_at.isoformat(),
        }
