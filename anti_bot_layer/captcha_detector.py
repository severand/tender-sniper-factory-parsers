"""Detect captcha challenges"""

from typing import Tuple, Optional
from bs4 import BeautifulSoup

from factory_parsers.shared.logger import logger


class CaptchaDetector:
    """Detect various captcha types"""
    
    CAPTCHA_PATTERNS = {
        "recaptcha_v2": [
            "g-recaptcha",
            "recaptcha__button",
            "recaptchaapi.js",
        ],
        "recaptcha_v3": [
            "recaptcha/api.js",
            "grecaptcha.ready",
        ],
        "hcaptcha": [
            "h-captcha",
            "hcaptcha.com",
        ],
        "cloudflare_turnstile": [
            "cf_challenge",
            "challenges.cloudflare.com",
            "turnstile",
        ],
        "image_captcha": [
            "captcha",
            "verification",
        ],
    }
    
    @staticmethod
    def detect_captcha(html_content: str) -> Tuple[bool, Optional[str]]:
        """Detect captcha in HTML
        
        Args:
            html_content: HTML page content
        
        Returns:
            Tuple of (is_captcha: bool, captcha_type: str or None)
        """
        for captcha_type, patterns in CaptchaDetector.CAPTCHA_PATTERNS.items():
            for pattern in patterns:
                if pattern in html_content:
                    logger.info(f"Detected {captcha_type}")
                    return True, captcha_type
        
        return False, None
    
    @staticmethod
    def detect_cloudflare(response_headers: dict) -> bool:
        """Detect Cloudflare
        
        Args:
            response_headers: HTTP response headers
        
        Returns:
            True if Cloudflare detected
        """
        server = response_headers.get("Server", "").lower()
        cf_ray = response_headers.get("CF-RAY")
        
        if "cloudflare" in server or cf_ray:
            logger.info("Cloudflare detected")
            return True
        
        return False
    
    @staticmethod
    def detect_block(status_code: int, html_content: str = None) -> Tuple[bool, Optional[str]]:
        """Detect if blocked
        
        Args:
            status_code: HTTP status code
            html_content: HTML response (optional)
        
        Returns:
            Tuple of (is_blocked: bool, block_reason: str or None)
        """
        if status_code == 429:
            logger.warning("Rate limited (429)")
            return True, "rate_limited"
        
        if status_code == 403:
            logger.warning("Forbidden (403)")
            return True, "forbidden"
        
        if status_code == 401:
            logger.warning("Unauthorized (401)")
            return True, "unauthorized"
        
        if html_content:
            is_captcha, captcha_type = CaptchaDetector.detect_captcha(html_content)
            if is_captcha:
                return True, f"captcha_{captcha_type}"
        
        return False, None
