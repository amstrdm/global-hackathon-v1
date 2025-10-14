# routes/evidence.py

import os

import aiofiles
from database.db import get_db
from database.models import Room, User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from utils.logging_config import get_logger

logger = get_logger("routes.evidence")
router = APIRouter()
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
UPLOAD_DIR = os.path.join(project_root, "uploads")


@router.post("/rooms/{room_phrase}/{user_id}/upload_evidence")
async def upload_evidence(
    room_phrase: str,
    user_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload evidence for a room with comprehensive error handling and logging"""
    logger.info(f"Evidence upload attempt - Room: {room_phrase}, User: {user_id}, Type: {evidence_type}, File: {file.filename}")
    
    try:
        # Validate input parameters
        if not room_phrase or not room_phrase.strip():
            logger.warning("Empty room_phrase provided for evidence upload")
            raise HTTPException(status_code=400, detail="Room phrase cannot be empty")
        
        if not user_id or not user_id.strip():
            logger.warning("Empty user_id provided for evidence upload")
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        if not evidence_type or not evidence_type.strip():
            logger.warning("Empty evidence_type provided for evidence upload")
            raise HTTPException(status_code=400, detail="Evidence type cannot be empty")
        
        if not file or not file.filename:
            logger.warning("No file provided for evidence upload")
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size (limit to 10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"File too large: {len(file_content)} bytes")
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Reset file pointer
        await file.seek(0)

        # Validate user and room exist
        user = db.query(User).filter_by(id=user_id).first()
        room = db.query(Room).filter_by(room_phrase=room_phrase).first()
        
        if not room:
            logger.warning(f"Room not found for evidence upload: {room_phrase}")
            raise HTTPException(status_code=404, detail="Room not found")
        
        if not user:
            logger.warning(f"User not found for evidence upload: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user is the seller
        if user.id != room.seller_id:
            logger.warning(f"Non-seller attempted to upload evidence: {user_id} (seller: {room.seller_id})")
            raise HTTPException(
                status_code=403, detail="Only the seller can upload evidence"
            )

        # Check if room is in dispute state
        if room.status != "DISPUTE" or room.dispute_status != "AWAITING_EVIDENCE":
            logger.warning(f"Evidence upload attempted in wrong room state: {room.status}, {room.dispute_status}")
            raise HTTPException(
                status_code=400, detail="Evidence can only be uploaded during active disputes"
            )

        # Create a secure directory for the room's uploads
        room_upload_dir = os.path.join(UPLOAD_DIR, room_phrase)
        try:
            os.makedirs(room_upload_dir, exist_ok=True)
            logger.debug(f"Created/verified upload directory: {room_upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise HTTPException(status_code=500, detail="Failed to create upload directory")

        # Generate secure filename to prevent path traversal
        import uuid
        file_extension = os.path.splitext(file.filename)[1]
        secure_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(room_upload_dir, secure_filename)

        # Save the file asynchronously
        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
            logger.debug(f"File saved successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")

        # Update the submitted_evidence JSON in the database
        try:
            if room.submitted_evidence is None:
                room.submitted_evidence = {}

            if evidence_type not in room.submitted_evidence:
                room.submitted_evidence[evidence_type] = []

            room.submitted_evidence[evidence_type].append(
                os.path.join(room_phrase, secure_filename)
            )
            flag_modified(room, "submitted_evidence")
            db.commit()
            logger.debug(f"Evidence record updated in database")
        except Exception as e:
            logger.error(f"Failed to update evidence in database: {e}")
            # Clean up the uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(status_code=500, detail="Failed to update evidence record")

        response_data = {
            "filename": secure_filename,
            "path": file_path,
            "status": "Evidence uploaded successfully",
        }
        
        logger.info(f"Evidence upload successful - Room: {room_phrase}, File: {secure_filename}")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as they are expected
        raise
    except Exception as e:
        logger.error(f"Unexpected error during evidence upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during evidence upload")
