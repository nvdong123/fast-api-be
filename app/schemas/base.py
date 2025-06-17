from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class BaseModelConfig(BaseModel):
    model_config = {"from_attributes": True}

class TimestampModel(BaseModelConfig):
    created_at: datetime
    updated_at: datetime

class UUIDModel(BaseModelConfig):
    id: UUID