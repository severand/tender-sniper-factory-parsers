"""Base spider classes for Scrapy"""

from typing import List, Dict, Any, Optional
import scrapy
from scrapy.http import Response

from factory_parsers.shared.logger import logger
from factory_parsers.admin_service.models import FieldMapping


class BaseTenderSpider(scrapy.Spider):
    """Base spider for tender scraping"""
    
    name = "base_spider"
    allowed_domains = []
    
    def __init__(self, platform_id: int, search_rule_id: int, *args, **kwargs):
        """Initialize spider with platform and rule configuration"""
        super().__init__(*args, **kwargs)
        self.platform_id = platform_id
        self.search_rule_id = search_rule_id
        self.field_mappings: List[FieldMapping] = []
    
    def start_requests(self):
        """Generate initial requests"""
        logger.info(f"Starting spider {self.name} for platform {self.platform_id}")
        # Override in subclass
        return []
    
    def parse(self, response: Response):
        """Parse tender list page"""
        logger.info(f"Parsing list page: {response.url}")
        # Override in subclass
        pass
    
    def parse_detail(self, response: Response):
        """Parse tender detail page"""
        logger.info(f"Parsing detail page: {response.url}")
        tender_data = self.extract_fields(response)
        return tender_data
    
    def extract_fields(self, response: Response) -> Dict[str, Any]:
        """Extract fields using mappings"""
        data = {}
        for mapping in self.field_mappings:
            try:
                # Extract using CSS selector or XPath
                if mapping.platform_field.startswith(".") or mapping.platform_field.startswith("#"):
                    # CSS selector
                    values = response.css(mapping.platform_field)
                else:
                    # XPath
                    values = response.xpath(mapping.platform_field)
                
                if values:
                    value = values[0].get() if hasattr(values[0], 'get') else str(values[0])
                    
                    # Extract attribute if specified
                    if mapping.attribute and hasattr(values[0], 'attrib'):
                        value = values[0].attrib.get(mapping.attribute)
                    
                    data[mapping.standard_field] = value
            except Exception as e:
                logger.error(f"Error extracting field {mapping.standard_field}: {str(e)}")
                if mapping.required:
                    raise
        
        return data
    
    def handle_error(self, failure):
        """Handle request errors"""
        logger.error(f"Request failed: {failure.value}")
        return None


class TenderListSpider(BaseTenderSpider):
    """Spider for tender lists"""
    
    def parse(self, response: Response):
        """Parse tender list"""
        # Extract list selector and parse items
        pass


class TenderDetailSpider(BaseTenderSpider):
    """Spider for tender details"""
    
    def parse_detail(self, response: Response):
        """Parse tender detail"""
        return self.extract_fields(response)
