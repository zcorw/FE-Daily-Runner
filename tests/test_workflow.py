from datetime import date
from pathlib import Path
from typing import Any

from fe_daily.config import RunMode, load_settings
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
                    "explanation": f"Explanation {index}",
                    "images": [{"publicPath": f"/assets/fe-siken/q{index}.png"}],
                }
                for index, url in enumerate(urls, start=1)
            ]
        }


class FakeGenerator:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        self.payload = payload
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
                "terms": [{"term": f"term-{index}", "meaning": "meaning"} for index in range(10)],
                "knowledge_points": [{"title": "SQL", "body": "Group rows."}],
                "questions": [
                    {
                        "source_url": question["source_url"],
                        "question_text": question["question_text"],
                        "choices": question["choices"],
                        "answer": question["answer"],
                        "explanation": question["explanation"],
                        "images": question["images"],
                    }
                    for question in payload["questions"]
                ],
                "review_table_template": [{"question_no": index} for index in range(1, 11)],
                "tomorrow_suggestion": {"theme": "Transactions"},
            }
        )


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
