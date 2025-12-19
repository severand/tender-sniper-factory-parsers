"""Elasticsearch client wrapper"""

from typing import Dict, List, Optional, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from factory_parsers.shared.config import get_settings
from factory_parsers.shared.logger import logger

settings = get_settings()


class ElasticsearchClient:
    """Elasticsearch client for tender search"""
    
    def __init__(self):
        self.es = Elasticsearch([settings.elasticsearch_url])
        self.index_name = "tenders"
        self._init_index()
    
    def _init_index(self):
        """Initialize Elasticsearch index"""
        try:
            if not self.es.indices.exists(index=self.index_name):
                # Create index with mappings
                mappings = {
                    "mappings": {
                        "properties": {
                            "tender_id": {"type": "keyword"},
                            "title": {
                                "type": "text",
                                "analyzer": "standard",
                                "fields": {"raw": {"type": "keyword"}}
                            },
                            "description": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "extracted_text": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "platform": {"type": "keyword"},
                            "customer": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "status": {"type": "keyword"},
                            "budget": {"type": "float"},
                            "currency": {"type": "keyword"},
                            "start_date": {"type": "date"},
                            "end_date": {"type": "date"},
                            "normalized_at": {"type": "date"},
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                    }
                }
                self.es.indices.create(index=self.index_name, body=mappings)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize index: {str(e)}")
            raise
    
    def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index single document"""
        try:
            self.es.index(index=self.index_name, id=doc_id, body=document)
            logger.debug(f"Indexed document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {str(e)}")
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> int:
        """Bulk index documents"""
        try:
            actions = [
                {
                    "_index": self.index_name,
                    "_id": doc["tender_id"],
                    "_source": doc,
                }
                for doc in documents
            ]
            
            success, _ = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Bulk indexed {success} documents")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            return 0
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 20,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """Search documents"""
        try:
            es_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "description", "extracted_text"],
                                "fuzziness": "AUTO",
                            }
                        }
                    ]
                }
            }
            
            # Add filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        es_query["bool"]["filter"] = {
                            "terms": {field: value}
                        }
                    else:
                        es_query["bool"]["filter"] = {
                            "term": {field: value}
                        }
            
            results = self.es.search(
                index=self.index_name,
                body={"query": es_query, "size": size, "from": from_}
            )
            
            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"hits": {"total": 0, "hits": []}}
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document"""
        try:
            self.es.delete(index=self.index_name, id=doc_id)
            logger.debug(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False
    
    def clear_index(self) -> bool:
        """Clear all documents from index"""
        try:
            self.es.indices.delete(index=self.index_name)
            self._init_index()
            logger.info(f"Cleared index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear index: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.es.indices.stats(index=self.index_name)
            return stats["indices"][self.index_name]["primaries"]["docs"]
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {"count": 0, "deleted": 0}
