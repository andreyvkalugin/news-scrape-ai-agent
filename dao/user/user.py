from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    telegram_id: int
    name: Optional[str] = None
    
