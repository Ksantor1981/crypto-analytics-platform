from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.channel import Channel
from ..schemas.channel import ChannelCreate, ChannelUpdate

class ChannelService:
    """
    Service for managing channel operations
    """
    
    @staticmethod
    def get_channels(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        platform: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Channel]:
        """
        Get all channels with optional filtering
        """
        query = db.query(Channel)
        
        if platform:
            query = query.filter(Channel.platform == platform)
        
        if category:
            query = query.filter(Channel.category == category)
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_channel_by_id(db: Session, channel_id: int) -> Channel:
        """
        Get a specific channel by ID
        """
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel with ID {channel_id} not found"
            )
        return channel
    
    @staticmethod
    def create_channel(db: Session, channel_data: ChannelCreate) -> Channel:
        """
        Create a new channel
        """
        # Check if channel with same URL already exists
        existing_channel = db.query(Channel).filter(Channel.url == channel_data.url).first()
        if existing_channel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel with URL {channel_data.url} already exists"
            )
        
        # Create new channel
        db_channel = Channel(**channel_data.dict())
        db.add(db_channel)
        db.commit()
        db.refresh(db_channel)
        return db_channel
    
    @staticmethod
    def update_channel(
        db: Session, channel_id: int, channel_data: ChannelUpdate
    ) -> Channel:
        """
        Update an existing channel
        """
        db_channel = ChannelService.get_channel_by_id(db, channel_id)
        
        # Update fields that are present in the request
        update_data = channel_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_channel, field, value)
        
        db.commit()
        db.refresh(db_channel)
        return db_channel
    
    @staticmethod
    def delete_channel(db: Session, channel_id: int) -> Dict[str, Any]:
        """
        Delete a channel
        """
        db_channel = ChannelService.get_channel_by_id(db, channel_id)
        
        db.delete(db_channel)
        db.commit()
        
        return {"message": f"Channel with ID {channel_id} deleted successfully"} 