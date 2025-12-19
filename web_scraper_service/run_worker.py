"""Scrapy worker entry point"""

import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from factory_parsers.shared.logger import logger
from factory_parsers.web_scraper_service.spiders.etender_kz import ETenderKzSpider
from factory_parsers.web_scraper_service.spiders.zakupki_gov_ru import ZakupkiGovRuSpider
from factory_parsers.web_scraper_service.spiders.planfact_kz import PlanfactKzSpider


def run_spider(spider_name: str, platform_id: int, search_rule_id: int):
    """Run specific spider
    
    Args:
        spider_name: Spider class name
        platform_id: Platform ID
        search_rule_id: SearchRule ID
    """
    logger.info(f"Starting spider {spider_name} for platform {platform_id}")
    
    process = CrawlerProcess({
        'USER_AGENT': 'Tender-Sniper/0.1',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 3,
        'COOKIES_ENABLED': False,
    })
    
    # Map spider names to classes
    spiders = {
        'etender_kz': ETenderKzSpider,
        'zakupki_gov_ru': ZakupkiGovRuSpider,
        'planfact_kz': PlanfactKzSpider,
    }
    
    spider_class = spiders.get(spider_name)
    if not spider_class:
        logger.error(f"Unknown spider: {spider_name}")
        return False
    
    try:
        process.crawl(spider_class, platform_id=platform_id, search_rule_id=search_rule_id)
        process.start()
        logger.info(f"Spider {spider_name} completed successfully")
        return True
    except Exception as e:
        logger.error(f"Spider {spider_name} failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python run_worker.py <spider_name> <platform_id> <search_rule_id>")
        print("Example: python run_worker.py etender_kz 1 1")
        sys.exit(1)
    
    spider_name = sys.argv[1]
    platform_id = int(sys.argv[2])
    search_rule_id = int(sys.argv[3])
    
    success = run_spider(spider_name, platform_id, search_rule_id)
    sys.exit(0 if success else 1)
