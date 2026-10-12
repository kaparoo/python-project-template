# TODO

Open work on this template that is not done yet: deferred, blocked on
a decision, or a known limitation. Delete an item in the commit that
resolves it.

## Releases and variants

- Cut `v1.6.0` once the user asks for it. `[Unreleased]` already holds
  a minor release: the `python_version` range moved to 3.13–3.15, the
  CI Python matrix, and the generated `AGENTS.md` documentation,
  dependency, and README rules.
- Run the generated CI on GitHub Actions once: render a project, push
  it to a scratch repository, and check that Linux runs every
  supported version while Windows and macOS fall back to
  `.python-version`. The tests only parse the matrix.

### Merge `main` into `pytorch`

`pytorch` has none of the commits from `v1.5.5` on. Expect conflicts
beyond the usual `CHANGELOG.md` one (see *Merging `main` into
`pytorch`* in `AGENTS.md`):

- `template/AGENTS.md.jinja`, which has drifted about 300 lines;
- `template/README.md.jinja`, whose PyTorch and CUDA badges now go
  right after the Python badge;
- `template/.github/workflows/ci.yml.jinja`: the Python matrix against
  the variant's CPU `torch` install and its `lock` job;
- `tests/test_generate.py`, where `use_pytest` defaults to `false`.

Before taking the matrix, check which Python versions the pinned
`torch` and `torchvision` ship wheels for, and narrow
`python_versions` on that branch to match.

Revisit when `v1.6.0` is tagged: shared work lands on `main` first.

### Remove the `3.12` choice in 2.0.0

`3.12` is deprecated in 1.6.0. Removing it makes a recorded `3.12`
answer fail validation on `copier update`, so 2.0.0 needs a
`_migrations` entry, or at least an after-update message, that moves
such a project to `3.13`.

Revisit when 2.0.0 is planned.

## Downstream projects

All three wait on `v1.6.0` (`cardiomyocytes` on the `pytorch-v*`
release that follows it). After `copier update`, each needs its
required status checks renamed, since CI job names now carry the
Python version.

### Bring `kaparoo-python` in line

- `README.md`: rename 🎯 Quick example to 🚀 Quick start and move it
  before 🧩 Modules; match the description's trailing period to
  `pyproject.toml`.
- `AGENTS.md`: drop the sub-README rule above the marker, which the
  template now carries.
- Sub-READMEs: list only `##` sections in `## Contents`.
- `TODO.md`: drop the heading emoji and the "Last updated" footer.

Revisit when `v1.6.0` is out.

### Bring `iivs-lib` in line

- `README.md`: move 🙏 Acknowledgements before 📋 TODO; cut
  🧩 Modules down to a hub over the sub-READMEs; add ⌨️ CLI for
  `iivs_cli`; replace the relative `./iivs/dhm/constants.py` link.
- Publish a release afterwards: the PyPI page keeps the broken
  relative links until a new version is uploaded.

Revisit when `v1.6.0` is out.

### Bring `cardiomyocytes` in line

- `README.md`: rename 🚀 Getting started to 📦 Setup, and write
  🚀 Usage and 🗂️ Layout for `configs/` and `scripts/`.
- `TODO.md`: move the settled decisions into `docs/decisions/`
  records, delete implemented and struck-through items, and keep the
  rest as items. It stays in Korean.

Revisit when the `pytorch-v*` release after `v1.6.0` is out.

## Generated `AGENTS.md` rules

- Definition of done: run the format, lint, type-check, and test gates
  before committing.
- Git scope for agents: when to push, whether to branch, and no force
  pushes or tag rewrites.
- Secrets: no tokens in code or docs; `.env` comes from a script or an
  example file.
- Tests: markers for slow or GPU tests, when to raise `fail_under`,
  and a failing regression test before a fix.
- Code style: file and module layout, class member order, docstrings,
  and comments. Start from the rules downstream projects already keep
  above their markers: `iivs-lib`'s `__all__` placements, singular
  module names, and PEP 695 alias imports; `cardiomyocytes`' two
  logging registers, meaningful `__repr__` for `%r`, and single-line
  error messages.
- `template/pyproject.toml.jinja`: select `ruff`'s `FIX` rules so a
  `# TODO` comment fails lint. Waits on the user's decision.

## Infrastructure

Each waits on the user's decision.

- `.github/workflows/`: CI for this repository, running
  `uv run pytest` on push. The suite needs `git`, `uv`, and a git
  identity.
- `template/.github/dependabot.yml`: Dependabot updates for generated
  projects' `uv` dependencies and GitHub Actions. The minimums inside
  `template/*.jinja` stay manual.
- `template/.github/workflows/ci.yml.jinja`: `uv build` and
  `uvx twine check` for libraries, so packaging breaks surface before
  a release.
- `template/.gitignore`: ignores all of `.claude/`; consider
  committing `.claude/settings.json` and ignoring only
  `settings.local.json`.
- `copier.yml`: `license_year` defaults to `2026`; bump it each
  January or compute it from the current date.
