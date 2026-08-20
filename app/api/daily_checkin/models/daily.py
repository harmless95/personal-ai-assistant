from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RequestState(BaseModel):
    stress_level: int = Field(ge=1, le=5)
    energy_level: int = Field(ge=1, le=5)
    plan_done: int = Field(ge=1, le=5)
    blocker_present: int = Field(ge=0, le=1)
    learning_done: int = Field(ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)


class AskCheckinRequest(BaseModel):
    user_id: int
    state: RequestState


class SelectedQuestion(BaseModel):
    question_id: str
    category: str
    text: str
    order: int


class AskCheckinResponse(BaseModel):
    checkin_id: UUID
    date: date
    selected_questions: list[SelectedQuestion]


class QuestionPoolItem(BaseModel):
    id: str
    category: str
    text: str
    weight: float
    trigger_tags: list[str]
    cooldown_days: int
