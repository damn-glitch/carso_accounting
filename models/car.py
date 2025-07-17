# models/user.py
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from models.warranty_policy import WarrantyPolicy
from models.service_record import ServiceRecord
from models.contract import Contract


@dataclass
class Car:
    id: int
    vin: str
    brand: str
    model: str
    year: int
    warranty_policy: Optional[WarrantyPolicy] = None
    service_record_list: List[ServiceRecord] = field(default_factory=list)
    contract_response_dto_list: List[Contract] = field(default_factory=list)