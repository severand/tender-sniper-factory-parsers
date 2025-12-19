"""Scrapy pipelines for data processing"""

from typing import Dict, Any
from scrapy.exceptions import DropItem

from factory_parsers.shared.logger import logger


class DataValidationPipeline:
    """Pipeline for data validation"""
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Validate item data"""
        # Check required fields
        required_fields = ['tender_id', 'title', 'description']
        for field in required_fields:
            if field not in item or not item[field]:
                logger.warning(f"Missing required field: {field}")
                raise DropItem(f"Missing required field: {field}")
        
        return item


class DataNormalizationPipeline:
    """Pipeline for data normalization"""
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Normalize item data"""
        # Clean whitespace
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()
        
        logger.debug(f"Normalized item: {item.get('tender_id')}")
        return item


class DuplicateCheckPipeline:
    """Pipeline for duplicate detection"""
    
    def __init__(self):
        self.seen_ids = set()
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Check for duplicates"""
        tender_id = item.get('tender_id')
        
        if tender_id in self.seen_ids:
            logger.warning(f"Duplicate tender: {tender_id}")
            raise DropItem(f"Duplicate tender: {tender_id}")
        
        self.seen_ids.add(tender_id)
        return item


class NormalizerPipeline:
    """Pipeline to send data to normalizer_service"""
    
    async def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Send item to normalizer service"""
        try:
            # TODO: Send to normalizer_service via task queue
            logger.info(f"Queuing for normalization: {item.get('tender_id')}")
            return item
        except Exception as e:
            logger.error(f"Normalizer error: {str(e)}")
            raise DropItem(f"Normalization failed: {str(e)}")
