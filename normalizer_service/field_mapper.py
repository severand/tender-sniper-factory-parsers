"""Field mapping service for normalizing platform-specific fields"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from .models import FieldMapping


class FieldMapper:
    """Maps platform-specific fields to normalized format"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}  # Cache platform mappings
    
    def get_mapping(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """Get field mapping for platform"""
        if platform_id in self._cache:
            return self._cache[platform_id]
        
        mapping = self.db.query(FieldMapping).filter(
            FieldMapping.platform_id == platform_id,
            FieldMapping.is_active == True
        ).first()
        
        if mapping:
            self._cache[platform_id] = mapping.field_mappings
            return mapping.field_mappings
        
        logger.warning(f"No active mapping found for platform: {platform_id}")
        return None
    
    def map_fields(self, raw_data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Apply mapping to raw data
        
        Args:
            raw_data: Original data from scraper
            mapping: Field mapping rules {normalized_field: source_field_key}
        
        Returns:
            Mapped data dictionary
        """
        mapped = {}
        
        for normalized_field, source_field in mapping.items():
            # Handle nested fields (e.g., "customer.name")
            if "." in source_field:
                value = self._get_nested(raw_data, source_field)
            else:
                value = raw_data.get(source_field)
            
            if value is not None:
                mapped[normalized_field] = value
        
        return mapped
    
    def _get_nested(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        """Get value from nested dictionary
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "customer.name")
        
        Returns:
            Value or None
        """
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    def create_mapping(self, platform_id: str, mappings: Dict[str, str]) -> FieldMapping:
        """Create or update field mapping
        
        Args:
            platform_id: Platform identifier
            mappings: Mapping rules
        
        Returns:
            FieldMapping record
        """
        # Check if exists
        existing = self.db.query(FieldMapping).filter(
            FieldMapping.platform_id == platform_id
        ).first()
        
        if existing:
            existing.field_mappings = mappings
            existing.is_active = True
        else:
            existing = FieldMapping(
                platform_id=platform_id,
                field_mappings=mappings,
                is_active=True
            )
            self.db.add(existing)
        
        self.db.commit()
        self._cache[platform_id] = mappings  # Update cache
        
        logger.info(f"Created/updated mapping for platform: {platform_id}")
        return existing
