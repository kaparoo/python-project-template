from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import generate

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from tests.helpers import Render


@pytest.fixture(scope="session")
def render(tmp_path_factory: pytest.TempPathFactory) -> Render:
    """Render the template once per set of answers, for tests that only read.

    A test that writes into the project, or runs `_tasks`, calls `generate`
    on its own `tmp_path` instead.
    """
    cache: dict[str, Path] = {}

    def render_once(data: Mapping[str, object] | None = None) -> Path:
        key = repr(sorted((data or {}).items()))
        if key not in cache:
            cache[key] = generate(tmp_path_factory.mktemp("project"), data)
        return cache[key]

    return render_once
