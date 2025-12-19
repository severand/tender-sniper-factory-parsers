"""Sberbank tender spider with Playwright (Sprint 43)"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from factory_parsers.shared.logger import LoggingService
from factory_parsers.shared.metrics import scraped_tenders_total, scraper_errors_total

logger = LoggingService.get_logger(__name__)


class SberbankSpider:
    """Playwright-based spider for Sberbank procurement"""
    
    name = 'sberbank'
    platform_id = 'sberbank'
    base_url = 'https://zakupki.sberbank.ru'
    
    def __init__(self):
        """Initialize spider"""
        self.browser = None
        self.page = None
        logger.info("Sberbank spider initialized", extra={
            'event_type': 'start',
            'platform_id': self.platform_id,
            'spider_name': self.name,
        })
    
    async def init_browser(self):
        """Initialize Playwright browser"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox'],
            )
            self.page = await self.browser.new_page()
            
            # Set realistic headers
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'ru-RU,ru;q=0.9',
            })
            
            logger.info("Browser initialized", extra={
                'event_type': 'success',
                'platform_id': self.platform_id,
            })
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error': str(e),
            })
            raise
    
    async def fetch_tenders(self, page_num: int = 1) -> Optional[list]:
        """Fetch tenders list
        
        Args:
            page_num: Page number
        
        Returns:
            List of tender URLs
        """
        try:
            url = f"{self.base_url}/tenders?page={page_num}"
            
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for dynamic content
            await self.page.wait_for_selector('a.tender-item', timeout=10000)
            
            # Extract tender links
            tender_links = await self.page.eval_on_selector_all(
                'a.tender-item',
                'elements => elements.map(e => e.href)'
            )
            
            logger.info(f"Found {len(tender_links)} tenders on page {page_num}", extra={
                'event_type': 'success',
                'platform_id': self.platform_id,
                'page': page_num,
                'count': len(tender_links),
            })
            
            scraped_tenders_total.labels(platform=self.platform_id).inc(len(tender_links))
            return tender_links
        
        except Exception as e:
            scraper_errors_total.labels(platform=self.platform_id, error_type='fetch_list').inc()
            logger.error(f"Failed to fetch tenders: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error_type': 'fetch_list',
                'error': str(e),
            })
            return None
    
    async def parse_tender(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse tender detail
        
        Args:
            url: Tender URL
        
        Returns:
            Tender data
        """
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Extract data
            tender = {
                'tender_id': await self.page.text_content('span.tender-id') or '',
                'external_id': await self.page.text_content('span.external-id') or '',
                'title': await self.page.text_content('h1.tender-title') or '',
                'description': await self.page.text_content('div.tender-description') or '',
                'customer_name': await self.page.text_content('span.customer') or '',
                'budget_amount': self._parse_budget(
                    await self.page.text_content('span.budget') or ''
                ),
                'budget_currency': 'RUB',
                'deadline_date': await self.page.text_content('span.deadline') or '',
                'status': 'new',
                'source_url': url,
                'platform_id': self.platform_id,
            }
            
            logger.info(f"Parsed tender: {tender['tender_id']}", extra={
                'event_type': 'success',
                'platform_id': self.platform_id,
                'tender_id': tender['tender_id'],
                'url': url,
            })
            
            return tender
        
        except Exception as e:
            scraper_errors_total.labels(platform=self.platform_id, error_type='parse_detail').inc()
            logger.error(f"Failed to parse tender: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error_type': 'parse_detail',
                'url': url,
                'error': str(e),
            })
            return None
    
    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    @staticmethod
    def _parse_budget(budget_str: str) -> Optional[float]:
        """Parse budget amount"""
        if not budget_str:
            return None
        try:
            return float(budget_str.replace(' ', '').replace(',', '.'))
        except ValueError:
            return None
