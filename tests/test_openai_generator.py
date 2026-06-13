import json
from types import SimpleNamespace

from fe_daily.config import load_settings
import pytest

from fe_daily.openai_generator import OpenAIGenerationError, OpenAIGenerator


def valid_content_payload():
    return {
        "date": "2026-06-13",
        "title": "Daily FE Study",
        "main_theme": "SQL",
        "plan_reference": {
            "date": "2026-06-13",
            "reading_assignment": "Ch.4.3 SQL p.129-133",
            "practice_focus": "SQL 10",
        },
        "questions": [
            {
                "source_url": "https://example.test/q1",
                "question_text": "Question text",
                "choices": {"ア": "A"},
                "answer": "ア",
                "explanation": "Explanation",
            }
        ],
    }


class FakeResponses:
    def __init__(self, response_payload):
        self.response_payload = response_payload
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(self.response_payload))


class FakeOpenAIClient:
    def __init__(self, response_payload):
        self.responses = FakeResponses(response_payload)


class SequenceResponses:
    def __init__(self, response_payloads):
        self.response_payloads = list(response_payloads)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(self.response_payloads.pop(0)))


class SequenceOpenAIClient:
    def __init__(self, response_payloads):
        self.responses = SequenceResponses(response_payloads)


def test_openai_generator_calls_responses_api_with_settings():
    settings = load_settings(
        _env_file=None,
        openai_model="gpt-test",
        openai_reasoning_effort="low",
        openai_text_verbosity="medium",
    )
    client = FakeOpenAIClient(valid_content_payload())
    generator = OpenAIGenerator(settings=settings, client=client)

    content = generator.generate({"plan": {"date": "2026-06-13"}})

    call = client.responses.calls[0]
    assert call["model"] == "gpt-test"
    assert call["reasoning"] == {"effort": "low"}
    assert call["text"]["verbosity"] == "medium"
    assert call["input"][0]["content"][0]["text"]
    assert content.main_theme == "SQL"


def test_openai_generator_parses_structured_json_output():
    settings = load_settings(_env_file=None)
    client = FakeOpenAIClient(valid_content_payload())
    generator = OpenAIGenerator(settings=settings, client=client)

    content = generator.generate({"plan": {"date": "2026-06-13"}})

    assert content.date.isoformat() == "2026-06-13"
    assert content.questions[0].answer == "ア"


def test_openai_generator_retries_once_with_validation_error_feedback():
    invalid_payload = {"date": "2026-06-13"}
    client = SequenceOpenAIClient([invalid_payload, valid_content_payload()])
    generator = OpenAIGenerator(settings=load_settings(_env_file=None), client=client)

    content = generator.generate({"plan": {"date": "2026-06-13"}})

    assert content.title == "Daily FE Study"
    assert len(client.responses.calls) == 2
    second_call_text = client.responses.calls[1]["input"][0]["content"][0]["text"]
    assert "Previous validation error" in second_call_text


def test_openai_generator_raises_after_second_invalid_output():
    invalid_payload = {"date": "2026-06-13"}
    client = SequenceOpenAIClient([invalid_payload, invalid_payload])
    generator = OpenAIGenerator(settings=load_settings(_env_file=None), client=client)

    with pytest.raises(OpenAIGenerationError):
        generator.generate({"plan": {"date": "2026-06-13"}})

    assert len(client.responses.calls) == 2
