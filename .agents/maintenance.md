# Maintaining the template

Checklists for recurring changes to this repository. Each one lists
every place a change of that kind touches.

## Adding a new copier option

1. Append the question to `copier.yml` under the appropriate
   `# ─── ... ───` section (e.g. `# ─── Project nature ───`).
2. Add conditional Jinja blocks in `template/pyproject.toml.jinja`,
   `template/.vscode/extensions.json.jinja`, etc., as needed.
3. Add tests in `tests/` covering both branches.
4. Commit changes, then run `uv run pytest` (clean tree required).
5. Update [`README.md`](../README.md) options table if applicable.

## Modifying ruff/ty/pytest config in generated projects

Edit `template/pyproject.toml.jinja`, then run the suite: the
integration tests render a generated project, build it (for libraries),
and run its lint/type/test gates, so a broken config surfaces here.

## Changing an existing `copier.yml` question

A question's default, choices, help, validator, or `when` is external
behavior (see *Changelog* in [`AGENTS.md`](../AGENTS.md#changelog)),
so a change to one touches:

1. `copier.yml`: the question itself.
2. [`README.md`](../README.md) options table: its row (type, default,
   notes) and the prose under the table that describes it.
3. `tests/test_project.py`: the new value and, where it matters, the
   old one.
4. `CHANGELOG.md` → `[Unreleased]`.

Removing a choice or a question breaks `copier update` for projects
that recorded it, which makes it `MAJOR` (see [`releases.md`](./releases.md)).
Within a major, deprecate instead: keep the value working under a
`(deprecated)` label, say when it goes in its `help`, and warn in
`_message_after_copy` / `_message_after_update`.

## Changing the `python_version` choices

The list of offered versions lives in `copier.yml`; everything else
reads the `python_version` answer. A change touches:

1. `copier.yml`: `choices`, `default`, `help`, the deprecation
   warnings in the after-copy / after-update messages, and the list in
   the computed `python_versions` right below the question.
2. [`README.md`](../README.md): the Python badge lists every version
   still offered (deprecated ones included), and the options table row
   and its notes.
3. `tests/test_project.py`: the default, a round-trip of each new
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
[`pyproject.toml`](../pyproject.toml)) moves independently: only when
the dev tooling needs it.

## Bumping tool minimums

Raise generated-project and workspace minimums to the current PyPI
release together, in one `⬆️` commit:

1. `template/pyproject.toml.jinja`: the `dev` dependency group
   (`ruff`, `ty`, `pytest`, `pytest-cov`), `[build-system] requires`
   (`uv_build>=X.Y.Z,<X.(Y+1)`), `[tool.ruff] required-version`, and the
   "omitted (ruff vX.Y.Z)" note at the end of the file; re-check that
   the sections it lists still use only defaults.
2. [`pyproject.toml`](../pyproject.toml): the workspace `dev` group
   (`copier`, `pytest`, `ruff`) and its `[tool.ruff] required-version`,
   then `uv lock --upgrade` for `uv.lock`.
3. [`AGENTS.md`](../AGENTS.md): `copier (>=X.Y.Z)` in *Toolchain
   choices*.
4. Run the full suite: the integration tests run the new versions on a
   generated project, so an incompatible release fails here.
5. `CHANGELOG.md` → `Changed` for the generated projects' new
   minimums. A workspace-only bump stays out.

## Bumping GitHub Actions

1. Every `uses:` in `template/.github/workflows/ci.yml.jinja` and
   `publish.yml.jinja`, and in this repo's own
   `.github/workflows/ci.yml`: one action, one version across all
   three files.
   `pypa/gh-action-pypi-publish` stays on `release/v1`, the ref PyPA
   documents.
2. The version assertions in `tests/test_workflows.py`
   (`test_ci_workflow_present_and_pinned` and the
   `test_release_automation_*` tests).
3. `CHANGELOG.md` → `Changed`.

## Keeping template files in step

The generated agent guides (`template/AGENTS.md.jinja`,
`template/.agents/`, and `template/{% if use_pytest %}tests{% endif %}/AGENTS.md.jinja`)
quote the other template files: the README section names
(📦 Installation, 🚀 Quick start, 🧩 Modules, 📦 Setup, 🚀 Usage,
🗂️ Layout, 📋 TODO, 📜 Changelog, ⚖️ License), the `CHANGELOG.md` and
`TODO.md` skeletons (`## [Unreleased]`, `## Open`, `_No entries yet._`,
the `[Unreleased]` link reference), what `publish.yml` does, and
`pyproject.toml` settings (`error-on-warning`, `fail_under`,
`required-imports`). The core `AGENTS.md` indexes every guide in its
*Task guides* table, so a guide added or removed changes the table
too. Change both sides in the same commit, and assert the shared
strings on both sides in `tests/`.

## Each new year

`license_year` defaults to the current year, typed in by hand: Copier
has no date in its render context without the `jinja2-time`
extension, which every user would then have to install alongside
Copier. In January:

1. `copier.yml`: raise `license_year`'s `default`.
2. [`README.md`](../README.md): the `license_year` row of the options
   table.
3. `CHANGELOG.md` → `Changed`.

A recorded answer keeps its year, so only new projects see the change.

## Keeping this repo's `README.md` current

This repo's own [`README.md`](../README.md) is internal and does not
follow the generated-project README rules, but it states facts that
live elsewhere:

- the Python badge ↔ the `python_version` choices in `copier.yml`;
- the ⚙️ Options table ↔ every question in `copier.yml` (name, type,
  default, choices, `when`);
- the 🗂️ Layout tree ↔ the repository's top-level files and
  directories;
- the commit-convention table ↔ the prefixes this repo uses.

A change to the source updates the README in the same commit.

## Verifying end-to-end manually (dogfooding)

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
