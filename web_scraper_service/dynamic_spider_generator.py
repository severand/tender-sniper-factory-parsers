"""Dynamic spider generator for platform configurations"""

from typing import Type
from datetime import datetime
from sqlalchemy.orm import Session
import scrapy

from shared.logger import logger
from shared.database import SessionLocal
from shared.models import Tender
from admin_service.models import Platform, SearchRule, FieldMapping
from admin_service.repositories import (
    PlatformRepository,
    SearchRuleRepository,
    FieldMappingRepository,
)
from web_scraper_service.base_spider import BaseTenderSpider


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
        class DynamicSpider(scrapy.Spider):
            name = f"dynamic_{platform.code}_{search_rule_id}"
            allowed_domains = [platform.url.split('/')[2]]
            start_urls = [rule.search_url]
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.platform_id = platform_id
                self.search_rule_id = search_rule_id
                self.field_mappings = {m.standard_field: m for m in mappings}
                self.list_selector = rule.list_selector
                self.pagination_type = rule.pagination_type
                self.pagination_selector = rule.pagination_selector or None
            
            def parse(self, response):
                """Parse tender list dynamically"""
                logger.info(f"Parsing list: {response.url}")
                
                # Extract list items
                items = response.css(self.list_selector)
                logger.info(f"Found {len(items)} items with selector: {self.list_selector}")
                
                for item in items:
                    # Извлекаем данные прямо из списка
                    yield self.extract_tender_data(item, response.url)
                
                # Handle pagination
                if self.pagination_type == "page" and self.pagination_selector:
                    next_page = response.css(self.pagination_selector).get()
                    if next_page:
                        yield response.follow(next_page, callback=self.parse)
            
            def extract_tender_data(self, item, page_url):
                """Extract tender data using field mappings"""
                data = {
                    'platform_id': self.platform_id,
                }
                
                # Извлекаем каждое поле по маппингу
                for field_name, mapping in self.field_mappings.items():
                    try:
                        selector = mapping.platform_field
                        
                        # Извлекаем значение
                        if '::attr(' in selector:
                            # Атрибут (например: a::attr(href))
                            css_part, attr_part = selector.split('::attr(')
                            attr_name = attr_part.rstrip(')')
                            value = item.css(f"{css_part}::attr({attr_name})").get()
                        elif '::text' in selector:
                            # Текст
                            css_part = selector.replace('::text', '')
                            value = item.css(f"{css_part}::text").get()
                        else:
                            # По умолчанию - текст
                            value = item.css(f"{selector}::text").get()
                        
                        if value:
                            value = value.strip()
                            
                            # Преобразуем тип данных
                            if mapping.field_type == 'number' or mapping.field_type == 'float':
                                # Очищаем от пробелов и запятых
                                value = value.replace(' ', '').replace(',', '.')
                                try:
                                    value = float(value)
                                except:
                                    value = None
                            
                            data[field_name] = value
                            logger.info(f"Extracted {field_name}: {value}")
                        else:
                            logger.warning(f"No value for {field_name} with selector {selector}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting {field_name}: {str(e)}")
                
                # Сохраняем в БД
                self.save_tender(data)
                
                return data
            
            def save_tender(self, data):
                """Save tender to database"""
                db = SessionLocal()
                try:
                    # Проверяем что URL уникальный
                    url = data.get('url')
                    if not url:
                        logger.warning("No URL found, skipping tender")
                        return
                    
                    # Проверяем существующий тендер
                    existing = db.query(Tender).filter(Tender.url == url).first()
                    if existing:
                        logger.info(f"Tender already exists: {url}")
                        return
                    
                    # Создаём новый тендер
                    tender = Tender(**data)
                    db.add(tender)
                    db.commit()
                    db.refresh(tender)
                    
                    logger.info(f"Saved tender #{tender.id}: {tender.title}")
                
                except Exception as e:
                    logger.error(f"Error saving tender: {str(e)}")
                    db.rollback()
                finally:
                    db.close()
        
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