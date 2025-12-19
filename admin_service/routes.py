"""FastAPI routes for admin_service"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from shared.database import get_db
from .models import Platform, SearchRule, FieldMapping
from .repositories import PlatformRepository, SearchRuleRepository, FieldMappingRepository

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic schemas
class PlatformCreate(BaseModel):
    name: str
    code: str
    url: str
    description: str = None
    api_endpoint: str = None
    api_key: str = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    max_retries: int = 3
    retry_delay: int = 5


class PlatformUpdate(BaseModel):
    name: str = None
    url: str = None
    description: str = None
    is_active: bool = None
    api_endpoint: str = None
    api_key: str = None


class PlatformResponse(BaseModel):
    id: int
    name: str
    code: str
    url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchRuleCreate(BaseModel):
    name: str
    search_url: str
    list_selector: str
    description: str = None
    pagination_type: str = "offset"
    schedule: str = "0 * * * *"


class FieldMappingCreate(BaseModel):
    standard_field: str
    platform_field: str
    field_type: str = "text"
    regex_pattern: str = None
    attribute: str = None
    required: bool = False


# Platform endpoints
@router.post("/platforms", response_model=PlatformResponse)
def create_platform(platform: PlatformCreate, db: Session = Depends(get_db)):
    """Create new platform"""
    repo = PlatformRepository(db)
    
    # Check if platform with code already exists
    existing = repo.get_by_code(platform.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform with code '{platform.code}' already exists"
        )
    
    return repo.create(**platform.dict())


@router.get("/platforms", response_model=List[PlatformResponse])
def list_platforms(active_only: bool = False, db: Session = Depends(get_db)):
    """List all platforms"""
    repo = PlatformRepository(db)
    return repo.list_all(active_only=active_only)


@router.get("/platforms/{platform_id}", response_model=PlatformResponse)
def get_platform(platform_id: int, db: Session = Depends(get_db)):
    """Get platform by ID"""
    repo = PlatformRepository(db)
    platform = repo.get_by_id(platform_id)
    if not platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    return platform


@router.put("/platforms/{platform_id}", response_model=PlatformResponse)
def update_platform(
    platform_id: int,
    platform_update: PlatformUpdate,
    db: Session = Depends(get_db)
):
    """Update platform"""
    repo = PlatformRepository(db)
    updated = repo.update(platform_id, **platform_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    return updated


@router.delete("/platforms/{platform_id}")
def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    """Delete platform"""
    repo = PlatformRepository(db)
    if not repo.delete(platform_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    return {"message": f"Platform {platform_id} deleted"}


# SearchRule endpoints
@router.post("/platforms/{platform_id}/search-rules")
def create_search_rule(
    platform_id: int,
    rule: SearchRuleCreate,
    db: Session = Depends(get_db)
):
    """Create search rule for platform"""
    platform_repo = PlatformRepository(db)
    if not platform_repo.get_by_id(platform_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")
    
    repo = SearchRuleRepository(db)
    return repo.create(platform_id, **rule.dict())


@router.get("/platforms/{platform_id}/search-rules")
def list_search_rules(platform_id: int, active_only: bool = False, db: Session = Depends(get_db)):
    """List search rules for platform"""
    repo = SearchRuleRepository(db)
    return repo.get_by_platform(platform_id, active_only=active_only)


# FieldMapping endpoints - ТОЛЬКО ДЛЯ SEARCH RULES
@router.post("/search-rules/{search_rule_id}/field-mappings")
def create_field_mapping_for_rule(
    search_rule_id: int,
    mapping: FieldMappingCreate,
    db: Session = Depends(get_db)
):
    """Create field mapping for search rule"""
    rule_repo = SearchRuleRepository(db)
    rule = rule_repo.get_by_id(search_rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SearchRule not found")
    
    mapping_repo = FieldMappingRepository(db)
    return mapping_repo.create(
        platform_id=rule.platform_id,
        search_rule_id=search_rule_id,
        **mapping.dict()
    )


@router.get("/search-rules/{search_rule_id}/field-mappings")
def list_field_mappings_for_rule(search_rule_id: int, db: Session = Depends(get_db)):
    """List field mappings for search rule"""
    repo = FieldMappingRepository(db)
    return repo.get_by_search_rule(search_rule_id)