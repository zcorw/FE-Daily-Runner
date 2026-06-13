import re
from urllib.parse import urlparse


ASSET_MARKER = "/assets/fe-siken/"
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")


class ImagePathError(ValueError):
    pass


def normalize_image_src(src: str) -> str:
    value = src.strip()
    parsed = urlparse(value)

    if value.startswith(ASSET_MARKER):
        normalized = value
        _validate_public_asset_path(normalized)
        return normalized

    if parsed.scheme and parsed.netloc and ASSET_MARKER in parsed.path:
        normalized = parsed.path[parsed.path.find(ASSET_MARKER) :]
        _validate_public_asset_path(normalized)
        return normalized

    raise ImagePathError(f"image path is not a public FE asset path: {src}")


def normalize_markdown_image_paths(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        alt = match.group("alt")
        src = match.group("src")
        return f"![{alt}]({normalize_image_src(src)})"

    return MARKDOWN_IMAGE_PATTERN.sub(replace, markdown)


def _validate_public_asset_path(path: str) -> None:
    if not path.startswith(ASSET_MARKER):
        raise ImagePathError(f"image path must start with {ASSET_MARKER}")

    parsed = urlparse(path)
    parts = [part for part in parsed.path.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise ImagePathError(f"image path must not contain traversal segments: {path}")
