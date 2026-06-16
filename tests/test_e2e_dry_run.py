from datetime import date
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from fe_daily.config import RunMode, load_settings
from fe_daily.output_schema import DailyLearningContent
from fe_daily.paths import daily_page_path
from fe_daily.workflow import run_daily_workflow


ROOT = Path(__file__).resolve().parents[1]


class FakeQuestionClient:
    def health(self) -> dict[str, Any]:
        return {"ok": True}

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "questions": [
                {"url": f"https://example.test/q{index}", "examPart": payload["examPart"]}
                for index in range(1, payload["limit"] + 1)
            ]
        }

    def details_batch(self, urls: list[str], *, include_answer: bool, include_explanation: bool) -> dict[str, Any]:
        return {
            "questions": [
                {
                    "url": url,
                    "questionText": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta"},
                    "answer": "A",
                    "explanation": f"これは日本語の解説です {index}",
                    "distractor_explanations": {"B": f"Bは題庫の誤答解説です {index}"},
                    "knowledge_point": f"題庫知識点 {index}",
                    "images": [{"publicPath": f"/assets/fe-siken/q{index}.png"}],
                }
                for index, url in enumerate(urls, start=1)
            ]
        }


class FakeGenerator:
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        assert "questions" not in payload
        return DailyLearningContent.model_validate(
            {
                "date": "2026-06-13",
                "title": "FE Daily 学習タスク",
                "main_theme": payload["plan"]["main_theme"],
                "plan_reference": {
                    "date": "2026-06-13",
                    "reading_assignment": payload["plan"]["reading_assignment"],
                    "practice_focus": payload["plan"]["practice_focus"],
                },
                "goals": ["科目Aの問題を練習する。"],
                "time_table": [{"minutes": 60, "task": "問題を解いて復習する"}],
                "terms": [
                    {
                        "term": f"term-{index}",
                        "meaning": "意味を確認する。",
                        "exam_note": f"試験での注意点 {index}",
                        "trap": f"混同しやすい点 {index}",
                    }
                    for index in range(10)
                ],
                "knowledge_points": [{"title": "SQLの要点", "body": "集計条件を確認する。"}],
                "questions": [],
                "review_table_template": [{"question_no": index} for index in range(1, 11)],
                "tomorrow_suggestion": {"theme": "トランザクション"},
            }
        )


class FakeNotifier:
    def __init__(self) -> None:
        self.call_count = 0
        self.messages: list[str] = []

    def send_html_message(self, html: str) -> object:
        self.call_count += 1
        self.messages.append(html)
        return object()


def test_e2e_dry_run_generates_artifacts_without_formal_page_or_telegram(tmp_path):
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
    notifier = FakeNotifier()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.DRY_RUN,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=FakeGenerator(),
        telegram_notifier=notifier,
    )

    assert result.status == "success"
    assert result.dry_run_artifacts is not None
    assert result.dry_run_artifacts.raw_json.exists()
    assert result.dry_run_artifacts.validated_json.exists()
    assert result.dry_run_artifacts.preview_html.exists()
    assert not daily_page_path(settings.output_dir, date(2026, 6, 13)).exists()
    assert notifier.call_count == 0


def test_e2e_write_generates_formal_outputs(tmp_path):
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

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.WRITE,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=FakeQuestionClient(),
        generator=FakeGenerator(),
    )

    daily_path = daily_page_path(settings.output_dir, date(2026, 6, 13))
    soup = BeautifulSoup(daily_path.read_text(encoding="utf-8"), "html.parser")

    assert result.status == "success"
    assert daily_path.exists()
    assert (settings.output_dir / "index.html").exists()
    assert (tmp_path / "personal" / "progress.md").exists()
    assert (tmp_path / "state" / "daily_state.json").exists()
    assert (tmp_path / "logs" / "daily_publish" / "2026-06-13.md").exists()
    assert len(soup.select("[data-question]")) == 10


def test_e2e_notify_sends_once_after_successful_write(tmp_path):
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
    settings = load_settings(
        _env_file=None,
        output_dir=tmp_path / "site",
        template_dir=ROOT / "templates",
        page_base_url="https://example.test",
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

    assert result.status == "success"
    assert notifier.call_count == 1
    assert "2026-06-13" in notifier.messages[0]
    assert "データベース: 集計・結合" in notifier.messages[0]
    assert "https://example.test/daily/2026-06-13/" in notifier.messages[0]
