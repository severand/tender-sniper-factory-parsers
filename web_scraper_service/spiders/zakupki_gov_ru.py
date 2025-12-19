"""Zakupki.gov.ru Parser with parsing modes support"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base_parser import BaseTenderParser

logger = logging.getLogger(__name__)


class ZakupkiParser(BaseTenderParser):
    """HTML parser for zakupki.gov.ru with parsing modes"""
    
    def __init__(self):
        super().__init__()
        self.source = "zakupki"
        self.base_url = "https://zakupki.gov.ru"
        self.search_url = f"{self.base_url}/epz/order/extendedsearch/results.html"
    
    def parse(
        self,
        keywords: List[str] = None,
        min_price: int = 0,
        max_price: Optional[int] = None,
        region: Optional[str] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Dict]:
        """Parse tenders from zakupki.gov.ru
        
        Args:
            keywords: Search keywords
            min_price: Minimum price in rubles
            max_price: Maximum price in rubles
            region: Region filter
            limit: Maximum tenders to return
        
        Returns:
            List of tender dictionaries
        """
        keywords = keywords or []
        search_query = ' '.join(keywords) if keywords else ''
        
        params = {
            'searchString': search_query,
            'morphology': 'on',
            'search-filter': 'Дате размещения',
            'pageNumber': 1,
            'sortDirection': 'false',
            'recordsPerPage': '_50',
            'showLotsInfoHidden': 'false',
            'sortBy': 'UPDATE_DATE',
            'fz44': 'on',
            'fz223': 'on',
            'ppRf615': 'on',
            'currencyIdGeneral': '-1'
        }
        
        if min_price:
            params['priceFromGeneral'] = min_price
        if max_price:
            params['priceToGeneral'] = max_price
        if region:
            params['selectedRegionDeleted'] = region
        
        logger.info(f"Parsing zakupki.gov.ru: '{search_query}' (mode: {self._mode_name})")
        
        # Make request using base parser (with delays and retries)
        response = self._make_request(self.search_url, params=params)
        
        if not response:
            logger.error("Failed to fetch zakupki.gov.ru search results")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tenders = []
        
        # Find tender cards
        tender_cards = soup.find_all('div', class_='search-registry-entry-block')
        if not tender_cards:
            tender_cards = soup.find_all('div', {'data-test-id': 'tender-card'})
        
        logger.info(f"Found {len(tender_cards)} tender cards")
        
        for card in tender_cards[:limit]:
            try:
                tender = self._parse_tender_card(card)
                if tender:
                    tenders.append(tender)
            except Exception as e:
                logger.warning(f"Failed to parse tender card: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(tenders)} tenders")
        return tenders
    
    def _parse_tender_card(self, card) -> Optional[Dict]:
        """Parse single tender card"""
        try:
            # Number
            number_elem = card.find('div', class_='registry-entry__header-mid__number')
            number = number_elem.text.strip() if number_elem else None
            
            # URL
            link_elem = card.find('a', class_='registry-entry__header-mid__number')
            tender_url = f"{self.base_url}{link_elem['href']}" if link_elem and link_elem.get('href') else None
            
            # Title
            title_elem = card.find('div', class_='registry-entry__body-value')
            title = title_elem.text.strip() if title_elem else None
            
            # Price
            price_elem = card.find('div', class_='price-block__value')
            price_text = price_elem.text.strip() if price_elem else '0'
            price = self._parse_price(price_text)
            
            # Customer
            customer_elem = card.find('div', class_='registry-entry__body-href')
            customer = customer_elem.text.strip() if customer_elem else None
            
            # Dates
            date_elem = card.find('div', class_='registry-entry__header-mid__publish-date')
            publish_date = date_elem.text.strip() if date_elem else None
            
            deadline_elem = card.find('div', class_='data-block__deadline')
            deadline = deadline_elem.text.strip() if deadline_elem else None
            
            # Law type
            law_elem = card.find('div', class_='registry-entry__header-mid__item')
            law_type = law_elem.text.strip() if law_elem else 'N/A'
            
            # Extract tender ID from URL
            tender_id = None
            if tender_url:
                parts = tender_url.split('/')
                if 'notice' in tender_url:
                    tender_id = parts[-1].split('?')[0]
            
            return {
                'id': tender_id or number,
                'number': number,
                'title': title,
                'start_price': price,
                'deadline': deadline,
                'publish_date': publish_date,
                'region': 'N/A',
                'customer': customer,
                'tender_url': tender_url,
                'law_type': law_type,
                'source': 'zakupki.gov.ru',
                'fetched_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error parsing tender card: {e}")
            return None
    
    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price from text"""
        try:
            clean = ''.join(c for c in price_text if c.isdigit() or c in ',.')
            clean = clean.replace(',', '.').replace(' ', '')
            return float(clean) if clean else 0.0
        except:
            return 0.0
    
    def fetch_tender_details(self, tender_url: str) -> Optional[Dict]:
        """Fetch detailed tender information"""
        response = self._make_request(tender_url)
        
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = {
            'full_description': None,
            'documents': [],
            'requirements': None
        }
        
        # Description
        desc_elem = soup.find('div', class_='notice__info')
        if desc_elem:
            details['full_description'] = desc_elem.text.strip()
        
        # Documents
        doc_links = soup.find_all('a', class_='document-link')
        for link in doc_links:
            details['documents'].append({
                'name': link.text.strip(),
                'url': f"{self.base_url}{link['href']}"
            })
        
        return details
