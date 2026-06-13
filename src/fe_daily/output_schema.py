from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PlanReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    reading_assignment: str = Field(min_length=1)
    practice_focus: str = Field(min_length=1)


class QuestionLearningBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_url: HttpUrl
    question_text: str = Field(min_length=1)
    choices: dict[str, str] = Field(min_length=1)
    answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    knowledge_point: str | None = None
    images: list[dict[str, Any]] = Field(default_factory=list)


class DailyLearningContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: date
    title: str = Field(min_length=1)
    main_theme: str = Field(min_length=1)
    plan_reference: PlanReference
    goals: list[Any] = Field(default_factory=list)
    time_table: list[Any] = Field(default_factory=list)
    terms: list[Any] = Field(default_factory=list)
    knowledge_points: list[Any] = Field(default_factory=list)
    questions: list[QuestionLearningBlock] = Field(min_length=1)
    review_table_template: list[Any] = Field(default_factory=list)
    tomorrow_suggestion: dict[str, Any] = Field(default_factory=dict)
    progress_summary: dict[str, Any] = Field(default_factory=dict)
