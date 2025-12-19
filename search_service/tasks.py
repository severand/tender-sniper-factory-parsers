"""Celery tasks for search service"""

from factory_parsers.scheduler_service.celery_app import task
from factory_parsers.shared.database import SessionLocal
from factory_parsers.shared.logger import logger
from factory_parsers.search_service.indexer import TenderIndexer


@task(name="index_tender")
def index_tender(tender_id: str) -> dict:
    """Index single tender to Elasticsearch
    
    Args:
        tender_id: Tender ID
    
    Returns:
        Indexing result
    """
    db = SessionLocal()
    try:
        logger.info(f"Indexing tender: {tender_id}")
        indexer = TenderIndexer(db)
        success = indexer.index_tender(tender_id)
        return {"status": "success" if success else "failed", "tender_id": tender_id}
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise
    finally:
        db.close()


@task(name="bulk_index_tenders")
def bulk_index_tenders(platform: str = None) -> dict:
    """Bulk index tenders
    
    Args:
        platform: Optional platform filter
    
    Returns:
        Bulk indexing result
    """
    db = SessionLocal()
    try:
        logger.info(f"Bulk indexing tenders (platform={platform})")
        indexer = TenderIndexer(db)
        count = indexer.bulk_index(platform=platform)
        return {"status": "success", "indexed_count": count}
    except Exception as e:
        logger.error(f"Bulk indexing failed: {str(e)}")
        raise
    finally:
        db.close()


@task(name="reindex_all_tenders")
def reindex_all_tenders() -> dict:
    """Reindex all tenders
    
    Returns:
        Reindexing result
    """
    db = SessionLocal()
    try:
        logger.info("Starting full reindex")
        indexer = TenderIndexer(db)
        count = indexer.reindex_all()
        return {"status": "success", "indexed_count": count}
    except Exception as e:
        logger.error(f"Reindexing failed: {str(e)}")
        raise
    finally:
        db.close()
