"""Base domain entity for all grid components."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ComponentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


@dataclass
class BaseComponent(ABC):
    """Abstract base for every grid component (supply or demand)."""

    id: uuid.UUID
    name: str
    status: ComponentStatus
    unit: str
    description: str
    created_at: datetime
    updated_at: datetime

    @abstractmethod
    def get_type(self) -> str:
        """Return the component sub-type string (e.g. 'wind_turbine')."""
