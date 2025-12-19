"""Spider for e-tender.kz platform"""

from factory_parsers.web_scraper_service.base_spider import BaseTenderSpider


class ETenderKzSpider(BaseTenderSpider):
    """Spider for Kazakhstan e-tender.kz platform"""
    
    name = "etender_kz"
    allowed_domains = ["etender.kz"]
    start_urls = ["https://www.etender.kz/"]
    
    def parse(self, response):
        """Parse tender list"""
        # Extract tender links
        tender_links = response.css("a.tender-link::attr(href)").getall()
        
        for link in tender_links:
            yield response.follow(link, callback=self.parse_detail)
        
        # Handle pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
