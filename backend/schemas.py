from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    real_name: str
    role: str
    phone: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str
    role: str
    phone: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class TokenData(BaseModel):
    user_id: int
    username: str
    role: str


class OrchardCreate(BaseModel):
    name: str
    owner_id: int
    location: Optional[str] = None
    area: Optional[float] = None
    crop_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    address: Optional[str] = None


class OrchardUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    area: Optional[float] = None
    crop_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    address: Optional[str] = None


class OrchardResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    location: Optional[str] = None
    area: Optional[float] = None
    crop_type: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrchardDetail(OrchardResponse):
    contracts: list["ContractResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class ContractCreate(BaseModel):
    orchard_id: int
    beekeeper_id: int
    hive_count: int
    start_date: datetime
    end_date: datetime
    unit_price: float
    penalty_clause: Optional[str] = None
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    hive_count: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    unit_price: Optional[float] = None
    penalty_clause: Optional[str] = None
    notes: Optional[str] = None


class ContractStatusUpdate(BaseModel):
    status: str


class ContractResponse(BaseModel):
    id: int
    contract_no: str
    orchard_id: int
    beekeeper_id: int
    hive_count: int
    start_date: datetime
    end_date: datetime
    unit_price: float
    penalty_clause: Optional[str] = None
    status: str
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    orchard_name: Optional[str] = None
    beekeeper_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContractDetail(ContractResponse):
    orchard: Optional[OrchardResponse] = None
    beekeeper: Optional[UserResponse] = None
    hives: list["HiveResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class HiveCreate(BaseModel):
    hive_no: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class HiveUpdate(BaseModel):
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    status: Optional[str] = None


class HiveDeploy(BaseModel):
    contract_id: int
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class HiveResponse(BaseModel):
    id: int
    hive_no: str
    contract_id: Optional[int] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    status: str
    last_inspection_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HiveDetail(HiveResponse):
    contract: Optional[ContractResponse] = None
    latest_inspection: Optional["InspectionResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class InspectionCreate(BaseModel):
    hive_id: int
    inspector_id: int
    colony_strength: int
    disease_found: bool = False
    disease_detail: Optional[str] = None
    feeding_needed: bool = False
    feeding_detail: Optional[str] = None
    photos: Optional[str] = None
    notes: Optional[str] = None
    inspected_at: Optional[datetime] = None


class InspectionResponse(BaseModel):
    id: int
    hive_id: int
    inspector_id: int
    colony_strength: int
    disease_found: bool
    disease_detail: Optional[str] = None
    feeding_needed: bool
    feeding_detail: Optional[str] = None
    photos: Optional[str] = None
    notes: Optional[str] = None
    inspected_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionDetail(InspectionResponse):
    hive: Optional[HiveResponse] = None
    inspector: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class OverdueHive(BaseModel):
    hive: HiveResponse
    contract: Optional[ContractResponse] = None
    days_overdue: int
    last_inspection_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnomalyCreate(BaseModel):
    hive_id: int
    contract_id: int
    type: str
    description: Optional[str] = None
    severity: str = "medium"


class AnomalyUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None


class AnomalyResolve(BaseModel):
    resolution: str
    restore_hive_status: bool = True


class AnomalyResponse(BaseModel):
    id: int
    hive_id: int
    contract_id: int
    reporter_id: int
    type: str
    description: Optional[str] = None
    severity: str
    status: str
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    created_at: datetime
    hive_no: Optional[str] = None
    contract_no: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnomalyDetail(AnomalyResponse):
    hive: Optional[HiveResponse] = None
    contract: Optional[ContractResponse] = None
    reporter: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementCreate(BaseModel):
    contract_id: int
    notes: Optional[str] = None


class SettlementConfirm(BaseModel):
    notes: Optional[str] = None


class SettlementPay(BaseModel):
    notes: Optional[str] = None


class SettlementResponse(BaseModel):
    id: int
    contract_id: int
    total_hive_days: int
    unit_price: float
    base_amount: float
    anomaly_deduction: float
    penalty_deduction: float
    total_amount: float
    status: str
    settled_by: Optional[int] = None
    settled_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    contract_no: Optional[str] = None
    orchard_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementDetail(SettlementResponse):
    contract: Optional[ContractResponse] = None
    settled_by_user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementPreview(BaseModel):
    contract_id: int
    total_hive_days: int
    unit_price: float
    base_amount: float
    anomaly_deduction: float
    penalty_deduction: float
    total_amount: float
    anomaly_count: int
    anomaly_details: list[dict]

    model_config = ConfigDict(from_attributes=True)


class AnomalyListItem(BaseModel):
    id: int
    hive_no: str
    type: str
    severity: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OverdueInspectionItem(BaseModel):
    hive_no: str
    location: Optional[str] = None
    last_inspection_at: Optional[datetime] = None
    days_overdue: int

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_contracts: int
    active_contracts: int
    total_hives: int
    deployed_hives: int
    pending_inspections: int
    pending_anomalies: int
    pending_settlements: int
    contracts_by_status: dict
    hives_by_status: dict
    anomalies_by_severity: dict
    recent_anomalies: list[AnomalyListItem] = []
    upcoming_inspections: list[OverdueInspectionItem] = []

    model_config = ConfigDict(from_attributes=True)
