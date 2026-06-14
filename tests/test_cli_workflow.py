from datetime import date
from pathlib import Path
from typing import Any

from fe_daily.cli import main
from fe_daily.output_schema import DailyLearningContent
from fe_daily.paths import daily_page_path


ROOT = Path(__file__).resolve().parents[1]


class FakeQuestionClient:
    def health(self) -> dict[str, Any]:
        return {"ok": True}

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
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
        return {
            "questions": [
                {
                    "url": url,
                    "questionText": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta"},
                    "answer": "A",
                    "explanation": f"Explanation {index}",
                    "images": [{"publicPath": f"/assets/fe-siken/sample/q{index}.png"}],
                }
                for index, url in enumerate(urls, start=1)
            ]
        }


class FakeGenerator:
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


def test_cli_dry_run_executes_workflow_and_writes_only_preview_artifacts(tmp_path):
    paths = write_input_documents(tmp_path)
    output_dir = tmp_path / "site"

    exit_code = main(
        ["--date", "2026-06-13", "--dry-run"],
        settings_overrides={
            "_env_file": None,
            "output_dir": output_dir,
            "template_dir": ROOT / "templates",
            **paths,
        },
        question_bank_client_factory=lambda _settings: FakeQuestionClient(),
        generator_factory=lambda _settings: FakeGenerator(),
    )

    dry_run_root = output_dir / "tmp" / "dry-run" / "2026-06-13"
    assert exit_code == 0
    assert (dry_run_root / "raw-openai-output.json").exists()
    assert (dry_run_root / "validated-output.json").exists()
    assert (dry_run_root / "preview.html").exists()
    assert not daily_page_path(output_dir, date(2026, 6, 13)).exists()


def test_cli_write_executes_workflow_and_writes_formal_outputs(tmp_path):
    paths = write_input_documents(tmp_path)
    output_dir = tmp_path / "site"

    exit_code = main(
        ["--date", "2026-06-13", "--write"],
        settings_overrides={
            "_env_file": None,
            "output_dir": output_dir,
            "template_dir": ROOT / "templates",
            **paths,
        },
        question_bank_client_factory=lambda _settings: FakeQuestionClient(),
        generator_factory=lambda _settings: FakeGenerator(),
    )

    daily_page = daily_page_path(output_dir, date(2026, 6, 13))
    html = daily_page.read_text(encoding="utf-8")
    assert exit_code == 0
    assert daily_page.exists()
    assert html.count("data-question=") == 10
    assert (output_dir / "index.html").exists()
    assert (tmp_path / "personal" / "progress.md").exists()
    assert (tmp_path / "state" / "daily_state.json").exists()
    assert (tmp_path / "logs" / "daily_publish" / "2026-06-13.md").exists()


def write_input_documents(tmp_path: Path) -> dict[str, Any]:
    study_plan_path = tmp_path / "study.md"
    weak_points_path = tmp_path / "weak.md"
    mistake_log_path = tmp_path / "mistakes.md"
    progress_context_path = tmp_path / "progress.md"
    study_plan_path.write_text(
        "\n".join(
            [
                "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
                "|---|---|---|---|",
                "| 2026-06-13 | Database aggregation | Ch.4.3 SQL p.129-133 | SQL 10 |",
            ]
        ),
        encoding="utf-8",
    )
    weak_points_path.write_text("- SQL", encoding="utf-8")
    mistake_log_path.write_text("- GROUP BY", encoding="utf-8")
    progress_context_path.write_text("- DB", encoding="utf-8")
    return {
        "study_plan_path": study_plan_path,
        "weak_points_path": weak_points_path,
        "mistake_log_path": mistake_log_path,
        "progress_context_path": progress_context_path,
    }
