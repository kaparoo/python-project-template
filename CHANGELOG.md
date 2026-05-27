# Changelog

All notable changes to this copier template are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The template is versioned with [Semantic Versioning](https://semver.org/):
`MAJOR` for changes that need a migration in generated projects, `MINOR`
for new copier options or features, `PATCH` for fixes.

## [Unreleased]

## [1.0.3] - 2026-05-27

### Removed

- Empty placeholder `tests/conftest.py` from generated projects.
  Real-world author experience (`kaparoo-python` commit `f446b26`)
  showed the file as friction without value — create it when a real
  fixture lands. The `tests/__init__.py` package marker remains (it
  satisfies ruff's `INP` rule and keeps the directory as a proper
  package).

### Changed

- The generated `AGENTS.md` "Conventions" section gains three bullets:
  where to put `conftest.py` (default `tests/conftest.py`; root only
  for `pytest_plugins` declarations, doctest fixtures shared with
  source files, or project-wide collection hooks); mirroring the
  package layout under `tests/`; and using `ty`'s own error names
  in `# ty: ignore[<error-name>]` suppressions rather than mypy /
  pyright codes.

### Fixed

- Adopted PEP 639 license metadata in the generated `pyproject.toml`:
  added `license-files = ["LICENSE"]` and dropped the deprecated
  `"License :: OSI Approved :: MIT License"` classifier (it emitted
  a `uv build` deprecation warning).

## [1.0.2] - 2026-05-21

### Fixed

- Generated projects with `is_library=false` + `use_pytest=true` now set
  `pythonpath = ["."]` under `[tool.pytest.ini_options]`. Without
  `[build-system]` uv does not editable-install the project, so the
  flat-layout package was not importable from `tests/` under pytest's
  default `--import-mode=importlib`. Added a `tests/test_generate.py`
  case for the previously-untested combination.

- Replaced the `shields.io` PyPI monthly downloads badge in the
  generated `README.md` with a Pepy badge. The `shields.io` endpoint
  frequently rendered as "rate limited by upstream service" once the
  generated project was actually published to PyPI
  ([badges/shields#11620](https://github.com/badges/shields/issues/11620)).
  Pepy serves the badge image directly and isn't subject to the same
  rate limits.

## [1.0.1] - 2026-05-21

### Fixed

- `tests/test_generate.py` renders the template at `HEAD` via copier's
  `vcs_ref`. Without it copier defaults to the latest tag, so commits
  made after a release tag were silently not exercised by the suite.

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

[Unreleased]: https://github.com/kaparoo/python-project-template/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/kaparoo/python-project-template/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/kaparoo/python-project-template/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/kaparoo/python-project-template/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/kaparoo/python-project-template/releases/tag/v1.0.0
