"""Dynamic spider generator for platform configurations"""

from typing import Type
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from factory_parsers.admin_service.models import Platform, SearchRule, FieldMapping
from factory_parsers.admin_service.repositories import (
    PlatformRepository,
    SearchRuleRepository,
    FieldMappingRepository,
)
from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class DynamicSpiderGenerator:
    """Generate spiders from platform configurations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.platform_repo = PlatformRepository(db)
        self.rule_repo = SearchRuleRepository(db)
        self.mapping_repo = FieldMappingRepository(db)
    
    def generate_spider_class(self, platform_id: int, search_rule_id: int) -> Type[BaseTenderSpider]:
        """Generate spider class from configuration
        
        Args:
            platform_id: Platform ID
            search_rule_id: SearchRule ID
        
        Returns:
            Generated spider class
        """
        platform = self.platform_repo.get_by_id(platform_id)
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")
        
        rule = self.rule_repo.get_by_id(search_rule_id)
        if not rule:
            raise ValueError(f"SearchRule {search_rule_id} not found")
        
        mappings = self.mapping_repo.get_by_search_rule(search_rule_id)
        if not mappings:
            logger.warning(f"No field mappings found for rule {search_rule_id}")
        
        logger.info(f"Generating spider for platform {platform.code}, rule {rule.name}")
        
        # Create dynamic spider class
        class DynamicSpider(BaseTenderSpider):
            name = f"dynamic_{platform.code}_{search_rule_id}"
            allowed_domains = [platform.url.split('/')[2]]
            start_urls = [rule.search_url]
            
            def __init__(self, *args, **kwargs):
                super().__init__(platform_id, search_rule_id, *args, **kwargs)
                self.field_mappings = mappings
                self.list_selector = rule.list_selector
                self.pagination_type = rule.pagination_type
                self.pagination_selector = rule.pagination_selector or None
                self.render_js = False  # Set to True for JS-heavy sites
            
            def parse(self, response):
                """Parse tender list dynamically"""
                logger.info(f"Parsing list: {response.url}")
                
                # Extract list items
                items = response.css(self.list_selector)
                logger.info(f"Found {len(items)} items")
                
                for item in items:
                    # Try to find detail link
                    detail_link = item.css("a::attr(href)").get()
                    if detail_link:
                        yield response.follow(detail_link, callback=self.parse_detail)
                
                # Handle pagination
                if self.pagination_type == "page":
                    next_page = response.css(self.pagination_selector).get()
                    if next_page:
                        yield response.follow(next_page, callback=self.parse)
                
                elif self.pagination_type == "offset":
                    # Offset pagination
                    pass
        
        return DynamicSpider
    
    def get_available_spiders(self) -> list:
        """Get list of available spider configurations
        
        Returns:
            List of spider configs
        """
        platforms = self.platform_repo.list_all(active_only=True)
        spiders = []
        
        for platform in platforms:
            rules = self.rule_repo.get_by_platform(platform.id, active_only=True)
            for rule in rules:
                spiders.append({
                    'name': f"dynamic_{platform.code}_{rule.id}",
                    'platform_id': platform.id,
                    'rule_id': rule.id,
                    'platform': platform.code,
                    'rule': rule.name,
                })
        
        return spiders


def generate_spider(db: Session, platform_id: int, search_rule_id: int) -> Type[BaseTenderSpider]:
    """Generate spider from configuration
    
    Args:
        db: Database session
        platform_id: Platform ID
        search_rule_id: SearchRule ID
    
    Returns:
        Generated spider class
    """
    generator = DynamicSpiderGenerator(db)
    return generator.generate_spider_class(platform_id, search_rule_id)
