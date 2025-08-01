from typing import (
    Protocol, TypeVar, Generic, Any, Dict, Optional, 
    Sequence, Type, runtime_checkable
)
from datetime import datetime
from sqlalchemy.engine.result import Result, ScalarResult
from sqlalchemy.sql.elements import ClauseElement

T = TypeVar('T')
ModelT = TypeVar('ModelT')

@runtime_checkable
class AsyncDatabaseProtocol(Protocol):
    """Protocol for async database operations"""
    async def execute(self, statement: ClauseElement) -> Result[Any]: ...
    async def scalar(self, statement: ClauseElement) -> Any: ...
    async def scalars(self, statement: ClauseElement) -> ScalarResult[Any]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def close(self) -> None: ...
    async def refresh(self, instance: Any) -> None: ...
    def add(self, instance: Any) -> None: ...
    def delete(self, instance: Any) -> None: ...
    async def flush(self, objects: Optional[Sequence[Any]] = None) -> None: ...
    
    @property
    def is_active(self) -> bool: ...

@runtime_checkable
class AsyncModelProtocol(Protocol[T]):
    """Protocol for async model operations"""
    id: int
    created_at: datetime
    
    @classmethod
    async def get_by_id(cls: Type[T], session: AsyncDatabaseProtocol, id: int) -> Optional[T]: ...
    
    @classmethod
    async def create(cls: Type[T], session: AsyncDatabaseProtocol, **kwargs: Any) -> T: ...
    
    async def update(self: T, session: AsyncDatabaseProtocol, **kwargs: Any) -> None: ...
    async def delete(self: T, session: AsyncDatabaseProtocol) -> None: ...
    def to_dict(self) -> Dict[str, Any]: ...

class DictConvertible(Protocol):
    """Protocol for objects that can be converted to dictionaries"""
    def to_dict(self) -> Dict[str, Any]: ...

class TimestampedModel(Protocol):
    """Protocol for models with timestamp fields"""
    created_at: datetime
    updated_at: Optional[datetime]

class IdentifiableModel(Protocol):
    """Protocol for models with ID fields"""
    id: int
