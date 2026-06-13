import json
from types import SimpleNamespace

from fe_daily.config import load_settings
from fe_daily.openai_generator import OpenAIGenerator


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
