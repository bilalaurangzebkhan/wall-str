from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Memo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_prompt: str
    sections: list["MemoSection"]


class MemoSection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group: str
    aspect: str
    content: str
    index: int
