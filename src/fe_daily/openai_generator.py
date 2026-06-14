import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from fe_daily.config import DailyRunnerSettings
from fe_daily.output_schema import DailyLearningContent


class OpenAIGenerationError(RuntimeError):
    pass


class OpenAIGenerator:
    def __init__(self, *, settings: DailyRunnerSettings, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client or OpenAI(
            api_key=(
                settings.openai_api_key.get_secret_value()
                if settings.openai_api_key is not None
                else None
            )
        )

    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        last_error: ValidationError | None = None
        for attempt in range(2):
            request_payload = payload
            if last_error is not None:
                request_payload = {
                    **payload,
                    "previous_validation_error": str(last_error),
                    "instruction": "Previous validation error must be fixed. Return valid structured JSON.",
                }
            response = self._create_response(request_payload)
            raw_text = response.output_text
            try:
                return DailyLearningContent.model_validate_json(raw_text)
            except ValidationError as exc:
                last_error = exc
                if attempt == 1:
                    raise OpenAIGenerationError(
                        f"OpenAI structured output failed validation after retry: {exc}"
                    ) from exc

        raise OpenAIGenerationError("OpenAI structured output failed validation")

    def _create_response(self, payload: dict[str, Any]) -> Any:
        response = self.client.responses.create(
            model=self.settings.openai_model,
            reasoning={"effort": self.settings.openai_reasoning_effort},
            text={
                "verbosity": self.settings.openai_text_verbosity,
                "format": {
                    "type": "json_schema",
                    "name": "daily_learning_content",
                    "schema": _strict_json_schema(DailyLearningContent.model_json_schema()),
                    "strict": True,
                },
            },
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(payload, ensure_ascii=False),
                        }
                    ],
                }
            ],
        )
        return response


def _strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") == "object":
        schema["additionalProperties"] = False

    for value in schema.values():
        if isinstance(value, dict):
            _strict_json_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _strict_json_schema(item)

    return schema
