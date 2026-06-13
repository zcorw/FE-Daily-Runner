import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from fe_daily.paths import ensure_within_base


@dataclass(frozen=True)
class DryRunArtifactPaths:
    raw_json: Path
    validated_json: Path
    preview_html: Path


def write_dry_run_artifacts(
    *,
    output_dir: Path,
    target_date: date,
    raw_output: dict[str, Any],
    validated_output: dict[str, Any],
    preview_html: str,
) -> DryRunArtifactPaths:
    base = Path(output_dir)
    target_root = ensure_within_base(
        base,
        base / "tmp" / "dry-run" / f"{target_date:%Y-%m-%d}",
    )
    target_root.mkdir(parents=True, exist_ok=True)

    paths = DryRunArtifactPaths(
        raw_json=target_root / "raw-openai-output.json",
        validated_json=target_root / "validated-output.json",
        preview_html=target_root / "preview.html",
    )

    paths.raw_json.write_text(json.dumps(raw_output, ensure_ascii=False, indent=2), encoding="utf-8")
    paths.validated_json.write_text(
        json.dumps(validated_output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths.preview_html.write_text(preview_html, encoding="utf-8")
    return paths
