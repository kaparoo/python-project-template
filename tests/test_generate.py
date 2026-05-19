"""Tests for the copier template.

Generates projects with various copier answers and asserts on the rendered
output. Most tests run with `unsafe=False` to skip _tasks (which spend
time on `git init` and `uv sync`); a single integration test runs the
full pipeline to confirm tasks behave end-to-end.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import copier

if TYPE_CHECKING:
    from collections.abc import Mapping


TEMPLATE_ROOT = Path(__file__).parent.parent


def _generate(
    dst: Path,
    data: Mapping[str, object] | None = None,
    *,
    run_tasks: bool = False,
) -> Path:
    """Render the template into dst with given answers.

    `unsafe=True` acknowledges the template declares `_tasks`;
    `skip_tasks` controls whether they actually execute.
    """
    answers: dict[str, object] = {"project_name": "test-app"}
    if data:
        answers.update(data)
    copier.run_copy(
        src_path=str(TEMPLATE_ROOT),
        dst_path=str(dst),
        data=answers,
        defaults=True,
        unsafe=True,
        skip_tasks=not run_tasks,
    )
    return dst


# ─── Structural tests — required files exist ───


def test_default_generation_creates_expected_files(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    expected = [
        "pyproject.toml",
        "LICENSE",
        "README.md",
        ".python-version",
        ".gitignore",
        ".vscode/settings.json",
        ".vscode/extensions.json",
        "AGENTS.md",
        "CLAUDE.md",
        "test_app/__init__.py",
        "test_app/py.typed",
        "tests/conftest.py",
        ".copier-answers.yml",
    ]
    missing = [path for path in expected if not (project / path).is_file()]
    assert not missing, f"Missing files: {missing}"


# ─── Variable substitution ───


def test_project_name_substituted_everywhere(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"project_name": "my-lib"})
    pyproject = (project / "pyproject.toml").read_text()
    assert 'name = "my-lib"' in pyproject
    assert 'module-name = "my_lib"' in pyproject
    assert 'known-first-party = ["my_lib"]' in pyproject
    assert (project / "my_lib" / "__init__.py").is_file()


def test_author_and_github_substituted(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {
            "author_name": "Jane Doe",
            "author_email": "jane@example.com",
            "github_username": "janedoe",
            "repo_name": "custom-repo",
        },
    )
    pyproject = (project / "pyproject.toml").read_text()
    assert '"Jane Doe"' in pyproject
    assert '"jane@example.com"' in pyproject
    assert "https://www.github.com/janedoe/custom-repo" in pyproject


def test_license_year_and_author(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {"license_year": 2030, "author_name": "Test User"},
    )
    license_text = (project / "LICENSE").read_text()
    assert "Copyright (c) 2030 Test User" in license_text


def test_python_version_propagates_to_all_locations(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"python_version": "3.13"})
    assert (project / ".python-version").read_text().strip() == "3.13"
    pyproject = (project / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.13"' in pyproject
    assert 'python-version = "3.13"' in pyproject
    assert "Python :: 3.13" in pyproject


# ─── Conditional features (use_numpy) ───


def test_default_excludes_numpy_everywhere(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    pyproject = (project / "pyproject.toml").read_text()
    extensions = (project / ".vscode" / "extensions.json").read_text()
    assert "numpy" not in pyproject
    assert '"ICN"' not in pyproject
    assert "datawrangler" not in extensions


def test_use_numpy_adds_dependency(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_numpy": True})
    pyproject = (project / "pyproject.toml").read_text()
    assert '"numpy>=2.0"' in pyproject


def test_use_numpy_adds_icn_rule(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_numpy": True})
    pyproject = (project / "pyproject.toml").read_text()
    assert '"ICN"' in pyproject


def test_use_numpy_adds_datawrangler_extension(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_numpy": True})
    extensions = (project / ".vscode" / "extensions.json").read_text()
    assert "ms-toolsai.datawrangler" in extensions


# ─── Answers file ───


def test_answers_file_records_all_inputs(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {"project_name": "answers-test", "use_numpy": True, "python_version": "3.12"},
    )
    answers = (project / ".copier-answers.yml").read_text()
    assert "project_name: answers-test" in answers
    assert "use_numpy: true" in answers
    assert "python_version: '3.12'" in answers


# ─── Integration: full pipeline with _tasks ───


def test_tasks_initialize_git_repo_with_initial_commit(tmp_path: Path) -> None:
    """End-to-end: _tasks should produce a git repo on `main` with one commit."""
    project = _generate(tmp_path, run_tasks=True)
    assert (project / ".git").is_dir()
    assert (project / "uv.lock").is_file()

    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert "Initial commit from copier template" in log.stdout

    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert branch.stdout.strip() == "main"
