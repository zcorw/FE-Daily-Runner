from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import shutil
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

from fe_daily.config import DailyRunnerSettings, RunMode
from fe_daily.content_validation import (
    ContentValidationError,
    validate_daily_html,
    validate_learning_content_quality,
    validate_question_facts,
)
from fe_daily.dry_run import DryRunArtifactPaths, write_dry_run_artifacts
from fe_daily.health_check import HealthStatus, check_runtime_health
from fe_daily.output_schema import DailyLearningContent, QuestionLearningBlock
from fe_daily.output_writer import atomic_write_text
from fe_daily.page_renderer import render_daily_page, render_index_page
from fe_daily.paths import ExistingOutputDecision, output_targets, resolve_existing_output
from fe_daily.progress_context import upsert_progress_entry
from fe_daily.prompt_builder import build_generation_payload
from fe_daily.question_details import load_required_details
from fe_daily.question_selection import (
    build_candidate_search_payloads,
    parse_practice_focus,
    select_subject_a_questions,
)
from fe_daily.study_plan import StudyPlanEntry, select_study_plan_entry
from fe_daily.run_log import write_run_log
from fe_daily.state import update_daily_state
from fe_daily.telegram_notifier import TelegramNotifier, render_telegram_message


class WorkflowQuestionClient(Protocol):
    def health(self) -> dict[str, Any]:
        pass

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        pass

    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        pass


class WorkflowGenerator(Protocol):
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        pass


class WorkflowNotifier(Protocol):
    def send_html_message(self, html: str) -> Any:
        pass


@dataclass(frozen=True)
class WorkflowResult:
    status: str
    target_date: date
    plan_source: str
    dry_run_artifacts: DryRunArtifactPaths | None = None
    notification_status: str = "not-run"


def run_daily_workflow(
    *,
    settings: DailyRunnerSettings,
    target_date: date,
    run_mode: RunMode,
    plan_path: str,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
    question_client: WorkflowQuestionClient,
    generator: WorkflowGenerator,
    telegram_notifier: WorkflowNotifier | None = None,
) -> WorkflowResult:
    target_paths = output_targets(settings.output_dir, target_date)
    if run_mode in (RunMode.WRITE, RunMode.NOTIFY):
        existing_decision = resolve_existing_output(target_paths.daily_page, settings.existing_page_policy)
        if existing_decision is ExistingOutputDecision.SKIP:
            return WorkflowResult(
                status="skipped",
                target_date=target_date,
                plan_source="not-run",
            )

    health = check_runtime_health(question_client)
    if health.status is not HealthStatus.OK:
        raise RuntimeError(health.message)

    plan_entry = select_study_plan_entry(
        plan_path,
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )
    plan_payload = _plan_payload(plan_entry)

    focus_targets = parse_practice_focus(plan_entry.practice_focus)
    candidate_payloads = build_candidate_search_payloads(focus_targets)
    candidate_groups = [
        question_client.search_candidates(payload).get("questions", [])
        for payload in candidate_payloads
    ]
    selected_questions = select_subject_a_questions(
        candidate_groups,
        required_count=10,
        focus_targets=focus_targets,
    )
    details = load_required_details(
        question_client,
        [question["url"] for question in selected_questions],
    )

    generation_payload = build_generation_payload(
        plan=plan_payload,
        weak_points=weak_points,
        progress_summary=recent_progress,
        mistake_log=mistake_log,
        questions=details,
    )
    page_url = _daily_page_url(target_date)
    content, html = _generate_validated_content(
        generator=generator,
        generation_payload=generation_payload,
        plan_entry=plan_entry,
        runtime_details=details,
        page_url=page_url,
        template_dir=settings.template_dir,
    )

    if run_mode is RunMode.DRY_RUN:
        artifacts = write_dry_run_artifacts(
            output_dir=settings.output_dir,
            target_date=target_date,
            raw_output=content.model_dump(mode="json"),
            validated_output=content.model_dump(mode="json"),
            preview_html=html,
        )
        return WorkflowResult(
            status="success",
            target_date=target_date,
            plan_source=plan_entry.plan_source,
            dry_run_artifacts=artifacts,
        )

    if run_mode in (RunMode.WRITE, RunMode.NOTIFY):
        atomic_write_text(target_paths.daily_page, html)
        workspace_root = settings.output_dir.parent
        index_html = render_index_page(
            [
                {
                    "date": target_date.isoformat(),
                    "title": content.main_theme,
                    "url": page_url,
                }
            ],
            current_strategy=plan_entry.practice_focus,
            updated_at=datetime.now(timezone.utc).isoformat(),
            template_dir=settings.template_dir,
        )
        atomic_write_text(target_paths.index_page, index_html)
        if settings.static_publish_dir is not None:
            _publish_static_site(settings.output_dir, settings.static_publish_dir)
        upsert_progress_entry(workspace_root / "personal" / "progress.md", content, page_url=page_url)
        update_daily_state(
            state_path=workspace_root / "state" / "daily_state.json",
            legacy_state_path=workspace_root / ".codex" / "daily_state.json",
            target_date=target_date,
            daily_page=page_url,
            topics=[content.main_theme],
            question_count=len(content.questions),
            status="success",
        )
        notification_status = "not-run"
        if run_mode is RunMode.NOTIFY and (
            settings.telegram_bot_token is None or settings.telegram_chat_id is None
        ):
            notification_status = "skipped: missing env"
        elif run_mode is RunMode.NOTIFY:
            notifier = telegram_notifier or TelegramNotifier(
                bot_token=settings.telegram_bot_token.get_secret_value(),
                chat_id=settings.telegram_chat_id.get_secret_value(),
            )
            message = render_telegram_message(
                date=target_date.isoformat(),
                main_theme=content.main_theme,
                page_url=_absolute_page_url(settings, page_url),
                template_dir=settings.template_dir,
            )
            send_result = notifier.send_html_message(message)
            notification_status = getattr(send_result, "status", "sent")
        write_run_log(
            log_root=workspace_root / "logs" / "daily_publish",
            target_date=target_date,
            started_at=datetime.now(timezone.utc),
            run_mode=run_mode.value,
            question_count=len(content.questions),
            output_paths=[str(target_paths.daily_page), str(target_paths.index_page)],
            plan_source=plan_entry.plan_source,
            notification_status=notification_status,
            status="success",
            errors=[],
        )
        return WorkflowResult(
            status="success",
            target_date=target_date,
            plan_source=plan_entry.plan_source,
            notification_status=notification_status,
        )

    raise NotImplementedError(f"workflow run mode is not implemented yet: {run_mode.value}")


def _publish_static_site(output_dir: Path | str, publish_dir: Path | str) -> None:
    source_root = Path(output_dir)
    target_root = Path(publish_dir)
    source_daily = source_root / "daily"
    source_index = source_root / "index.html"

    if source_daily.exists():
        _copy_directory_contents(source_daily, target_root)
    if source_index.exists():
        target_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_index, target_root / "index.html")

    _make_tree_readable(target_root)


def _copy_directory_contents(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, destination)


def _make_tree_readable(root: Path) -> None:
    if not root.exists():
        return
    for path in [root, *root.rglob("*")]:
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            path.chmod(0o644)


def _plan_payload(plan_entry: StudyPlanEntry) -> dict[str, Any]:
    return {
        "date": plan_entry.date.isoformat(),
        "main_theme": plan_entry.main_theme,
        "reading_assignment": plan_entry.reading_assignment,
        "practice_focus": plan_entry.practice_focus,
        "plan_source": plan_entry.plan_source,
    }


def _expected_plan(plan_entry: StudyPlanEntry) -> dict[str, Any]:
    return {
        "date": plan_entry.date.isoformat(),
        "main_theme": plan_entry.main_theme,
        "reading_assignment": plan_entry.reading_assignment,
        "practice_focus": plan_entry.practice_focus,
    }


def _restore_plan_fields(content: DailyLearningContent, plan_entry: StudyPlanEntry) -> None:
    content.date = plan_entry.date
    content.title = f"FE Daily Study Task - {plan_entry.date.isoformat()}"
    content.main_theme = plan_entry.main_theme
    content.plan_reference.date = plan_entry.date
    content.plan_reference.reading_assignment = plan_entry.reading_assignment
    content.plan_reference.practice_focus = plan_entry.practice_focus


def _generate_validated_content(
    *,
    generator: WorkflowGenerator,
    generation_payload: dict[str, Any],
    plan_entry: StudyPlanEntry,
    runtime_details: list[dict[str, Any]],
    page_url: str,
    template_dir: str | Path,
    max_attempts: int = 3,
) -> tuple[DailyLearningContent, str]:
    last_error: ContentValidationError | None = None
    for _ in range(max_attempts):
        request_payload = generation_payload
        if last_error is not None:
            request_payload = {
                **generation_payload,
                "previous_content_validation_error": str(last_error),
                "content_quality_requirements": _content_quality_requirements(),
                "instruction": (
                    "Previous content quality validation failed. Fix that exact issue while preserving "
                    "all Runtime question facts and the plan reference."
                ),
            }
        content = generator.generate(request_payload)
        _restore_plan_fields(content, plan_entry)
        _inject_runtime_questions(content, runtime_details)
        try:
            validate_question_facts(content, runtime_details)
            validate_learning_content_quality(content, _expected_plan(plan_entry))
            html = render_daily_page(content, page_url=page_url, template_dir=template_dir)
            validate_daily_html(html, content, page_url=page_url)
        except ContentValidationError as exc:
            last_error = exc
            continue
        return content, html

    if last_error is not None:
        raise last_error
    raise RuntimeError("content generation did not run")


def _inject_runtime_questions(content: DailyLearningContent, runtime_details: list[dict[str, Any]]) -> None:
    content.questions = [
        QuestionLearningBlock.model_validate(_question_block_from_runtime_detail(detail))
        for detail in runtime_details
    ]


def _question_block_from_runtime_detail(detail: dict[str, Any]) -> dict[str, Any]:
    choices = detail.get("choices")
    answer = detail.get("answer")
    distractor_explanations = _learning_field(
        detail,
        "distractor_explanations",
        "distractorExplanationsJa",
        default={},
    )
    return {
        "source_url": detail.get("url"),
        "question_text": detail.get("questionText"),
        "choices": choices,
        "answer": answer,
        "explanation": _learning_field(detail, "explanation", "explanationJa"),
        "knowledge_point": _learning_field(detail, "knowledge_point", "knowledgePointJa"),
        "distractor_explanations": _complete_distractor_explanations(
            choices,
            answer,
            distractor_explanations,
        ),
        "images": detail.get("images", []),
        "exam_point": _learning_field(detail, "exam_point", "examPointJa"),
        "common_trap": _learning_field(detail, "common_trap", "commonTrapJa"),
        "syllabus_area": detail.get("syllabusArea"),
        "topic_tags": detail.get("topicTags", []),
        "knowledge_points": detail.get("knowledgePoints", []),
    }


def _complete_distractor_explanations(
    choices: Any,
    answer: Any,
    explanations: Any,
) -> dict[str, str]:
    completed = dict(explanations) if isinstance(explanations, dict) else {}
    if not isinstance(choices, dict) or not isinstance(answer, str):
        return completed

    for label in choices:
        if label == answer or label in completed:
            continue
        completed[label] = f"{label}は正解ではありません。解説を確認し、正解との差を整理してください。"
    return completed


def _learning_field(
    detail: dict[str, Any],
    normalized_key: str,
    runtime_key: str,
    *,
    default: Any = None,
) -> Any:
    if normalized_key in detail and detail[normalized_key] is not None:
        return detail[normalized_key]
    if runtime_key in detail and detail[runtime_key] is not None:
        return detail[runtime_key]
    learning = detail.get("learningExplanation")
    if isinstance(learning, dict) and learning.get(runtime_key) is not None:
        return learning[runtime_key]
    return default


def _content_quality_requirements() -> dict[str, Any]:
    return {
        "minimum_key_terms": 10,
        "key_terms_table_fields": [
            "term",
            "meaning",
            "exam_note",
            "trap",
        ],
        "key_terms_instruction": (
            "Return at least 10 distinct key terms. Every key term must include a non-empty term, "
            "meaning, exam_note, and trap. The exam_note and trap values must be specific and must "
            "not repeat across rows. All generated learning text must be written in Japanese."
        ),
        "generated_learning_content_language": "Japanese",
        "japanese_content_fields": [
            "goals",
            "time_table.task",
            "terms.meaning",
            "terms.exam_note",
            "terms.trap",
            "daily_explanation.title",
            "daily_explanation.body",
            "knowledge_points.title",
            "knowledge_points.body",
            "tomorrow_suggestion.theme",
        ],
        "daily_explanation_instruction": (
            "Return 4 to 6 daily_explanation items. Every item must include a non-empty Japanese title "
            "and body, and must connect the day's reading assignment, weak points, and selected question "
            "knowledge summaries."
        ),
    }


def _absolute_page_url(settings: DailyRunnerSettings, page_url: str) -> str:
    if settings.page_base_url is None:
        return page_url
    base = _site_origin(settings.page_base_url)
    return base.rstrip("/") + page_url


def _daily_page_url(target_date: date) -> str:
    return f"/daily/{target_date:%Y/%m/%Y-%m-%d}/"


def _site_origin(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    return base_url
