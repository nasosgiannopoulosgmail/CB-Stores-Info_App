"""
Store schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class StoreBase(BaseModel):
    """Base store schema"""
    name: str
    latitude: Decimal = Field(..., ge=-90, le=90, decimal_places=8)
    longitude: Decimal = Field(..., ge=-180, le=180, decimal_places=8)
    entersoft_key: Optional[str] = None
    inorder_key: Optional[str] = None
    future_proof_key: Optional[str] = None
    current_franchisee_id: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    active: bool = True


class StoreCreate(StoreBase):
    """Create store request"""
    pass


class StoreUpdate(BaseModel):
    """Update store request"""
    name: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    entersoft_key: Optional[str] = None
    inorder_key: Optional[str] = None
    future_proof_key: Optional[str] = None
    current_franchisee_id: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Store response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StoreListResponse(BaseModel):
    """List of stores response"""
    stores: list[StoreResponse]
    total: int
    page: int
    page_size: int
