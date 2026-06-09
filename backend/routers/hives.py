from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import get_db
from models import Hive, Contract, Inspection
from schemas import (
    HiveCreate,
    HiveUpdate,
    HiveDeploy,
    HiveResponse,
    HiveDetail,
    ContractResponse,
    InspectionResponse,
)
from auth import get_current_user

router = APIRouter(prefix="/hives", tags=["蜂箱管理"])


@router.get("", response_model=list[HiveResponse])
def list_hives(
    status: str = Query(None),
    contract_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Hive).options(joinedload(Hive.contract))
    if status:
        query = query.filter(Hive.status == status)
    if contract_id is not None:
        query = query.filter(Hive.contract_id == contract_id)
    query = query.order_by(Hive.created_at.desc())
    results = query.all()
    response = []
    for h in results:
        resp = HiveResponse.model_validate(h)
        resp.contract_no = h.contract.contract_no if h.contract else None
        response.append(resp)
    return response


@router.post("", response_model=HiveResponse, status_code=status.HTTP_201_CREATED)
def create_hive(
    data: HiveCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    existing = db.query(Hive).filter(Hive.hive_no == data.hive_no).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"蜂箱编号 '{data.hive_no}' 已存在",
        )

    hive = Hive(
        hive_no=data.hive_no,
        gps_lat=data.gps_lat,
        gps_lng=data.gps_lng,
        status="idle",
    )
    db.add(hive)
    db.commit()
    db.refresh(hive)
    return hive


@router.get("/{hive_id}", response_model=HiveDetail)
def get_hive(
    hive_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = (
        db.query(Hive)
        .options(joinedload(Hive.contract))
        .filter(Hive.id == hive_id)
        .first()
    )
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")

    latest_inspection = (
        db.query(Inspection)
        .filter(Inspection.hive_id == hive_id)
        .order_by(Inspection.inspected_at.desc())
        .first()
    )

    result = HiveDetail.model_validate(hive)
    result.latest_inspection = InspectionResponse.model_validate(latest_inspection) if latest_inspection else None
    return result


@router.put("/{hive_id}", response_model=HiveResponse)
def update_hive(
    hive_id: int,
    data: HiveUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = db.query(Hive).filter(Hive.id == hive_id).first()
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")

    update_data = data.model_dump(exclude_unset=True)
    valid_statuses = {"idle", "deployed", "inspecting", "anomaly", "withdrawn"}
    if "status" in update_data and update_data["status"] not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的蜂箱状态，有效状态: {', '.join(valid_statuses)}",
        )

    for key, value in update_data.items():
        setattr(hive, key, value)

    db.commit()
    db.refresh(hive)
    return hive


@router.post("/{hive_id}/deploy", response_model=HiveResponse)
def deploy_hive(
    hive_id: int,
    data: HiveDeploy,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = db.query(Hive).filter(Hive.id == hive_id).first()
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")
    if hive.status not in ("idle", "withdrawn"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 '{hive.status}' 的蜂箱无法部署，只有空闲或已撤回的蜂箱可以部署",
        )

    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status not in ("effective", "ongoing"):
        raise HTTPException(
            status_code=400,
            detail="只有生效或进行中的合同可以部署蜂箱",
        )

    deployed_count = db.query(Hive).filter(
        Hive.contract_id == data.contract_id,
        Hive.status == "deployed",
    ).count()
    if deployed_count >= contract.hive_count:
        raise HTTPException(
            status_code=400,
            detail=f"该合同已部署 {deployed_count} 个蜂箱，达到合同要求数量 {contract.hive_count}",
        )

    hive.contract_id = data.contract_id
    hive.status = "deployed"
    hive.deployed_at = datetime.now()
    if data.gps_lat is not None:
        hive.gps_lat = data.gps_lat
    if data.gps_lng is not None:
        hive.gps_lng = data.gps_lng

    if contract.status == "effective":
        contract.status = "ongoing"
        contract.updated_at = datetime.now()

    db.commit()
    db.refresh(hive)
    return hive


@router.post("/{hive_id}/withdraw", response_model=HiveResponse)
def withdraw_hive(
    hive_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = db.query(Hive).filter(Hive.id == hive_id).first()
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")
    if hive.status not in ("deployed", "inspecting", "anomaly"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 '{hive.status}' 的蜂箱无法撤回",
        )

    hive.status = "withdrawn"
    db.commit()
    db.refresh(hive)
    return hive
