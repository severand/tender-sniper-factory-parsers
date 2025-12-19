"""Proxy management and rotation"""

import random
from typing import List, Dict, Optional

from factory_parsers.shared.logger import logger


class ProxyManager:
    """Manage and rotate proxy servers"""
    
    PROXY_PROFILES = {
        "mobile": {
            "user_agents": [
                "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
            ]
        },
        "desktop": {
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            ]
        },
        "headless": {
            "user_agents": [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]
        },
    }
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.current_index = 0
    
    def add_proxies(self, proxies: List[str]) -> None:
        """Add proxies to rotation
        
        Args:
            proxies: List of proxy URLs
        """
        self.proxy_list.extend(proxies)
        logger.info(f"Added {len(proxies)} proxies, total: {len(self.proxy_list)}")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation
        
        Returns:
            Proxy URL or None
        """
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get random proxy
        
        Returns:
            Proxy URL or None
        """
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    def get_user_agent(self, profile: str = "desktop") -> str:
        """Get random user agent for profile
        
        Args:
            profile: Profile name (mobile, desktop, headless)
        
        Returns:
            User agent string
        """
        if profile not in self.PROXY_PROFILES:
            profile = "desktop"
        
        return random.choice(self.PROXY_PROFILES[profile]["user_agents"])
    
    def get_headers(self, profile: str = "desktop") -> Dict[str, str]:
        """Get request headers with rotation
        
        Args:
            profile: Profile name
        
        Returns:
            Headers dictionary
        """
        return {
            "User-Agent": self.get_user_agent(profile),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
