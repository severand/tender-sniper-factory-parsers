"""Spider for Joomla-based tender portals"""

from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class JoomlaTenderPortalSpider(BaseTenderSpider):
    """Spider for Joomla-based tender portals"""
    
    name = "joomla_tender_portal"
    allowed_domains = []
    render_js = True  # Joomla sites often use JS
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Will be set from configuration
        self.start_urls = []
    
    def parse(self, response):
        """Parse tender list from Joomla portal"""
        # Extract links using common Joomla classes
        tender_links = response.css("a[class*='tender']::attr(href)").getall()
        tender_links += response.css("a[class*='item']::attr(href)").getall()
        
        for link in tender_links:
            yield response.follow(link, callback=self.parse_detail, meta={'render_js': True})
        
        # Handle pagination
        next_page = response.css("a.pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse, meta={'render_js': True})
