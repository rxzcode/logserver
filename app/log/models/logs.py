from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum
from pydantic.generics import GenericModel

# Enums
class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Response Wrapper
T = TypeVar("T")

class ResponseWrapper(GenericModel, Generic[T]):
    code: int
    msg: str
    data: T

class LogEntry(BaseModel):
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str]
    user_agent: Optional[str]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    severity: Severity

class Log(LogEntry):
    id: str
    user_id: str
    tenant_id: str
