from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta

from database import get_db
from models import Inspection, Hive, Contract, User
from schemas import (
    InspectionCreate,
    InspectionResponse,
    InspectionDetail,
    OverdueHive,
    HiveResponse,
    ContractResponse,
)
from auth import get_current_user

router = APIRouter(prefix="/inspections", tags=["巡检管理"])

INSPECTION_CYCLE_DAYS = 7


@router.get("/overdue", response_model=list[OverdueHive])
def get_overdue_inspections(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deployed_hives = (
        db.query(Hive)
        .options(joinedload(Hive.contract))
        .filter(Hive.status == "deployed")
        .all()
    )

    overdue_list = []
    threshold = datetime.now() - timedelta(days=INSPECTION_CYCLE_DAYS)

    for hive in deployed_hives:
        last_inspection = hive.last_inspection_at
        if last_inspection is None:
            days_overdue = INSPECTION_CYCLE_DAYS
            if hive.deployed_at and (datetime.now() - hive.deployed_at).days > INSPECTION_CYCLE_DAYS:
                days_overdue = (datetime.now() - hive.deployed_at).days - INSPECTION_CYCLE_DAYS
        elif last_inspection < threshold:
            days_overdue = (datetime.now() - last_inspection).days - INSPECTION_CYCLE_DAYS
        else:
            continue

        overdue_list.append(
            OverdueHive(
                hive=HiveResponse.model_validate(hive),
                contract=ContractResponse.model_validate(hive.contract) if hive.contract else None,
                days_overdue=max(days_overdue, 0),
                last_inspection_at=last_inspection,
            )
        )

    overdue_list.sort(key=lambda x: x.days_overdue, reverse=True)
    return overdue_list


@router.get("", response_model=list[InspectionResponse])
def list_inspections(
    hive_id: int = Query(None),
    inspector_id: int = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Inspection).options(
        joinedload(Inspection.hive),
        joinedload(Inspection.inspector),
    )
    if hive_id:
        query = query.filter(Inspection.hive_id == hive_id)
    if inspector_id:
        query = query.filter(Inspection.inspector_id == inspector_id)
    if start_date:
        query = query.filter(Inspection.inspected_at >= start_date)
    if end_date:
        query = query.filter(Inspection.inspected_at <= end_date)
    query = query.order_by(Inspection.inspected_at.desc())
    results = query.all()
    response = []
    for insp in results:
        resp = InspectionResponse.model_validate(insp)
        resp.hive_no = insp.hive.hive_no if insp.hive else None
        resp.inspector_name = insp.inspector.real_name if insp.inspector else None
        response.append(resp)
    return response


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
def create_inspection(
    data: InspectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = db.query(Hive).filter(Hive.id == data.hive_id).first()
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")

    if data.colony_strength < 1 or data.colony_strength > 10:
        raise HTTPException(
            status_code=400,
            detail="蜂群强度必须在1-10之间",
        )

    inspected_at = data.inspected_at or datetime.now()

    inspection = Inspection(
        hive_id=data.hive_id,
        inspector_id=data.inspector_id,
        colony_strength=data.colony_strength,
        disease_found=data.disease_found,
        disease_detail=data.disease_detail,
        feeding_needed=data.feeding_needed,
        feeding_detail=data.feeding_detail,
        photos=data.photos,
        notes=data.notes,
        inspected_at=inspected_at,
    )
    db.add(inspection)

    hive.last_inspection_at = inspected_at
    if hive.status == "deployed":
        hive.status = "inspecting"
        db.flush()
        hive.status = "deployed"

    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("/{inspection_id}", response_model=InspectionDetail)
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    inspection = (
        db.query(Inspection)
        .options(joinedload(Inspection.hive), joinedload(Inspection.inspector))
        .filter(Inspection.id == inspection_id)
        .first()
    )
    if not inspection:
        raise HTTPException(status_code=404, detail="巡检记录不存在")
    return inspection
