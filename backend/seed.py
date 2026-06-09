from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models import User, Orchard, Contract, Hive, Inspection, Anomaly, Settlement
from auth import hash_password


def seed_data(db: Session):
    user_count = db.query(User).count()
    if user_count > 0:
        return

    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        real_name="管理员",
        role="admin",
        phone="13800000000",
    )
    beekeeper1 = User(
        username="beekeeper1",
        password_hash=hash_password("123456"),
        real_name="蜂农-张三",
        role="beekeeper",
        phone="13800000001",
    )
    owner1 = User(
        username="owner1",
        password_hash=hash_password("123456"),
        real_name="果园主-李四",
        role="orchard_owner",
        phone="13800000002",
    )
    supervisor1 = User(
        username="supervisor1",
        password_hash=hash_password("123456"),
        real_name="监管员-王五",
        role="supervisor",
        phone="13800000003",
    )
    db.add_all([admin, beekeeper1, owner1, supervisor1])
    db.flush()

    orchard1 = Orchard(
        name="阳光苹果园",
        owner_id=owner1.id,
        location="山东烟台",
        area=120.5,
        crop_type="苹果",
        gps_lat=37.4638,
        gps_lng=121.4479,
        address="山东省烟台市栖霞区阳光路88号",
    )
    orchard2 = Orchard(
        name="翠绿梨园",
        owner_id=owner1.id,
        location="安徽砀山",
        area=85.0,
        crop_type="梨",
        gps_lat=34.4267,
        gps_lng=116.3667,
        address="安徽省宿州市砀山县翠绿大道66号",
    )
    orchard3 = Orchard(
        name="金橙柑橘园",
        owner_id=owner1.id,
        location="江西赣州",
        area=200.0,
        crop_type="柑橘",
        gps_lat=25.8314,
        gps_lng=114.9353,
        address="江西省赣州市信丰县金橙路188号",
    )
    db.add_all([orchard1, orchard2, orchard3])
    db.flush()

    now = datetime.now()
    contract1 = Contract(
        contract_no=f"HT{now.strftime('%Y%m%d')}0001",
        orchard_id=orchard1.id,
        beekeeper_id=beekeeper1.id,
        hive_count=5,
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=60),
        unit_price=15.0,
        penalty_clause="500",
        status="ongoing",
        total_amount=5 * 15.0 * 90,
        notes="苹果花期授粉合同，需在花期前后完成部署",
    )
    contract2 = Contract(
        contract_no=f"HT{now.strftime('%Y%m%d')}0002",
        orchard_id=orchard2.id,
        beekeeper_id=beekeeper1.id,
        hive_count=3,
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=100),
        unit_price=12.0,
        penalty_clause="300",
        status="effective",
        total_amount=3 * 12.0 * 90,
        notes="梨树授粉合同，待部署蜂箱",
    )
    db.add_all([contract1, contract2])
    db.flush()

    hives = []
    for i in range(1, 6):
        hives.append(Hive(
            hive_no=f"BEE-2024-{str(i).zfill(3)}",
            contract_id=contract1.id,
            gps_lat=37.4638 + i * 0.001,
            gps_lng=121.4479 + i * 0.001,
            status="deployed",
            last_inspection_at=now - timedelta(days=i),
            deployed_at=now - timedelta(days=25),
        ))

    for i in range(6, 8):
        hives.append(Hive(
            hive_no=f"BEE-2024-{str(i).zfill(3)}",
            contract_id=None,
            gps_lat=34.4267 + (i - 5) * 0.001,
            gps_lng=116.3667 + (i - 5) * 0.001,
            status="idle",
        ))

    for i in range(8, 11):
        hives.append(Hive(
            hive_no=f"BEE-2024-{str(i).zfill(3)}",
            contract_id=contract2.id if i <= 9 else None,
            gps_lat=34.4267 + (i - 7) * 0.001,
            gps_lng=116.3667 + (i - 7) * 0.001,
            status="deployed" if i <= 9 else "idle",
            deployed_at=now - timedelta(days=5) if i <= 9 else None,
            last_inspection_at=now - timedelta(days=3) if i <= 9 else None,
        ))

    db.add_all(hives)
    db.flush()

    inspections = [
        Inspection(
            hive_id=hives[0].id,
            inspector_id=supervisor1.id,
            colony_strength=8,
            disease_found=False,
            feeding_needed=False,
            notes="蜂群状况良好，活动正常",
            inspected_at=now - timedelta(days=1),
        ),
        Inspection(
            hive_id=hives[1].id,
            inspector_id=supervisor1.id,
            colony_strength=7,
            disease_found=False,
            feeding_needed=True,
            feeding_detail="需要补充糖水喂养",
            notes="蜂群中等偏上，建议补充饲料",
            inspected_at=now - timedelta(days=2),
        ),
        Inspection(
            hive_id=hives[2].id,
            inspector_id=supervisor1.id,
            colony_strength=6,
            disease_found=False,
            feeding_needed=True,
            feeding_detail="花粉不足需补充",
            notes="蜂群中等，需要关注",
            inspected_at=now - timedelta(days=3),
        ),
        Inspection(
            hive_id=hives[3].id,
            inspector_id=beekeeper1.id,
            colony_strength=9,
            disease_found=False,
            feeding_needed=False,
            notes="蜂群强壮，授粉效果良好",
            inspected_at=now - timedelta(days=4),
        ),
        Inspection(
            hive_id=hives[4].id,
            inspector_id=beekeeper1.id,
            colony_strength=5,
            disease_found=True,
            disease_detail="疑似螨虫感染，需进一步检查",
            feeding_needed=True,
            feeding_detail="蜂群较弱需加强营养",
            notes="蜂群偏弱，发现疑似螨虫",
            inspected_at=now - timedelta(days=5),
        ),
    ]
    db.add_all(inspections)
    db.flush()

    anomaly1 = Anomaly(
        hive_id=hives[4].id,
        contract_id=contract1.id,
        reporter_id=supervisor1.id,
        type="病虫害",
        description="蜂群疑似螨虫感染，蜂群强度下降明显",
        severity="medium",
        status="reported",
    )
    anomaly2 = Anomaly(
        hive_id=hives[2].id,
        contract_id=contract1.id,
        reporter_id=beekeeper1.id,
        type="天气影响",
        description="连续暴雨天气，蜂箱可能受损，需检查",
        severity="high",
        status="processing",
    )
    db.add_all([anomaly1, anomaly2])
    db.flush()

    total_hive_days = 5 * 25
    base_amount = total_hive_days * 15.0
    anomaly_deduction = 200 + 500
    penalty_deduction = 0
    settlement = Settlement(
        contract_id=contract1.id,
        total_hive_days=total_hive_days,
        unit_price=15.0,
        base_amount=base_amount,
        anomaly_deduction=anomaly_deduction,
        penalty_deduction=penalty_deduction,
        total_amount=base_amount - anomaly_deduction - penalty_deduction,
        status="pending",
        settled_by=admin.id,
        settled_at=now,
        notes="合同进行中结算预览",
    )
    db.add(settlement)

    hives[4].status = "anomaly"

    db.commit()
