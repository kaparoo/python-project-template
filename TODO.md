# TODO

Open work on this template that is not done yet: deferred, blocked on
a decision, or a known limitation. Delete an item in the commit that
resolves it.

## Releases and variants

- Cut `v2.0.0` once the user asks for it. It is a major release:
  removing the `3.12` choice breaks `copier update` for a project that
  recorded it. `[Unreleased]` also holds the CI Python matrix and build
  job, the stricter `ruff` settings, and the generated `AGENTS.md`
  workflow, code style, test, dependency, and documentation rules.
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
- the modules in `tests/`, where `use_pytest` defaults to `false`.

Work the variant needs beyond resolving conflicts:

- Narrow the `python_version` choices and the computed
  `python_versions` to 3.13–3.14. `torch` 2.12.1 and `torchvision`
  0.27.1 ship wheels for cp310–cp314 only (CPU and `cu130` alike), so a
  3.15 job could not install them. Widen it once they ship cp315.
- Fold the new CI into the variant's: the matrix and `setup-uv`'s
  `python-version` under the job-level `UV_INDEX` CPU override, the
  separate `lock` job in place of `--locked`, and `UV_INDEX` on the
  library `build` job too, or its isolated install pulls the CUDA
  `torch` from PyPI.
- In the generated `AGENTS.md`: say the `lock` job, not
  `uv sync --locked`, catches a stale lock; add to *Supported Python
  versions* that `torch` must ship wheels for each one; list what moves
  with `torch_version` (the minimum and the badge); recast the
  variant-only lines that still use em dashes.
- Add `{"use_pytest": True}` to the new tests that assume pytest, and
  expect the narrower matrix.
- Also, as agreed: generate a `tests/marks.py` holding a
  `requires_cuda` skip mark when `use_pytest` is on, and pre-fill the
  GPU and driver requirement in an application's 📦 Setup when
  `compute_backend` is `cuda`.

Revisit when `v2.0.0` is tagged: shared work lands on `main` first.

## Infrastructure

### Dependabot for generated projects

`template/.github/dependabot.yml`: Dependabot updates for generated
projects' `uv` dependencies and GitHub Actions. The minimums inside
`template/*.jinja` stay manual. The user postponed it until the code
style and test rules landed; both are now in.

Revisit when the user takes it up.
