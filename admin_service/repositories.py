"""Repository classes for admin_service models"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .models import Platform, SearchRule, FieldMapping


class PlatformRepository:
    """Repository for Platform model operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, code: str, url: str, **kwargs) -> Platform:
        """Create new platform"""
        platform = Platform(
            name=name,
            code=code,
            url=url,
            **kwargs
        )
        self.db.add(platform)
        self.db.commit()
        self.db.refresh(platform)
        return platform
    
    def get_by_id(self, platform_id: int) -> Optional[Platform]:
        """Get platform by ID"""
        return self.db.query(Platform).filter(Platform.id == platform_id).first()
    
    def get_by_code(self, code: str) -> Optional[Platform]:
        """Get platform by code"""
        return self.db.query(Platform).filter(Platform.code == code).first()
    
    def list_all(self, active_only: bool = False) -> List[Platform]:
        """List all platforms"""
        query = self.db.query(Platform)
        if active_only:
            query = query.filter(Platform.is_active == True)
        return query.all()
    
    def update(self, platform_id: int, **kwargs) -> Optional[Platform]:
        """Update platform"""
        platform = self.get_by_id(platform_id)
        if platform:
            for key, value in kwargs.items():
                if hasattr(platform, key):
                    setattr(platform, key, value)
            self.db.commit()
            self.db.refresh(platform)
        return platform
    
    def delete(self, platform_id: int) -> bool:
        """Delete platform"""
        platform = self.get_by_id(platform_id)
        if platform:
            self.db.delete(platform)
            self.db.commit()
            return True
        return False


class SearchRuleRepository:
    """Repository for SearchRule model operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, platform_id: int, name: str, search_url: str, list_selector: str, **kwargs) -> SearchRule:
        """Create new search rule"""
        rule = SearchRule(
            platform_id=platform_id,
            name=name,
            search_url=search_url,
            list_selector=list_selector,
            **kwargs
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule
    
    def get_by_id(self, rule_id: int) -> Optional[SearchRule]:
        """Get search rule by ID"""
        return self.db.query(SearchRule).filter(SearchRule.id == rule_id).first()
    
    def get_by_platform(self, platform_id: int, active_only: bool = False) -> List[SearchRule]:
        """Get search rules for platform"""
        query = self.db.query(SearchRule).filter(SearchRule.platform_id == platform_id)
        if active_only:
            query = query.filter(SearchRule.is_active == True)
        return query.all()
    
    def update(self, rule_id: int, **kwargs) -> Optional[SearchRule]:
        """Update search rule"""
        rule = self.get_by_id(rule_id)
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            self.db.commit()
            self.db.refresh(rule)
        return rule
    
    def delete(self, rule_id: int) -> bool:
        """Delete search rule"""
        rule = self.get_by_id(rule_id)
        if rule:
            self.db.delete(rule)
            self.db.commit()
            return True
        return False


class FieldMappingRepository:
    """Repository for FieldMapping model operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        platform_id: int,
        standard_field: str,
        platform_field: str,
        **kwargs
    ) -> FieldMapping:
        """Create new field mapping"""
        mapping = FieldMapping(
            platform_id=platform_id,
            standard_field=standard_field,
            platform_field=platform_field,
            **kwargs
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping
    
    def get_by_id(self, mapping_id: int) -> Optional[FieldMapping]:
        """Get field mapping by ID"""
        return self.db.query(FieldMapping).filter(FieldMapping.id == mapping_id).first()
    
    def get_by_platform(self, platform_id: int) -> List[FieldMapping]:
        """Get field mappings for platform"""
        return self.db.query(FieldMapping).filter(FieldMapping.platform_id == platform_id).all()
    
    def get_by_search_rule(self, search_rule_id: int) -> List[FieldMapping]:
        """Get field mappings for search rule"""
        return self.db.query(FieldMapping).filter(FieldMapping.search_rule_id == search_rule_id).all()
    
    def update(self, mapping_id: int, **kwargs) -> Optional[FieldMapping]:
        """Update field mapping"""
        mapping = self.get_by_id(mapping_id)
        if mapping:
            for key, value in kwargs.items():
                if hasattr(mapping, key):
                    setattr(mapping, key, value)
            self.db.commit()
            self.db.refresh(mapping)
        return mapping
    
    def delete(self, mapping_id: int) -> bool:
        """Delete field mapping"""
        mapping = self.get_by_id(mapping_id)
        if mapping:
            self.db.delete(mapping)
            self.db.commit()
            return True
        return False
