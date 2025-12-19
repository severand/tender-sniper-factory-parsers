"""Duplicate detection for tenders"""

import hashlib
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from .models import NormalizedTender


class DuplicateDetector:
    """Detect and handle duplicate tenders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_duplicate(self, external_id: str, platform_id: str, title: str) -> Tuple[bool, Optional[int]]:
        """Check if tender is duplicate
        
        Args:
            external_id: External platform ID
            platform_id: Platform identifier
            title: Tender title
        
        Returns:
            (is_duplicate: bool, duplicate_of_id: int or None)
        """
        # Strategy 1: Exact external_id match on same platform
        exact_match = self.db.query(NormalizedTender).filter(
            NormalizedTender.external_id == external_id,
            NormalizedTender.platform_id == platform_id
        ).first()
        
        if exact_match:
            logger.debug(f"Duplicate detected (exact ID): {external_id}")
            return True, exact_match.id
        
        # Strategy 2: Title + platform fuzzy match
        title_hash = self._hash_title(title)
        fuzzy_match = self.db.query(NormalizedTender).filter(
            NormalizedTender.platform_id == platform_id,
            NormalizedTender.is_duplicate == False
        ).all()
        
        for tender in fuzzy_match:
            if self._hash_title(tender.title) == title_hash:
                logger.debug(f"Duplicate detected (fuzzy title): {title}")
                return True, tender.id
        
        return False, None
    
    def mark_as_duplicate(self, tender_id: int, duplicate_of_id: int) -> None:
        """Mark tender as duplicate
        
        Args:
            tender_id: Tender to mark
            duplicate_of_id: ID of original tender
        """
        tender = self.db.query(NormalizedTender).filter(
            NormalizedTender.id == tender_id
        ).first()
        
        if tender:
            tender.is_duplicate = True
            tender.duplicate_of = str(duplicate_of_id)
            self.db.commit()
            logger.info(f"Marked tender {tender_id} as duplicate of {duplicate_of_id}")
    
    def get_duplicates_for(self, tender_id: int) -> list:
        """Get all duplicates of a tender
        
        Args:
            tender_id: Original tender ID
        
        Returns:
            List of duplicate tender IDs
        """
        duplicates = self.db.query(NormalizedTender).filter(
            NormalizedTender.duplicate_of == str(tender_id),
            NormalizedTender.is_duplicate == True
        ).all()
        
        return [d.id for d in duplicates]
    
    @staticmethod
    def _hash_title(title: str) -> str:
        """Create normalized hash of title for fuzzy matching
        
        Args:
            title: Tender title
        
        Returns:
            MD5 hash of normalized title
        """
        # Normalize: lowercase, remove extra spaces, keep only alphanumeric + spaces
        normalized = " ".join(title.lower().split())  # lowercase + collapse spaces
        return hashlib.md5(normalized.encode()).hexdigest()
