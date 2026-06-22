# Changelog

All notable changes to this copier template are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The template is versioned with [Semantic Versioning](https://semver.org/):
`MAJOR` for changes that need a migration in generated projects, `MINOR`
for new copier options or features, `PATCH` for fixes.

## [Unreleased]

## [1.5.3] - 2026-06-22

### Changed

- Reordered the generated `README.md` badges and gave two of them logos:
  the `License` badge now leads (with the OSI logo via
  `?logo=opensourceinitiative`), `Python` gains the Python logo, and the
  `Copier` badge sits last (its documented placement). Library mode keeps
  its `PyPI` / `Downloads` badges, now after `License`. Badge URLs only —
  no rendered-content change beyond order and logos.

## [1.5.2] - 2026-06-22

### Changed

- Bumped generated dev-dependency minimums to the current latest:
  `ruff>=0.15.18`, `ty>=0.0.51`, `pytest>=9.1.1`, and `uv_build>=0.11.23`
  (`<0.12` kept). `pytest-cov` stays `>=7.1.0`. The generated
  `[tool.ruff]` `required-version` floor and the omitted-defaults note
  move to `0.15.18` in lockstep. Workspace dev tooling bumped to match
  (`copier>=9.15.2`, `pytest>=9.1.1`, `ruff>=0.15.18`).

## [1.5.1] - 2026-06-22

### Changed

- The generated `publish.yml`'s `github-release` job
  (`release_automation = github-oidc`) now fails fast when no matching
  `CHANGELOG.md` section is found for the tag, instead of silently
  creating a GitHub Release with an empty body. Promote `[Unreleased]`
  to a dated `## [X.Y.Z]` heading before tagging.

## [1.5.0] - 2026-06-22

### Added

- **CI hardening** in the generated `ci.yml`: a `concurrency` group
  (`ci-${{ github.ref }}`, `cancel-in-progress: true`) that cancels
  superseded runs, a `timeout-minutes: 20` cap on the matrix job, and
  `--locked` on `uv sync` so a stale `uv.lock` fails CI instead of being
  silently re-resolved.
- `publish.yml` (`release_automation = github-oidc`) gains three steps:
  the `build` job fails fast when the pushed `v*` tag does not match the
  `pyproject.toml` version (`uv version --short`); the TestPyPI upload
  sets `skip-existing: true` so a re-run tolerates an already-staged
  version; and a final `github-release` job creates the GitHub Release
  for the tag, pulling notes from the matching `CHANGELOG.md` section and
  attaching the sdist + wheel. The generated `AGENTS.md` "Releases"
  section documents the new pipeline shape.

### Changed

- Expanded the generated `AGENTS.md` conventions, distilled from a
  downstream project's review cycle:
  - **Docstrings** — summary-shape carve-outs (property getters and
    boolean *methods* take a noun phrase / "Whether ..."; boolean
    *functions* stay imperative), the self-explainable-consumed-method
    rule vs. generic abstract-base contracts, the closed-hierarchy
    family-map exception, and backticks on literal option values.
  - **Tests** (`use_pytest` only) — flat `def test_*` vs. grouping-only
    `class TestX:`, which source files legitimately need no test,
    helper/fixture locations, and a test-*quality* bullet (assert values
    *and* side effects, `pytest.raises(..., match=...)`, independently
    computed numbers, deterministic timing/IO, spy-verified batching).
  - **Error messages** — a *content* convention (name the valid set or
    the fix, not just the failure) layered on top of the `EM` ruff rule's
    format enforcement.
  - **Python style** — blank-line grouping with a blank line before the
    final `return`, and boxed comment banners in long modules.

## [1.4.4] - 2026-06-01

### Changed

- Stripped boilerplate comments from the generated `publish.yml`
  (the `# Reuse the CI workflow ...`, `# Build the artifacts ...`,
  `# Stage on TestPyPI first ...`, `# Manual-approval gate ...`, and
  `# OIDC for ... Trusted Publishing` annotations) and normalized
  to single blank-line separation between jobs. Architectural
  rationale lives in the generated `AGENTS.md` "Releases" section
  and in this CHANGELOG; the workflow file itself now reads as a
  clean declarative pipeline. Functional output is unchanged.

## [1.4.3] - 2026-06-01

### Changed

- Pulled `build` out of the `publish` job so the `github-oidc`
  `publish.yml` pipeline is always `ci → build → [testpypi →] pypi`,
  with `testpypi` the only conditional job. Previously,
  `use_testpypi=false` collapsed build + publish into a single job
  to save one runner; that meant the OIDC-holding job also ran the
  build, blurring the boundary between code that needs the Trusted
  Publishing token and code that doesn't. Now every `pypi` job
  downloads a pre-built artifact, so `id-token: write` is scoped
  strictly to the publish jobs and the `build` job has no token
  capability. Trade-off: one extra runner + ~10 s of artifact
  upload/download on every `use_testpypi=false` release.
- Simplified the `publish.yml` Jinja template alongside the
  structural change — the inner conditional now wraps just the
  optional `testpypi` job (~25 lines) and selects the `pypi` job's
  `needs:` target. Generated `use_testpypi=true` output is
  byte-identical to v1.4.2's.

## [1.4.2] - 2026-06-01

### Changed

- Collapsed the two conditional-filename `publish.yml` variants into a
  single `template/.github/workflows/publish.yml.jinja` with an
  internal `{% if use_testpypi %}` branch, gated by a Jinja-templated
  entry in `copier.yml`'s `_exclude`. The previous two-file design
  worked around copier's empirically verified behavior that filename
  conditionals don't trigger `.jinja`-suffix stripping
  (`{% if cond %}publish.yml.jinja{% endif %}` renders as a literal
  `publish.yml.jinja` with un-templated content). `_exclude` patterns
  are Jinja-templated and matched against destination paths
  (post-`.jinja` strip), so the same exclusion semantics carry over
  without splitting the source. Generated `publish.yml` output is
  byte-identical to the previous variants for both `use_testpypi`
  values; the change is purely internal.

## [1.4.1] - 2026-06-01

### Changed

- Aligned the generated `publish.yml` with the proven `kaparoo-python`
  workflow shape (both `use_testpypi` variants):
  - Swapped `uv publish --trusted-publishing always` for
    [`pypa/gh-action-pypi-publish@release/v1`](https://github.com/pypa/gh-action-pypi-publish)
    — PyPA's official OIDC publisher — with `print-hash: true` and
    `attestations: true` explicit. Functional behavior is unchanged
    (still Trusted Publishing + PEP 740 attestations), but the action
    is the de-facto standard and decouples the publish step from
    `uv`'s release cadence.
  - Each job gets a human-readable `name:` (`Verify`,
    `Build distributions`, `Publish to TestPyPI`, `Publish to PyPI`).
  - The build job's `setup-uv` step enables the action's cache
    (`enable-cache: true`) for faster repeat builds.
  - Switched the tag-pattern quotes from `"v*.*.*"` to `'v*.*.*'`
    for consistency with `kaparoo-python`.

## [1.4.0] - 2026-06-01

### Added

- New `use_testpypi` copier question (default `true`, gated on
  `is_library`) — controls whether generated projects stage releases
  on TestPyPI before pushing to real PyPI. PyPI uploads are permanent,
  so a TestPyPI rehearsal catches install-time issues (dependency
  resolution, missing files in the wheel, entry points) that
  `uvx twine check` doesn't.
- When `release_automation = manual`: `pyproject.toml` ships both
  `pypi` and `testpypi` named `[[tool.uv.index]]` entries with
  `publish-url`, and the generated `AGENTS.md` "Releases" section
  includes a `uv publish --index testpypi` rehearsal step before
  PyPI. With `use_testpypi=false`, only the `pypi` index ships and
  the rehearsal step is dropped.
- When `release_automation = github-oidc`: `publish.yml` becomes a
  4-job pipeline (`ci → build → testpypi → pypi`) that uploads
  built distributions as an artifact, publishes them to TestPyPI
  via Trusted Publishing, then — once the `pypi` environment is
  approved — publishes the *same* artifacts to PyPI. The setup
  checklist gains a "TestPyPI Trusted Publisher" item. With
  `use_testpypi=false`, the previous 2-job pipeline ships unchanged.

## [1.3.1] - 2026-05-28

### Changed

- Hardened the generated `publish.yml` (`release_automation=github-oidc`)
  to match the proven `kaparoo-python` workflow: added a
  `uvx twine check dist/*` metadata-verification step before upload, and
  tightened the trigger to `v*.*.*` (X.Y.Z only — no stray `v` tags).
  `uv publish` already uploads PEP 740 attestations by default, so no
  change was needed there.

## [1.3.0] - 2026-05-28

### Added

- Opt-in PyPI **publish automation** via a new `release_automation`
  copier question (`manual` default / `github-oidc`), gated on
  `is_library`. `github-oidc` ships `.github/workflows/publish.yml`:
  a `v*` tag push reuses the CI workflow as a release gate
  (`workflow_call`), then a `pypi` GitHub environment (manual-approval
  reviewer) gates a build and `uv publish --trusted-publishing always`
  — PyPI Trusted Publishing over OIDC, no stored token. The generated
  `AGENTS.md` "Releases" section branches on the answer: automated mode
  gets a tag-triggered procedure plus a one-time setup checklist
  (register the PyPI Trusted Publisher, create the `pypi` environment
  with a required reviewer); `manual` keeps the TestPyPI → PyPI keyring
  flow. TestPyPI staging stays a documented manual step.

## [1.2.0] - 2026-05-28

Real-world feedback batch from `kaparoo-python` (generated from
`v1.0.2`): CI, coverage, docstrings, line endings, dependency bumps.

### Added

- `.github/workflows/ci.yml` — a CI workflow running on push to
  `main`, PRs, and `workflow_call`. A 3-OS matrix
  (ubuntu/windows/macos) runs `uv sync`, `ruff format --check`,
  `ruff check`, `ty check`, and (only when `use_pytest`) `pytest`.
  Action majors pinned to the Node.js-24 natives current as of
  2026-05 (`actions/checkout@v6`, `astral-sh/setup-uv@v8.1.0`).
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
  Just Works against OS keyring tokens.
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

[Unreleased]: https://github.com/kaparoo/python-project-template/compare/v1.5.3...HEAD
[1.5.3]: https://github.com/kaparoo/python-project-template/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/kaparoo/python-project-template/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/kaparoo/python-project-template/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/kaparoo/python-project-template/compare/v1.4.4...v1.5.0
[1.4.4]: https://github.com/kaparoo/python-project-template/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/kaparoo/python-project-template/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/kaparoo/python-project-template/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/kaparoo/python-project-template/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/kaparoo/python-project-template/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/kaparoo/python-project-template/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/kaparoo/python-project-template/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/kaparoo/python-project-template/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/kaparoo/python-project-template/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/kaparoo/python-project-template/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/kaparoo/python-project-template/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/kaparoo/python-project-template/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/kaparoo/python-project-template/releases/tag/v1.0.0
