"""
Franchisee management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.db.database import get_db
from app.models.franchisee import Franchisee
from app.api.dependencies import verify_api_key

router = APIRouter()


class FranchiseeBase(BaseModel):
    """Base franchisee schema"""
    name: str
    company_name: Optional[str] = None
    entersoft_key: Optional[str] = None
    inorder_key: Optional[str] = None
    future_proof_key: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    active: bool = True


class FranchiseeCreate(FranchiseeBase):
    """Create franchisee request"""
    pass


class FranchiseeUpdate(BaseModel):
    """Update franchisee request"""
    name: Optional[str] = None
    company_name: Optional[str] = None
    entersoft_key: Optional[str] = None
    inorder_key: Optional[str] = None
    future_proof_key: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    active: Optional[bool] = None


class FranchiseeResponse(FranchiseeBase):
    """Franchisee response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[FranchiseeResponse])
async def list_franchisees(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """List all franchisees"""
    query = db.query(Franchisee)
    
    if active_only:
        query = query.filter(Franchisee.active == True)
    
    franchisees = query.all()
    return [FranchiseeResponse.from_orm(f) for f in franchisees]


@router.get("/{franchisee_id}", response_model=FranchiseeResponse)
async def get_franchisee(
    franchisee_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get franchisee by ID"""
    franchisee = db.query(Franchisee).filter(Franchisee.id == franchisee_id).first()
    
    if not franchisee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Franchisee {franchisee_id} not found"
        )
    
    return FranchiseeResponse.from_orm(franchisee)


@router.post("/", response_model=FranchiseeResponse, status_code=status.HTTP_201_CREATED)
async def create_franchisee(
    franchisee: FranchiseeCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Create a new franchisee"""
    db_franchisee = Franchisee(**franchisee.dict())
    db.add(db_franchisee)
    db.commit()
    db.refresh(db_franchisee)
    
    return FranchiseeResponse.from_orm(db_franchisee)


@router.put("/{franchisee_id}", response_model=FranchiseeResponse)
async def update_franchisee(
    franchisee_id: int,
    franchisee: FranchiseeUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Update franchisee"""
    db_franchisee = db.query(Franchisee).filter(Franchisee.id == franchisee_id).first()
    
    if not db_franchisee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Franchisee {franchisee_id} not found"
        )
    
    update_data = franchisee.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_franchisee, key, value)
    
    db.commit()
    db.refresh(db_franchisee)
    
    return FranchiseeResponse.from_orm(db_franchisee)
