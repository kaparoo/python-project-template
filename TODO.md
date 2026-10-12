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

- Code style: file and module layout, class member order, docstrings,
  and comments. Start from the rules downstream projects already keep
  above their markers: `iivs-lib`'s `__all__` placements, singular
  module names, and PEP 695 alias imports; `cardiomyocytes`' two
  logging registers, meaningful `__repr__` for `%r`, and single-line
  error messages.

## Infrastructure

### Dependabot for generated projects

`template/.github/dependabot.yml`: Dependabot updates for generated
projects' `uv` dependencies and GitHub Actions. The minimums inside
`template/*.jinja` stay manual. Postponed by the user until the code
style and test rules land.

Revisit when the code style and test rules are in the generated
`AGENTS.md`.
