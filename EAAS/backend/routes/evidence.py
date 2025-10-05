# routes/evidence.py

import os

import aiofiles
from database.db import get_db
from database.models import Room, User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()
UPLOAD_DIR = "./uploads"


@router.post("/rooms/{room_phrase}/{user_id}/upload_evidence")
async def upload_evidence(
    room_phrase: str,
    user_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=user_id).first()
    room = db.query(Room).filter_by(room_phrase=room_phrase).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not user:
        raise HTTPException(status_code=404, detail="Room not found")

    if user.id != room.seller_id:
        raise HTTPException(
            status_code=403, detail="Only the seller can upload evidence"
        )

    # Create a secure directory for the room's uploads
    room_upload_dir = os.path.join(UPLOAD_DIR, room_phrase)
    os.makedirs(room_upload_dir, exist_ok=True)

    file_path = os.path.join(room_upload_dir, file.filename)

    # Save the file asynchronously
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Update the submitted_evidence JSON in the database
    if room.submitted_evidence is None:
        room.submitted_evidence = {}

    if evidence_type not in room.submitted_evidence:
        room.submitted_evidence[evidence_type] = []

    room.submitted_evidence[evidence_type].append(file_path)
    flag_modified(room, "submitted_evidence")

    db.commit()

    return {
        "filename": file.filename,
        "path": file_path,
        "status": "Evidence uploaded successfully",
    }
