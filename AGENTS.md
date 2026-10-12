# Agent guide: `python-project-template`

This file is for AI coding assistants (Claude Code, Copilot, etc.) working
**on this repository itself**, the copier template source.

> ⚠️ Do not confuse with [`template/AGENTS.md`](./template/AGENTS.md), which
> is the (empty) AGENTS.md that ships **inside** generated projects.

---

## What this repo is

A personal [copier](https://copier.readthedocs.io/) template for bootstrapping
Python projects with `uv`, `ruff`, `ty`, and `pytest` pre-configured.

- **Author / sole user**: Jaewoo Park (`kaparoo`)
- **Audience of generated projects**: also the author
- **Public consumption**: not expected; design for the author's workflow first

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
[Merging `main` into `pytorch`](#merging-main-into-pytorch) below for
the recurring `CHANGELOG.md` resolution pattern.

## Layout: two distinct concerns

```
.
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

## Critical workflow rules

### 1. Working tree must be clean when running `pytest`

Copier's "dirty changes" handling has a known issue: untracked files at
the workspace root can cause `.vscode/extensions.json` to be silently
dropped during rendering. Tests will fail with confusing
`FileNotFoundError`s.

**Workflow**: commit (or stash) all changes → run `uv run pytest`. Expect
a couple of minutes: the integration tests that spin up generated
projects dominate the runtime (more so on `pytorch`, which adds `torch` /
index assertions and a real `uv lock` test), and a cold `uv` cache adds
more. It's slow, not hung.

### 2. Both branches of every `copier.yml` option must be tested

When adding a new option (e.g., `use_xyz`), add at least one test per
branch in `tests/test_generate.py`. Default-vs-enabled coverage is the
minimum bar.

### 3. Verify after every `template/` change

`uv run pytest` runs copier in-process for every scenario in
`tests/test_generate.py`. If even one file in `template/` changes,
run the suite before committing.

[`.github/workflows/ci.yml`](./.github/workflows/ci.yml) runs the same
suite, with `ruff format --check` and `ruff check`, on Ubuntu and
Windows for every push to `main` or `pytorch` and every pull request.
It catches what slipped through; it does not replace the local run.

### 4. Some tests run the real toolchain on a generated project

A few integration tests in `tests/test_generate.py` don't just inspect
rendered text: they `git init` / `uv lock` / `uv sync` / commit a
generated project, run the gates its `ci.yml` defines (`ruff format
--check`, `ruff check`, `ty check`, `pytest`), and build a library with
`uv build`, so a template or dependency change that breaks a generated
project fails here rather than only in manual dogfooding. These need:
- `git` and `uv` on PATH
- A configured git identity (`user.email`, `user.name`)
- Internet access (uv may download Python or wheels)

## Commit convention

Follow the commit convention documented under *Commit convention* in
[`README.md`](./README.md): emoji prefix, backticked
tool names, single-purpose commits, no rewriting of published history,
no skipped hooks.

In this repository, commit each completed step as you go, without
waiting to be asked; the user reviews the history step by step. This
differs on purpose from generated projects, whose `AGENTS.md` has
agents accumulate changes and commit only on request, split with
`git stash`. Pushing still waits for the user.

**AI-specific requirement**: append a `Co-Authored-By` trailer with the
acting assistant's own published identity; do not hardcode one vendor.

```
Co-Authored-By: <agent-name> <agent-email>
```

Examples:
- Claude Code → `Co-Authored-By: Claude <noreply@anthropic.com>`
- GitHub Copilot → `Co-Authored-By: Copilot <198982749+Copilot@users.noreply.github.com>`

## Changelog

`CHANGELOG.md` follows the same rules generated projects get; read
*Documentation → `CHANGELOG.md`* in
[`template/AGENTS.md.jinja`](./template/AGENTS.md.jinja) (skip the Jinja
tags; the library wording applies). In short: the six Keep a Changelog
categories only, in order; noun phrases under `Added` / `Removed`,
subject + present tense elsewhere; short entries, with `**Breaking:**`,
`Deprecated`, and `Removed` spelling out the upgrade; link references
at the bottom.

What counts as **external behavior** here is what a template user meets
through `copier copy` / `copier update`:

- the questions (names, help, choices, defaults, validators, `when`);
- the generated files and their content, including `.copier-answers.yml`;
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
repositories. `TODO.md` follows the rules generated projects
get; read *Documentation → `TODO.md`* in
[`template/AGENTS.md.jinja`](./template/AGENTS.md.jinja). Read it
before starting a change, and delete an item in the commit that
resolves it.

## Releases

This workspace itself is versioned with SemVer (see
[`CHANGELOG.md`](./CHANGELOG.md)):

- `MAJOR`: changes that break `copier update` for an existing
  generated project: a removed question or choice, or anything that
  needs a `_migrations` entry in `copier.yml` to update across.
- `MINOR`: new copier options, new generated files, new sections in
  generated docs.
- `PATCH`: fixes, doc tweaks, behavior-preserving cleanup.

### Cutting a release

For both branches the procedure is the same shape; only the tag form
differs (`vX.Y.Z` on `main`, `pytorch-vX.Y.Z` on `pytorch`).

1. Land all changes in `[Unreleased]` first. Verify with
   `uv run pytest` on a clean tree.
2. Promote: rename `## [Unreleased]` content to a dated
   `## [X.Y.Z] - YYYY-MM-DD` heading, add a fresh empty
   `## [Unreleased]` above, append the new comparison link at the
   bottom of the file.
3. Commit: `📝 Cut release \`vX.Y.Z\`` (body summarizes the bundle).
4. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Push: `git push origin <branch>` then `git push origin vX.Y.Z`.

For shared work, the order is **main first, then `pytorch`**:
release `vX.Y.Z` on `main`, merge `main` into `pytorch` (resolving
the CHANGELOG conflict per below), then promote pytorch's own
`[Unreleased]` to `[X.Y.Z]` and tag `pytorch-vX.Y.Z`. The two
version sequences are **independent**: `pytorch-v1.1.0` is not
required to mirror `v1.1.0` numerically once they diverge.

### Merging `main` into `pytorch`

After every `main` change cycle, merge forward:

```bash
git switch pytorch
git merge main --no-ff -m "🔀 Merge \`main\` into \`pytorch\`"
```

**Recurring `CHANGELOG.md` conflict**: pytorch keeps a variant-only
changelog (it does NOT mirror `main`'s release history). Resolution
principle:

- **Take** main's new `[Unreleased]` bullets (Added / Changed / Fixed):
  the underlying template change applies to both branches.
- **Drop** main's `## [X.Y.Z]` heading and any base `v*` comparison
  links: pytorch has its own release line.
- **Keep** pytorch's existing `## [X.Y.Z]` headings (the variant's
  prior releases) and the `pytorch-v*` comparison links at the
  bottom.

`tests/test_generate.py` may also conflict when the default values
diverge (notably `use_pytest`): keep pytorch's `{"use_pytest": True}`
override in tests that assume the pytest layer; keep pytorch's
expected-files list (no `tests/__init__.py` when use_pytest is
default-false there).

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

## Common workflows

### Adding a new copier option

1. Append the question to `copier.yml` under the appropriate
   `# ─── ... ───` section (e.g. `# ─── Project nature ───`).
2. Add conditional Jinja blocks in `template/pyproject.toml.jinja`,
   `template/.vscode/extensions.json.jinja`, etc., as needed.
3. Add tests in `tests/test_generate.py` covering both branches.
4. Commit changes, then run `uv run pytest` (clean tree required).
5. Update [`README.md`](./README.md) options table if applicable.

### Modifying ruff/ty/pytest config in generated projects

Edit `template/pyproject.toml.jinja`, then run the suite: the
integration tests render a generated project, build it (for libraries),
and run its lint/type/test gates, so a broken config surfaces here.

### Changing an existing `copier.yml` question

A question's default, choices, help, validator, or `when` is external
behavior (see [Changelog](#changelog)), so a change to one touches:

1. `copier.yml`: the question itself.
2. [`README.md`](./README.md) options table: its row (type, default,
   notes) and the prose under the table that describes it.
3. `tests/test_generate.py`: the new value and, where it matters, the
   old one.
4. `CHANGELOG.md` → `[Unreleased]`.

Removing a choice or a question breaks `copier update` for projects
that recorded it, which makes it `MAJOR` (see [Releases](#releases)).
Within a major, deprecate instead: keep the value working under a
`(deprecated)` label, say when it goes in its `help`, and warn in
`_message_after_copy` / `_message_after_update`.

### Changing the `python_version` choices

The list of offered versions lives in `copier.yml`; everything else
reads the `python_version` answer. A change touches:

1. `copier.yml`: `choices`, `default`, `help`, the deprecation
   warnings in the after-copy / after-update messages, and the list in
   the computed `python_versions` right below the question.
2. [`README.md`](./README.md): the Python badge lists every version
   still offered (deprecated ones included), and the options table row
   and its notes.
3. `tests/test_generate.py`: the default, a round-trip of each new
   choice, rejection of a version outside the list, and the warning for
   a deprecated choice and its absence on the default.
4. `CHANGELOG.md`: `Added` for a new choice, `Changed` for a new
   default, `Deprecated` / `Removed` for a choice on its way out.

Inside `template/`, `python_version` (the oldest supported version)
is rendered into `.python-version`, `requires-python`,
`[tool.ty.environment] python-version`, the README requirement line,
and the generated `AGENTS.md`. `python_versions` (every offered
version from that one up, computed and never recorded in
`.copier-answers.yml`) is rendered into the classifiers, the README
badge, and the `ci.yml` test matrix. A new place that needs a version
reads one of the two variables, never a literal.

The workspace's own Python (`.python-version`, `requires-python` in
[`pyproject.toml`](./pyproject.toml)) moves independently: only when
the dev tooling needs it.

### Bumping tool minimums

Raise generated-project and workspace minimums to the current PyPI
release together, in one `⬆️` commit:

1. `template/pyproject.toml.jinja`: the `dev` dependency group
   (`ruff`, `ty`, `pytest`, `pytest-cov`), `[build-system] requires`
   (`uv_build>=X.Y.Z,<X.(Y+1)`), `[tool.ruff] required-version`, and the
   "omitted (ruff vX.Y.Z)" note at the end of the file; re-check that
   the sections it lists still use only defaults.
2. [`pyproject.toml`](./pyproject.toml): the workspace `dev` group
   (`copier`, `pytest`, `ruff`) and its `[tool.ruff] required-version`,
   then `uv lock --upgrade` for `uv.lock`.
3. This file: `copier (>=X.Y.Z)` in
   [Toolchain choices](#toolchain-choices-dont-second-guess-without-cause).
4. Run the full suite: the integration tests run the new versions on a
   generated project, so an incompatible release fails here.
5. `CHANGELOG.md` → `Changed` for the generated projects' new
   minimums. A workspace-only bump stays out.

### Bumping GitHub Actions

1. Every `uses:` in `template/.github/workflows/ci.yml.jinja` and
   `publish.yml.jinja`, and in this repo's own
   `.github/workflows/ci.yml`: one action, one version across all
   three files.
   `pypa/gh-action-pypi-publish` stays on `release/v1`, the ref PyPA
   documents.
2. The version assertions in `tests/test_generate.py`
   (`test_ci_workflow_present_and_pinned` and the
   `test_release_automation_*` tests).
3. `CHANGELOG.md` → `Changed`.

### Keeping template files in step

`template/AGENTS.md.jinja` quotes the other template files: the README
section names (📦 Installation, 🚀 Quick start, 🧩 Modules, 📦 Setup,
🚀 Usage, 🗂️ Layout, 📋 TODO, 📜 Changelog, ⚖️ License), the
`CHANGELOG.md` and `TODO.md` skeletons (`## [Unreleased]`, `## Open`,
`_No entries yet._`, the `[Unreleased]` link reference), what
`publish.yml` does, and `pyproject.toml` settings (`error-on-warning`,
`fail_under`, `required-imports`). Change both sides in the same
commit, and assert the shared strings on both sides in
`tests/test_generate.py`.

### Each new year

`license_year` defaults to the current year, typed in by hand: Copier
has no date in its render context without the `jinja2-time`
extension, which every user would then have to install alongside
Copier. In January:

1. `copier.yml`: raise `license_year`'s `default`.
2. [`README.md`](./README.md): the `license_year` row of the options
   table.
3. `CHANGELOG.md` → `Changed`.

A recorded answer keeps its year, so only new projects see the change.

### Keeping this repo's `README.md` current

This repo's own [`README.md`](./README.md) is internal and does not
follow the generated-project README rules, but it states facts that
live elsewhere:

- the Python badge ↔ the `python_version` choices in `copier.yml`;
- the ⚙️ Options table ↔ every question in `copier.yml` (name, type,
  default, choices, `when`);
- the 🗂️ Layout tree ↔ the repository's top-level files and
  directories;
- the commit-convention table ↔ the prefixes this repo uses.

A change to the source updates the README in the same commit.

### Verifying end-to-end manually (dogfooding)

```bash
copier copy --vcs-ref HEAD --UNSAFE . ~/tmp/dogfood-$(date +%s) -d project_name=dogfood
cd ~/tmp/dogfood-*
uv run ruff check .
uv run ty check
uv run pytest    # may exit 5 = no tests collected, that's expected
uv build
```

`--vcs-ref HEAD` renders the current working commit; without it copier
falls back to the latest tag and silently misses post-tag changes.

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
