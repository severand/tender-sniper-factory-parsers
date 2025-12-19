"""Shared database models"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from shared.database import Base


class Tender(Base):
    """Scraped tender data"""
    
    __tablename__ = "tenders"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), index=True, nullable=False)
    
    # Main fields
    title = Column(String(1000), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Financial data
    price = Column(Float, nullable=True)
    currency = Column(String(10), default="RUB")
    
    # Dates
    published_date = Column(DateTime, nullable=True)
    deadline_date = Column(DateTime, nullable=True)
    
    # Additional data
    customer = Column(String(500), nullable=True)
    category = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    
    # Raw data from platform
    raw_data = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Tender(id={self.id}, title={self.title[:50]}, platform_id={self.platform_id})>"