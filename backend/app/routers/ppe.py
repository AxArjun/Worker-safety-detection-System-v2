import logging
from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session

from ..models.database import get_db, User
from ..models.schemas import PPEResponse
from .auth import get_current_user
from ..services.ppe_service import PPEService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ppe", tags=["PPE Analysis"])

@router.post("/analyze", response_model=PPEResponse)
async def analyze_ppe_image(
    request: Request,
    image: UploadFile = File(..., description="JPEG/PNG image for enterprise PPE verification"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enterprise PPE Analysis Endpoint.
    - Strictly enforces 'Assume Unsafe' logic.
    - Persists audit logs to the database.
    - Returns professional annotated results.
    """
    try:
        image_bytes = await image.read()
        
        # Initialize service with detector from app state
        # Following Clean Architecture: Service handles business logic & persistence
        ppe_svc = PPEService(ppe_detector=request.app.state.ppe_detector)
        
        result = ppe_svc.analyze_and_audit(
            image_bytes=image_bytes,
            db=db,
            user_id=current_user.id
        )
        
        return result

    except ValueError as ve:
        logger.warning(f"Validation error during PPE analysis: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Critical failure in PPE analysis pipeline: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred during industrial safety analysis."
        )
