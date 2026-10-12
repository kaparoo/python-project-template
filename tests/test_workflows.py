from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from tests.helpers import Render


def test_ci_workflow_present_and_pinned(render: Render) -> None:
    project = render()
    ci_path = project / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file()
    ci = ci_path.read_text(encoding="utf-8")
    assert "name: CI" in ci
    assert "actions/checkout@v7" in ci
    assert "astral-sh/setup-uv@v10.3.0" in ci
    assert "${{ matrix.os }}" in ci
    assert "raw" not in ci
    assert "concurrency:" in ci
    assert "group: ci-${{ github.ref }}" in ci
    assert "cancel-in-progress: true" in ci
    assert "timeout-minutes: 20" in ci
    assert "uv sync --group dev --locked" in ci
    assert "uv run pytest" in ci


def test_ci_matrix_tests_every_version_on_linux_and_one_elsewhere(
    render: Render,
) -> None:
    project = render({"python_version": "3.13"})
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


def test_ci_build_job_checks_library_distributions(render: Render) -> None:
    library = render({"python_version": "3.13"})
    ci = yaml.safe_load(
        (library / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    runs = [s["run"] for s in ci["jobs"]["build"]["steps"] if "run" in s]
    assert runs[:2] == ["uv build", "uvx twine check dist/*"]
    assert runs[2].startswith(
        "uv run --isolated --no-project --python 3.13 --with dist/*.whl"
    )
    assert "files('test_app').joinpath('py.typed').is_file()" in runs[2]

    application = render({"is_library": False})
    ci = yaml.safe_load(
        (application / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    assert set(ci["jobs"]) == {"check"}


def test_ci_workflow_omits_test_step_without_pytest(render: Render) -> None:
    project = render({"use_pytest": False})
    ci = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv run pytest" not in ci
    assert "uv run ruff check ." in ci
    assert "uv run ty check" in ci
    assert 'run: uv run python -c "import test_app"' in ci


def test_release_automation_manual_default(render: Render) -> None:
    project = render()
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert releases.startswith("# Releasing `test-app`\n")
    assert "uv publish --index testpypi" in releases
    assert "Trusted Publishing" not in releases


def test_release_automation_github_oidc(render: Render) -> None:
    project = render({"release_automation": "github-oidc"})
    publish = project / ".github" / "workflows" / "publish.yml"
    assert publish.is_file()
    yml = publish.read_text(encoding="utf-8")
    assert "tags: ['v*.*.*']" in yml
    assert "uses: ./.github/workflows/ci.yml" in yml
    assert "uvx twine check dist/*" in yml
    assert "actions/upload-artifact@v7" in yml
    assert "actions/download-artifact@v8" in yml
    assert "pypa/gh-action-pypi-publish@release/v1" in yml
    assert "repository-url: https://test.pypi.org/legacy/" in yml
    assert "attestations: true" in yml
    assert "print-hash: true" in yml
    assert "environment: pypi" in yml
    assert "id-token: write" in yml
    assert "Verify tag matches project version" in yml
    assert "uv version --short" in yml
    assert "skip-existing: true" in yml
    assert "github-release:" in yml
    assert "needs: pypi" in yml
    assert "gh release create" in yml
    assert "No CHANGELOG section for" in yml
    assert "join the CHANGELOG's hard-wrapped lines" in yml
    assert "**Full Changelog**" in yml
    assert "No [$version] link reference in CHANGELOG.md" in yml
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert "Trusted Publishing" in releases
    assert "Trusted Publisher" in releases
    assert "TestPyPI Trusted Publisher" in releases
    assert "required reviewer" in releases
    assert "github-release" in releases


def test_release_automation_github_oidc_without_testpypi(render: Render) -> None:
    project = render(
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
    assert "actions/upload-artifact@v7" in yml
    assert "actions/download-artifact@v8" in yml
    assert "needs: build" in yml
    assert "testpypi" not in yml.lower()
    assert "Verify tag matches project version" in yml
    assert "github-release:" in yml
    assert "gh release create" in yml
    assert "skip-existing" not in yml
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert "Trusted Publishing" in releases
    assert "TestPyPI Trusted Publisher" not in releases
    assert "use_testpypi=true" in releases
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' not in pyproject


def test_release_automation_manual_without_testpypi(render: Render) -> None:
    project = render({"use_testpypi": False})
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert releases.startswith("# Releasing `test-app`\n")
    assert "uv publish --index testpypi" not in releases
    assert "uv publish --index pypi" in releases
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "pypi"' in pyproject
    assert 'name = "testpypi"' not in pyproject


def test_application_omits_release_machinery(render: Render) -> None:
    project = render({"is_library": False})
    assert not (project / ".github" / "workflows" / "publish.yml").exists()
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert releases.startswith("# Releasing `test-app`\n")
    assert "is an application and is not published" in releases
    assert "git tag -a vX.Y.Z" in releases
    assert "uv publish" not in releases
    assert "uv build" not in releases
    assert "Trusted Publishing" not in releases
