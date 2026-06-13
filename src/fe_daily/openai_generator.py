import json
from typing import Any

from openai import OpenAI

from fe_daily.config import DailyRunnerSettings
from fe_daily.output_schema import DailyLearningContent


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
        response = self.client.responses.create(
            model=self.settings.openai_model,
            reasoning={"effort": self.settings.openai_reasoning_effort},
            text={
                "verbosity": self.settings.openai_text_verbosity,
                "format": {
                    "type": "json_schema",
                    "name": "daily_learning_content",
                    "schema": DailyLearningContent.model_json_schema(),
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
        raw_text = response.output_text
        return DailyLearningContent.model_validate_json(raw_text)
