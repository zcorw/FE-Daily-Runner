from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, WithJsonSchema, field_validator


class PlanReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    reading_assignment: str = Field(min_length=1)
    practice_focus: str = Field(min_length=1)


ChoiceMap = Annotated[
    dict[str, str],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["label", "text"],
                "additionalProperties": False,
            },
        }
    ),
]


class QuestionLearningBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_url: HttpUrl
    question_text: str = Field(min_length=1)
    choices: ChoiceMap = Field(min_length=1)
    answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    knowledge_point: str | None = None
    images: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("choices", mode="before")
    @classmethod
    def normalize_choice_list(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value

        normalized: dict[str, str] = {}
        for choice in value:
            if not isinstance(choice, dict):
                continue
            label = choice.get("label")
            text = choice.get("text")
            if isinstance(label, str) and isinstance(text, str):
                normalized[label] = text
        return normalized


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
