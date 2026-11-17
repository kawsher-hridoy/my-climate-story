from pathlib import Path

import pytest

from scripts.check_docs import check_document, links_in_markdown, repository_paths


def test_markdown_links_include_images_references_and_titles():
    content = '[Guide](docs/guide.md "Guide")\n![Preview](<docs/preview image.png>)\n[source]: docs/source.md\n'
    assert links_in_markdown(content) == [
        (1, "docs/guide.md"),
        (2, "docs/preview image.png"),
        (3, "docs/source.md"),
    ]


def test_links_in_fenced_examples_and_inline_code_are_not_checked():
    content = "```md\n[Example](not-a-file.md)\n```\n~~~text\n[Example](also-not-a-file.md)\n~~~\n`[Example](inline.md)`\n[Guide](guide.md)\n"
    assert links_in_markdown(content) == [(8, "guide.md")]


@pytest.mark.parametrize("target", ["https://example.com/page", "mailto:maintainer@example.com", "#section", "/api/v1/health/ready"])
def test_non_file_links_are_ignored(tmp_path, target):
    document = tmp_path / "README.md"
    document.write_text(f"[Link]({target})\n", encoding="utf-8")
    assert check_document(tmp_path, document) == []


def test_relative_links_resolve_from_the_document_directory(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (docs / "guide with spaces.md").write_text("# Guide\n", encoding="utf-8")
    document = docs / "README.md"
    document.write_text("[Project](../README.md#project)\n[Guide](guide%20with%20spaces.md)\n", encoding="utf-8")
    assert check_document(tmp_path, document) == []


def test_missing_target_reports_document_and_line(tmp_path):
    document = tmp_path / "README.md"
    document.write_text("# Project\n\n[Guide](missing.md)\n", encoding="utf-8")
    issue, = check_document(tmp_path, document)
    assert (issue.document, issue.line, issue.target, issue.reason) == (
        "README.md", 3, "missing.md", "target does not exist"
    )


def test_links_outside_the_repository_are_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (tmp_path / "private.md").write_text("private\n", encoding="utf-8")
    document = root / "README.md"
    document.write_text("[Private](../private.md)\n", encoding="utf-8")
    issue, = check_document(root, document)
    assert issue.reason == "target leaves the repository"


def test_existing_ignored_artifacts_are_not_public_link_targets(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "report.md").write_text("private\n", encoding="utf-8")
    document = tmp_path / "README.md"
    document.write_text("[Report](output/report.md)\n", encoding="utf-8")
    issue, = check_document(tmp_path, document, {"README.md"})
    assert issue.reason == "target is not tracked or trackable"


def test_directories_require_public_files(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
    document = tmp_path / "README.md"
    document.write_text("[Docs](docs/)\n", encoding="utf-8")
    assert check_document(tmp_path, document, {"README.md", "docs/guide.md"}) == []
    issue, = check_document(tmp_path, document, {"README.md"})
    assert issue.reason == "directory has no tracked or trackable files"


def test_repository_root_directory_can_be_linked(tmp_path):
    document = tmp_path / "README.md"
    document.write_text("[Project](.)\n", encoding="utf-8")
    assert check_document(tmp_path, document, {"README.md"}) == []


def test_repository_paths_exclude_working_notes_and_execution_artifacts():
    paths = repository_paths(Path(__file__).resolve().parents[1])
    assert "README.md" in paths
    excluded = {
        "AGENTS.md",
        "plan.md",
        "docs/code-review.md",
        "docs/review-fixes.md",
        "docs/verification.md",
        "docs/release-notes.md",
    }
    assert not paths.intersection(excluded)
    assert not any(name.startswith(("output/", "docs/evidence/")) for name in paths)
