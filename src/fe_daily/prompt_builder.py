import json
from typing import Any


FORBIDDEN_PROMPT_MARKERS = (
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "ADMIN_API_TOKEN",
    ".env",
)


class PromptBoundaryError(ValueError):
    pass


def build_generation_payload(
    *,
    plan: dict[str, Any],
    weak_points: str,
    progress_summary: str,
    mistake_log: str,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "plan": plan,
        "personal_context": {
            "weak_points": weak_points,
            "progress_summary": progress_summary,
            "mistake_log": mistake_log,
        },
        "daily_explanation_context": _daily_explanation_context(
            plan=plan,
            weak_points=weak_points,
            mistake_log=mistake_log,
            questions=questions,
        ),
        "generation_rules": {
            "openai_must_not_generate_question_content": True,
            "output_must_copy_plan_fields_exactly": [
                "date",
                "main_theme",
                "reading_assignment",
                "practice_focus",
            ],
            "page_structure_language": "Japanese",
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
            "page_format_reference": "FE Daily Study Task markdown",
            "minimum_key_terms": 10,
            "key_terms_table_fields": [
                "term",
                "meaning",
                "exam_note",
                "trap",
            ],
            "key_terms_must_have_unique_exam_notes_and_traps": True,
            "key_terms_instruction": (
                "Return at least 10 distinct key terms for the daily theme. Every key term must include "
                "a non-empty term, meaning, exam_note, and trap. The exam_note and trap values must be "
                "specific to that term, must not repeat across rows, and must be written in Japanese."
            ),
            "daily_explanation_instruction": (
                "Return 4 to 6 daily_explanation items for the section titled 今日知识点讲解. Use the "
                "reading assignment, concept focus, confusion pairs, and question knowledge summaries. "
                "Each item must explain one exam-relevant idea in 2 to 4 Japanese sentences. Do not copy "
                "or generate practice question text, choices, answers, or source URLs."
            ),
            "language_instruction": (
                "Write all generated learning content in Japanese. Do not generate practice questions, "
                "question text, choices, answers, explanations, or distractor explanations; those fields "
                "are injected from the Runtime question-bank response after OpenAI generation."
            ),
            "required_page_sections_in_order": [
                "今日の目標",
                "時間配分",
                "書籍の読解範囲",
                "学習チェックリスト",
                "重要用語",
                "今日知识点讲解",
                "知識メモ",
                "科目A 練習問題",
                "復習欄",
                "明日の提案",
            ],
            "openai_must_not_decide_paths_or_secrets": True,
            "python_validates_output_schema": True,
        },
    }
    _reject_forbidden_markers(payload)
    return payload


def _daily_explanation_context(
    *,
    plan: dict[str, Any],
    weak_points: str,
    mistake_log: str,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    concept_focus = _unique_non_blank(
        [
            *_split_focus_terms(str(plan.get("main_theme", ""))),
            *_split_focus_terms(str(plan.get("practice_focus", ""))),
            *_first_context_items(weak_points, limit=6),
            *_first_context_items(mistake_log, limit=4),
            *[
                str(question.get("knowledge_point") or question.get("knowledgePointJa") or "")
                for question in questions
            ],
        ],
        limit=16,
    )
    return {
        "book_section_context": {
            "reading_assignment": plan.get("reading_assignment", ""),
            "summary_instruction": (
                "Explain only the concepts implied by the assigned small book range. Keep the explanation "
                "aligned to the daily theme and avoid adding unrelated broad chapter content."
            ),
        },
        "concept_focus": concept_focus,
        "confusion_pairs": _confusion_pairs(concept_focus),
        "selected_question_summary": _selected_question_summary(questions),
    }


def _selected_question_summary(questions: list[dict[str, Any]]) -> list[dict[str, str]]:
    summaries: list[dict[str, str]] = []
    for index, question in enumerate(questions[:10], start=1):
        summary = {
            "question_no": str(index),
            "knowledge_point": _string_value(question, "knowledge_point", "knowledgePointJa"),
            "exam_point": _string_value(question, "exam_point", "examPointJa"),
            "common_trap": _string_value(question, "common_trap", "commonTrapJa"),
            "planned_bucket": _string_value(question, "planned_bucket", "plannedBucket"),
            "syllabus_area": _string_value(question, "syllabus_area", "syllabusArea"),
        }
        summaries.append({key: value for key, value in summary.items() if value})
    return summaries


def _string_value(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    learning = source.get("learningExplanation")
    if isinstance(learning, dict):
        for key in keys:
            value = learning.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _split_focus_terms(text: str) -> list[str]:
    terms: list[str] = []
    for raw in text.replace("/", ",").replace("・", ",").replace(" / ", ",").split(","):
        cleaned = raw.strip()
        if not cleaned:
            continue
        cleaned = cleaned.split(" ", 1)[0].strip()
        if cleaned:
            terms.append(cleaned)
    return terms


def _first_context_items(text: str, *, limit: int) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        item = line.strip().lstrip("-*").strip()
        if item:
            items.append(item)
        if len(items) >= limit:
            break
    return items


def _unique_non_blank(values: list[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique


def _confusion_pairs(concepts: list[str]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    pair_candidates = [
        ("WAF", "ファイアウォール"),
        ("IDS", "IPS"),
        ("SIEM", "UTM"),
        ("リスクアセスメント", "リスク対応"),
        ("認証", "暗号化"),
        ("DNS", "DHCP"),
        ("正規化", "トランザクション"),
    ]
    concepts_text = " ".join(concepts)
    for left, right in pair_candidates:
        if left in concepts_text or right in concepts_text:
            pairs.append({"left": left, "right": right})
    return pairs[:6]


def _reject_forbidden_markers(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False)
    for marker in FORBIDDEN_PROMPT_MARKERS:
        if marker in rendered:
            raise PromptBoundaryError(f"prompt payload contains forbidden marker: {marker}")
