"""
Store media (pictures) management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
from pathlib import Path

from app.db.database import get_db
from app.models.media import StoreMedia
from app.models.store import Store
from app.config import settings
from app.api.dependencies import verify_api_key

router = APIRouter()


class MediaResponse(BaseModel):
    """Media response"""
    id: int
    store_id: int
    franchisee_id: Optional[int] = None
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    description: Optional[str] = None
    is_primary: bool
    
    class Config:
        from_attributes = True


@router.get("/stores/{store_id}/media", response_model=List[MediaResponse])
async def get_store_media(
    store_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get all media for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    media = db.query(StoreMedia).filter(
        StoreMedia.store_id == store_id
    ).order_by(StoreMedia.uploaded_at.desc()).all()
    
    return [MediaResponse.from_orm(m) for m in media]


@router.post("/stores/{store_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_store_media(
    store_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    is_primary: bool = False,
    franchisee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Upload media for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size ({settings.max_upload_size} bytes)"
        )
    
    # Create media directory if it doesn't exist
    media_dir = Path(settings.media_root) / str(store_id)
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = media_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # If this is primary, unset previous primary
    if is_primary:
        db.query(StoreMedia).filter(
            StoreMedia.store_id == store_id,
            StoreMedia.is_primary == True
        ).update({"is_primary": False})
    
    # Create media record
    db_media = StoreMedia(
        store_id=store_id,
        franchisee_id=franchisee_id,
        file_path=str(file_path.relative_to(settings.media_root)),
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        description=description,
        is_primary=is_primary
    )
    
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    
    return MediaResponse.from_orm(db_media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Delete media"""
    media = db.query(StoreMedia).filter(StoreMedia.id == media_id).first()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media {media_id} not found"
        )
    
    # Delete file
    file_path = Path(settings.media_root) / media.file_path
    if file_path.exists():
        file_path.unlink()
    
    # Delete record
    db.delete(media)
    db.commit()
    
    return None
