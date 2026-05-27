# TODO

Tracked items for the `python-project-template` workspace itself
(not for projects generated from it). Promote an item to a CHANGELOG
entry once it lands.

## Open

- [ ] **CI workflow** — add `.github/workflows/ci.yml` running
      `uv run ruff format --check .`, `uv run ruff check .`,
      `uv run ty check`, and `uv run pytest` on push and pull request.
      The generated projects' `AGENTS.md` already documents this
      pattern; mirror it for the template repository so regressions
      in the generation-test suite are caught at PR time. Once stable,
      consider extending to both branches via a matrix.

- [ ] **Coverage measurement** — add `pytest-cov` to the workspace
      `dev` dependency group and configure `addopts = [..., "--cov=tests",
      "--cov-report=term-missing"]` in `[tool.pytest.ini_options]`,
      plus a `[tool.coverage.*]` section in `pyproject.toml`. Tracks
      whether new copier options actually exercise their conditional
      branches in `tests/test_generate.py`. Consider a minimum-threshold
      gate in the CI workflow once a baseline is established.
