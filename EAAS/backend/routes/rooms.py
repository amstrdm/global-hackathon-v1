from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Room
from routes.utils.utils import room_to_dict

router = APIRouter()


@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    """Get all available rooms (waiting for buyers)"""
    rooms = db.query(Room).filter(
        Room.status == "WAITING_FOR_BUYER"
    ).all()
    
    return [room_to_dict(room) for room in rooms]


@router.get("/rooms/{room_phrase}")
def get_room(room_phrase: str, db: Session = Depends(get_db)):
    """Get specific room details"""
    room = db.query(Room).filter_by(room_phrase=room_phrase).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return room_to_dict(room)
