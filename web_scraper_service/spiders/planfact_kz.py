"""Spider for planfact.kz platform"""

from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class PlanfactKzSpider(BaseTenderSpider):
    """Spider for Kazakhstan planfact.kz platform"""
    
    name = "planfact_kz"
    allowed_domains = ["planfact.kz"]
    start_urls = ["https://www.planfact.kz/"]
    
    def parse(self, response):
        """Parse tender list"""
        # Extract tender links
        tender_links = response.css("a.tender-item::attr(href)").getall()
        
        for link in tender_links:
            yield response.follow(link, callback=self.parse_detail)
        
        # Handle pagination
        next_page = response.css("a.pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
