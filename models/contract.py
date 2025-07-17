from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Contract:
    id: int
    contract_name: str
    contract_number: str
    status: str
    link: str