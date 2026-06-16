import json
from datetime import datetime, timezone
from pathlib import Path
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
        payload_text = json.dumps(payload, ensure_ascii=False)
        schema = _openai_json_schema(DailyLearningContent.model_json_schema())
        response = self.client.responses.create(
            model=self.settings.openai_model,
            reasoning={"effort": self.settings.openai_reasoning_effort},
            text={
                "verbosity": self.settings.openai_text_verbosity,
                "format": {
                    "type": "json_schema",
                    "name": "daily_learning_content",
                    "schema": schema,
                    "strict": True,
                },
            },
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": payload_text,
                        }
                    ],
                }
            ],
        )
        _append_token_usage_log(
            log_path=self.settings.openai_token_usage_log_path,
            payload=payload,
            payload_text=payload_text,
            schema=schema,
            settings=self.settings,
            response=response,
        )
        return response


def _openai_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return _strict_json_schema(_inline_local_refs(schema, schema.get("$defs", {})))


def _inline_local_refs(schema: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(schema, list):
        return [_inline_local_refs(item, definitions) for item in schema]
    if not isinstance(schema, dict):
        return schema

    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        name = ref.removeprefix("#/$defs/")
        resolved = definitions[name]
        return _inline_local_refs({**resolved, **{key: value for key, value in schema.items() if key != "$ref"}}, definitions)

    return {
        key: _inline_local_refs(value, definitions)
        for key, value in schema.items()
        if key != "$defs"
    }


def _strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    schema.pop("format", None)
    schema.pop("minProperties", None)

    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        if isinstance(schema.get("properties"), dict):
            schema["required"] = list(schema["properties"].keys())

    for value in schema.values():
        if isinstance(value, dict):
            _strict_json_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _strict_json_schema(item)

    return schema


def _append_token_usage_log(
    *,
    log_path: str | Path,
    payload: dict[str, Any],
    payload_text: str,
    schema: dict[str, Any],
    settings: DailyRunnerSettings,
    response: Any,
) -> None:
    usage = _usage_payload(getattr(response, "usage", None))
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plan_date": _nested_value(payload, "plan", "date"),
        "main_theme": _nested_value(payload, "plan", "main_theme"),
        "model": settings.openai_model,
        "reasoning_effort": settings.openai_reasoning_effort,
        "text_verbosity": settings.openai_text_verbosity,
        "usage": usage,
        "request_shape": {
            "question_count": len(payload.get("questions", [])) if isinstance(payload.get("questions"), list) else None,
            "payload_json_chars": len(payload_text),
            "schema_json_chars": len(json.dumps(schema, ensure_ascii=False)),
            "has_previous_validation_error": "previous_validation_error" in payload,
            "has_previous_content_validation_error": "previous_content_validation_error" in payload,
        },
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _usage_payload(usage: Any) -> dict[str, int | None]:
    output_details = _value(usage, "output_tokens_details")
    input_details = _value(usage, "input_tokens_details")
    return {
        "input_tokens": _value(usage, "input_tokens"),
        "output_tokens": _value(usage, "output_tokens"),
        "reasoning_tokens": _value(output_details, "reasoning_tokens"),
        "cached_input_tokens": _value(input_details, "cached_tokens"),
        "total_tokens": _value(usage, "total_tokens"),
    }


def _value(source: Any, key: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _nested_value(source: dict[str, Any], *keys: str) -> Any:
    current: Any = source
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
