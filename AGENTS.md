# Agent guide: `python-project-template`

This file is for AI coding assistants (Claude Code, Copilot, etc.)
working **on this repository itself**, the copier template source.

> ⚠️ Do not confuse it with
> [`template/AGENTS.md.jinja`](./template/AGENTS.md.jinja), which
> renders the `AGENTS.md` that ships **inside** generated projects.

---

## What this repo is

A personal [copier](https://copier.readthedocs.io/) template for bootstrapping
Python projects with `uv`, `ruff`, `ty`, and `pytest` pre-configured.

- **Author / sole user**: Jaewoo Park (`kaparoo`)
- **Audience of generated projects**: also the author
- **Public consumption**: not expected; design for the author's
  workflow first

## Variants

Two branches, two independent version lines. Never confuse them:

| Branch | Tag form | `copier` resolution | Default `use_pytest` |
|--------|----------|----------------------|----------------------|
| `main` | `vX.Y.Z` (PEP 440) | Latest `v*` tag, used when no `--vcs-ref` | `true` |
| `pytorch` | `pytorch-vX.Y.Z` (not PEP 440 → ignored by copier auto-resolve) | Requires explicit `--vcs-ref pytorch` (or `--vcs-ref pytorch-vX.Y.Z`) | `false` (DL workflows are non-deterministic) |

The `pytorch-v*` tags are **deliberately** not PEP 440 so they never
shadow the base template's `copier copy` / `copier update` resolution;
otherwise a default `copier copy gh:kaparoo/python-project-template`
would hijack to the highest tag regardless of branch.

**Variant policy**: shared changes land on `main` first, then are
merged forward into `pytorch`. The reverse direction is never used:
`pytorch`-only features (torch dependencies, compute-backend questions,
PyTorch wheel index) stay on `pytorch`. See
[`.agents/releases.md`](./.agents/releases.md#merging-main-into-pytorch)
for the recurring `CHANGELOG.md` resolution pattern.

## Layout: two distinct concerns

```
.
├── .agents/                   ← task guides for this repo (not shipped)
├── .github/workflows/ci.yml   ← CI for this repo (not shipped)
├── copier.yml                 ← template configuration (questions, tasks, etc.)
├── pyproject.toml             ← WORKSPACE tooling only (copier + pytest + ruff)
├── tests/                     ← tests for the template itself
├── TODO.md                    ← open work on the template itself
├── template/                  ← THE TEMPLATE: every file here ships to users
│   ├── pyproject.toml.jinja   ← rendered into generated projects
│   ├── ...
│   └── {{ package_name }}/    ← directory name is a Jinja variable
└── AGENTS.md                  ← this file
```

**Never confuse `pyproject.toml` (workspace dev tooling) with
`template/pyproject.toml.jinja` (what generated projects receive).**
Changes meant for downstream projects belong in `template/`.

## Toolchain choices (don't second-guess without cause)

| Concern | Choice | Why |
|---------|--------|-----|
| Package manager / lock | `uv` | Fast, single tool for env + lock + run |
| Build backend | `uv_build` | Astral consistency, 10–35× faster than alternatives |
| Linter / formatter | `ruff` | Single binary, comprehensive ruleset |
| Type checker | `ty` (beta) | Astral, plugin-free; Ruff `ANN` rules cover annotation enforcement |
| Test runner | `pytest` | Standard |
| Template engine | `copier` (>=9.18.2) | Update-friendly via `.copier-answers.yml` |
| AI agent config | `AGENTS.md` + `CLAUDE.md` (just `@AGENTS.md`) | Editor-agnostic with Claude Code shim |

## Critical workflow rules

### 1. Working tree must be clean when running `pytest`

Copier's "dirty changes" handling has a known issue: untracked files at
the workspace root can cause `.vscode/extensions.json` to be silently
dropped during rendering. Tests will fail with confusing
`FileNotFoundError`s.

**Workflow**: commit (or stash) all changes, then run `uv run pytest`.
Expect about a minute: the integration tests that spin up generated
projects dominate the runtime (more so on `pytorch`, which adds
`torch` and index assertions and a real `uv lock` test), and a cold
`uv` cache adds more. It is slow, not hung.

### 2. Both branches of every `copier.yml` option must be tested

When adding a new option (e.g., `use_xyz`), add at least one test per
branch, usually in `tests/test_project.py`. Default-vs-enabled
coverage is the minimum bar.

### 3. Verify after every `template/` change

`uv run pytest` runs copier in-process for every scenario in
`tests/`. If even one file in `template/` changes, run the suite
before committing; `uv run pytest -m "not slow"` skips the
real-toolchain tests for quick iteration, but not before a commit.

The suite has one module per concern: `test_project.py` (questions,
generated files, `pyproject.toml`), `test_docs.py` (README, CHANGELOG,
TODO, and the width and dash checks over every generated document),
`test_agents_md.py`, `test_workflows.py` (CI and `publish.yml`), and
`test_integration.py` (the real toolchain, marked `slow`). Shared code
lives in `tests/helpers.py`; `tests/conftest.py` holds a session
`render` fixture that renders each set of answers once for the tests
that only read. A test that writes into the project or runs `_tasks`
calls `generate` on its own `tmp_path`. Tests follow the test rules
generated projects get: no docstrings or comments, and `prose()` for
phrases that a rewrap could split.

[`.github/workflows/ci.yml`](./.github/workflows/ci.yml) runs the same
suite, with `ruff format --check` and `ruff check`, on Ubuntu and
Windows for every push to `main` or `pytorch` and every pull request.
It catches what slipped through; it does not replace the local run.

### 4. Some tests run the real toolchain on a generated project

The integration tests in `tests/test_integration.py` don't just inspect
rendered text: they `git init` / `uv lock` / `uv sync` / commit a
generated project, run the gates its `ci.yml` defines (`ruff format
--check`, `ruff check`, `ty check`, `pytest`), and build a library with
`uv build`, so a template or dependency change that breaks a generated
project fails here rather than only in manual dogfooding. These need:
- `git` and `uv` on PATH
- A configured git identity (`user.email`, `user.name`)
- Internet access (uv may download Python or wheels)

## Task guides

Rules for one kind of task live in their own file. Read the guide
before you start that task:

| Before you ...                                  | Read                      |
| ----------------------------------------------- | ------------------------- |
| add or change a `copier.yml` question           | `.agents/maintenance.md`  |
| change the `python_version` choices             | `.agents/maintenance.md`  |
| bump tool minimums or GitHub Actions            | `.agents/maintenance.md`  |
| change a string the agent guides quote          | `.agents/maintenance.md`  |
| change the facts this repo's `README.md` states | `.agents/maintenance.md`  |
| raise `license_year` in January                 | `.agents/maintenance.md`  |
| dogfood a generated project by hand             | `.agents/maintenance.md`  |
| cut a release (only when the user asks)         | `.agents/releases.md`     |
| merge `main` into `pytorch`                     | `.agents/releases.md`     |

## Commit convention

Commits here follow the convention generated projects get: read
[`template/.agents/commits.md.jinja`](./template/.agents/commits.md.jinja)
(subject form, emoji table, body, trailers, fixed forms). Only these
differ:

- Commit each completed step as you go, without waiting to be asked;
  the user reviews the history step by step. Generated projects
  instead accumulate changes and commit only on request, split with
  `git stash`. Pushing still waits for the user.
- A release commit is `🔖 Release version X.Y.Z` on `main` and
  `` 🔖 Release `pytorch` version X.Y.Z `` on `pytorch`.
- Merging `main` forward is `` 🔀 Merge `main` into `pytorch` ``.
- The object of a subject names the file or area of this repository:
  `copier.yml`, `template/README.md.jinja`, the generated `AGENTS.md`,
  or the workspace `pyproject.toml`.

## Changelog

`CHANGELOG.md` follows the same rules generated projects get; read
[`template/.agents/changelog.md.jinja`](./template/.agents/changelog.md.jinja)
(skip the Jinja tags; the library wording applies). In short: the six
Keep a Changelog categories only, in order; noun phrases under
`Added` / `Removed`, subject + present tense elsewhere; short entries,
with `**Breaking:**`, `Deprecated`, and `Removed` spelling out the
upgrade; link references at the bottom.

What counts as **external behavior** here is what a template user meets
through `copier copy` / `copier update`:

- the questions (names, help, choices, defaults, validators, `when`);
- the generated files and their content, including
  `.copier-answers.yml`;
- `_tasks`, the after-copy / after-update messages, and `_migrations`.

Everything that stays in this repository is internal and stays out:
`pyproject.toml` / `uv.lock` / `.python-version` / `.vscode/` of the
workspace, `tests/`, and this repo's own `README.md` and `AGENTS.md`.

The `pytorch` branch keeps its variant changelog under the same rules.

## TODO

[`TODO.md`](./TODO.md) holds open work on this template: releases, the
`pytorch` variant, and rule or infrastructure changes put off for
later. What the generated projects must change after an update is
theirs, not the template's, and stays out of it: the user keeps that
list in `../python-project-template-downstream.md`, next to the
repositories. `TODO.md` follows the rules generated projects get,
in the template's `.agents/` TODO guide (its file name is a Jinja
conditional). Read it before starting a change, and delete an item in
the commit that resolves it.

## Things to avoid

- Editing `template/.vscode/extensions.json` (no extension): the active
  file is `template/.vscode/extensions.json.jinja`. The same applies to
  every `.jinja` file.
- Adding Python plugin-based tools (`mypy plugins`, `django-stubs`)
  to generated projects: `ty` deliberately has no plugin system. Use
  PEP 681 `dataclass_transform` or direct stubs instead.
- Committing `dist/`, `.venv/`, `.cache/`, `_gen_*/` test artifacts.
- Force-pushing to `main` or `pytorch` without explicit user
  authorization. Tags (`v*`, `pytorch-v*`) are equally off-limits to
  rewrites once pushed.
- Cherry-picking `pytorch`-only commits back onto `main`. The variant
  flow is one-directional (`main` → `pytorch`); back-porting would
  put torch dependencies on the base template.
