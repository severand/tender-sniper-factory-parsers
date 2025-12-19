"""Celery tasks for normalizer service - SPRINT 32"""

from datetime import datetime
from sqlalchemy.orm import Session

from factory_parsers.scheduler_service.celery_app import task
from factory_parsers.shared.database import SessionLocal
from factory_parsers.shared.logger import logger
from factory_parsers.normalizer_service.normalizer import TenderNormalizer
from factory_parsers.normalizer_service.text_extractor import TextExtractor
from factory_parsers.normalizer_service.repositories import NormalizedTenderRepository


@task(name="normalize_tender", bind=True, max_retries=3)
def normalize_tender_task(self, raw_tender_data: dict, platform_id: str) -> dict:
    """Normalize single tender (Sprint 32.7)
    
    Args:
        raw_tender_data: Raw tender from scraper/API
        platform_id: Platform identifier
    
    Returns:
        Result dict
    """
    db = SessionLocal()
    try:
        tender_id = raw_tender_data.get('tender_id')
        logger.info(f"Normalizing tender {tender_id} from platform {platform_id}")
        
        normalizer = TenderNormalizer(db)
        success, stored_id = normalizer.normalize_and_store(raw_tender_data, platform_id)
        
        if success:
            logger.info(f"Successfully normalized tender {tender_id}")
            return {
                'status': 'success',
                'tender_id': tender_id,
                'stored_id': stored_id,
            }
        else:
            logger.error(f"Failed to normalize tender {tender_id}")
            return {
                'status': 'failed',
                'tender_id': tender_id,
                'error': 'Normalization failed',
            }
    
    except Exception as e:
        logger.error(f"Normalization error: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    
    finally:
        db.close()


@task(name="extract_text_from_tender_attachments", bind=True)
def extract_text_from_attachments(self, tender_id: str, attachment_urls: list) -> dict:
    """Extract text from tender attachments
    
    Args:
        tender_id: Tender ID
        attachment_urls: List of attachment URLs
    
    Returns:
        Extraction results
    """
    db = SessionLocal()
    try:
        logger.info(f"Extracting text from {len(attachment_urls)} attachments for {tender_id}")
        
        extracted_texts = []
        errors = []
        
        for url in attachment_urls:
            try:
                text = TextExtractor.extract_from_url(url)
                if text:
                    extracted_texts.append(text)
            except Exception as e:
                logger.error(f"Failed to extract from {url}: {str(e)}")
                errors.append({"url": url, "error": str(e)})
        
        # Update tender with extracted text
        if extracted_texts:
            combined_text = '\n\n---\n\n'.join(extracted_texts)
            tender_repo = NormalizedTenderRepository(db)
            tender_repo.update_extracted_text(tender_id, combined_text)
            logger.info(f"Extracted {len(extracted_texts)} documents from {tender_id}")
        
        return {
            'status': 'success' if not errors else 'partial',
            'tender_id': tender_id,
            'extracted_count': len(extracted_texts),
            'errors': errors,
        }
    
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return {
            'status': 'failed',
            'tender_id': tender_id,
            'error': str(e),
        }
    
    finally:
        db.close()


@task(name="batch_normalize_tenders")
def batch_normalize_tenders(tenders_data: list, platform_id: str) -> dict:
    """Normalize batch of tenders (Sprint 32.7)
    
    Args:
        tenders_data: List of raw tender data
        platform_id: Platform identifier
    
    Returns:
        Batch processing results
    """
    results = {
        'total': len(tenders_data),
        'success': 0,
        'failed': 0,
        'errors': [],
    }
    
    logger.info(f"Starting batch normalization: {len(tenders_data)} tenders from {platform_id}")
    
    for tender_data in tenders_data:
        try:
            # Queue each tender for normalization
            normalize_tender_task.delay(tender_data, platform_id)
            results['success'] += 1
        except Exception as e:
            logger.error(f"Batch queuing failed: {str(e)}")
            results['failed'] += 1
            results['errors'].append(str(e))
    
    logger.info(f"Batch queued: {results['success']}/{results['total']} success")
    return results


@task(name="reprocess_failed_tenders")
def reprocess_failed_tenders(limit: int = 100) -> dict:
    """Reprocess tenders with failed normalization
    
    Args:
        limit: Max tenders to reprocess
    
    Returns:
        Reprocessing results
    """
    db = SessionLocal()
    try:
        logger.info(f"Reprocessing up to {limit} failed tenders")
        repo = NormalizedTenderRepository(db)
        # TODO: Query failed tenders from NormalizationLog and re-queue
        return {'status': 'pending'}
    
    finally:
        db.close()
