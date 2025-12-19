"""Database models for normalized tenders"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Float, JSON, Boolean, Index

fromshared.database import Base


class NormalizedTender(Base):
    """Normalized tender record (по ARCHITECTURE.md спецификация)"""
    
    __tablename__ = "normalized_tenders"
    __table_args__ = {"extend_existing": True}  # ← ДОБАВЬ ЭТУ СТРОКУ
    
    # Identifiers
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(255), unique=True, index=True, nullable=False)  # UUID
    platform_id = Column(String(100), index=True, nullable=False)  # Platform reference
    external_id = Column(String(500), nullable=False)  # ID на исходной площадке
    
    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # AI-generated summary
    category = Column(String(100), index=True, nullable=True)
    
    # Customer info
    customer_name = Column(String(255), index=True, nullable=True)
    customer_contact = Column(String(500), nullable=True)
    customer_id = Column(String(100), nullable=True)
    
    # Timeline
    published_date = Column(DateTime, index=True, nullable=True)
    deadline_date = Column(DateTime, index=True, nullable=True)
    start_date = Column(DateTime, index=True, nullable=True)
    end_date = Column(DateTime, index=True, nullable=True)
    
    # Financial
    budget_amount = Column(Float, index=True, nullable=True)
    budget_currency = Column(String(3), default="RUB", nullable=False)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    
    # Status and metadata
    status = Column(String(50), index=True, default="new", nullable=False)  # new, active, closed, cancelled
    source_url = Column(String(500), nullable=True)  # Ссылка на оригинальный тендер
    
    # Structured data (JSON)
    requirements = Column(JSON, nullable=True)  # List of requirements
    criteria = Column(JSON, nullable=True)  # List of selection criteria
    restrictions = Column(JSON, nullable=True)  # List of restrictions
    attachments = Column(JSON, nullable=True)  # List of file info
    
    # AI Extraction data
    ai_extracted = Column(JSON, nullable=True)  # {
                                                  #   key_points: [],
                                                  #   risk_flags: [],
                                                  #   estimated_workload: string
                                                  # }
    ai_summary = Column(Text, nullable=True)  # AI-generated summary
    ai_keywords = Column(JSON, nullable=True)  # List of extracted keywords
    
    # Raw data tracking
    raw_data = Column(JSON, nullable=True)  # Original data from scraper
    extracted_text = Column(Text, nullable=True)  # Extracted text from attachments
    raw_data_id = Column(String(255), nullable=True)  # Reference to raw data storage
    
    # Quality metrics
    data_quality_score = Column(Float, default=0.0)  # 0-100 for validation
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of = Column(String(255), nullable=True)  # Reference to main tender
    normalization_success_rate = Column(Float, default=0.0)  # % of fields successfully normalized
    
    # Processing metadata
    scraped_at = Column(DateTime, nullable=True)
    normalized_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)  # Time spent normalizing
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_platform_date', 'platform_id', 'published_date'),
        Index('idx_status_date', 'status', 'deadline_date'),
        Index('idx_customer_date', 'customer_name', 'published_date'),
        Index('idx_duplicate', 'is_duplicate'),
        Index('idx_quality_score', 'data_quality_score'),
    )
    
    def __repr__(self) -> str:
        return f"<NormalizedTender(id={self.id}, tender_id={self.tender_id}, title={self.title[:50]})>"


class NormalizationLog(Base):
    """Log of normalization operations"""
    
    __tablename__ = "normalization_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(255), index=True, nullable=False)
    raw_data_id = Column(String(255), nullable=True)
    
    # Operation info
    status = Column(String(50), nullable=False)  # success, failed, partial
    message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Details
    errors = Column(JSON, nullable=True)  # List of validation errors
    warnings = Column(JSON, nullable=True)  # List of warnings
    
    def __repr__(self) -> str:
        return f"<NormalizationLog(id={self.id}, tender_id={self.tender_id}, status={self.status})>"


class FieldMapping(Base):
    """Field mapping between platform-specific formats and normalized format"""
    
    __tablename__ = "field_mappings"
    __table_args__ = {"extend_existing": True}  # ← ДОБАВЬ ЭТУ СТРОКУ
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(String(100), index=True, nullable=False)
    
    # Mapping configuration (JSON)
    # {
    #   "title": "h1.tender-title",
    #   "budget": "span.price",
    #   "deadline": "span.deadline",
    #   ...
    # }
    field_mappings = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    __table_args__ = (
        Index('idx_platform_active', 'platform_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<FieldMapping(platform_id={self.platform_id})>"
