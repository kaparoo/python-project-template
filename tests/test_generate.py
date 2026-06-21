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
        ".gitattributes",
        "test_app/__init__.py",
        "test_app/py.typed",
        "tests/__init__.py",
        "CHANGELOG.md",
        "TODO.md",
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
    assert '"pytest-cov>=7.1.0"' in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
    # Coverage is wired with a default-off gate.
    assert "--cov" in pyproject
    assert "[tool.coverage.run]" in pyproject
    assert "fail_under = 0" in pyproject
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
    assert '"pytest-cov>=' not in pyproject
    assert "[tool.pytest.ini_options]" not in pyproject
    assert "[tool.coverage.run]" not in pyproject
    assert "--cov" not in pyproject
    assert '"PT",' not in pyproject
    # per-file-ignores table still exists (for `__init__.py`), but the
    # pytest-specific `tests/**` entry is gone.
    assert '"tests/**"' not in pyproject
    assert "[tool.ruff.lint.flake8-pytest-style]" not in pyproject
    extensions = (project / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    assert "test-adapter" not in extensions
    settings = (project / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "pytestEnabled" not in settings


def test_coverage_fail_under_question(tmp_path: Path) -> None:
    """`coverage_fail_under` flows into the gate; default is 0 (off)."""
    default = _generate(tmp_path / "d")
    assert "fail_under = 0" in (default / "pyproject.toml").read_text(encoding="utf-8")
    custom = _generate(tmp_path / "c", {"coverage_fail_under": 85})
    assert "fail_under = 85" in (custom / "pyproject.toml").read_text(encoding="utf-8")


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
    # Library mode ships named publish indexes for `uv publish`.
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' in pyproject
    assert 'publish-url = "https://upload.pypi.org/legacy/"' in pyproject
    assert 'publish-url = "https://test.pypi.org/legacy/"' in pyproject
    # ...and an AGENTS.md `## Releases` workflow that references them.
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" in agents
    assert "uv publish --index testpypi" in agents
    assert "uvx twine check dist/*" in agents


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
    # Application mode has nothing to publish — no named indexes / Releases.
    assert 'name = "testpypi"' not in pyproject
    assert "upload.pypi.org" not in pyproject
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" not in agents
    assert "uv publish" not in agents


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
    # Gitmoji palette table is present with a representative spread of prefixes.
    assert "Common prefixes used in this project" in agents
    for prefix in ("✨", "🐛", "♻️", "📝", "🔖", "🔧"):
        assert prefix in agents, f"missing {prefix} in gitmoji palette"


def test_generated_changelog_skeleton(tmp_path: Path) -> None:
    """Every generated project ships a Keep-a-Changelog skeleton."""
    project = _generate(tmp_path)
    changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "# Changelog" in changelog
    assert "Keep a Changelog" in changelog
    assert "Semantic Versioning" in changelog
    assert "## [Unreleased]" in changelog


def test_include_todo_true_creates_todo_md_and_readme_link(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"include_todo": True})
    assert (project / "TODO.md").is_file()
    todo = (project / "TODO.md").read_text(encoding="utf-8")
    assert "# TODO" in todo
    assert "Promote an" in todo
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" in readme
    assert "[TODO.md](./TODO.md)" in readme


def test_include_todo_false_omits_todo_md_and_readme_link(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"include_todo": False})
    assert not (project / "TODO.md").exists()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" not in readme
    assert "TODO.md" not in readme


def test_readme_includes_five_sections_for_library(tmp_path: Path) -> None:
    """Default (`is_library=True`, `include_todo=True`) → all 5 sections."""
    project = _generate(tmp_path)
    readme = (project / "README.md").read_text(encoding="utf-8")
    for section in (
        "## 📦 Installation",
        "## 🧩 Modules",
        "## 📋 TODO",
        "## 📜 Changelog",
        "## ⚖️ License",
    ):
        assert section in readme, f"missing {section}"
    assert "uv add test-app" in readme
    assert "pip install test-app" in readme


def test_readme_for_application_swaps_install_to_dev_setup(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"is_library": False})
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📦 Development setup" in readme
    assert "## 📦 Installation" not in readme
    assert "## 🧩 Modules" not in readme  # library-only section
    assert "uv add test-app" not in readme
    assert "uv sync --group dev" in readme


# ─── CI workflow ───


def test_ci_workflow_present_and_pinned(tmp_path: Path) -> None:
    """Generated projects ship a CI workflow with Node-24 action majors."""
    project = _generate(tmp_path)
    ci_path = project / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file()
    ci = ci_path.read_text(encoding="utf-8")
    assert "name: CI" in ci
    assert "actions/checkout@v6" in ci
    assert "astral-sh/setup-uv@v8.1.0" in ci
    # GitHub Actions expressions survived Jinja rendering verbatim.
    assert "${{ matrix.os }}" in ci
    assert "raw" not in ci  # {% raw %} wrappers fully consumed
    # Hardening: cancel superseded runs, cap runaway jobs, fail on a
    # stale lock.
    assert "concurrency:" in ci
    assert "group: ci-${{ github.ref }}" in ci
    assert "cancel-in-progress: true" in ci
    assert "timeout-minutes: 20" in ci
    assert "uv sync --group dev --locked" in ci
    # use_pytest default true → a Tests step runs pytest.
    assert "uv run pytest" in ci


def test_ci_workflow_omits_test_step_without_pytest(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_pytest": False})
    ci = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv run pytest" not in ci
    # lint + type-check steps always remain
    assert "uv run ruff check ." in ci
    assert "uv run ty check" in ci


# ─── Release automation (publish.yml) ───


def test_release_automation_manual_default(tmp_path: Path) -> None:
    """Default `manual` — no publish workflow, manual `uv publish` docs."""
    project = _generate(tmp_path)  # is_library default true, release_automation manual
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" in agents
    assert "uv publish --index testpypi" in agents
    assert "Trusted Publishing" not in agents


def test_release_automation_github_oidc(tmp_path: Path) -> None:
    """`github-oidc` default — 4-job publish.yml with TestPyPI staging."""
    project = _generate(tmp_path, {"release_automation": "github-oidc"})
    publish = project / ".github" / "workflows" / "publish.yml"
    assert publish.is_file()
    yml = publish.read_text(encoding="utf-8")
    assert "tags: ['v*.*.*']" in yml  # X.Y.Z only — no stray v-tags
    assert "uses: ./.github/workflows/ci.yml" in yml  # CI reused as a gate
    assert "uvx twine check dist/*" in yml  # metadata verification
    # 4-job pipeline: ci → build → testpypi → pypi.
    assert "actions/upload-artifact@v7" in yml  # build job ships artifacts
    assert "actions/download-artifact@v7" in yml  # testpypi/publish consume them
    # PyPA official action with explicit attestations + hash echo.
    assert "pypa/gh-action-pypi-publish@release/v1" in yml
    assert "repository-url: https://test.pypi.org/legacy/" in yml
    assert "attestations: true" in yml
    assert "print-hash: true" in yml
    assert "environment: pypi" in yml  # approval gate on the final job
    assert "id-token: write" in yml
    # Build job fails fast when the tag and project version disagree.
    assert "Verify tag matches project version" in yml
    assert "uv version --short" in yml
    # Re-runnable TestPyPI staging tolerates an already-uploaded version.
    assert "skip-existing: true" in yml
    # A final job publishes a GitHub Release from the CHANGELOG + artifacts.
    assert "github-release:" in yml
    assert "needs: pypi" in yml
    assert "gh release create" in yml
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Trusted Publishing" in agents
    assert "Trusted Publisher" in agents  # one-time setup checklist
    assert "TestPyPI Trusted Publisher" in agents  # extra setup item
    assert "required reviewer" in agents
    assert "github-release" in agents  # release-automation pipeline doc synced


def test_release_automation_github_oidc_without_testpypi(tmp_path: Path) -> None:
    """`github-oidc` + `use_testpypi=false` — 3-job publish.yml (no staging)."""
    project = _generate(
        tmp_path,
        {"release_automation": "github-oidc", "use_testpypi": False},
    )
    publish = project / ".github" / "workflows" / "publish.yml"
    assert publish.is_file()
    yml = publish.read_text(encoding="utf-8")
    assert "tags: ['v*.*.*']" in yml
    assert "uses: ./.github/workflows/ci.yml" in yml
    assert "uvx twine check dist/*" in yml
    assert "environment: pypi" in yml
    assert "pypa/gh-action-pypi-publish@release/v1" in yml
    assert "attestations: true" in yml
    # 3-job structure: ci → build → pypi. Build still ships artifacts
    # so OIDC publish has no build-time dependency footprint.
    assert "actions/upload-artifact@v7" in yml
    assert "actions/download-artifact@v7" in yml
    assert "needs: build" in yml  # pypi job depends on build (no testpypi)
    assert "testpypi" not in yml.lower()  # but no staging job either
    # Tag-version verification and the GitHub Release job still ship; the
    # TestPyPI-only `skip-existing` does not.
    assert "Verify tag matches project version" in yml
    assert "github-release:" in yml
    assert "gh release create" in yml
    assert "skip-existing" not in yml
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Trusted Publishing" in agents
    assert "TestPyPI Trusted Publisher" not in agents
    # Escape hatch documented in the AGENTS setup checklist.
    assert "use_testpypi=true" in agents
    # pyproject loses the testpypi named index.
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' not in pyproject


def test_release_automation_manual_without_testpypi(tmp_path: Path) -> None:
    """`manual` + `use_testpypi=false` — Releases docs drop the staging step."""
    project = _generate(tmp_path, {"use_testpypi": False})
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" in agents
    assert "uv publish --index testpypi" not in agents
    assert "uv publish --index pypi" in agents
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' not in pyproject


def test_application_omits_release_machinery(tmp_path: Path) -> None:
    """is_library=False — no publish workflow, no Releases section at all."""
    project = _generate(tmp_path, {"is_library": False})
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" not in agents


def test_agents_md_documents_python_style(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Python style" in agents
    assert "from __future__ import annotations" in agents
    assert "Google style" in agents
    assert "PEP 723" in agents
    # Docstring philosophy (intent/contracts, not just format).
    assert "intent and contracts" in agents
    assert "Type Parameters:" in agents
    # Expanded docstring guidance: summary-shape carve-outs + family map.
    assert "family map" in agents
    assert "self-explainable" in agents
    # Literal option values are backticked like identifiers.
    assert "Literal option values get backticks" in agents
    # Body-layout conventions ported from the project.
    assert "blank line before the final" in agents
    assert "boxed comment" in agents


def test_agents_md_documents_error_message_content(tmp_path: Path) -> None:
    """Beyond the EM ruff rule (format), messages must name the fix."""
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "name the valid set or the fix" in agents


def test_agents_md_documents_test_conventions_with_pytest(tmp_path: Path) -> None:
    """`use_pytest` projects get layout + quality guidance; omitted otherwise."""
    project = _generate(tmp_path)  # default use_pytest true
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Don't mix the two styles" in agents  # flat vs class TestX layout
    assert "verify it with a spy" in agents  # test-quality guidance

    no_pytest = _generate(tmp_path / "np", {"use_pytest": False})
    agents_np = (no_pytest / "AGENTS.md").read_text(encoding="utf-8")
    assert "verify it with a spy" not in agents_np
    assert "Don't mix the two styles" not in agents_np


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
