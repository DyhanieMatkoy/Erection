"""Reference models"""
from dataclasses import dataclass


@dataclass
class Counterparty:
    id: int = 0
    name: str = ""
    inn: str = ""
    contact_person: str = ""
    phone: str = ""
    marked_for_deletion: bool = False


@dataclass
class Object:
    id: int = 0
    name: str = ""
    owner_id: int = 0
    address: str = ""
    marked_for_deletion: bool = False


@dataclass
class Work:
    id: int = 0
    name: str = ""
    unit: str = ""
    price: float = 0.0
    labor_rate: float = 0.0
    marked_for_deletion: bool = False


@dataclass
class Person:
    id: int = 0
    full_name: str = ""
    position: str = ""
    phone: str = ""
    user_id: int = 0
    marked_for_deletion: bool = False


@dataclass
class Organization:
    id: int = 0
    name: str = ""
    inn: str = ""
    default_responsible_id: int = 0
    marked_for_deletion: bool = False
