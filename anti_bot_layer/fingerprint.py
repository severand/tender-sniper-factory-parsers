"""Browser fingerprinting and TLS configuration"""

import random
from typing import Dict


class BrowserFingerprint:
    """Generate realistic browser fingerprints"""
    
    @staticmethod
    def get_tls_version() -> str:
        """Get TLS version
        
        Returns:
            TLS version
        """
        return random.choice(["1.2", "1.3"])
    
    @staticmethod
    def get_ciphers() -> str:
        """Get cipher suite
        
        Returns:
            Cipher suite string
        """
        suites = [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        ]
        return random.choice(suites)
    
    @staticmethod
    def get_screen_resolution() -> str:
        """Get screen resolution
        
        Returns:
            Resolution string
        """
        resolutions = [
            "1920x1080",
            "1366x768",
            "1440x900",
            "1536x864",
        ]
        return random.choice(resolutions)
    
    @staticmethod
    def get_languages() -> str:
        """Get language preferences
        
        Returns:
            Language header
        """
        return "en-US,en;q=0.9,ru;q=0.8"
    
    @staticmethod
    def get_fingerprint() -> Dict[str, str]:
        """Get complete browser fingerprint
        
        Returns:
            Fingerprint dictionary
        """
        return {
            "tls_version": BrowserFingerprint.get_tls_version(),
            "cipher_suite": BrowserFingerprint.get_ciphers(),
            "screen_resolution": BrowserFingerprint.get_screen_resolution(),
            "languages": BrowserFingerprint.get_languages(),
        }
