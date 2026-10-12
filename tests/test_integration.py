from __future__ import annotations

import shlex
import subprocess
from typing import TYPE_CHECKING

import pytest
import yaml

from tests.helpers import generate, run_in_project

if TYPE_CHECKING:
    from pathlib import Path


pytestmark = pytest.mark.slow


def test_tasks_initialize_git_repo_with_initial_commit(tmp_path: Path) -> None:
    project = generate(tmp_path, run_tasks=True)
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


def test_generated_library_passes_its_own_ci(tmp_path: Path) -> None:
    project = generate(tmp_path, run_tasks=True)
    run_in_project(project, ["uv", "run", "ruff", "format", "--check", "."])
    run_in_project(project, ["uv", "run", "ruff", "check", "."])
    run_in_project(project, ["uv", "run", "ty", "check"])
    run_in_project(project, ["uv", "run", "pytest"], allow_codes=(0, 5))
    ci = yaml.safe_load(
        (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    commands = [s["run"] for s in ci["jobs"]["build"]["steps"] if "run" in s]
    assert commands[0] == "uv build"
    for command in commands:
        args: list[str] = []
        for arg in shlex.split(command):
            matches = (
                sorted(m for m in project.glob(arg) if not m.name.startswith("."))
                if "*" in arg
                else []
            )
            args.extend([str(m) for m in matches] if matches else [arg])
        run_in_project(project, args)
    dist = project / "dist"
    assert any(dist.glob("*.whl")), "uv build produced no wheel"
    assert any(dist.glob("*.tar.gz")), "uv build produced no sdist"
    probe = project / "test_app" / "probe.py"
    probe.write_text(
        "from __future__ import annotations\n\n"
        "from . import sibling\n\n"
        "# TODO: probe\n"
        f"WIDE = {'x' * 90!r}\n",
        encoding="utf-8",
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
    assert "TID252" in result.stdout
    assert "E501" in result.stdout
    probe = project / "tests" / "test_probe.py"
    probe.write_text(
        "import pytest\n\n\n@pytest.mark.slow\ndef test_probe():\n    pass\n",
        encoding="utf-8",
    )
    run_in_project(project, ["uv", "run", "pytest", "--no-cov", str(probe)])
    run_in_project(
        project,
        ["uv", "run", "pytest", "--no-cov", "-m", "not slow", str(probe)],
        allow_codes=(5,),
    )
    probe.unlink()


def test_generated_minimal_application_passes_lint_and_type_check(
    tmp_path: Path,
) -> None:
    project = generate(
        tmp_path,
        {"is_library": False, "use_pytest": False},
        run_tasks=True,
    )
    run_in_project(project, ["uv", "run", "ruff", "format", "--check", "."])
    run_in_project(project, ["uv", "run", "ruff", "check", "."])
    run_in_project(project, ["uv", "run", "ty", "check"])
