import json
from types import SimpleNamespace

from fe_daily.config import load_settings
import pytest

from fe_daily.openai_generator import OpenAIGenerationError, OpenAIGenerator


@pytest.fixture(autouse=True)
def isolate_token_usage_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


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
                "distractor_explanations": {},
            }
        ],
    }


class FakeResponses:
    def __init__(self, response_payload, *, usage=None):
        self.response_payload = response_payload
        self.usage = usage
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(self.response_payload), usage=self.usage)


class FakeOpenAIClient:
    def __init__(self, response_payload, *, usage=None):
        self.responses = FakeResponses(response_payload, usage=usage)


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
    assert_objects_disallow_additional_properties(call["text"]["format"]["schema"])
    assert_schema_does_not_use_unsupported_format(call["text"]["format"]["schema"])
    assert_schema_does_not_use_min_properties(call["text"]["format"]["schema"])
    assert_object_required_lists_include_all_properties(call["text"]["format"]["schema"])
    assert_schema_does_not_use_refs(call["text"]["format"]["schema"])
    assert call["input"][0]["content"][0]["text"]
    assert content.main_theme == "SQL"


def test_openai_generator_parses_structured_json_output():
    settings = load_settings(_env_file=None)
    client = FakeOpenAIClient(valid_content_payload())
    generator = OpenAIGenerator(settings=settings, client=client)

    content = generator.generate({"plan": {"date": "2026-06-13"}})

    assert content.date.isoformat() == "2026-06-13"
    assert content.questions[0].answer == "ア"


def test_openai_generator_writes_token_usage_jsonl_without_prompt_text(tmp_path):
    usage = SimpleNamespace(
        input_tokens=1200,
        output_tokens=600,
        total_tokens=1800,
        output_tokens_details=SimpleNamespace(reasoning_tokens=90),
    )
    settings = load_settings(
        _env_file=None,
        openai_model="gpt-test",
        openai_reasoning_effort="medium",
        openai_text_verbosity="low",
        openai_token_usage_log_path=tmp_path / "logs" / "openai_token_usage.jsonl",
    )
    client = FakeOpenAIClient(valid_content_payload(), usage=usage)
    generator = OpenAIGenerator(settings=settings, client=client)

    generator.generate(
        {
            "plan": {"date": "2026-06-13", "main_theme": "SQL"},
            "questions": [{"source_url": "https://example.test/q1"}],
            "personal_context": {"weak_points": "secret personal note"},
        }
    )

    log_lines = settings.openai_token_usage_log_path.read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1
    record = json.loads(log_lines[0])
    assert record["plan_date"] == "2026-06-13"
    assert record["model"] == "gpt-test"
    assert record["reasoning_effort"] == "medium"
    assert record["text_verbosity"] == "low"
    assert record["usage"]["input_tokens"] == 1200
    assert record["usage"]["output_tokens"] == 600
    assert record["usage"]["reasoning_tokens"] == 90
    assert record["usage"]["total_tokens"] == 1800
    assert record["request_shape"]["question_count"] == 1
    assert record["request_shape"]["payload_json_chars"] > 0
    assert record["request_shape"]["schema_json_chars"] > 0
    assert "secret personal note" not in log_lines[0]
    assert "Question text" not in log_lines[0]


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


def assert_objects_disallow_additional_properties(schema):
    if not isinstance(schema, dict):
        return

    if schema.get("type") == "object":
        assert schema.get("additionalProperties") is False

    for value in schema.values():
        if isinstance(value, dict):
            assert_objects_disallow_additional_properties(value)
        elif isinstance(value, list):
            for item in value:
                assert_objects_disallow_additional_properties(item)


def assert_schema_does_not_use_unsupported_format(schema):
    if not isinstance(schema, dict):
        return

    assert "format" not in schema

    for value in schema.values():
        if isinstance(value, dict):
            assert_schema_does_not_use_unsupported_format(value)
        elif isinstance(value, list):
            for item in value:
                assert_schema_does_not_use_unsupported_format(item)


def assert_schema_does_not_use_min_properties(schema):
    if not isinstance(schema, dict):
        return

    assert "minProperties" not in schema

    for value in schema.values():
        if isinstance(value, dict):
            assert_schema_does_not_use_min_properties(value)
        elif isinstance(value, list):
            for item in value:
                assert_schema_does_not_use_min_properties(item)


def assert_object_required_lists_include_all_properties(schema):
    if not isinstance(schema, dict):
        return

    if schema.get("type") == "object" and isinstance(schema.get("properties"), dict):
        assert sorted(schema.get("required", [])) == sorted(schema["properties"].keys())

    for value in schema.values():
        if isinstance(value, dict):
            assert_object_required_lists_include_all_properties(value)
        elif isinstance(value, list):
            for item in value:
                assert_object_required_lists_include_all_properties(item)


def assert_schema_does_not_use_refs(schema):
    if not isinstance(schema, dict):
        return

    assert "$defs" not in schema
    assert "$ref" not in schema

    for value in schema.values():
        if isinstance(value, dict):
            assert_schema_does_not_use_refs(value)
        elif isinstance(value, list):
            for item in value:
                assert_schema_does_not_use_refs(item)
