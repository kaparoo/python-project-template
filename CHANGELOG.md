# Changelog — PyTorch variant

All notable changes to the **PyTorch variant** of this copier template
(the `pytorch` branch) are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The variant is versioned **independently** from the base template, using
`pytorch-v*` Git tags and [Semantic Versioning](https://semver.org/):
`MAJOR` for changes that need a migration in generated projects, `MINOR`
for new copier options or features, `PATCH` for fixes.

> The base template (the `main` branch) keeps its own `v*` tags and
> [`CHANGELOG.md`](https://github.com/kaparoo/python-project-template/blob/main/CHANGELOG.md).
> `pytorch-v*` tags are deliberately not PEP 440 versions, so they never
> shadow the base template's `copier copy` / `copier update` resolution.

## [Unreleased]

## [1.3.0] - 2026-05-28

### Added

- `.github/workflows/ci.yml` — the variant's own CI workflow, resolving
  the item deferred at `1.2.0`. Runs on push to `main`, PRs, and
  `workflow_call` across a 3-OS matrix (ubuntu/windows/macos). A
  workflow-level `UV_INDEX: pytorch=https://download.pytorch.org/whl/cpu`
  forces the CPU PyTorch build for every `uv` command, so CI never
  downloads the multi-gigabyte CUDA wheel and the macOS leg resolves
  (CUDA wheels aren't published for macOS). `uv` re-resolves against
  that index, ignoring the committed CUDA `uv.lock` for the CI run.
  Steps: `uv sync`, `ruff format --check`, `ruff check`, `ty check`,
  and — only when `use_pytest` — `pytest`. Action majors pinned to the
  Node.js-24 natives (`actions/checkout@v6`, `astral-sh/setup-uv@v8.1.0`).

## [1.2.0] - 2026-05-28

Real-world feedback batch from `kaparoo-python` (generated from base
`v1.0.2`): coverage, docstrings, line endings, dependency bumps.

> The batch's `.github/workflows/ci.yml` is **not** shipped on the
> `pytorch` variant. The base template's CI runs `uv sync` on a 3-OS
> matrix, which would pull the multi-gigabyte `torch` wheel; a
> torch-install-avoidance CI strategy is deferred to its own design.

### Added

- `pytest-cov` integration: `pytest-cov>=7.1.0` dev dependency,
  `--cov` / `--cov-report=term-missing` in `addopts`, and
  `[tool.coverage.*]` config (branch coverage, data under
  `.cache/coverage/`). New `coverage_fail_under` copier question
  (default `0` = measure-only so a fresh project doesn't fail
  `pytest`; raise it once a baseline exists). All `use_pytest`-gated.
- `.gitattributes` normalizing line endings (`* text=auto` plus
  `eol=lf` for yml/yaml/toml/lock/py/md) — removes the Windows
  `LF will be replaced by CRLF` warnings.

### Changed

- Bumped generated dev-dependency minimums to the current latest:
  `ruff>=0.15.14`, `ty>=0.0.40`, `uv_build>=0.11.16` (`<0.12` kept).
  `pytest` stays `>=9.0.3`.
- Expanded the generated `AGENTS.md` docstring guidance from format-only
  to the intent/contracts philosophy (one-line summary shape, surface
  what the signature can't, Google sections incl. `Yields:` /
  `Type Parameters:`, backtick identifiers).

## [1.1.0] - 2026-05-27

### Added

- Generated projects now ship a Keep-a-Changelog `CHANGELOG.md`
  skeleton (empty `[Unreleased]`) so the documented release workflow
  has a target from the first commit.
- New `include_todo` copier question (default `true`) generates a
  `TODO.md` skeleton at the project root and links to it from the
  `README.md` 📋 TODO section. Disable to skip both.
- `template/AGENTS.md.jinja` gains a 17-row Gitmoji palette table
  under "Commit convention" so generated projects ship a uniform
  commit vocabulary distilled from the `kaparoo-python` v0.2.0 cycle.
- **Library mode only**: two named `[[tool.uv.index]]` entries in
  `pyproject.toml` (`pypi` as default, `testpypi` as `explicit = true`)
  configured with `publish-url` so `uv publish --index {testpypi,pypi}`
  Just Works against OS keyring tokens. For `pytorch` variant projects
  in library mode, these coexist with the existing PyTorch wheel index.
- **Library mode only**: new `## Releases` section in `AGENTS.md`
  documenting the 7-step procedure (CHANGELOG trim → version bump →
  `uv build` + `uvx twine check` → isolated install smoke test →
  TestPyPI → PyPI → annotated tag).

### Changed

- `template/README.md.jinja` replaces the bare badges + License body
  with a 5-section structure: 📦 Installation / 🧩 Modules / 📋 TODO
  / 📜 Changelog / ⚖️ License. Library mode shows `uv add` / `pip install`
  plus a Modules placeholder; application mode swaps to a 📦 Development
  setup section (clone + `uv sync`) and drops Modules.

### Fixed

- `copier.yml` `_exclude` no longer lists `CHANGELOG.md`. The entry
  was a leftover from before `_subdirectory: template` and was
  silently discarding the new `template/CHANGELOG.md.jinja` from
  every generation.

## [1.0.2] - 2026-05-27

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

## [1.0.1] - 2026-05-21

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

## [1.0.0] - 2026-05-21

First release of the PyTorch variant, forked from the base template
v1.0.1. It inherits every feature of that release; only the
PyTorch-specific deltas are listed below.

### Added

- `torch` / `torchvision` runtime dependencies in the generated
  `pyproject.toml`.
- Four copier questions: `torch_version` (default `2.11.0`),
  `torchvision_version` (default `0.26.0`), `compute_backend`
  (`cpu` / `cuda`, default `cuda`), and `cuda_version`
  (`12.6` / `12.8` / `13.0`, default `12.8`, asked only for `cuda`).
- A dedicated `[[tool.uv.index]]` plus `[tool.uv.sources]` that route
  `torch` / `torchvision` through the PyTorch wheel index matching the
  chosen compute backend (`cpu` or `cuXXX`).
- `Topic :: Scientific/Engineering :: Artificial Intelligence` classifier
  in the generated `pyproject.toml`.
- Three generation tests (`torch` dependencies, CUDA index routing, CPU
  index routing) and a `uv lock` resolution integration test — 18 tests
  total.

### Changed

- `use_pytest` now defaults to `false` (base template: `true`) —
  deterministic pytest workflows are impractical for most deep-learning
  code.
- The integration test resolves dependencies with `uv lock` instead of
  running the full post-generation `_tasks`; `uv sync` would download
  the multi-gigabyte `torch` wheel.
- `copier update` in generated projects must be invoked with
  `--vcs-ref pytorch`; the variant lives on a branch, not on the
  latest Git tag.

[Unreleased]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.3.0...pytorch
[1.3.0]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.2.0...pytorch-v1.3.0
[1.2.0]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.1.0...pytorch-v1.2.0
[1.1.0]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.0.2...pytorch-v1.1.0
[1.0.2]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.0.1...pytorch-v1.0.2
[1.0.1]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.0.0...pytorch-v1.0.1
[1.0.0]: https://github.com/kaparoo/python-project-template/releases/tag/pytorch-v1.0.0
