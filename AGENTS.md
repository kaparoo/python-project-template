# Agent guide — `python-project-template`

This file is for AI coding assistants (Claude Code, Copilot, etc.) working
**on this repository itself** — the copier template source.

> ⚠️ Do not confuse with [`template/AGENTS.md`](./template/AGENTS.md), which
> is the (empty) AGENTS.md that ships **inside** generated projects.

---

## What this repo is

A personal [copier](https://copier.readthedocs.io/) template for bootstrapping
Python projects with `uv`, `ruff`, `ty`, and `pytest` pre-configured.

- **Author / sole user**: Jaewoo Park (`kaparoo`)
- **Audience of generated projects**: also the author
- **Public consumption**: not expected — design for the author's workflow first

## Variants

Two branches, two independent version lines — never confuse them:

| Branch | Tag form | `copier` resolution | Default `use_pytest` |
|--------|----------|----------------------|----------------------|
| `main` | `vX.Y.Z` (PEP 440) | Latest `v*` tag — used when no `--vcs-ref` | `true` |
| `pytorch` | `pytorch-vX.Y.Z` (not PEP 440 → ignored by copier auto-resolve) | Requires explicit `--vcs-ref pytorch` (or `--vcs-ref pytorch-vX.Y.Z`) | `false` (DL workflows are non-deterministic) |

The `pytorch-v*` tags are **deliberately** not PEP 440 so they never
shadow the base template's `copier copy` / `copier update` resolution —
otherwise a default `copier copy gh:kaparoo/python-project-template`
would hijack to the highest tag regardless of branch.

**Variant policy**: shared changes land on `main` first, then are
merged forward into `pytorch`. The reverse direction is never used —
`pytorch`-only features (torch dependencies, compute-backend questions,
PyTorch wheel index) stay on `pytorch`. See
[Merging `main` into `pytorch`](#merging-main-into-pytorch) below for
the recurring `CHANGELOG.md` resolution pattern.

## Layout — two distinct concerns

```
.
├── copier.yml                 ← template configuration (questions, tasks, etc.)
├── pyproject.toml             ← WORKSPACE tooling only (copier + pytest + ruff)
├── tests/                     ← tests for the template itself
├── template/                  ← THE TEMPLATE — every file here ships to users
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

**Workflow**: commit (or stash) all changes → run `uv run pytest`. The
suite takes roughly **60–90 s** on `main` and **80–100 s** on `pytorch`
(the latter runs extra `torch` / index assertions and a real `uv lock`
integration test).

### 2. Both branches of every `copier.yml` option must be tested

When adding a new option (e.g., `use_xyz`), add at least one test per
branch in `tests/test_generate.py`. Default-vs-enabled coverage is the
minimum bar.

### 3. Verify after every `template/` change

`uv run pytest` runs copier in-process for every scenario in
`tests/test_generate.py`. If even one file in `template/` changes,
run the suite before committing.

### 4. The integration test runs real `_tasks`

`test_tasks_initialize_git_repo_with_initial_commit` actually executes
`git init`, `uv lock`, `uv sync`, `git add`, `git commit`. It needs:
- `git` and `uv` on PATH
- A configured git identity (`user.email`, `user.name`)
- Internet access (uv may download Python or wheels)

## Commit convention

Follow the commit convention documented in
[`README.md`](./README.md#commit-convention) — emoji prefix, backticked
tool names, single-purpose commits, no rewriting of published history,
no skipped hooks.

**AI-specific requirement**: append a `Co-Authored-By` trailer with the
acting assistant's own published identity — do not hardcode one vendor.

```
Co-Authored-By: <agent-name> <agent-email>
```

Examples:
- Claude Code → `Co-Authored-By: Claude <noreply@anthropic.com>`
- GitHub Copilot → `Co-Authored-By: Copilot <198982749+Copilot@users.noreply.github.com>`

## Releases

This workspace itself is versioned with SemVer (see
[`CHANGELOG.md`](./CHANGELOG.md)):

- `MAJOR` — changes that need a `_migrations` entry in `copier.yml`
  (so existing generated projects can update across them).
- `MINOR` — new copier options, new generated files, new sections in
  generated docs.
- `PATCH` — fixes, doc tweaks, behavior-preserving cleanup.

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
version sequences are **independent** — `pytorch-v1.1.0` is not
required to mirror `v1.1.0` numerically once they diverge.

### Merging `main` into `pytorch`

After every `main` change cycle, merge forward:

```bash
git switch pytorch
git merge main --no-ff -m "🔀 Merge \`main\` into \`pytorch\`"
```

**Recurring `CHANGELOG.md` conflict** — pytorch keeps a variant-only
changelog (it does NOT mirror `main`'s release history). Resolution
principle:

- **Take** main's new `[Unreleased]` bullets (Added / Changed / Fixed) —
  the underlying template change applies to both branches.
- **Drop** main's `## [X.Y.Z]` heading and any base `v*` comparison
  links — pytorch has its own release line.
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
| Template engine | `copier` (>=9.15.1) | Update-friendly via `.copier-answers.yml` |
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

Edit `template/pyproject.toml.jinja`. Run the test suite to confirm
the rendered output still passes `uv build`, `ruff check`, `ty check`,
and `pytest` in the integration test.

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

- Editing `template/.vscode/extensions.json` (no extension) — the active
  file is `template/.vscode/extensions.json.jinja`. The same applies to
  every `.jinja` file.
- Adding Python plugin-based tools (`mypy plugins`, `django-stubs`)
  to generated projects — `ty` deliberately has no plugin system. Use
  PEP 681 `dataclass_transform` or direct stubs instead.
- Committing `dist/`, `.venv/`, `.cache/`, `_gen_*/` test artifacts.
- Force-pushing to `main` or `pytorch` without explicit user
  authorization. Tags (`v*`, `pytorch-v*`) are equally off-limits to
  rewrites once pushed.
- Cherry-picking `pytorch`-only commits back onto `main`. The variant
  flow is one-directional (`main` → `pytorch`); back-porting would
  put torch dependencies on the base template.
