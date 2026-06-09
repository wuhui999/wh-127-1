from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import get_db
from models import Anomaly, Hive, Contract
from schemas import (
    AnomalyCreate,
    AnomalyUpdate,
    AnomalyResolve,
    AnomalyResponse,
    AnomalyDetail,
)
from auth import get_current_user

router = APIRouter(prefix="/anomalies", tags=["异常管理"])

SEVERITY_DEDUCTION = {
    "low": 50,
    "medium": 200,
    "high": 500,
}


@router.get("", response_model=list[AnomalyResponse])
def list_anomalies(
    type: str = Query(None),
    anomaly_status: str = Query(None, alias="status"),
    severity: str = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Anomaly).options(
        joinedload(Anomaly.hive),
        joinedload(Anomaly.contract),
    )
    if type:
        query = query.filter(Anomaly.type == type)
    if anomaly_status:
        query = query.filter(Anomaly.status == anomaly_status)
    if severity:
        query = query.filter(Anomaly.severity == severity)
    query = query.order_by(Anomaly.created_at.desc())
    results = query.all()
    response = []
    for a in results:
        resp = AnomalyResponse.model_validate(a)
        resp.hive_no = a.hive.hive_no if a.hive else None
        resp.contract_no = a.contract.contract_no if a.contract else None
        response.append(resp)
    return response


@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
def report_anomaly(
    data: AnomalyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hive = db.query(Hive).filter(Hive.id == data.hive_id).first()
    if not hive:
        raise HTTPException(status_code=404, detail="蜂箱不存在")

    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    valid_types = {"swarm_escape", "disease", "weather", "other", "逃蜂", "病虫害", "天气影响", "其他"}
    if data.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的异常类型，有效类型: 逃蜂, 病虫害, 天气影响, 其他",
        )

    valid_severities = {"low", "medium", "high"}
    if data.severity not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"无效的严重程度，有效值: {', '.join(valid_severities)}",
        )

    anomaly = Anomaly(
        hive_id=data.hive_id,
        contract_id=data.contract_id,
        reporter_id=current_user.id,
        type=data.type,
        description=data.description,
        severity=data.severity,
        status="reported",
    )
    db.add(anomaly)

    hive.status = "anomaly"

    db.commit()
    db.refresh(anomaly)
    return anomaly


@router.get("/{anomaly_id}", response_model=AnomalyDetail)
def get_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    anomaly = (
        db.query(Anomaly)
        .options(
            joinedload(Anomaly.hive),
            joinedload(Anomaly.contract),
            joinedload(Anomaly.reporter),
        )
        .filter(Anomaly.id == anomaly_id)
        .first()
    )
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常记录不存在")
    return anomaly


@router.put("/{anomaly_id}", response_model=AnomalyResponse)
def update_anomaly(
    anomaly_id: int,
    data: AnomalyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常记录不存在")

    update_data = data.model_dump(exclude_unset=True)

    valid_severities = {"low", "medium", "high"}
    if "severity" in update_data and update_data["severity"] not in valid_severities:
        raise HTTPException(status_code=400, detail="无效的严重程度")

    valid_statuses = {"reported", "processing", "resolved"}
    if "status" in update_data and update_data["status"] not in valid_statuses:
        raise HTTPException(status_code=400, detail="无效的状态")

    for key, value in update_data.items():
        setattr(anomaly, key, value)

    if data.resolution and not anomaly.resolved_at:
        if anomaly.status != "resolved":
            anomaly.status = "resolved"
        anomaly.resolved_at = datetime.now()

    db.commit()
    db.refresh(anomaly)
    return anomaly


@router.put("/{anomaly_id}/resolve", response_model=AnomalyResponse)
def resolve_anomaly(
    anomaly_id: int,
    data: AnomalyResolve,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常记录不存在")

    if anomaly.status == "resolved":
        raise HTTPException(status_code=400, detail="异常已解决")

    anomaly.status = "resolved"
    anomaly.resolution = data.resolution
    anomaly.resolved_at = datetime.now()

    if data.restore_hive_status:
        hive = db.query(Hive).filter(Hive.id == anomaly.hive_id).first()
        if hive and hive.status == "anomaly":
            if hive.contract_id:
                hive.status = "deployed"
            else:
                hive.status = "idle"

    db.commit()
    db.refresh(anomaly)
    return anomaly
