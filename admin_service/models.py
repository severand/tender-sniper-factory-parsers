"""Database models for admin_service"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from shared.database import Base


class Platform(Base):
    """Tender platform configuration"""
    
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    api_endpoint = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    
    # Rate limiting
    rate_limit_requests = Column(Integer, default=100)
    rate_limit_window = Column(Integer, default=3600)  # seconds
    
    # Retry policy
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=5)  # seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    search_rules = relationship("SearchRule", back_populates="platform", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="platform", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Platform(id={self.id}, name={self.name}, code={self.code})>"


class SearchRule(Base):
    """Search and parsing rules for a platform"""
    
    __tablename__ = "search_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), index=True, nullable=False)
    
    # Rule configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Search parameters
    search_url = Column(String(500), nullable=False)
    search_params = Column(JSON, nullable=True)  # Dictionary of search parameters
    
    # Parsing selectors
    list_selector = Column(String(500), nullable=False)  # CSS selector for list items
    pagination_type = Column(String(50), default="offset")  # offset, page, cursor, none
    pagination_selector = Column(String(500), nullable=True)  # Selector for next page
    
    # Activity
    is_active = Column(Boolean, default=True, index=True)
    schedule = Column(String(100), default="0 * * * *")  # Cron schedule
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    platform = relationship("Platform", back_populates="search_rules")
    field_mappings = relationship("FieldMapping", back_populates="search_rule", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<SearchRule(id={self.id}, platform_id={self.platform_id}, name={self.name})>"


class FieldMapping(Base):
    """Field mapping from platform to standard tender schema"""
    
    __tablename__ = "field_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), index=True, nullable=False)
    search_rule_id = Column(Integer, ForeignKey("search_rules.id"), index=True, nullable=True)
    
    # Field configuration
    standard_field = Column(String(100), index=True, nullable=False)  # tender_id, title, description, etc.
    platform_field = Column(String(500), nullable=False)  # CSS selector or XPath
    
    # Parsing options
    field_type = Column(String(50), default="text")  # text, int, date, float, json
    regex_pattern = Column(String(500), nullable=True)  # For extracting specific parts
    attribute = Column(String(100), nullable=True)  # HTML attribute (href, data-id, etc.)
    
    # Transformation
    transformation = Column(String(500), nullable=True)  # Custom transformation function name
    required = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    platform = relationship("Platform", back_populates="field_mappings")
    search_rule = relationship("SearchRule", back_populates="field_mappings")
    
    def __repr__(self) -> str:
        return f"<FieldMapping(id={self.id}, standard_field={self.standard_field}, platform_field={self.platform_field})>"