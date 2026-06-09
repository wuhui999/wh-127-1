from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import get_db
from models import Settlement, Contract, Hive, Anomaly
from schemas import (
    SettlementCreate,
    SettlementConfirm,
    SettlementPay,
    SettlementResponse,
    SettlementDetail,
    SettlementPreview,
)
from auth import get_current_user

router = APIRouter(prefix="/settlements", tags=["结算管理"])

SEVERITY_DEDUCTION = {
    "low": 50,
    "medium": 200,
    "high": 500,
}


def calculate_settlement(contract_id: int, db: Session) -> dict:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deployed_hives = db.query(Hive).filter(
        Hive.contract_id == contract_id,
        Hive.status.in_(["deployed", "withdrawn", "anomaly", "inspecting"]),
    ).all()

    total_hive_days = 0
    for hive in deployed_hives:
        if hive.deployed_at:
            end = datetime.now()
            days = (end - hive.deployed_at).days
            total_hive_days += max(days, 0)

    unit_price = contract.unit_price
    base_amount = total_hive_days * unit_price

    anomalies = db.query(Anomaly).filter(Anomaly.contract_id == contract_id).all()
    anomaly_deduction = 0
    anomaly_details = []
    for anomaly in anomalies:
        deduction = SEVERITY_DEDUCTION.get(anomaly.severity, 0)
        anomaly_deduction += deduction
        anomaly_details.append({
            "id": anomaly.id,
            "type": anomaly.type,
            "severity": anomaly.severity,
            "deduction": deduction,
            "status": anomaly.status,
        })

    penalty_deduction = 0
    if contract.penalty_clause:
        try:
            penalty_value = float(contract.penalty_clause)
            penalty_deduction = penalty_value
        except (ValueError, TypeError):
            penalty_deduction = 0

    total_amount = base_amount - anomaly_deduction - penalty_deduction
    total_amount = max(total_amount, 0)

    return {
        "contract_id": contract_id,
        "total_hive_days": total_hive_days,
        "unit_price": unit_price,
        "base_amount": base_amount,
        "anomaly_deduction": anomaly_deduction,
        "penalty_deduction": penalty_deduction,
        "total_amount": total_amount,
        "anomaly_count": len(anomalies),
        "anomaly_details": anomaly_details,
    }


@router.get("/calculate/{contract_id}", response_model=SettlementPreview)
def preview_settlement(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = calculate_settlement(contract_id, db)
    return SettlementPreview(**result)


@router.get("", response_model=list[SettlementResponse])
def list_settlements(
    contract_id: int = Query(None),
    settlement_status: str = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Settlement).options(
        joinedload(Settlement.contract).joinedload(Contract.orchard),
    )
    if contract_id:
        query = query.filter(Settlement.contract_id == contract_id)
    if settlement_status:
        query = query.filter(Settlement.status == settlement_status)
    query = query.order_by(Settlement.created_at.desc())
    results = query.all()
    response = []
    for s in results:
        resp = SettlementResponse.model_validate(s)
        resp.contract_no = s.contract.contract_no if s.contract else None
        resp.orchard_name = s.contract.orchard.name if s.contract and s.contract.orchard else None
        response.append(resp)
    return response


@router.post("", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
def create_settlement(
    data: SettlementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    existing = db.query(Settlement).filter(
        Settlement.contract_id == data.contract_id,
        Settlement.status.in_(["pending", "confirmed"]),
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="该合同已有待处理或已确认的结算单",
        )

    calc = calculate_settlement(data.contract_id, db)

    settlement = Settlement(
        contract_id=data.contract_id,
        total_hive_days=calc["total_hive_days"],
        unit_price=calc["unit_price"],
        base_amount=calc["base_amount"],
        anomaly_deduction=calc["anomaly_deduction"],
        penalty_deduction=calc["penalty_deduction"],
        total_amount=calc["total_amount"],
        status="pending",
        settled_by=current_user.id,
        settled_at=datetime.now(),
        notes=data.notes,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/{settlement_id}", response_model=SettlementDetail)
def get_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settlement = (
        db.query(Settlement)
        .options(joinedload(Settlement.contract), joinedload(Settlement.settled_by_user))
        .filter(Settlement.id == settlement_id)
        .first()
    )
    if not settlement:
        raise HTTPException(status_code=404, detail="结算单不存在")
    return settlement


@router.put("/{settlement_id}/confirm", response_model=SettlementResponse)
def confirm_settlement(
    settlement_id: int,
    data: SettlementConfirm,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算单不存在")
    if settlement.status != "pending":
        raise HTTPException(status_code=400, detail="只有待确认的结算单可以确认")

    settlement.status = "confirmed"
    if data.notes:
        settlement.notes = data.notes
    db.commit()
    db.refresh(settlement)
    return settlement


@router.put("/{settlement_id}/pay", response_model=SettlementResponse)
def pay_settlement(
    settlement_id: int,
    data: SettlementPay,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算单不存在")
    if settlement.status != "confirmed":
        raise HTTPException(status_code=400, detail="只有已确认的结算单可以标记为已支付")

    settlement.status = "paid"
    if data.notes:
        settlement.notes = data.notes
    db.commit()
    db.refresh(settlement)
    return settlement
