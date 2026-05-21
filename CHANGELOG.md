# Changelog

All notable changes to this copier template are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The template is versioned with [Semantic Versioning](https://semver.org/):
`MAJOR` for changes that need a migration in generated projects, `MINOR`
for new copier options or features, `PATCH` for fixes.

## [Unreleased]

## [1.0.0] - 2026-05-21

First tagged release — a personal copier template for bootstrapping
Python projects with the Astral toolchain (`uv`, `ruff`, `ty`) plus
`pytest`.

### Added

- Copier template rendered from `template/`, with 11 questions: project
  identity (`project_name`, `project_description`, `package_name`),
  author, GitHub, `python_version`, `license_year`, and the `is_library`
  / `use_pytest` feature toggles.
- Validators for `project_name` (PEP 503 form) and `package_name`
  (Python identifier).
- Pre-configured toolchain in the generated `pyproject.toml`: `uv` with
  the `uv_build` backend, `ruff`, `ty`, and `pytest`.
- `is_library` option — toggles `[build-system]`,
  `[tool.uv.build-backend]`, the `py.typed` marker, the `Typing :: Typed`
  classifier, and the PyPI badges.
- `use_pytest` option — toggles the `tests/` suite, `[tool.pytest.ini_options]`,
  the ruff `PT` rule with `flake8-pytest-style`, per-file-ignores, and the
  test-adapter VSCode extension.
- Post-generation `_tasks` — `git init`, `uv lock`, `uv sync`, and an
  initial commit (run with `copier copy --UNSAFE`).
- After-action messages for `copier copy` and `copier update`, plus a
  `_migrations` scaffold for future breaking changes.
- Enforced Python conventions in generated projects: `from __future__
  import annotations` in every module (empty `__init__.py` exempt),
  builtin generics over `typing.List`/`Dict`/`Tuple`/`Type`, and
  ruff-driven import ordering.
- Generated `AGENTS.md` — a starter agent guide covering the toolchain,
  commands, the Gitmoji commit convention, and Python style (including
  Google-style docstrings and PEP 723 scripts).
- Workspace tooling: `copier` + `pytest` + `ruff`, 15 generation tests
  in `tests/test_generate.py`, and an `AGENTS.md` for the template
  repository itself.

[Unreleased]: https://github.com/kaparoo/python-project-template/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/kaparoo/python-project-template/releases/tag/v1.0.0
