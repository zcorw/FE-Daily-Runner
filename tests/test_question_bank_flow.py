from datetime import date
from pathlib import Path
from typing import Any

from fe_daily.config import RunMode, load_settings
from fe_daily.output_schema import DailyLearningContent
from fe_daily.workflow import run_daily_workflow


ROOT = Path(__file__).resolve().parents[1]


class FlowQuestionClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def health(self) -> dict[str, Any]:
        self.calls.append("health")
        return {"ok": True}

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append("search")
        return {
            "questions": [
                {
                    "url": f"https://www.fe-siken.com/kakomon/sample/q{index}.html",
                    "examPart": "科目A",
                }
                for index in range(1, payload["limit"] + 1)
            ]
        }

    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        self.calls.append("details")
        assert include_answer is True
        assert include_explanation is True
        return {
            "questions": [
                {
                    "url": url,
                    "questionText": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta"},
                    "answer": "A",
                    "explanation": f"中文说明 {index}",
                    "images": [
                        {
                            "publicPath": (
                                "http://question-bank-runtime:8000"
                                f"/assets/fe-siken/sample/q{index}.png"
                            )
                        }
                    ],
                }
                for index, url in enumerate(urls, start=1)
            ]
        }


class FlowGenerator:
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
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


def test_documented_query_flow_normalizes_runtime_asset_urls_for_browser_output(tmp_path):
    plan_path = tmp_path / "study.md"
    plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-13 | Database aggregation | Ch.4.3 SQL p.129-133 | SQL 10 |",
            ]
        ),
        encoding="utf-8",
    )
    settings = load_settings(_env_file=None, output_dir=tmp_path / "site", template_dir=ROOT / "templates")
    question_client = FlowQuestionClient()

    result = run_daily_workflow(
        settings=settings,
        target_date=date(2026, 6, 13),
        run_mode=RunMode.DRY_RUN,
        plan_path=plan_path,
        weak_points="- SQL",
        mistake_log="- GROUP BY",
        recent_progress="- DB",
        question_client=question_client,
        generator=FlowGenerator(),
    )

    assert question_client.calls == ["health", "search", "details"]
    assert result.dry_run_artifacts is not None
    html = result.dry_run_artifacts.preview_html.read_text(encoding="utf-8")
    assert "/assets/fe-siken/sample/q1.png" in html
    assert "question-bank-runtime" not in html
