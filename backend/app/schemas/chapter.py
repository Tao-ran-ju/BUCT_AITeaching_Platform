from pydantic import BaseModel, ConfigDict


class ChapterBase(BaseModel):
    name: str
    sort: int = 0


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(ChapterBase):
    pass


class ChapterOut(ChapterBase):
    id: int
    course_id: int

    model_config = ConfigDict(from_attributes=True)

