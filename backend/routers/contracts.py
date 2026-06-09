from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import get_db
from models import Contract, Orchard, User, Hive
from schemas import (
    ContractCreate,
    ContractUpdate,
    ContractStatusUpdate,
    ContractResponse,
    ContractDetail,
    OrchardResponse,
    UserResponse,
    HiveResponse,
)
from auth import get_current_user

router = APIRouter(prefix="/contracts", tags=["合同管理"])

VALID_STATUS_TRANSITIONS = {
    "draft": ["effective"],
    "effective": ["ongoing"],
    "ongoing": ["completed", "disputed"],
    "completed": [],
    "disputed": [],
}


def generate_contract_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    count = db.query(Contract).filter(Contract.contract_no.like(f"HT{today}%")).count()
    return f"HT{today}{str(count + 1).zfill(4)}"


@router.get("", response_model=list[ContractResponse])
def list_contracts(
    status: str = Query(None),
    beekeeper_id: int = Query(None),
    orchard_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Contract).options(
        joinedload(Contract.orchard),
        joinedload(Contract.beekeeper),
    )
    if status:
        query = query.filter(Contract.status == status)
    if beekeeper_id:
        query = query.filter(Contract.beekeeper_id == beekeeper_id)
    if orchard_id:
        query = query.filter(Contract.orchard_id == orchard_id)
    query = query.order_by(Contract.created_at.desc())
    results = query.all()
    response = []
    for c in results:
        resp = ContractResponse.model_validate(c)
        resp.orchard_name = c.orchard.name if c.orchard else None
        resp.beekeeper_name = c.beekeeper.real_name if c.beekeeper else None
        response.append(resp)
    return response


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    orchard = db.query(Orchard).filter(Orchard.id == data.orchard_id).first()
    if not orchard:
        raise HTTPException(status_code=404, detail="果园不存在")
    beekeeper = db.query(User).filter(User.id == data.beekeeper_id).first()
    if not beekeeper:
        raise HTTPException(status_code=404, detail="蜂农不存在")
    if beekeeper.role != "beekeeper":
        raise HTTPException(status_code=400, detail="指定用户不是蜂农角色")

    contract_no = generate_contract_no(db)
    total_amount = data.hive_count * data.unit_price

    contract = Contract(
        contract_no=contract_no,
        orchard_id=data.orchard_id,
        beekeeper_id=data.beekeeper_id,
        hive_count=data.hive_count,
        start_date=data.start_date,
        end_date=data.end_date,
        unit_price=data.unit_price,
        penalty_clause=data.penalty_clause,
        status="draft",
        total_amount=total_amount,
        notes=data.notes,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractDetail)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = (
        db.query(Contract)
        .options(
            joinedload(Contract.orchard),
            joinedload(Contract.beekeeper),
            joinedload(Contract.hives),
        )
        .filter(Contract.id == contract_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿状态的合同可以编辑")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract, key, value)

    if data.hive_count is not None or data.unit_price is not None:
        hive_count = contract.hive_count
        unit_price = contract.unit_price
        contract.total_amount = hive_count * unit_price

    contract.updated_at = datetime.now()
    db.commit()
    db.refresh(contract)
    return contract


@router.put("/{contract_id}/status", response_model=ContractResponse)
def change_contract_status(
    contract_id: int,
    data: ContractStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    new_status = data.status
    allowed = VALID_STATUS_TRANSITIONS.get(contract.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"合同状态不允许从 '{contract.status}' 变更为 '{new_status}'，允许的状态: {allowed}",
        )

    contract.status = new_status
    contract.updated_at = datetime.now()
    db.commit()
    db.refresh(contract)
    return contract


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿状态的合同可以删除")

    hives = db.query(Hive).filter(Hive.contract_id == contract_id).all()
    for hive in hives:
        hive.contract_id = None
        hive.status = "idle"
        hive.deployed_at = None

    db.delete(contract)
    db.commit()
    return {"message": "合同已删除"}
