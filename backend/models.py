from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)

    orchards = relationship("Orchard", back_populates="owner")
    contracts_as_beekeeper = relationship("Contract", back_populates="beekeeper", foreign_keys="Contract.beekeeper_id")
    inspections = relationship("Inspection", back_populates="inspector")
    reported_anomalies = relationship("Anomaly", back_populates="reporter")
    settled_settlements = relationship("Settlement", back_populates="settled_by_user")


class Orchard(Base):
    __tablename__ = "orchards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String(200))
    area = Column(Float)
    crop_type = Column(String(50))
    gps_lat = Column(Float)
    gps_lng = Column(Float)
    address = Column(String(300))
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="orchards")
    contracts = relationship("Contract", back_populates="orchard")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(50), unique=True, nullable=False)
    orchard_id = Column(Integer, ForeignKey("orchards.id"), nullable=False)
    beekeeper_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hive_count = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    unit_price = Column(Float, nullable=False)
    penalty_clause = Column(Text)
    status = Column(String(20), default="draft")
    total_amount = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    orchard = relationship("Orchard", back_populates="contracts")
    beekeeper = relationship("User", back_populates="contracts_as_beekeeper", foreign_keys=[beekeeper_id])
    hives = relationship("Hive", back_populates="contract")
    anomalies = relationship("Anomaly", back_populates="contract")
    settlements = relationship("Settlement", back_populates="contract")


class Hive(Base):
    __tablename__ = "hives"

    id = Column(Integer, primary_key=True, index=True)
    hive_no = Column(String(50), unique=True, nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    gps_lat = Column(Float)
    gps_lng = Column(Float)
    status = Column(String(20), default="idle")
    last_inspection_at = Column(DateTime)
    deployed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    contract = relationship("Contract", back_populates="hives")
    inspections = relationship("Inspection", back_populates="hive", order_by="Inspection.inspected_at.desc()")
    anomalies = relationship("Anomaly", back_populates="hive")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    hive_id = Column(Integer, ForeignKey("hives.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    colony_strength = Column(Integer, nullable=False)
    disease_found = Column(Boolean, default=False)
    disease_detail = Column(Text)
    feeding_needed = Column(Boolean, default=False)
    feeding_detail = Column(Text)
    photos = Column(Text)
    notes = Column(Text)
    inspected_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    hive = relationship("Hive", back_populates="inspections")
    inspector = relationship("User", back_populates="inspections")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    hive_id = Column(Integer, ForeignKey("hives.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(30), nullable=False)
    description = Column(Text)
    severity = Column(String(10), nullable=False)
    status = Column(String(20), default="reported")
    resolved_at = Column(DateTime)
    resolution = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    hive = relationship("Hive", back_populates="anomalies")
    contract = relationship("Contract", back_populates="anomalies")
    reporter = relationship("User", back_populates="reported_anomalies")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    total_hive_days = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    base_amount = Column(Float, nullable=False)
    anomaly_deduction = Column(Float, default=0)
    penalty_deduction = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    settled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    settled_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    contract = relationship("Contract", back_populates="settlements")
    settled_by_user = relationship("User", back_populates="settled_settlements")
