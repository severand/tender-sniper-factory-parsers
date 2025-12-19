"""RTS (Российская торговая система) API client (Sprint 42)"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from factory_parsers.shared.logger import LoggingService
from factory_parsers.shared.metrics import http_requests_total

logger = LoggingService.get_logger(__name__)


class RTSAPIClient:
    """RTS API client for tender data"""
    
    BASE_URL = 'https://api.rts-tender.ru/v1'
    platform_id = 'rts'
    
    def __init__(self, api_key: str, timeout: int = 30):
        """Initialize RTS API client
        
        Args:
            api_key: RTS API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        })
        
        logger.info("RTS API client initialized", extra={
            'event_type': 'start',
            'platform_id': self.platform_id,
        })
    
    def get_tenders(self, page: int = 1, page_size: int = 100) -> Optional[Dict[str, Any]]:
        """Get list of tenders from RTS
        
        Args:
            page: Page number
            page_size: Results per page
        
        Returns:
            API response or None on error
        """
        try:
            url = f"{self.BASE_URL}/tenders"
            params = {'page': page, 'page_size': page_size}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            http_requests_total.labels(method='GET', path='/tenders', status=response.status_code).inc()
            
            if response.status_code == 200:
                logger.info(f"Retrieved {len(response.json().get('items', []))} tenders", extra={
                    'event_type': 'success',
                    'platform_id': self.platform_id,
                    'count': len(response.json().get('items', [])),
                })
                return response.json()
            else:
                logger.error(f"API error: {response.status_code}", extra={
                    'event_type': 'error',
                    'platform_id': self.platform_id,
                    'status_code': response.status_code,
                })
                return None
        
        except Exception as e:
            logger.error(f"Request failed: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'error': str(e),
            })
            return None
    
    def get_tender_detail(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Get tender details
        
        Args:
            tender_id: Tender ID
        
        Returns:
            Tender data or None on error
        """
        try:
            url = f"{self.BASE_URL}/tenders/{tender_id}"
            
            response = self.session.get(url, timeout=self.timeout)
            http_requests_total.labels(method='GET', path='/tenders/{id}', status=response.status_code).inc()
            
            if response.status_code == 200:
                data = response.json()
                tender = {
                    'tender_id': data.get('id'),
                    'external_id': data.get('external_id'),
                    'title': data.get('title'),
                    'description': data.get('description'),
                    'customer_name': data.get('customer', {}).get('name'),
                    'budget_amount': data.get('budget', {}).get('amount'),
                    'budget_currency': data.get('budget', {}).get('currency', 'RUB'),
                    'deadline_date': data.get('deadline'),
                    'status': data.get('status', 'new'),
                    'source_url': f"https://rts-tender.ru/tender/{tender_id}",
                    'platform_id': self.platform_id,
                }
                
                logger.info(f"Retrieved tender detail: {tender_id}", extra={
                    'event_type': 'success',
                    'platform_id': self.platform_id,
                    'tender_id': tender_id,
                })
                
                return tender
            else:
                logger.error(f"Failed to get tender {tender_id}: {response.status_code}", extra={
                    'event_type': 'error',
                    'platform_id': self.platform_id,
                    'tender_id': tender_id,
                    'status_code': response.status_code,
                })
                return None
        
        except Exception as e:
            logger.error(f"Failed to get tender detail: {str(e)}", extra={
                'event_type': 'error',
                'platform_id': self.platform_id,
                'tender_id': tender_id,
                'error': str(e),
            })
            return None
