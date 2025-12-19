"""Data normalization and standardization - SPRINT 32 Implementation"""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from .models import NormalizedTender, NormalizationLog
from .field_mapper import FieldMapper
from .duplicate_detector import DuplicateDetector
from .elasticsearch_indexer import ElasticsearchIndexer


class TenderNormalizer:
    """Complete tender normalization pipeline (Sprint 32)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.field_mapper = FieldMapper(db)
        self.duplicate_detector = DuplicateDetector(db)
        self.es_indexer = ElasticsearchIndexer()
    
    def normalize_and_store(self, raw_data: Dict[str, Any], platform_id: str) -> Tuple[bool, Optional[int]]:
        """Complete normalization pipeline (data → PostgreSQL + Elasticsearch)
        
        Args:
            raw_data: Raw tender data from scraper/API
            platform_id: Platform identifier
        
        Returns:
            Tuple of (success: bool, tender_id: int or None)
        """
        log = NormalizationLog(
            tender_id=raw_data.get('tender_id', 'unknown'),
            raw_data_id=raw_data.get('id'),
            status='started',
            started_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Apply field mapping
            mapping = self.field_mapper.get_mapping(platform_id)
            if not mapping:
                logger.warning(f"No mapping for platform {platform_id}, using raw data")
                mapped_data = raw_data
            else:
                mapped_data = self.field_mapper.map_fields(raw_data, mapping)
            
            # Step 2: Normalize individual fields
            normalized_data = self._normalize_fields(mapped_data, platform_id)
            
            # Step 3: Validate data
            is_valid, errors = self._validate_tender(normalized_data)
            if not is_valid:
                log.status = 'failed'
                log.errors = errors
                log.message = f"Validation failed: {'; '.join(errors)}"
                self.db.commit()
                logger.error(f"Tender validation failed: {errors}")
                return False, None
            
            # Step 4: Detect duplicates
            is_dup, dup_of = self.duplicate_detector.is_duplicate(
                normalized_data.get('external_id', ''),
                platform_id,
                normalized_data.get('title', '')
            )
            
            if is_dup and dup_of:
                self.duplicate_detector.mark_as_duplicate(
                    normalized_data.get('tender_id'),
                    dup_of
                )
                log.status = 'duplicate'
                log.message = f"Duplicate of tender {dup_of}"
                self.db.commit()
                logger.info(f"Tender marked as duplicate")
                return True, dup_of
            
            # Step 5: Store in PostgreSQL
            tender = NormalizedTender(
                tender_id=normalized_data['tender_id'],
                platform_id=platform_id,
                external_id=normalized_data.get('external_id', ''),
                title=normalized_data.get('title'),
                description=normalized_data.get('description'),
                summary=normalized_data.get('summary'),
                category=normalized_data.get('category'),
                customer_name=normalized_data.get('customer_name'),
                customer_contact=normalized_data.get('customer_contact'),
                published_date=normalized_data.get('published_date'),
                deadline_date=normalized_data.get('deadline_date'),
                start_date=normalized_data.get('start_date'),
                end_date=normalized_data.get('end_date'),
                budget_amount=normalized_data.get('budget_amount'),
                budget_currency=normalized_data.get('budget_currency', 'RUB'),
                status=normalized_data.get('status', 'new'),
                source_url=normalized_data.get('source_url'),
                requirements=normalized_data.get('requirements'),
                criteria=normalized_data.get('criteria'),
                restrictions=normalized_data.get('restrictions'),
                attachments=normalized_data.get('attachments'),
                ai_extracted=normalized_data.get('ai_extracted'),
                ai_keywords=normalized_data.get('ai_keywords'),
                raw_data=raw_data,
                extracted_text=normalized_data.get('extracted_text'),
                data_quality_score=self._calculate_quality_score(normalized_data),
                is_duplicate=False,
                normalized_at=datetime.utcnow(),
                processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
            
            self.db.add(tender)
            self.db.commit()
            
            # Step 6: Index in Elasticsearch
            indexed = self.es_indexer.index_tender(tender)
            if not indexed:
                logger.warning(f"Failed to index tender in Elasticsearch")
            
            # Update log
            log.status = 'success'
            log.completed_at = datetime.utcnow()
            log.duration_ms = int((log.completed_at - log.started_at).total_seconds() * 1000)
            self.db.commit()
            
            logger.info(f"Successfully normalized and stored tender: {tender.tender_id}")
            return True, tender.id
        
        except Exception as e:
            logger.error(f"Normalization error: {str(e)}", exc_info=True)
            log.status = 'failed'
            log.message = str(e)
            log.completed_at = datetime.utcnow()
            self.db.commit()
            return False, None
    
    def _normalize_fields(self, data: Dict[str, Any], platform_id: str) -> Dict[str, Any]:
        """Normalize individual fields
        
        Args:
            data: Mapped data
            platform_id: Platform identifier
        
        Returns:
            Normalized data
        """
        return {
            'tender_id': data.get('tender_id'),
            'external_id': data.get('external_id'),
            'title': self._normalize_text(data.get('title')),
            'description': self._normalize_text(data.get('description')),
            'summary': data.get('summary'),
            'category': self._normalize_text(data.get('category')),
            'customer_name': self._normalize_text(data.get('customer_name')),
            'customer_contact': data.get('customer_contact'),
            'published_date': self._normalize_date(data.get('published_date')),
            'deadline_date': self._normalize_date(data.get('deadline_date')),
            'start_date': self._normalize_date(data.get('start_date')),
            'end_date': self._normalize_date(data.get('end_date')),
            'budget_amount': self._normalize_budget(data.get('budget_amount')),
            'budget_currency': self._normalize_currency(data.get('budget_currency')),
            'status': data.get('status', 'new'),
            'source_url': data.get('source_url'),
            'requirements': data.get('requirements'),
            'criteria': data.get('criteria'),
            'restrictions': data.get('restrictions'),
            'attachments': data.get('attachments'),
            'ai_extracted': data.get('ai_extracted'),
            'ai_keywords': data.get('ai_keywords'),
            'extracted_text': data.get('extracted_text'),
        }
    
    @staticmethod
    def _normalize_text(text: str) -> Optional[str]:
        """Normalize text field"""
        if not text:
            return None
        text = re.sub(r'\s+', ' ', str(text))
        text = text.strip()
        return text if text else None
    
    @staticmethod
    def _normalize_date(date_str: str) -> Optional[datetime]:
        """Normalize date to datetime"""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%d %b %Y',
            '%d %B %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    @staticmethod
    def _normalize_budget(budget_str: str) -> Optional[float]:
        """Normalize budget to float"""
        if not budget_str:
            return None
        
        if isinstance(budget_str, (int, float)):
            return float(budget_str)
        
        budget_str = re.sub(r'[\s,\-]+', '', str(budget_str))
        numbers = re.findall(r'\d+', budget_str)
        
        if numbers:
            try:
                return float(''.join(numbers))
            except ValueError:
                pass
        
        logger.warning(f"Could not parse budget: {budget_str}")
        return None
    
    @staticmethod
    def _normalize_currency(currency_str: str) -> str:
        """Normalize currency code"""
        if not currency_str:
            return "RUB"
        
        currency_str = str(currency_str).upper().strip()
        
        currency_map = {
            'РУБ': 'RUB', 'РУБ.': 'RUB', 'РУБЛЬ': 'RUB', 'РУБЛЕЙ': 'RUB',
            'KZT': 'KZT', 'ТЕНГЕ': 'KZT',
            'USD': 'USD', 'DOLLAR': 'USD', 'ДОЛЛАР': 'USD',
            'EUR': 'EUR', 'EURO': 'EUR', 'ЕВРО': 'EUR',
        }
        
        return currency_map.get(currency_str, currency_str[:3])
    
    @staticmethod
    def _validate_tender(data: Dict[str, Any]) -> Tuple[bool, list]:
        """Validate normalized tender data"""
        errors = []
        
        required = ['tender_id', 'title']
        for field in required:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                errors.append("start_date is after end_date")
        
        if data.get('budget_amount') and data['budget_amount'] < 0:
            errors.append("Budget is negative")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _calculate_quality_score(data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-100)
        
        Args:
            data: Normalized tender data
        
        Returns:
            Quality score
        """
        score = 0.0
        max_score = 100.0
        
        # Check presence of important fields
        fields_weight = {
            'title': 20,
            'budget_amount': 15,
            'deadline_date': 15,
            'customer_name': 15,
            'description': 15,
            'category': 10,
            'requirements': 5,
            'attachments': 5,
        }
        
        for field, weight in fields_weight.items():
            if data.get(field):
                score += weight
        
        return min(score, max_score)
