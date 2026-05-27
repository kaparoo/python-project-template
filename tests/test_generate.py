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
    `skip_tasks` controls whether they actually execute. `vcs_ref="HEAD"`
    renders the current commit — without it copier would prefer the
    latest tag and miss commits made after it.
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
        vcs_ref="HEAD",
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
        "tests/__init__.py",
        ".copier-answers.yml",
    ]
    missing = [path for path in expected if not (project / path).is_file()]
    assert not missing, f"Missing files: {missing}"


# ─── Variable substitution ───


def test_project_name_substituted_everywhere(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"project_name": "my-lib"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
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
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"Jane Doe"' in pyproject
    assert '"jane@example.com"' in pyproject
    assert "https://www.github.com/janedoe/custom-repo" in pyproject


def test_license_year_and_author(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {"license_year": 2030, "author_name": "Test User"},
    )
    license_text = (project / "LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2030 Test User" in license_text


def test_python_version_propagates_to_all_locations(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"python_version": "3.13"})
    assert (project / ".python-version").read_text(encoding="utf-8").strip() == "3.13"
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.13"' in pyproject
    assert 'python-version = "3.13"' in pyproject
    assert "Python :: 3.13" in pyproject


def test_pyproject_uses_pep639_license_metadata(tmp_path: Path) -> None:
    """PEP 639: explicit `license-files` key, no deprecated classifier."""
    project = _generate(tmp_path)
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject
    assert "License :: OSI Approved" not in pyproject


# ─── Conditional features (use_pytest) ───


def test_use_pytest_true_includes_pytest_machinery(tmp_path: Path) -> None:
    project = _generate(tmp_path)  # default true
    assert (project / "tests" / "__init__.py").is_file()
    # No placeholder `conftest.py` — create one when a real fixture lands.
    assert not (project / "tests" / "conftest.py").exists()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pytest>=9.0.3"' in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
    # Library mode → editable install handles imports, no `pythonpath` needed.
    assert "pythonpath" not in pyproject
    assert '"PT",' in pyproject
    assert "[tool.ruff.lint.per-file-ignores]" in pyproject
    assert "[tool.ruff.lint.flake8-pytest-style]" in pyproject
    extensions = (project / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    assert "test-adapter" in extensions
    settings = (project / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "pytestEnabled" in settings


def test_use_pytest_false_omits_pytest_machinery(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_pytest": False})
    assert not (project / "tests").exists()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pytest>=' not in pyproject
    assert "[tool.pytest.ini_options]" not in pyproject
    assert '"PT",' not in pyproject
    # per-file-ignores table still exists (for `__init__.py`), but the
    # pytest-specific `tests/**` entry is gone.
    assert '"tests/**"' not in pyproject
    assert "[tool.ruff.lint.flake8-pytest-style]" not in pyproject
    extensions = (project / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    assert "test-adapter" not in extensions
    settings = (project / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "pytestEnabled" not in settings


def test_application_with_pytest_adds_pythonpath(tmp_path: Path) -> None:
    """Application + pytest: no editable install, so pytest needs the project
    root on `sys.path` to import the flat-layout package from `tests/`.
    """
    project = _generate(tmp_path, {"is_library": False, "use_pytest": True})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
    assert 'pythonpath = ["."]' in pyproject


def test_minimal_application_combination(tmp_path: Path) -> None:
    """Application without pytest: no build-system, no py.typed, no tests."""
    project = _generate(tmp_path, {"is_library": False, "use_pytest": False})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert '"pytest>=' not in pyproject
    assert not (project / "tests").exists()
    assert not (project / "test_app" / "py.typed").exists()
    # ty and ruff should still be in dev deps
    assert '"ty>=' in pyproject
    assert '"ruff>=' in pyproject


# ─── Conditional features (is_library) ───


def test_is_library_true_includes_build_system_and_py_typed(tmp_path: Path) -> None:
    project = _generate(tmp_path)  # default true
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" in pyproject
    assert "uv_build" in pyproject
    assert "[tool.uv.build-backend]" in pyproject
    assert '"Typing :: Typed"' in pyproject
    assert (project / "test_app" / "py.typed").is_file()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "pypi/v/test-app" in readme
    assert "pepy.tech/badge/test-app" in readme


def test_is_library_false_omits_build_system_and_py_typed(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"is_library": False})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert "uv_build" not in pyproject
    assert "[tool.uv.build-backend]" not in pyproject
    assert '"Typing :: Typed"' not in pyproject
    assert not (project / "test_app" / "py.typed").exists()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "pypi/" not in readme
    assert "pepy.tech" not in readme


# ─── Answers file ───


def test_answers_file_records_all_inputs(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {"project_name": "answers-test", "python_version": "3.12"},
    )
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "project_name: answers-test" in answers
    assert "python_version: '3.12'" in answers


# ─── Agent guide ───


def test_agents_md_documents_commit_convention(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"project_name": "agent-app"})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "agent-app" in agents
    assert "## Commit convention" in agents
    assert "Gitmoji" in agents
    assert "Co-Authored-By" in agents


def test_agents_md_documents_python_style(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Python style" in agents
    assert "from __future__ import annotations" in agents
    assert "Google style" in agents
    assert "PEP 723" in agents


# ─── Python file conventions ───


def test_future_import_required_with_init_exempt(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"package_name": "fut_app"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'required-imports = ["from __future__ import annotations"]' in pyproject
    assert '"__init__.py" = ["I002"]' in pyproject

    # Empty package marker stays empty — no future import.
    init = (project / "fut_app" / "__init__.py").read_text(encoding="utf-8")
    assert init.strip() == ""
    # `tests/__init__.py` is also a package marker and stays empty too.
    tests_init = (project / "tests" / "__init__.py").read_text(encoding="utf-8")
    assert tests_init.strip() == ""


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
