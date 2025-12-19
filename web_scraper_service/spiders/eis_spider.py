"""EIS (Единая информационная система) spider (Sprint 41)"""

import scrapy
from typing import Optional, Dict, Any

from factory_parsers.shared.logger import LoggingService
from factory_parsers.shared.metrics import scraped_tenders_total, scraper_errors_total

logger = LoggingService.get_logger(__name__)


class EISSpider(scrapy.Spider):
    """Web scraper for EIS tender platform"""
    
    name = 'eis'
    allowed_domains = ['eis.zakupki.gov.ru']
    platform_id = 'eis'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = ['https://eis.zakupki.gov.ru/etp/customer/tenders']
        logger.info(f"EIS spider initialized", extra={
            'event_type': 'start',
            'platform_id': self.platform_id,
            'spider_name': self.name,
        })
    
    def start_requests(self):
        """Generate initial requests"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list,
                meta={'dont_retry': False, 'max_retries': 3},
            )
    
    def parse_list(self, response):
        """Parse tender list page"""
        try:
            # Extract tender links
            tender_links = response.css('a.tender-link::attr(href)').getall()
            
            for link in tender_links:
                yield scrapy.Request(
                    response.urljoin(link),
                    callback=self.parse_detail,
                    meta={'dont_retry': False, 'max_retries': 3},
                )
            
            # Next page
            next_page = response.css('a.next-page::attr(href)').get()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    callback=self.parse_list,
                )
            
            scraped_tenders_total.labels(platform=self.platform_id).inc(len(tender_links))
            logger.info(f"Parsed {len(tender_links)} tender links", extra={
                'event_type': 'success',
                'platform_id': self.platform_id,
                'count': len(tender_links),
            })
        
        except Exception as e:
            scraper_errors_total.labels(platform=self.platform_id, error_type='parse_list').inc()
            logger.error(f"Error parsing list: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error_type': 'parse_list',
                'error': str(e),
            })
    
    def parse_detail(self, response):
        """Parse tender detail page"""
        try:
            tender = {
                'tender_id': response.css('span.tender-id::text').get(''),
                'external_id': response.css('span.external-id::text').get(''),
                'title': response.css('h1.tender-title::text').get(''),
                'description': response.css('div.tender-description::text').get(''),
                'customer_name': response.css('span.customer::text').get(''),
                'budget_amount': self._parse_budget(response.css('span.budget::text').get('')),
                'budget_currency': 'RUB',
                'deadline_date': response.css('span.deadline::text').get(''),
                'status': response.css('span.status::text').get('new'),
                'source_url': response.url,
                'platform_id': self.platform_id,
            }
            
            logger.info(f"Parsed tender detail: {tender['tender_id']}", extra={
                'event_type': 'success',
                'platform_id': self.platform_id,
                'tender_id': tender['tender_id'],
            })
            
            yield tender
        
        except Exception as e:
            scraper_errors_total.labels(platform=self.platform_id, error_type='parse_detail').inc()
            logger.error(f"Error parsing detail: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error_type': 'parse_detail',
                'error': str(e),
            })
    
    @staticmethod
    def _parse_budget(budget_str: str) -> Optional[float]:
        """Parse budget amount"""
        if not budget_str:
            return None
        try:
            return float(budget_str.replace(' ', '').replace(',', '.'))
        except ValueError:
            return None
