"""Check local Markdown link targets without network access or application services.

Checks inline/image links and reference definitions in tracked or trackable Markdown.
External URLs, site-root routes, and fragment identifiers are not validated.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^\n)]*)?\)")
REFERENCE_LINK = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
INLINE_CODE = re.compile(r"(`+).*?\1")
ESCAPED_PUNCTUATION = re.compile(r"\\([\\`*{}\[\]()#+\-.!_<>])")


@dataclass(frozen=True)
class LinkIssue:
    document: str
    line: int
    target: str
    reason: str


def links_in_markdown(content: str) -> list[tuple[int, str]]:
    links = []
    fence = None
    for number, line in enumerate(content.splitlines(), 1):
        marker = FENCE.match(line)
        if marker:
            token, trailing = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not trailing.strip():
                fence = None
            continue
        if fence is not None:
            continue
        line = INLINE_CODE.sub("", line)
        reference = REFERENCE_LINK.match(line)
        matches = [reference] if reference else list(INLINE_LINK.finditer(line))
        for match in matches:
            target = match.group(1).removeprefix("<").removesuffix(">")
            links.append((number, ESCAPED_PUNCTUATION.sub(r"\1", target)))
    return links


def check_document(root: Path, document: Path, public_paths: set[str] | None = None) -> list[LinkIssue]:
    root = root.resolve()
    document = document.resolve()
    issues = []
    for line, target in links_in_markdown(document.read_text(encoding="utf-8")):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
            continue
        path = (document.parent / unquote(parsed.path)).resolve()
        reason = None
        if not path.is_relative_to(root):
            reason = "target leaves the repository"
        elif not path.exists():
            reason = "target does not exist"
        elif public_paths is not None:
            relative = path.relative_to(root).as_posix()
            if path.is_file() and relative not in public_paths:
                reason = "target is not tracked or trackable"
            elif path.is_dir():
                prefix = "" if path == root else relative + "/"
                if not any(name.startswith(prefix) for name in public_paths):
                    reason = "directory has no tracked or trackable files"
        if reason:
            issues.append(LinkIssue(document.relative_to(root).as_posix(), line, target, reason))
    return issues


def repository_paths(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return {
        name
        for name in result.stdout.decode("utf-8").split("\0")
        if name and (root / name).is_file()
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    public_paths = repository_paths(root)
    documents = sorted(name for name in public_paths if name.endswith(".md"))
    issues = [issue for name in documents for issue in check_document(root, root / name, public_paths)]
    for issue in issues:
        print(f"{issue.document}:{issue.line}: {issue.target} — {issue.reason}")
    print(f"Checked {len(documents)} Markdown documents; {len(issues)} broken local link(s).")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
