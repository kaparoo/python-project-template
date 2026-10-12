"""Tests for the copier template.

Generates projects with various copier answers and asserts on the rendered
output. Most tests run with `unsafe=False` to skip _tasks (which spend
time on `git init` and `uv sync`); a single integration test runs the
full pipeline to confirm tasks behave end-to-end.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import copier
import pytest
import yaml

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


def test_python_version_defaults_to_3_14(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    assert (project / ".python-version").read_text(encoding="utf-8").strip() == "3.14"
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.14"' in pyproject


def test_python_version_rejects_versions_outside_the_supported_range(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Invalid choice for 'python_version'"):
        _generate(tmp_path, {"python_version": "3.11"})


def test_python_version_3_12_renders_with_a_deprecation_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _generate(tmp_path, {"python_version": "3.12"})
    assert (project / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "python_version: '3.12'" in answers
    assert "Python 3.12 is deprecated" in capsys.readouterr().err


def test_python_version_default_has_no_deprecation_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _generate(tmp_path)
    assert "deprecated" not in capsys.readouterr().err


@pytest.mark.parametrize(
    ("python_version", "supported"),
    (
        ("3.12", ["3.12", "3.13", "3.14", "3.15"]),
        ("3.14", ["3.14", "3.15"]),
        ("3.15", ["3.15"]),
    ),
)
def test_supported_python_versions_span_from_the_oldest(
    tmp_path: Path, python_version: str, supported: list[str]
) -> None:
    """`python_versions` runs from the answer to the newest choice and
    drives the classifiers, the README badge, and the CI matrix alike,
    without being recorded as an answer."""
    project = _generate(tmp_path, {"python_version": python_version})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    classifiers = re.findall(r'"Programming Language :: Python :: (3\.\d+)"', pyproject)
    assert classifiers == supported
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert f"badge/python-{'%20%7C%20'.join(supported)}-blue.svg" in readme
    ci = yaml.safe_load(
        (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    assert ci["jobs"]["check"]["strategy"]["matrix"]["python-version"] == supported
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "python_versions" not in answers


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
    assert '"pytest>=9.1.1"' in pyproject
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
    # Application mode has nothing to publish — no named indexes, and the
    # Releases section only tags versions.
    assert 'name = "testpypi"' not in pyproject
    assert "upload.pypi.org" not in pyproject
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "uv publish" not in agents


# ─── Answers file ───


def test_answers_file_records_all_inputs(tmp_path: Path) -> None:
    project = _generate(
        tmp_path,
        {"project_name": "answers-test", "python_version": "3.15"},
    )
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "project_name: answers-test" in answers
    assert "python_version: '3.15'" in answers


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
    # Link reference the release procedure rewrites to a compare link.
    assert "[Unreleased]: https://github.com/kaparoo/test-app/commits/main" in changelog


def test_include_todo_true_creates_todo_md_and_readme_link(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"include_todo": True})
    assert (project / "TODO.md").is_file()
    todo = (project / "TODO.md").read_text(encoding="utf-8")
    assert "# TODO" in todo
    assert "Open work that is not done yet" in todo
    assert "Promote" not in todo
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" in readme
    assert "[TODO.md](https://github.com/kaparoo/test-app/blob/main/TODO.md)" in readme


def test_include_todo_false_omits_todo_md_and_readme_link(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"include_todo": False})
    assert not (project / "TODO.md").exists()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "## 📋 TODO" not in readme
    assert "TODO.md" not in readme


def _sections(readme: str) -> list[str]:
    """The `##` headings of a rendered README, in order."""
    return [line for line in readme.splitlines() if line.startswith("## ")]


def test_readme_sections_for_library(tmp_path: Path) -> None:
    """Default (`is_library=True`, `include_todo=True`): lead sections
    Installation → Quick start → Modules, then the closing three."""
    project = _generate(tmp_path)
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert _sections(readme) == [
        "## 📦 Installation",
        "## 🚀 Quick start",
        "## 🧩 Modules",
        "## 📋 TODO",
        "## 📜 Changelog",
        "## ⚖️ License",
    ]
    assert "uv add test-app" in readme
    assert "pip install test-app" in readme


def test_readme_sections_for_application(tmp_path: Path) -> None:
    """Application: lead sections Setup → Usage (Layout is added on demand)."""
    project = _generate(tmp_path, {"is_library": False})
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert _sections(readme) == [
        "## 📦 Setup",
        "## 🚀 Usage",
        "## 📋 TODO",
        "## 📜 Changelog",
        "## ⚖️ License",
    ]
    assert "uv add test-app" not in readme
    assert "uv sync --group dev" in readme


def test_library_readme_links_repository_files_absolutely(tmp_path: Path) -> None:
    """A library's README is its PyPI page, which has no other repo files."""
    project = _generate(tmp_path)
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# test-app\n")
    assert "](./" not in readme
    base = "https://github.com/kaparoo/test-app/blob/main"
    for target in ("LICENSE", "TODO.md", "CHANGELOG.md"):
        assert f"]({base}/{target})" in readme, f"missing link to {target}"


def test_application_readme_links_repository_files_relatively(
    tmp_path: Path,
) -> None:
    """An application's README is only read on GitHub or in a clone."""
    project = _generate(tmp_path, {"is_library": False})
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# test-app\n")
    assert "https://github.com/kaparoo/test-app/blob/main" not in readme
    for target in ("LICENSE", "TODO.md", "CHANGELOG.md"):
        assert f"](./{target})" in readme, f"missing link to {target}"


# ─── CI workflow ───


def test_ci_workflow_present_and_pinned(tmp_path: Path) -> None:
    """Generated projects ship a CI workflow with Node-24 action majors."""
    project = _generate(tmp_path)
    ci_path = project / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file()
    ci = ci_path.read_text(encoding="utf-8")
    assert "name: CI" in ci
    assert "actions/checkout@v7" in ci
    assert "astral-sh/setup-uv@v10.3.0" in ci
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


def test_ci_matrix_tests_every_version_on_linux_and_one_elsewhere(
    tmp_path: Path,
) -> None:
    """Linux runs each supported Python; Windows and macOS run the
    `.python-version` interpreter, which `setup-uv` falls back to."""
    project = _generate(tmp_path, {"python_version": "3.13"})
    ci = yaml.safe_load(
        (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    job = ci["jobs"]["check"]
    assert job["strategy"]["fail-fast"] is False
    assert job["strategy"]["matrix"] == {
        "os": ["ubuntu-latest"],
        "python-version": ["3.13", "3.14", "3.15"],
        "include": [{"os": "windows-latest"}, {"os": "macos-latest"}],
    }
    setup_uv = next(s for s in job["steps"] if s.get("name") == "Set up uv")
    assert setup_uv["with"]["python-version"] == "${{ matrix.python-version }}"
    assert "${{ matrix.python-version || '.python-version' }}" in job["name"]


def test_ci_workflow_omits_test_step_without_pytest(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_pytest": False})
    ci = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv run pytest" not in ci
    # lint + type-check steps always remain
    assert "uv run ruff check ." in ci
    assert "uv run ty check" in ci
    # The matrix still checks each version imports, with no tests to run.
    assert 'run: uv run python -c "import test_app"' in ci


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
    assert "actions/download-artifact@v8" in yml  # testpypi/publish consume them
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
    # A final job publishes a GitHub Release from the CHANGELOG + artifacts,
    # failing fast if the tag has no matching CHANGELOG section (rather than
    # creating a Release with an empty body).
    assert "github-release:" in yml
    assert "needs: pypi" in yml
    assert "gh release create" in yml
    assert "No CHANGELOG section for" in yml
    # Release notes join hard-wrapped CHANGELOG lines (GitHub would render
    # each newline as a break) and close with the version's compare link.
    assert "join the CHANGELOG's hard-wrapped lines" in yml
    assert "**Full Changelog**" in yml
    assert "No [$version] link reference in CHANGELOG.md" in yml
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
    assert "actions/download-artifact@v8" in yml
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
    """is_library=False — no publish workflow; Releases only tags versions."""
    project = _generate(tmp_path, {"is_library": False})
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases" in agents
    assert "is an application and is not published" in agents
    assert "git tag -a vX.Y.Z" in agents
    assert "uv publish" not in agents
    assert "uv build" not in agents
    assert "Trusted Publishing" not in agents


def test_agents_md_documents_doc_upkeep_rules(tmp_path: Path) -> None:
    """Default (library + TODO): rules for every maintained document."""
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Documentation" in agents
    # CHANGELOG: the six categories only, scope, phrasing, and upgrades.
    assert "### `CHANGELOG.md`" in agents
    assert "| `Deprecated` |" in agents
    assert "never invent new ones" in agents
    assert "imports the library" in agents
    assert "Internal refactoring stays out" in agents
    assert "`Added` and `Removed` lead with *what*" in agents
    assert "**Breaking:**" in agents
    assert "`DeprecationWarning`" in agents
    assert "Cut a release only when the user asks" in agents
    assert "https://github.com/kaparoo/test-app/compare/vX.Y.Z...HEAD" in agents
    # TODO: open work only, one line or a short body with a revisit trigger.
    assert "### `TODO.md`" in agents
    assert "holds **open work only**" in agents
    assert "`Revisit when ...`" in agents
    assert 'no "Done" section' in agents
    assert "Before starting a task, read the items" in agents
    assert "brought in line once" in agents
    assert "document already written in another language" in agents
    assert "This project keeps no `TODO.md`" not in agents
    # README: the root's layout top to bottom, then sub-READMEs as spokes.
    assert "### `README.md`" in agents
    assert "The root `README.md` is the landing page" in agents
    assert "word for word the\n   `description` in `pyproject.toml`" in agents
    for lead in ("📦 Installation —", "🚀 Quick start —", "🧩 Modules —"):
        assert lead in agents, f"missing lead section {lead}"
    assert "5. Project-specific sections" in agents
    assert "📋 TODO, 📜 Changelog, ⚖️ License." in agents
    assert 'No hand-written table of contents and no "back to top"' in agents
    assert "https://github.com/kaparoo/test-app/blob/main/<path>" in agents
    assert "#### Sub-READMEs" in agents
    assert "so it has no fixed sections" in agents
    assert "never folded into\n  `<details>`" in agents
    assert "Keep `## Contents` in step with the headings" in agents
    assert "`#resolving-conflicts-on_conflict`" in agents
    assert "| that README → `## Contents`, if present" in agents
    assert "only the root README reaches PyPI" in agents
    assert "📦 Setup —" not in agents
    assert "🗂️ Layout" not in agents
    # Design decisions as MADR records, and AGENTS itself.
    assert "### `docs/decisions/`" in agents
    assert "`docs/decisions/NNNN-title-with-dashes.md`" in agents
    assert "superseded by NNNN" in agents
    assert "### `AGENTS.md`" in agents


def test_agents_md_doc_upkeep_rules_follow_options(tmp_path: Path) -> None:
    """Application without TODO: no TODO or Modules rules, app wording."""
    project = _generate(tmp_path, {"is_library": False, "include_todo": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Documentation" in agents
    assert "### `CHANGELOG.md`" in agents
    assert "runs the application" in agents
    assert "a command, an option, or a configuration" in agents
    assert "DeprecationWarning" not in agents
    assert "This project keeps no `TODO.md`" in agents
    assert "### `TODO.md`" not in agents
    assert "📋 TODO" not in agents
    assert "🧩 Modules" not in agents
    assert "PyPI" not in agents
    for lead in ("📦 Setup —", "🚀 Usage —", "🗂️ Layout, once"):
        assert lead in agents, f"missing lead section {lead}"
    assert "| `README.md` → 🚀 Usage" in agents
    assert "   📜 Changelog, ⚖️ License." in agents
    assert "A directory whose use outgrows its 🗂️ Layout entry" in agents
    assert "#### Sub-READMEs" in agents
    assert "### `docs/decisions/`" in agents


def test_agents_md_documents_dependency_rules(tmp_path: Path) -> None:
    """Default (library + pytest): `uv`-only changes, lock with them, the
    `ruff` lockstep, and every place the supported Python versions live."""
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Dependencies" in agents
    assert "`uv add --group dev <pkg>`" in agents
    assert "`uv add --optional <extra> <pkg>`" in agents
    assert "Commit `pyproject.toml` and `uv.lock`" in agents
    assert "`uv lock --upgrade-package <pkg>`" in agents
    assert (
        "Raising `ruff`'s minimum also raises `[tool.ruff] required-version`" in agents
    )
    assert "### Supported Python versions" in agents
    for place in (
        "`requires-python` in `pyproject.toml`",
        "`[tool.ty.environment] python-version`",
        "`Programming Language :: Python :: X.Y` classifier",
        "`.python-version`",
        "the requirement line in 📦 Installation",
    ):
        assert place in agents, f"missing {place}"
    assert "`copier update -d python_version=X.Y`" in agents
    assert "the `python-version` list in `.github/workflows/ci.yml`" in agents
    assert "drop\nit from the classifiers, the CI list, and the badge" in agents
    assert "| \N{HEAVY PLUS SIGN}     | Add a dependency" in agents
    assert "| \N{HEAVY MINUS SIGN}     | Remove a dependency" in agents


def test_agents_md_dependency_rules_follow_options(tmp_path: Path) -> None:
    """Application without pytest: no extras, Setup, and an import check."""
    project = _generate(tmp_path, {"is_library": False, "use_pytest": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Dependencies" in agents
    assert "--optional" not in agents
    assert "the requirement line in 📦 Setup" in agents
    assert "--isolated" not in agents


def test_agents_md_documents_readme_upkeep_details(tmp_path: Path) -> None:
    """Default library: the CLI section, dependency badges, link upkeep,
    and one wrap width for every document."""
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "All of them wrap prose at 72 columns" in agents
    assert "(`[project.scripts]`) comes first among them" in agents
    assert "`[project.scripts]` | `README.md` → ⌨️ CLI" in agents
    assert "A badge for a dependency" in agents
    assert "Links stay valid" in agents
    assert "| that README → the link" in agents


def test_agents_md_readme_upkeep_details_follow_options(tmp_path: Path) -> None:
    """Application: commands live in 🚀 Usage, so no ⌨️ CLI section."""
    project = _generate(tmp_path, {"is_library": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "[project.scripts]" not in agents
    assert "Links stay valid" in agents
    assert "All of them wrap prose at 72 columns" in agents


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
    tmp_path: Path, answers: dict[str, object]
) -> None:
    """The generated docs keep the wrap rule their own `AGENTS.md` sets.

    Exempt, as that rule says: tables, code blocks, headings, and lines
    holding a URL or consisting of a single command in backticks.
    """
    project = _generate(tmp_path, answers)
    too_wide = []
    for name in ("AGENTS.md", "README.md", "CHANGELOG.md", "TODO.md"):
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


def test_agents_md_documents_workflow_and_secrets(tmp_path: Path) -> None:
    """Default (pytest): the gates that make a change done, git actions
    only on request, and secrets kept out of the repository."""
    project = _generate(tmp_path)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Workflow" in agents
    assert (
        "uv run ruff format .\nuv run ruff check --fix .\n"
        "uv run ty check\nuv run pytest\n```"
    ) in agents
    assert "instead of skipping it silently" in agents
    assert "Commit only when the user asks; see *Committing* below." in agents
    assert "### Committing" in agents
    assert "`git stash push --include-untracked -m" in agents
    assert "so each commit passes on its own" in agents
    assert "`git checkout stash@{0} -- <file>`" in agents
    assert "No `git add -p` or other interactive commands." in agents
    assert "Drop a stash only once its changes are back" in agents
    assert "Push only when the user asks" in agents
    assert "Never force-push" in agents
    assert "Create a branch only when" in agents
    assert "### Secrets" in agents
    assert "The credential has to be revoked and replaced" in agents


def test_agents_md_workflow_gates_follow_options(tmp_path: Path) -> None:
    """Without pytest, the import check CI runs is the last gate."""
    project = _generate(tmp_path, {"use_pytest": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert 'uv run ty check\nuv run python -c "import test_app"\n```' in agents
    assert "uv run pytest\n```" not in agents


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


def test_fixme_comments_fail_lint_and_agents_md_says_so(tmp_path: Path) -> None:
    """`FIX` is selected, and both `AGENTS.md` variants send deferred work
    elsewhere: to `TODO.md`, or to the user when there is none."""
    project = _generate(tmp_path / "with_todo")
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"FIX",   # flake8-fixme' in pyproject
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "This\n  file is the only place for it: `ruff` rejects `TODO`" in agents

    no_todo = _generate(tmp_path / "no_todo", {"include_todo": False})
    agents = (no_todo / "AGENTS.md").read_text(encoding="utf-8")
    assert "report work you defer to the user.\n`ruff` rejects" in agents


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


# ─── Integration: a generated project passes its own CI gates ───


def _run_in_project(
    project: Path,
    cmd: list[str],
    *,
    allow_codes: tuple[int, ...] = (0,),
) -> None:
    """Run `cmd` inside the generated project; fail with captured output.

    Mirrors what the generated `ci.yml` runs, so a template change that
    yields a project failing its own lint/type/test gates is caught here
    rather than only in manual dogfooding.
    """
    result = subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode in allow_codes, (
        f"`{' '.join(cmd)}` exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


def test_generated_library_passes_its_own_ci(tmp_path: Path) -> None:
    """Default (library + pytest): a freshly generated project passes the
    gates its `ci.yml` defines (`ruff format --check`, `ruff check`,
    `ty check`, `pytest`) and also builds a distribution (`uv build`).
    Exercises the pinned tool versions end-to-end — ruff/ty config
    validity, pytest + pytest-cov plugin load, and the `uv_build` backend
    actually producing an sdist + wheel — which the resolve-only `_tasks`
    test cannot catch.
    """
    project = _generate(tmp_path, run_tasks=True)  # _tasks already ran `uv sync`
    _run_in_project(project, ["uv", "run", "ruff", "format", "--check", "."])
    _run_in_project(project, ["uv", "run", "ruff", "check", "."])
    _run_in_project(project, ["uv", "run", "ty", "check"])
    # A fresh project has no tests → pytest exits 5 (none collected), but the
    # run still loads the pytest + pytest-cov plugins (the real compat check).
    _run_in_project(project, ["uv", "run", "pytest"], allow_codes=(0, 5))
    # Beyond ci.yml: a library is published, so confirm the `uv_build`
    # backend actually produces an sdist + wheel from the generated config.
    _run_in_project(project, ["uv", "build"])
    dist = project / "dist"
    assert any(dist.glob("*.whl")), "uv build produced no wheel"
    assert any(dist.glob("*.tar.gz")), "uv build produced no sdist"
    # The `FIX` rules are live: a deferred-work comment fails lint, which
    # is what pushes it into `TODO.md`.
    probe = project / "test_app" / "probe.py"
    probe.write_text(
        "from __future__ import annotations\n\n# TODO: probe\n", encoding="utf-8"
    )
    result = subprocess.run(
        ["uv", "run", "ruff", "check", str(probe)],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    probe.unlink()
    assert result.returncode == 1
    assert "FIX002" in result.stdout


def test_generated_minimal_application_passes_lint_and_type_check(
    tmp_path: Path,
) -> None:
    """Opposite corner (application, no pytest): the lean config — no
    build-system, no pytest layer — still lints and type-checks clean.
    """
    project = _generate(
        tmp_path,
        {"is_library": False, "use_pytest": False},
        run_tasks=True,
    )
    _run_in_project(project, ["uv", "run", "ruff", "format", "--check", "."])
    _run_in_project(project, ["uv", "run", "ruff", "check", "."])
    _run_in_project(project, ["uv", "run", "ty", "check"])
