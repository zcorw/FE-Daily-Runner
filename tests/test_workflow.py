from datetime import date
from pathlib import Path
from typing import Any

import pytest

from fe_daily.config import ExistingPagePolicy, RunMode, load_settings
from fe_daily.output_schema import DailyLearningContent
from fe_daily.paths import daily_page_path
from fe_daily.workflow import run_daily_workflow


ROOT = Path(__file__).resolve().parents[1]


class FakeQuestionClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def health(self) -> dict[str, Any]:
        self.calls.append("health")
        return {"ok": True}

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append("search_candidates")
        limit = payload["limit"]
        return {
            "questions": [
                {"url": f"https://example.test/q{index}", "examPart": payload["examPart"]}
                for index in range(1, limit + 1)
            ]
        }

    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        self.calls.append("details_batch")
        return {
            "questions": [
                {
                    "url": url,
                    "questionText": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta"},
                    "answer": "A",
                    "explanation": f"中文说明 {index}",
                    "images": [{"publicPath": f"/assets/fe-siken/q{index}.png"}],
                }
                for index, url in enumerate(urls, start=1)
            ]
        }


class FakeGenerator:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None
        self.payloads: list[dict[str, Any]] = []
        self.call_count = 0

    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        self.call_count += 1
        self.payload = payload
        self.payloads.append(payload)
        return DailyLearningContent.model_validate(
            {
                "date": payload["plan"]["date"],
                "title": "Daily FE Study",
                "main_theme": payload["plan"]["main_theme"],
                "plan_reference": {
                    "date": payload["plan"]["date"],
                    "reading_assignment": payload["plan"]["reading_assignment"],
                    "practice_focus": payload["plan"]["practice_focus"],
                },
                "goals": ["Practice subject A"],
                "time_table": [{"minutes": 60, "task": "Practice"}],
                "terms": [
                    {
                        "term": f"term-{index}",
                        "meaning": "meaning",
                        "exam_note": f"exam note {index}",
                        "trap": f"trap {index}",
                    }
                    for index in range(10)
                ],
                "knowledge_points": [{"title": "SQL", "body": "Group rows."}],
                "questions": [
                    {
                        "source_url": question["source_url"],
                        "question_text": question["question_text"],
                        "choices": question["choices"],
                        "answer": question["answer"],
                        "explanation": question["explanation"],
                        "distractor_explanations": {"B": "B不是正确选项"},
                        "images": question["images"],
                    }
                    for question in payload["questions"]
                ],
                "review_table_template": [{"question_no": index} for index in range(1, 11)],
                "tomorrow_suggestion": {"theme": "Transactions"},
            }
        )


class InvalidGenerator(FakeGenerator):
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        content = super().generate(payload)
        content.terms = content.terms[:9]
        return content


class FlakyQualityGenerator(FakeGenerator):
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        content = super().generate(payload)
        if self.call_count == 1:
            content.terms = content.terms[:8]
        return content


class PlanDriftGenerator(FakeGenerator):
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        content = super().generate(payload)
        content.title = "model rewritten title"
        content.main_theme = "model rewritten theme"
        content.plan_reference.reading_assignment = "model rewritten reading"
        content.plan_reference.practice_focus = "model rewritten focus"
        return content


class FakeNotifier:
    def __init__(self) -> None:
        self.call_count = 0

    def send_html_message(self, html: str) -> object:
        self.call_count += 1
        return type("SendResult", (), {"status": "sent"})()


def test_run_daily_workflow_dry_run_uses_full_chain_without_formal_write(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-13 | データベース: 集計・結合 | Ch.4.3 SQL p.129-133 | SQL 10 |",
            ]
        ),
        encoding="utf-8",
    )
    settings = load_settings(_env_file=None, output_dir=tmp_path / "site", template_dir=ROOT / "templates")
    question_client = FakeQuestionClient()
    generator = FakeGenerator()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.DRY_RUN,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=question_client,
        generator=generator,
    )

    assert result.status == "success"
    assert question_client.calls == ["health", "search_candidates", "details_batch"]
    assert generator.payload is not None
    assert len(generator.payload["questions"]) == 10
    assert result.dry_run_artifacts is not None
    assert result.dry_run_artifacts.preview_html.exists()
    assert not daily_page_path(settings.output_dir, date(2026, 6, 13)).exists()


def write_plan(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-13 | データベース: 集計・結合 | Ch.4.3 SQL p.129-133 | SQL 10 |",
            ]
        ),
        encoding="utf-8",
    )


def test_run_daily_workflow_skip_policy_does_not_call_openai_for_existing_page(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.SKIP,
    )
    target = daily_page_path(settings.output_dir, date(2026, 6, 13))
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    generator = FakeGenerator()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.WRITE,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=generator,
    )

    assert result.status == "skipped"
    assert generator.call_count == 0
    assert target.read_text(encoding="utf-8") == "existing"


def test_run_daily_workflow_restores_plan_fields_from_source(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(_env_file=None, output_dir=tmp_path / "site", template_dir=ROOT / "templates")

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.DRY_RUN,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=PlanDriftGenerator(),
    )

    assert result.status == "success"
    validated = result.dry_run_artifacts.validated_json.read_text(encoding="utf-8")
    assert "model rewritten theme" not in validated
    assert "model rewritten title" not in validated
    assert "FE Daily Study Task - 2026-06-13" in validated
    assert "model rewritten reading" not in validated
    assert "model rewritten focus" not in validated


def test_run_daily_workflow_retries_model_quality_failures(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(_env_file=None, output_dir=tmp_path / "site", template_dir=ROOT / "templates")
    generator = FlakyQualityGenerator()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.DRY_RUN,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=generator,
    )

    assert result.status == "success"
    assert generator.call_count == 2
    assert "previous_content_validation_error" in generator.payloads[1]
    assert "terms must contain at least 10 items" in generator.payloads[1]["previous_content_validation_error"]


def test_run_daily_workflow_fail_policy_raises_for_existing_page_before_openai(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.FAIL,
    )
    target = daily_page_path(settings.output_dir, date(2026, 6, 13))
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    generator = FakeGenerator()

    with pytest.raises(FileExistsError):
        run_daily_workflow(
            settings=settings,
            target_date=date(2026, 6, 13),
            run_mode=RunMode.WRITE,
            plan_path=plan_path,
            weak_points="- SQL",
            mistake_log="- GROUP BY",
            recent_progress="- DB",
            question_client=FakeQuestionClient(),
            generator=generator,
        )

    assert generator.call_count == 0


def test_run_daily_workflow_overwrite_policy_replaces_existing_page(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.OVERWRITE,
    )
    target = daily_page_path(settings.output_dir, date(2026, 6, 13))
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    generator = FakeGenerator()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.WRITE,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=generator,
    )

    assert result.status == "success"
    assert generator.call_count == 1
    text = target.read_text(encoding="utf-8")
    assert "existing" not in text
    assert "データベース: 集計・結合" in text


def test_run_daily_workflow_notify_skips_missing_telegram_config_after_write(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.OVERWRITE,
        telegram_bot_token=None,
        telegram_chat_id=None,
    )

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.NOTIFY,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=FakeGenerator(),
    )

    assert result.status == "success"
    assert result.notification_status == "skipped: missing env"
    assert daily_page_path(settings.output_dir, date(2026, 6, 13)).exists()


def test_run_daily_workflow_notify_records_final_notification_status(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.OVERWRITE,
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
    )
    notifier = FakeNotifier()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.NOTIFY,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=FakeGenerator(),
        telegram_notifier=notifier,
    )

    log_text = (tmp_path / "logs" / "daily_publish" / "2026-06-13.md").read_text(encoding="utf-8")
    assert result.notification_status == "sent"
    assert "notification_status: sent" in log_text


def test_run_daily_workflow_notify_does_not_send_when_validation_fails(tmp_path):
    plan_path = tmp_path / "june-study-plan.md"
    write_plan(plan_path)
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        existing_page_policy=ExistingPagePolicy.OVERWRITE,
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
    )
    notifier = FakeNotifier()

    with pytest.raises(ValueError):
        run_daily_workflow(
            settings=settings,
            target_date=date(2026, 6, 13),
            run_mode=RunMode.NOTIFY,
            plan_path=plan_path,
            weak_points="- SQL",
            mistake_log="- GROUP BY",
            recent_progress="- DB",
            question_client=FakeQuestionClient(),
            generator=InvalidGenerator(),
            telegram_notifier=notifier,
        )

    assert notifier.call_count == 0
    assert not daily_page_path(settings.output_dir, date(2026, 6, 13)).exists()
