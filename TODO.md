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

## Infrastructure

### Dependabot for generated projects

`template/.github/dependabot.yml`: Dependabot updates for generated
projects' `uv` dependencies and GitHub Actions. The minimums inside
`template/*.jinja` stay manual. The user postponed it until the code
style and test rules landed; both are now in.

Revisit when the user takes it up.

## This repository

- `tests/test_generate.py`: refactor it to the test rules generated
  projects now get, for consistency. Its tests carry docstrings and
  explanatory comments, which those rules leave out unless the user
  asks; the file is also one 1,100-line module where the rules would
  split it by concern.
