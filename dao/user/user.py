from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: Optional[str] = None
    telegram_id: int
