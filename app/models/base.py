from typing import (
    Optional, Dict, Any, Type, TypeVar, Protocol,
    runtime_checkable, Generic, Union
)
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import Select
from sqlalchemy.engine import Result
from sqlalchemy import Integer, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

DBModel = TypeVar('DBModel', bound='DatabaseModel')
QueryType = Union[Select[Any], TextClause]

@runtime_checkable
class AsyncDatabase(Protocol):
    """Protocol defining async database operations"""
    async def execute(self, statement: QueryType) -> Result[Any]: ...
    async def scalar(self, statement: QueryType) -> Any: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def close(self) -> None: ...
    def add(self, instance: Any) -> None: ...
    def delete(self, instance: Any) -> None: ...
    async def flush(self) -> None: ...
    
    @property
    def is_active(self) -> bool: ...

class DatabaseOperations(ABC, Generic[DBModel]):
    """Abstract base class for database operations"""
    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[DBModel]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def create(self, **data: Any) -> DBModel:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, entity: DBModel, **data: Any) -> DBModel:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, entity: DBModel) -> None:
        """Delete entity"""
        pass

class DatabaseModel(DeclarativeBase):
    """Base class for all database models"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns  # type: ignore
        }
