from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.target import Target
from app.models.scan import Scan
from app.schemas.target import TargetCreate, TargetResponse
from app.utils.validators import validate_target_input

router = APIRouter(prefix="/targets", tags=["targets"])

@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    # Validate target format
    is_valid, err_msg = validate_target_input(payload.target, payload.target_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg
        )

    target_obj = Target(
        name=payload.name.strip(),
        target=payload.target.strip(),
        target_type=payload.target_type,
        description=payload.description.strip() if payload.description else None,
        authorization_confirmed=payload.authorization_confirmed,
    )
    db.add(target_obj)
    db.commit()
    db.refresh(target_obj)
    
    resp = TargetResponse.model_validate(target_obj)
    resp.scan_count = 0
    return resp

@router.get("", response_model=List[TargetResponse])
def list_targets(db: Session = Depends(get_db)):
    targets = db.query(Target).order_by(Target.created_at.desc()).all()
    results = []
    for t in targets:
        resp = TargetResponse.model_validate(t)
        resp.scan_count = len(t.scans)
        results.append(resp)
    return results

@router.get("/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, db: Session = Depends(get_db)):
    target_obj = db.query(Target).filter(Target.id == target_id).first()
    if not target_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    resp = TargetResponse.model_validate(target_obj)
    resp.scan_count = len(target_obj.scans)
    return resp

@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target_obj = db.query(Target).filter(Target.id == target_id).first()
    if not target_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    
    # Task 2.3: Restrict deletion if target has scans
    scans_count = db.query(Scan).filter(Scan.target_id == target_id).count()
    if scans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Target cannot be deleted because it has {scans_count} associated scan(s). Historical scans must be preserved for comparison integrity."
        )
    
    db.delete(target_obj)
    db.commit()
    return None
