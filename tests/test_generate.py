"""Tests for the copier template (pytorch branch).

Generates projects with various copier answers and asserts on the rendered
output. Tests skip _tasks — the heavy `uv sync` would download torch; a
single integration test runs `uv lock` to confirm the project resolves.
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
        ".copier-answers.yml",
    ]
    missing = [path for path in expected if not (project / path).is_file()]
    assert not missing, f"Missing files: {missing}"
    # `use_pytest` defaults to false on this branch — no test suite.
    assert not (project / "tests").exists()


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


# ─── Conditional features (use_pytest) ───


def test_use_pytest_true_includes_pytest_machinery(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"use_pytest": True})
    assert (project / "tests" / "conftest.py").is_file()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pytest>=9.0.3"' in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
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
    assert "pypi/dm/test-app" in readme


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
    project = _generate(tmp_path, {"package_name": "fut_app", "use_pytest": True})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'required-imports = ["from __future__ import annotations"]' in pyproject
    assert '"__init__.py" = ["I002"]' in pyproject

    # Empty package marker stays empty — no future import.
    init = (project / "fut_app" / "__init__.py").read_text(encoding="utf-8")
    assert init.strip() == ""

    # conftest.py is a real module — it carries the future import.
    conftest = (project / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "from __future__ import annotations" in conftest


# ─── PyTorch ───


def test_torch_in_dependencies(tmp_path: Path) -> None:
    project = _generate(tmp_path)
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"torch>=2.11.0"' in pyproject
    assert '"torchvision>=0.26.0"' in pyproject
    assert "Artificial Intelligence" in pyproject


def test_cuda_backend_routes_to_cuda_index(tmp_path: Path) -> None:
    # Default backend is cuda with cuda_version 12.8 -> cu128.
    project = _generate(tmp_path)
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[[tool.uv.index]]" in pyproject
    assert "https://download.pytorch.org/whl/cu128" in pyproject
    assert '[tool.uv.sources]' in pyproject
    assert 'torch = { index = "pytorch" }' in pyproject
    assert 'torchvision = { index = "pytorch" }' in pyproject


def test_cpu_backend_routes_to_cpu_index(tmp_path: Path) -> None:
    project = _generate(tmp_path, {"compute_backend": "cpu"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://download.pytorch.org/whl/cpu" in pyproject
    assert "cu128" not in pyproject


# ─── Integration: dependency resolution ───


def test_generated_project_resolves_with_torch(tmp_path: Path) -> None:
    """`uv lock` resolves the generated project — torch is installable.

    This stops short of `uv sync` on purpose: syncing would download the
    multi-gigabyte torch wheel. Resolution alone confirms torch and
    torchvision are installable for the chosen Python version.
    """
    project = _generate(tmp_path)
    result = subprocess.run(
        ["uv", "lock"],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    lock = (project / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "torch"' in lock
    assert 'name = "torchvision"' in lock
