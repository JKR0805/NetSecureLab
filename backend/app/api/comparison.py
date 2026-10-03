from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.comparison import ComparisonResponse
from app.services.comparison.service import compare_scans

router = APIRouter(prefix="/scans/compare", tags=["comparison"])

@router.get("/{scan1_id}/{scan2_id}", response_model=ComparisonResponse)
def compare_two_scans(scan1_id: int, scan2_id: int, db: Session = Depends(get_db)):
    try:
        return compare_scans(scan1_id, scan2_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
