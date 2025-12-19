"""RTS (Russian Trading System) Parser"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .base_parser import BaseTenderParser

logger = logging.getLogger(__name__)


class RTSParser(BaseTenderParser):
    """Parser for RTS - government purchases"""
    
    def __init__(self):
        super().__init__()
        self.source = "rts"
        self.base_url = "https://www.rts.ru"
        self.api_url = "https://api.rts.ru"
    
    def parse(self, page: int = 1, limit: int = 50, **kwargs) -> List[Dict[str, Any]]:
        """Parse RTS tenders"""
        logger.info(f"Parsing RTS: page={page}, limit={limit} (mode: {self._mode_name})")
        
        url = f"{self.api_url}/openapi/4_0_0/tenders"
        params = {
            "pageNum": page,
            "pageSize": limit,
            "sorting": "BY_PUBLICATION_DATE_DESC"
        }
        
        response = self._make_request(url, params=params)
        
        if not response:
            logger.error("Failed to fetch RTS tenders")
            return []
        
        try:
            data = response.json()
            tenders = []
            
            for tender_data in data.get("tenders", []):
                tender = {
                    "source": self.source,
                    "external_id": tender_data.get("id"),
                    "title": tender_data.get("name"),
                    "description": tender_data.get("description"),
                    "customer": tender_data.get("customer", {}).get("name"),
                    "budget": float(tender_data.get("budget", 0)) if tender_data.get("budget") else None,
                    "deadline": tender_data.get("deadlineDate"),
                    "status": "active",
                    "url": f"{self.base_url}/auction/{tender_data.get('id')}",
                    "parsed_at": datetime.utcnow().isoformat()
                }
                tenders.append(tender)
            
            logger.info(f"Parsed {len(tenders)} RTS tenders")
            return tenders
        
        except Exception as e:
            logger.error(f"Failed to parse RTS response: {e}")
            return []
    
    def fetch_tender_details(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed tender information from RTS"""
        url = f"{self.api_url}/openapi/4_0_0/tenders/{tender_id}"
        response = self._make_request(url)
        
        if not response:
            return None
        
        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse RTS tender details: {e}")
            return None
