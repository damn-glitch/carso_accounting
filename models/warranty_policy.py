from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class WarrantyPolicy:
    id: int
    created_time: datetime
    car_id: int
    end_time: datetime
    max_mileage: int
    # You may want to reference CarResponseDTO here