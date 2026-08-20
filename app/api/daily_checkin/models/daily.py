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
    user_id: UUID
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


class AnswerItem(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=1)


class AnswerCheckinRequest(BaseModel):
    checkin_id: UUID
    answers: list[AnswerItem] = Field(min_length=5, max_length=5)


class DayInsights(BaseModel):
    top_risk_or_blocker: str
    top_strength: str
    learning_gap: str


class RecommendedActions(BaseModel):
    today_action: str
    two_checkpoints: list[str]


class AnswerCheckinResponse(BaseModel):
    checkin_id: UUID
    answers_received: bool
    day_summary: str
    insights: DayInsights
    recommended_actions: RecommendedActions
