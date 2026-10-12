from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from tests.helpers import sections

if TYPE_CHECKING:
    from tests.helpers import Render

DOCS = ("AGENTS.md", "README.md", "CHANGELOG.md", "TODO.md")
GUIDES = (
    ".agents/changelog.md",
    ".agents/commits.md",
    ".agents/decisions.md",
    ".agents/dependencies.md",
    ".agents/readme.md",
    ".agents/releases.md",
    ".agents/todo.md",
    "tests/AGENTS.md",
)


def test_generated_changelog_skeleton(render: Render) -> None:
    project = render()
    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "# Changelog" in changelog
    assert "Keep a Changelog" in changelog
    assert "Semantic Versioning" in changelog
    assert "## [Unreleased]" in changelog
    assert "[Unreleased]: https://github.com/kaparoo/test-app/commits/main" in changelog


def test_include_todo_true_creates_todo_md_and_readme_link(render: Render) -> None:
    project = render({"include_todo": True})
    assert (project / "TODO.md").is_file()
    todo = (project / "TODO.md").read_text(encoding="utf-8")
    assert "# TODO" in todo
    assert "Open work that is not done yet" in todo
    assert "Promote" not in todo
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" in readme
    assert "[TODO.md](https://github.com/kaparoo/test-app/blob/main/TODO.md)" in readme


def test_include_todo_false_omits_todo_md_and_readme_link(render: Render) -> None:
    project = render({"include_todo": False})
    assert not (project / "TODO.md").exists()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" not in readme
    assert "TODO.md" not in readme


def test_readme_sections_for_library(render: Render) -> None:
    project = render()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert sections(readme) == [
        "## 📦 Installation",
        "## 🚀 Quick start",
        "## 🧩 Modules",
        "## 📋 TODO",
        "## 📜 Changelog",
        "## ⚖️ License",
    ]
    assert "uv add test-app" in readme
    assert "pip install test-app" in readme


def test_readme_sections_for_application(render: Render) -> None:
    project = render({"is_library": False})
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert sections(readme) == [
        "## 📦 Setup",
        "## 🚀 Usage",
        "## 📋 TODO",
        "## 📜 Changelog",
        "## ⚖️ License",
    ]
    assert "uv add test-app" not in readme
    assert "uv sync --group dev" in readme


def test_library_readme_links_repository_files_absolutely(render: Render) -> None:
    project = render()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# test-app\n")
    assert "](./" not in readme
    base = "https://github.com/kaparoo/test-app/blob/main"
    for target in ("LICENSE", "TODO.md", "CHANGELOG.md"):
        assert f"]({base}/{target})" in readme, f"missing link to {target}"


def test_application_readme_links_repository_files_relatively(
    render: Render,
) -> None:
    project = render({"is_library": False})
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# test-app\n")
    assert "https://github.com/kaparoo/test-app/blob/main" not in readme
    for target in ("LICENSE", "TODO.md", "CHANGELOG.md"):
        assert f"](./{target})" in readme, f"missing link to {target}"


@pytest.mark.parametrize(
    "answers",
    (
        {},
        {"release_automation": "github-oidc"},
        {"use_testpypi": False},
        {"is_library": False, "use_pytest": False, "include_todo": False},
    ),
)
def test_generated_markdown_wraps_prose_at_72_columns(
    render: Render, answers: dict[str, object]
) -> None:
    project = render(answers)
    too_wide = []
    for name in (*DOCS, *GUIDES):
        path = project / name
        if not path.exists():
            continue
        in_code = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            exempt = (
                in_code
                or stripped.startswith(("|", "#"))
                or "://" in line
                or re.fullmatch(r"`[^`]+`[.,]?", stripped) is not None
            )
            if not exempt and len(line) > 72:
                too_wide.append(f"{name}:{number}: {line}")
    assert not too_wide, "\n".join(too_wide)


@pytest.mark.parametrize(
    "answers",
    (
        {},
        {"release_automation": "github-oidc"},
        {"is_library": False, "use_pytest": False, "include_todo": False},
    ),
)
def test_generated_docs_use_no_em_dash(
    render: Render, answers: dict[str, object]
) -> None:
    project = render(answers)
    dashed = []
    for name in (*DOCS, *GUIDES, "pyproject.toml"):
        path = project / name
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prose = re.sub(r"`[^`]*`", "", line)
            if "\N{EM DASH}" in line or " -- " in prose:
                dashed.append(f"{name}:{number}: {line}")
    assert not dashed, "\n".join(dashed)


def test_generated_files_use_lf_line_endings(render: Render) -> None:
    project = render()
    crlf = [
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file() and b"\r\n" in path.read_bytes()
    ]
    assert not crlf, f"CRLF line endings in {crlf}"
