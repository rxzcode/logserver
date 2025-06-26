import re

from pydantic import BaseModel, Field, validator
from typing import List, Generic, TypeVar, Optional, Any
from pydantic.generics import GenericModel
from datetime import datetime

T = TypeVar("T")
class ResponseWrapper(GenericModel, Generic[T]):
    code: int
    msg: str
    data: T

class TenantEntry(BaseModel):
    key: str = Field(..., description="Tenant Key")
    name: str = Field(..., description="Tenant Name")

    @validator("key")
    def validate_key_format(cls, v):
        if not re.fullmatch(r"[a-z0-9_-]+", v):
            raise ValueError("Key must be lowercase alphanumeric with dashes or underscores (no spaces or special characters)")
        return v

class Tenant(BaseModel):
    name: str
    key: str
    secret: str
    created_at: datetime
