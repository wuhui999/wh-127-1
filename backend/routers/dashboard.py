from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Contract, Hive, Anomaly, Inspection, Settlement, User, Orchard
from schemas import DashboardStats, AnomalyListItem, OverdueInspectionItem
from auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total_contracts = db.query(func.count(Contract.id)).scalar() or 0
    active_contracts = db.query(func.count(Contract.id)).filter(
        Contract.status.in_(["effective", "ongoing"])
    ).scalar() or 0

    total_hives = db.query(func.count(Hive.id)).scalar() or 0
    deployed_hives = db.query(func.count(Hive.id)).filter(
        Hive.status == "deployed"
    ).scalar() or 0

    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    deployed_hive_ids = db.query(Hive.id).filter(Hive.status == "deployed").subquery()
    recently_inspected = db.query(func.count(func.distinct(Inspection.hive_id))).filter(
        Inspection.hive_id.in_(deployed_hive_ids),
        Inspection.inspected_at >= seven_days_ago,
    ).scalar() or 0
    pending_inspections = max(deployed_hives - recently_inspected, 0)

    pending_anomalies = db.query(func.count(Anomaly.id)).filter(
        Anomaly.status.in_(["reported", "processing"])
    ).scalar() or 0

    pending_settlements = db.query(func.count(Settlement.id)).filter(
        Settlement.status.in_(["pending", "confirmed"])
    ).scalar() or 0

    contracts_by_status_raw = db.query(Contract.status, func.count(Contract.id)).group_by(Contract.status).all()
    contracts_by_status = {row[0]: row[1] for row in contracts_by_status_raw}

    hives_by_status_raw = db.query(Hive.status, func.count(Hive.id)).group_by(Hive.status).all()
    hives_by_status = {row[0]: row[1] for row in hives_by_status_raw}

    anomalies_by_severity_raw = db.query(Anomaly.severity, func.count(Anomaly.id)).filter(
        Anomaly.status.in_(["reported", "processing"])
    ).group_by(Anomaly.severity).all()
    anomalies_by_severity = {row[0]: row[1] for row in anomalies_by_severity_raw}

    recent_anomaly_rows = db.query(Anomaly, Hive.hive_no).join(
        Hive, Anomaly.hive_id == Hive.id
    ).filter(
        Anomaly.status.in_(["reported", "processing"])
    ).order_by(Anomaly.created_at.desc()).limit(5).all()

    recent_anomalies = [
        AnomalyListItem(
            id=row.Anomaly.id,
            hive_no=row.hive_no,
            type=row.Anomaly.type,
            severity=row.Anomaly.severity,
            status=row.Anomaly.status,
            created_at=row.Anomaly.created_at,
        )
        for row in recent_anomaly_rows
    ]

    overdue_hives = db.query(Hive).filter(
        Hive.status == "deployed",
        Hive.last_inspection_at == None
    ).all()
    overdue_hives += db.query(Hive).filter(
        Hive.status == "deployed",
        Hive.last_inspection_at < seven_days_ago,
    ).all()

    upcoming_inspections = []
    for h in overdue_hives[:10]:
        contract_info = db.query(Contract).join(Orchard, Contract.orchard_id == Orchard.id).filter(
            Contract.id == h.contract_id
        ).first()
        location = contract_info.orchard.name if contract_info and contract_info.orchard else "未知"
        days_overdue = 0
        if h.last_inspection_at:
            days_overdue = (datetime.now() - h.last_inspection_at).days - 7
        else:
            days_overdue = (datetime.now() - h.deployed_at).days if h.deployed_at else 0
        upcoming_inspections.append(OverdueInspectionItem(
            hive_no=h.hive_no,
            location=location,
            last_inspection_at=h.last_inspection_at,
            days_overdue=max(days_overdue, 0),
        ))

    return DashboardStats(
        total_contracts=total_contracts,
        active_contracts=active_contracts,
        total_hives=total_hives,
        deployed_hives=deployed_hives,
        pending_inspections=pending_inspections,
        pending_anomalies=pending_anomalies,
        pending_settlements=pending_settlements,
        contracts_by_status=contracts_by_status,
        hives_by_status=hives_by_status,
        anomalies_by_severity=anomalies_by_severity,
        recent_anomalies=recent_anomalies,
        upcoming_inspections=upcoming_inspections,
    )
