from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChapterBase(BaseModel):
    name: str

class ChapterCreate(ChapterBase):
    pass

class ChapterUpdate(BaseModel):
    name: Optional[str] = None

class ChapterOut(ChapterBase):
    id: int
    course_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

