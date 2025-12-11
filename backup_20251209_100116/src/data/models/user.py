"""User model"""
from dataclasses import dataclass


@dataclass
class User:
    id: int = 0
    username: str = ""
    password_hash: str = ""
    role: str = ""
    is_active: bool = True
