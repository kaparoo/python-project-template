from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
import yaml

from tests.helpers import prose

if TYPE_CHECKING:
    from tests.helpers import Render


def test_default_generation_creates_expected_files(render: Render) -> None:
    project = render()
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
        "tests/AGENTS.md",
        "tests/CLAUDE.md",
        "tests/test_test_app.py",
        "CHANGELOG.md",
        "TODO.md",
        ".copier-answers.yml",
        ".agents/changelog.md",
        ".agents/commits.md",
        ".agents/decisions.md",
        ".agents/dependencies.md",
        ".agents/readme.md",
        ".agents/releases.md",
        ".agents/todo.md",
    ]
    missing = [path for path in expected if not (project / path).is_file()]
    assert not missing, f"Missing files: {missing}"


def test_project_name_substituted_everywhere(render: Render) -> None:
    project = render({"project_name": "my-lib"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "my-lib"' in pyproject
    assert 'module-name = "my_lib"' in pyproject
    assert 'known-first-party = ["my_lib"]' in pyproject
    assert (project / "my_lib" / "__init__.py").is_file()


def test_author_and_github_substituted(render: Render) -> None:
    project = render(
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


def test_license_year_and_author(render: Render) -> None:
    project = render(
        {"license_year": 2030, "author_name": "Test User"},
    )
    license_text = (project / "LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2030 Test User" in license_text


def test_python_version_propagates_to_all_locations(render: Render) -> None:
    project = render({"python_version": "3.13"})
    assert (project / ".python-version").read_text(encoding="utf-8").strip() == "3.13"
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.13"' in pyproject
    assert 'python-version = "3.13"' in pyproject
    assert "Python :: 3.13" in pyproject


def test_python_version_defaults_to_3_14(render: Render) -> None:
    project = render()
    assert (project / ".python-version").read_text(encoding="utf-8").strip() == "3.14"
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.14"' in pyproject


def test_python_version_rejects_versions_outside_the_supported_range(
    render: Render,
) -> None:
    with pytest.raises(ValueError, match="Invalid choice for 'python_version'"):
        render({"python_version": "3.12"})


@pytest.mark.parametrize(
    ("python_version", "supported"),
    (
        ("3.13", ["3.13", "3.14", "3.15"]),
        ("3.14", ["3.14", "3.15"]),
        ("3.15", ["3.15"]),
    ),
)
def test_supported_python_versions_span_from_the_oldest(
    render: Render, python_version: str, supported: list[str]
) -> None:
    project = render({"python_version": python_version})
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


def test_pyproject_uses_pep639_license_metadata(render: Render) -> None:
    project = render()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject
    assert "License :: OSI Approved" not in pyproject


def test_use_pytest_true_includes_pytest_machinery(render: Render) -> None:
    project = render()
    assert (project / "tests" / "__init__.py").is_file()
    assert not (project / "tests" / "conftest.py").exists()
    smoke = (project / "tests" / "test_test_app.py").read_text(encoding="utf-8")
    assert "import test_app\n" in smoke
    assert 'assert test_app.__name__ == "test_app"' in smoke
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pytest>=9.1.1"' in pyproject
    assert '"pytest-cov>=7.1.0"' in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
    assert "--cov" in pyproject
    assert "[tool.coverage.run]" in pyproject
    assert "fail_under = 0" in pyproject
    assert (
        """'slow: takes seconds or more; deselect with -m "not slow"',""" in pyproject
    )
    gitignore = (project / ".gitignore").read_text(encoding="utf-8")
    assert "\ntests/assets/local/\n" in gitignore
    assert "pythonpath" not in pyproject
    assert '"PT",' in pyproject
    assert "[tool.ruff.lint.per-file-ignores]" in pyproject
    assert "[tool.ruff.lint.flake8-pytest-style]" in pyproject
    extensions = (project / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    assert "test-adapter" in extensions
    settings = (project / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "pytestEnabled" in settings


def test_use_pytest_false_omits_pytest_machinery(render: Render) -> None:
    project = render({"use_pytest": False})
    assert not (project / "tests").exists()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pytest>=' not in pyproject
    assert '"pytest-cov>=' not in pyproject
    assert "[tool.pytest.ini_options]" not in pyproject
    assert "[tool.coverage.run]" not in pyproject
    assert "--cov" not in pyproject
    assert "slow:" not in pyproject
    assert '"PT",' not in pyproject
    assert '"tests/**"' not in pyproject
    assert "[tool.ruff.lint.flake8-pytest-style]" not in pyproject
    extensions = (project / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    assert "test-adapter" not in extensions
    settings = (project / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "pytestEnabled" not in settings


def test_coverage_fail_under_question(render: Render) -> None:
    default = render()
    assert "fail_under = 0" in (default / "pyproject.toml").read_text(encoding="utf-8")
    custom = render({"coverage_fail_under": 85})
    assert "fail_under = 85" in (custom / "pyproject.toml").read_text(encoding="utf-8")


def test_application_with_pytest_adds_pythonpath(render: Render) -> None:
    project = render({"is_library": False, "use_pytest": True})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert "[tool.pytest.ini_options]" in pyproject
    assert 'pythonpath = ["."]' in pyproject


def test_minimal_application_combination(render: Render) -> None:
    project = render({"is_library": False, "use_pytest": False})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert '"pytest>=' not in pyproject
    assert not (project / "tests").exists()
    assert not (project / "test_app" / "py.typed").exists()
    assert '"ty>=' in pyproject
    assert '"ruff>=' in pyproject


def test_is_library_true_includes_build_system_and_py_typed(render: Render) -> None:
    project = render()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" in pyproject
    assert "uv_build" in pyproject
    assert "[tool.uv.build-backend]" in pyproject
    assert '"Typing :: Typed"' in pyproject
    assert (project / "test_app" / "py.typed").is_file()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "pypi/v/test-app" in readme
    assert "pepy.tech/badge/test-app" in readme
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' in pyproject
    assert 'publish-url = "https://upload.pypi.org/legacy/"' in pyproject
    assert 'publish-url = "https://test.pypi.org/legacy/"' in pyproject
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert "uv publish --index testpypi" in releases
    assert "uvx twine check dist/*" in releases


def test_is_library_false_omits_build_system_and_py_typed(render: Render) -> None:
    project = render({"is_library": False})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in pyproject
    assert "uv_build" not in pyproject
    assert "[tool.uv.build-backend]" not in pyproject
    assert '"Typing :: Typed"' not in pyproject
    assert not (project / "test_app" / "py.typed").exists()
    readme = (project / "README.md").read_text(encoding="utf-8")
    assert "pypi/" not in readme
    assert "pepy.tech" not in readme
    assert 'name = "testpypi"' not in pyproject
    assert "upload.pypi.org" not in pyproject
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert "uv publish" not in releases


def test_answers_file_records_all_inputs(render: Render) -> None:
    project = render(
        {"project_name": "answers-test", "python_version": "3.15"},
    )
    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "project_name: answers-test" in answers
    assert "python_version: '3.15'" in answers


def test_future_import_required_with_init_exempt(render: Render) -> None:
    project = render({"package_name": "fut_app"})
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'required-imports = ["from __future__ import annotations"]' in pyproject
    assert '"__init__.py" = ["I002"]' in pyproject
    assert 'ban-relative-imports = "all"' in pyproject
    assert '"E501"' not in pyproject

    init = (project / "fut_app" / "__init__.py").read_text(encoding="utf-8")
    assert init.strip() == ""
    tests_init = (project / "tests" / "__init__.py").read_text(encoding="utf-8")
    assert tests_init.strip() == ""


def test_fixme_comments_fail_lint_and_agents_md_says_so(render: Render) -> None:
    project = render()
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert '"FIX",   # flake8-fixme' in pyproject
    todo = (project / ".agents" / "todo.md").read_text(encoding="utf-8")
    assert "`TODO.md` is the only place for it: `ruff` rejects `TODO`" in prose(todo)

    no_todo = render({"include_todo": False})
    agents = (no_todo / "AGENTS.md").read_text(encoding="utf-8")
    assert "report work you defer to the user. `ruff` rejects" in prose(agents)
