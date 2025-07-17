from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ServiceCenter:
    id: int
    name: str
    address: str
    contactPhone: str
    email: str