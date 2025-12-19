"""Playwright browser handler for JavaScript rendering"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser

from factory_parsers.shared.logger import logger


class PlaywrightHandler:
    """Handler for Playwright browser automation"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def launch(self):
        """Launch Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            logger.info("Playwright browser launched")
        except Exception as e:
            logger.error(f"Failed to launch Playwright: {str(e)}")
            raise
    
    async def close(self):
        """Close Playwright browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")
    
    async def render_page(self, url: str, wait_selector: Optional[str] = None) -> str:
        """Render page and return HTML
        
        Args:
            url: Page URL
            wait_selector: CSS selector to wait for
        
        Returns:
            Rendered HTML content
        """
        if not self.browser:
            await self.launch()
        
        page: Optional[Page] = None
        try:
            page = await self.browser.new_page()
            
            # Set viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to page
            await page.goto(url, wait_until="networkidle")
            
            # Wait for selector if provided
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=30000)
            
            # Wait for dynamic content
            await page.wait_for_timeout(2000)  # 2 seconds for JS rendering
            
            # Get HTML content
            html = await page.content()
            logger.info(f"Rendered page: {url}")
            return html
        
        except Exception as e:
            logger.error(f"Failed to render page {url}: {str(e)}")
            raise
        
        finally:
            if page:
                await page.close()
    
    async def extract_data(self, url: str, selectors: dict) -> dict:
        """Extract data from rendered page
        
        Args:
            url: Page URL
            selectors: Dict of field names to CSS selectors
        
        Returns:
            Extracted data
        """
        if not self.browser:
            await self.launch()
        
        page: Optional[Page] = None
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            data = {}
            for field, selector in selectors.items():
                try:
                    element = await page.query_selector(selector)
                    if element:
                        value = await element.text_content()
                        data[field] = value.strip() if value else None
                except Exception as e:
                    logger.warning(f"Failed to extract {field}: {str(e)}")
                    data[field] = None
            
            logger.info(f"Extracted data from {url}")
            return data
        
        except Exception as e:
            logger.error(f"Failed to extract data from {url}: {str(e)}")
            raise
        
        finally:
            if page:
                await page.close()


async def render_page_async(url: str, wait_selector: Optional[str] = None) -> str:
    """Async function to render page
    
    Args:
        url: Page URL
        wait_selector: CSS selector to wait for
    
    Returns:
        Rendered HTML
    """
    handler = PlaywrightHandler(headless=True)
    try:
        await handler.launch()
        html = await handler.render_page(url, wait_selector)
        return html
    finally:
        await handler.close()


def render_page_sync(url: str, wait_selector: Optional[str] = None) -> str:
    """Sync wrapper for render_page_async
    
    Args:
        url: Page URL
        wait_selector: CSS selector to wait for
    
    Returns:
        Rendered HTML
    """
    return asyncio.run(render_page_async(url, wait_selector))
