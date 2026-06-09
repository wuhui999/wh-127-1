from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Orchard, User, Contract
from schemas import (
    OrchardCreate,
    OrchardUpdate,
    OrchardResponse,
    OrchardDetail,
    ContractResponse,
)
from auth import get_current_user

router = APIRouter(prefix="/orchards", tags=["果园管理"])


@router.get("", response_model=list[OrchardResponse])
def list_orchards(
    owner_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Orchard)
    if owner_id:
        query = query.filter(Orchard.owner_id == owner_id)
    query = query.order_by(Orchard.created_at.desc())
    return query.all()


@router.post("", response_model=OrchardResponse, status_code=status.HTTP_201_CREATED)
def create_orchard(
    data: OrchardCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    owner = db.query(User).filter(User.id == data.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="果园主不存在")
    if owner.role != "orchard_owner":
        raise HTTPException(status_code=400, detail="指定用户不是果园主角色")

    orchard = Orchard(
        name=data.name,
        owner_id=data.owner_id,
        location=data.location,
        area=data.area,
        crop_type=data.crop_type,
        gps_lat=data.gps_lat,
        gps_lng=data.gps_lng,
        address=data.address,
    )
    db.add(orchard)
    db.commit()
    db.refresh(orchard)
    return orchard


@router.get("/{orchard_id}", response_model=OrchardDetail)
def get_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    orchard = (
        db.query(Orchard)
        .options(joinedload(Orchard.contracts))
        .filter(Orchard.id == orchard_id)
        .first()
    )
    if not orchard:
        raise HTTPException(status_code=404, detail="果园不存在")
    return orchard


@router.put("/{orchard_id}", response_model=OrchardResponse)
def update_orchard(
    orchard_id: int,
    data: OrchardUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    orchard = db.query(Orchard).filter(Orchard.id == orchard_id).first()
    if not orchard:
        raise HTTPException(status_code=404, detail="果园不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(orchard, key, value)

    db.commit()
    db.refresh(orchard)
    return orchard
