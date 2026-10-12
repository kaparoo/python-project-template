from __future__ import annotations

__all__ = (
    "TEMPLATE_ROOT",
    "Render",
    "generate",
    "prose",
    "run_in_project",
    "sections",
)

import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final

import copier

TEMPLATE_ROOT: Final = Path(__file__).parent.parent

type Render = Callable[[Mapping[str, object] | None], Path]


def generate(
    dst: Path,
    data: Mapping[str, object] | None = None,
    *,
    run_tasks: bool = False,
) -> Path:
    """Render the template into `dst` with the given answers.

    `project_name` defaults to `test-app`. `vcs_ref="HEAD"` renders the
    current commit, uncommitted changes included; without it Copier would
    take the latest tag. `run_tasks` runs `_tasks` (`git init`, `uv lock`,
    `uv sync`, the first commit), which only the integration tests need.
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


def run_in_project(
    project: Path,
    cmd: list[str],
    *,
    allow_codes: tuple[int, ...] = (0,),
) -> None:
    """Run `cmd` inside a generated project and fail with its output."""
    result = subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    stdout, stderr = result.stdout, result.stderr
    assert result.returncode in allow_codes, (
        f"`{' '.join(cmd)}` exited {result.returncode}\n"
        f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}"
    )


def sections(readme: str) -> list[str]:
    """Return the `##` headings of a rendered README, in order."""
    return [line for line in readme.splitlines() if line.startswith("## ")]


def prose(text: str) -> str:
    """Return `text` with every run of whitespace flattened to one space.

    Rendered documents wrap at 72 columns, so a phrase can break across
    lines anywhere; checking against the flattened text keeps an
    assertion independent of where the wrap falls.
    """
    return re.sub(r"\s+", " ", text)
