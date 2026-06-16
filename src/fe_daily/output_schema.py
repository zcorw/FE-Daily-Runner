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
QuestionImages = Annotated[
    list[dict[str, Any]],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "publicPath": {"type": "string"},
                },
            },
        }
    ),
]
DistractorExplanations = Annotated[
    dict[str, str],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["label", "explanation"],
                "additionalProperties": False,
            },
        }
    ),
]

Goals = Annotated[list[Any], WithJsonSchema({"type": "array", "items": {"type": "string"}})]
TimeTable = Annotated[
    list[Any],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "minutes": {"type": "integer"},
                    "task": {"type": "string"},
                },
            },
        }
    ),
]
Terms = Annotated[
    list[Any],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "meaning": {"type": "string"},
                    "exam_note": {"type": "string"},
                    "trap": {"type": "string"},
                },
            },
        }
    ),
]
KnowledgePoints = Annotated[
    list[Any],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
        }
    ),
]
ReviewTable = Annotated[
    list[Any],
    WithJsonSchema(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_no": {"type": "integer"},
                },
            },
        }
    ),
]
TomorrowSuggestion = Annotated[
    dict[str, Any],
    WithJsonSchema(
        {
            "type": "object",
            "properties": {
                "theme": {"type": "string"},
            },
        }
    ),
]
ProgressSummary = Annotated[
    dict[str, Any],
    WithJsonSchema(
        {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
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
    distractor_explanations: DistractorExplanations = Field(default_factory=dict)
    images: QuestionImages = Field(default_factory=list)

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

    @field_validator("distractor_explanations", mode="before")
    @classmethod
    def normalize_distractor_explanation_list(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value

        normalized: dict[str, str] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            explanation = item.get("explanation")
            if isinstance(label, str) and isinstance(explanation, str):
                normalized[label] = explanation
        return normalized


class DailyLearningContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: date
    title: str = Field(min_length=1)
    main_theme: str = Field(min_length=1)
    plan_reference: PlanReference
    goals: Goals = Field(default_factory=list)
    time_table: TimeTable = Field(default_factory=list)
    terms: Terms = Field(default_factory=list)
    knowledge_points: KnowledgePoints = Field(default_factory=list)
    questions: list[QuestionLearningBlock] = Field(default_factory=list)
    review_table_template: ReviewTable = Field(default_factory=list)
    tomorrow_suggestion: TomorrowSuggestion = Field(default_factory=dict)
    progress_summary: ProgressSummary = Field(default_factory=dict)
