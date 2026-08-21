from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuestionCategory(StrEnum):
    RISK = "RISK"
    FOCUS = "FOCUS"
    ENERGY = "ENERGY"
    LEARNING = "LEARNING"
    ACTION = "ACTION"


class CheckinStatus(StrEnum):
    ASKED = "asked"
    ANSWERED = "answered"


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
    question_id: UUID
    category: QuestionCategory
    text: str
    order: int


class AskCheckinResponse(BaseModel):
    checkin_id: UUID
    date: date
    selected_questions: list[SelectedQuestion]


class QuestionPoolItem(BaseModel):
    id: UUID
    category: QuestionCategory
    text: str
    weight: float
    trigger_tags: list[str]
    cooldown_days: int


class AnswerItem(BaseModel):
    question_id: UUID
    answer_text: str = Field(min_length=1)


class AnswerCheckinRequest(BaseModel):
    checkin_id: UUID
    user_id: UUID
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


class HistoryItem(BaseModel):
    checkin_id: UUID
    date: date
    status: CheckinStatus


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class ArtifactResponse(BaseModel):
    checkin_id: UUID
    date: date
    day_summary: str
    insights: DayInsights
    recommended_actions: RecommendedActions
