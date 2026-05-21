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

[Unreleased]: https://github.com/kaparoo/python-project-template/compare/pytorch-v1.0.0...pytorch
[1.0.0]: https://github.com/kaparoo/python-project-template/releases/tag/pytorch-v1.0.0
