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
                    "explanation": f"これは日本語の解説です {index}",
                    "distractor_explanations": {"B": f"Bは題庫の誤答解説です {index}"},
                    "knowledge_point": f"題庫知識点 {index}",
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
        assert "questions" not in payload
        return DailyLearningContent.model_validate(
            {
                "date": payload["plan"]["date"],
                "title": "FE Daily 学習タスク",
                "main_theme": payload["plan"]["main_theme"],
                "plan_reference": {
                    "date": payload["plan"]["date"],
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
