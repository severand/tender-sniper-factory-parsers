"""Scrapy middleware for Playwright rendering"""

from typing import Optional
from scrapy.http import Request, Response, HtmlResponse
from twisted.internet import defer

from factory_parsers.shared.logger import logger
from factory_parsers.web_scraper_service.playwright_handler import render_page_sync


class PlaywrightMiddleware:
    """Middleware for rendering JavaScript with Playwright"""
    
    def __init__(self):
        self.render_js = False
    
    def process_request(self, request: Request, spider):
        """Process request with Playwright if needed"""
        # Check if spider wants JS rendering
        if hasattr(spider, 'render_js') and spider.render_js:
            self.render_js = True
        
        # Mark request for Playwright processing
        if self.render_js or request.meta.get('render_js', False):
            return self.render_with_playwright(request, spider)
        
        return None
    
    def render_with_playwright(self, request: Request, spider):
        """Render page with Playwright
        
        Args:
            request: Scrapy request
            spider: Scrapy spider
        
        Returns:
            Deferred or Response
        """
        logger.info(f"Rendering with Playwright: {request.url}")
        
        try:
            # Get wait selector if specified
            wait_selector = request.meta.get('wait_selector')
            
            # Render page
            html = render_page_sync(request.url, wait_selector)
            
            # Create response from rendered HTML
            response = HtmlResponse(
                url=request.url,
                body=html.encode('utf-8'),
                encoding='utf-8',
                request=request,
            )
            
            logger.info(f"Rendered successfully: {request.url}")
            return response
        
        except Exception as e:
            logger.error(f"Playwright rendering failed: {str(e)}")
            # Fallback to static rendering if JS rendering fails
            logger.info(f"Falling back to static rendering: {request.url}")
            return None


class PlaywrightDegradationMiddleware:
    """Fallback middleware for failed JS rendering"""
    
    def process_exception(self, request: Request, exception, spider):
        """Handle rendering exceptions"""
        if request.meta.get('render_js'):
            logger.warning(f"JS rendering failed, retrying without JS: {request.url}")
            # Retry without JS rendering
            request.meta['render_js'] = False
            return request
        
        return None
