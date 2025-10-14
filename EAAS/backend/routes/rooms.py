from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Room
from routes.utils.utils import room_to_dict
from utils.logging_config import get_logger

logger = get_logger("routes.rooms")
router = APIRouter()


@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    """Get all available rooms (waiting for buyers)"""
    logger.info("Fetching all available rooms")
    
    try:
        rooms = db.query(Room).filter(
            Room.status == "WAITING_FOR_BUYER"
        ).all()
        
        logger.info(f"Found {len(rooms)} available rooms")
        return [room_to_dict(room) for room in rooms]
        
    except Exception as e:
        logger.error(f"Error fetching rooms: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching rooms")


@router.get("/rooms/{room_phrase}")
def get_room(room_phrase: str, db: Session = Depends(get_db)):
    """Get specific room details"""
    logger.info(f"Fetching room details for: {room_phrase}")
    
    try:
        if not room_phrase or not room_phrase.strip():
            logger.warning("Empty room phrase provided")
            raise HTTPException(status_code=400, detail="Room phrase cannot be empty")
        
        room = db.query(Room).filter_by(room_phrase=room_phrase).first()
        if not room:
            logger.warning(f"Room not found: {room_phrase}")
            raise HTTPException(status_code=404, detail="Room not found")
        
        logger.info(f"Room found: {room_phrase}, status: {room.status}")
        return room_to_dict(room)
        
    except HTTPException:
        # Re-raise HTTP exceptions as they are expected
        raise
    except Exception as e:
        logger.error(f"Error fetching room {room_phrase}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching room details")
