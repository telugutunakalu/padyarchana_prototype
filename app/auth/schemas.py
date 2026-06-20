"""
Tiny auth schemas — used by templates and dependencies.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: str  # "admin" or "viewer"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
