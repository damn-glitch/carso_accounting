# models/user.py
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class User:
    id: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    enabled: bool = False
    attributes: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        # если в attributes есть собственное full_name
        fn = self.attributes.get("full_name")
        if isinstance(fn, list) and fn:
            return fn[0]
        # иначе первое + фамилия
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip()
