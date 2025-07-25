from __future__ import annotations
from typing import TypeVar, Any
from app.models.models import Base

ModelType = TypeVar("ModelType", bound=Base)

def to_dict(obj: ModelType) -> dict[str, Any]:
    """Convert SQLAlchemy model instance to dictionary"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
