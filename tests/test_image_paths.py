import pytest

from fe_daily.image_paths import ImagePathError, normalize_image_src, normalize_markdown_image_paths


def test_normalize_image_src_keeps_public_asset_path():
    assert normalize_image_src("/assets/fe-siken/r7/q1.png") == "/assets/fe-siken/r7/q1.png"


def test_normalize_image_src_strips_runtime_origin():
    assert (
        normalize_image_src("http://question-bank-runtime:8000/assets/fe-siken/r7/q1.png")
        == "/assets/fe-siken/r7/q1.png"
    )


def test_normalize_image_src_rejects_local_filesystem_path():
    with pytest.raises(ImagePathError):
        normalize_image_src("docs/assets/fe-siken/r7/q1.png")


def test_normalize_image_src_rejects_path_traversal():
    with pytest.raises(ImagePathError):
        normalize_image_src("/assets/fe-siken/../secret.png")


def test_normalize_markdown_image_paths_rewrites_runtime_urls():
    markdown = "![q](http://question-bank-runtime:8000/assets/fe-siken/r7/q1.png)"

    assert normalize_markdown_image_paths(markdown) == "![q](/assets/fe-siken/r7/q1.png)"


def test_normalize_markdown_image_paths_rejects_local_paths():
    with pytest.raises(ImagePathError):
        normalize_markdown_image_paths("![q](docs/assets/fe-siken/r7/q1.png)")
