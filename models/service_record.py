from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
from models.service_center import ServiceCenter
from models.contract import Contract

@dataclass
class ServiceRecord:
    id: int
    mileage: int
    service_type: str
    description: str
    car_id: int
    service_center_id: int
    # You may want to reference ServiceCenterResponseDTO here
    service_center: Optional[ServiceCenter] = None