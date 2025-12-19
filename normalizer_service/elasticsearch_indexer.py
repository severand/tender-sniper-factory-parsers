"""Elasticsearch indexing for normalized tenders"""

from typing import Dict, Any, Optional

fromshared.logger import logger
fromsearch_service.elasticsearch_client import ElasticsearchClient
from .models import NormalizedTender


class ElasticsearchIndexer:
    """Index normalized tenders in Elasticsearch"""
    
    def __init__(self):
        self.es_client = ElasticsearchClient()
        self.index_name = "tenders_normalized"
    
    def index_tender(self, tender: NormalizedTender) -> bool:
        """Index single tender
        
        Args:
            tender: NormalizedTender record
        
        Returns:
            Success status
        """
        try:
            doc = self._tender_to_doc(tender)
            self.es_client.index_document(
                index=self.index_name,
                doc_id=tender.tender_id,
                document=doc
            )
            logger.info(f"Indexed tender: {tender.tender_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index tender {tender.tender_id}: {str(e)}")
            return False
    
    def bulk_index(self, tenders: list) -> Dict[str, int]:
        """Bulk index multiple tenders
        
        Args:
            tenders: List of NormalizedTender records
        
        Returns:
            Indexing stats {indexed: count, errors: count}
        """
        docs = [self._tender_to_doc(t) for t in tenders]
        result = self.es_client.bulk_index(
            index=self.index_name,
            documents=docs
        )
        logger.info(f"Bulk indexed {len(tenders)} tenders")
        return result
    
    def delete_tender(self, tender_id: str) -> bool:
        """Delete tender from index
        
        Args:
            tender_id: Tender ID to delete
        
        Returns:
            Success status
        """
        try:
            self.es_client.delete_document(self.index_name, tender_id)
            logger.info(f"Deleted tender from index: {tender_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tender {tender_id}: {str(e)}")
            return False
    
    @staticmethod
    def _tender_to_doc(tender: NormalizedTender) -> Dict[str, Any]:
        """Convert NormalizedTender to ES document
        
        Args:
            tender: NormalizedTender record
        
        Returns:
            Document for indexing
        """
        return {
            "tender_id": tender.tender_id,
            "platform_id": tender.platform_id,
            "external_id": tender.external_id,
            "title": tender.title,
            "description": tender.description,
            "summary": tender.summary or tender.ai_summary,
            "category": tender.category,
            "customer_name": tender.customer_name,
            "budget_amount": tender.budget_amount,
            "budget_currency": tender.budget_currency,
            "status": tender.status,
            "published_date": tender.published_date.isoformat() if tender.published_date else None,
            "deadline_date": tender.deadline_date.isoformat() if tender.deadline_date else None,
            "start_date": tender.start_date.isoformat() if tender.start_date else None,
            "end_date": tender.end_date.isoformat() if tender.end_date else None,
            "requirements": tender.requirements or [],
            "criteria": tender.criteria or [],
            "ai_keywords": tender.ai_keywords or [],
            "data_quality_score": tender.data_quality_score,
            "is_duplicate": tender.is_duplicate,
            "normalized_at": tender.normalized_at.isoformat(),
        }
