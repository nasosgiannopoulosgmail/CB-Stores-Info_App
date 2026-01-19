"""
Store management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.database import get_db
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse, StoreListResponse
from app.api.dependencies import verify_api_key, verify_oauth_token

router = APIRouter()


@router.get("/", response_model=StoreListResponse)
async def list_stores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)  # Require authentication
):
    """List all stores"""
    query = db.query(Store)
    
    if active_only:
        query = query.filter(Store.active == True)
    
    if search:
        query = query.filter(
            Store.name.ilike(f"%{search}%")
        )
    
    total = query.count()
    stores = query.offset(skip).limit(limit).all()
    
    return StoreListResponse(
        stores=[StoreResponse.from_orm(s) for s in stores],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get store by ID"""
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    return StoreResponse.from_orm(store)


@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    store: StoreCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Create a new store"""
    # Check for duplicates
    existing = db.query(Store).filter(
        (Store.entersoft_key == store.entersoft_key) & (Store.entersoft_key.isnot(None))
        | (Store.inorder_key == store.inorder_key) & (Store.inorder_key.isnot(None))
        | (Store.name == store.name) & (Store.latitude == store.latitude) & (Store.longitude == store.longitude)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Store already exists"
        )
    
    db_store = Store(**store.dict())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    
    return StoreResponse.from_orm(db_store)


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: int,
    store: StoreUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Update store"""
    db_store = db.query(Store).filter(Store.id == store_id).first()
    
    if not db_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    update_data = store.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_store, key, value)
    
    db.commit()
    db.refresh(db_store)
    
    return StoreResponse.from_orm(db_store)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Delete store (soft delete - sets active=False)"""
    db_store = db.query(Store).filter(Store.id == store_id).first()
    
    if not db_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    db_store.active = False
    db.commit()
    
    return None


@router.get("/search/by-key", response_model=StoreResponse)
async def search_store_by_key(
    entersoft_key: Optional[str] = None,
    inorder_key: Optional[str] = None,
    future_proof_key: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Search store by external keys"""
    query = db.query(Store)
    
    if entersoft_key:
        query = query.filter(Store.entersoft_key == entersoft_key)
    elif inorder_key:
        query = query.filter(Store.inorder_key == inorder_key)
    elif future_proof_key:
        query = query.filter(Store.future_proof_key == future_proof_key)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one key must be provided"
        )
    
    store = query.first()
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    return StoreResponse.from_orm(store)
