from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from tests.helpers import generate

if TYPE_CHECKING:
    from pathlib import Path


pytestmark = pytest.mark.slow


def test_generated_project_resolves_with_torch(tmp_path: Path) -> None:
    project = generate(tmp_path)
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
