"""Spider for fz44.ru platform (JS-heavy)"""

from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class Fz44RuSpider(BaseTenderSpider):
    """Spider for Russia fz44.ru platform"""
    
    name = "fz44_ru"
    allowed_domains = ["fz44.ru"]
    start_urls = ["https://www.fz44.ru/"]
    render_js = True  # Requires JS rendering
    
    def parse(self, response):
        """Parse tender list"""
        # Extract tender links from JS-rendered content
        tender_links = response.css("a.purchase-link::attr(href)").getall()
        
        for link in tender_links:
            yield response.follow(link, callback=self.parse_detail, meta={'render_js': True})
        
        # Handle pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse, meta={'render_js': True})
