"""Scraper manager for coordinating spider execution"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from scrapy.crawler import CrawlerProcess

from shared.logger import logger
from admin_service.repositories import PlatformRepository, SearchRuleRepository
from web_scraper_service.dynamic_spider_generator import DynamicSpiderGenerator
from scheduler_service.celery_app import task


class ScraperManager:
    """Manage spider execution and coordination"""
    
    def __init__(self, db: Session):
        self.db = db
        self.platform_repo = PlatformRepository(db)
        self.rule_repo = SearchRuleRepository(db)
        self.generator = DynamicSpiderGenerator(db)
    
    def run_spider(self, platform_id: int, search_rule_id: int) -> bool:
        """Run spider for platform and rule
        
        Args:
            platform_id: Platform ID
            search_rule_id: SearchRule ID
        
        Returns:
            Success status
        """
        logger.info(f"Starting spider: platform {platform_id}, rule {search_rule_id}")
        
        try:
            # Generate spider class
            spider_class = self.generator.generate_spider_class(platform_id, search_rule_id)
            
            # Create and run crawler
            process = CrawlerProcess({
                'USER_AGENT': 'Tender-Sniper/0.1',
                'ROBOTSTXT_OBEY': True,
                'CONCURRENT_REQUESTS': 8,
                'DOWNLOAD_DELAY': 5,
                'COOKIES_ENABLED': True,
                'REDIRECT_ENABLED': True,
            })
            
            process.crawl(
                spider_class,
                platform_id=platform_id,
                search_rule_id=search_rule_id,
            )
            process.start()
            
            logger.info(f"Spider completed: platform {platform_id}, rule {search_rule_id}")
            return True
        
        except Exception as e:
            logger.error(f"Spider failed: {str(e)}")
            return False
    
    def run_all_platforms(self) -> Dict[str, int]:
        """Run spiders for all active platforms
        
        Returns:
            Statistics dict
        """
        platforms = self.platform_repo.list_all(active_only=True)
        
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
        }
        
        for platform in platforms:
            rules = self.rule_repo.get_by_platform(platform.id, active_only=True)
            for rule in rules:
                stats['total'] += 1
                try:
                    success = self.run_spider(platform.id, rule.id)
                    if success:
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                except Exception as e:
                    logger.error(f"Error running spider: {str(e)}")
                    stats['failed'] += 1
        
        return stats
    
    def get_spider_status(self, platform_id: int) -> Dict:
        """Get spider status for platform
        
        Args:
            platform_id: Platform ID
        
        Returns:
            Status dict
        """
        platform = self.platform_repo.get_by_id(platform_id)
        if not platform:
            return {'error': 'Platform not found'}
        
        rules = self.rule_repo.get_by_platform(platform_id)
        
        return {
            'platform_id': platform_id,
            'platform_name': platform.name,
            'total_rules': len(rules),
            'active_rules': len([r for r in rules if r.is_active]),
            'rules': [
                {
                    'id': r.id,
                    'name': r.name,
                    'active': r.is_active,
                }
                for r in rules
            ],
        }


@task(name="run_scraper_for_platform")
def run_scraper_for_platform(platform_id: int, search_rule_id: int) -> bool:
    """Celery task to run scraper
    
    Args:
        platform_id: Platform ID
        search_rule_id: SearchRule ID
    
    Returns:
        Success status
    """
    from shared.database import SessionLocal
    
    db = SessionLocal()
    try:
        manager = ScraperManager(db)
        return manager.run_spider(platform_id, search_rule_id)
    finally:
        db.close()


@task(name="run_all_scrapers")
def run_all_scrapers() -> Dict[str, int]:
    """Celery task to run all scrapers
    
    Returns:
        Statistics dict
    """
    from shared.database import SessionLocal
    
    db = SessionLocal()
    try:
        manager = ScraperManager(db)
        return manager.run_all_platforms()
    finally:
        db.close()