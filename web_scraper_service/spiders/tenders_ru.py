"""Spider for tenders.ru platform (JS-heavy)"""

from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class TendersRuSpider(BaseTenderSpider):
    """Spider for Russia tenders.ru platform"""
    
    name = "tenders_ru"
    allowed_domains = ["tenders.ru"]
    start_urls = ["https://www.tenders.ru/"]
    render_js = True  # Requires JS rendering
    
    def parse(self, response):
        """Parse tender list"""
        # Extract tender links from JS-rendered content
        tender_links = response.css("a.tender-link::attr(href)").getall()
        
        for link in tender_links:
            yield response.follow(link, callback=self.parse_detail, meta={'render_js': True})
        
        # Handle pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse, meta={'render_js': True})
