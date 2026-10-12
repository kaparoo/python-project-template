# python-project-template

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?logo=opensourceinitiative&logoColor=white)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%20%7C%203.14%20%7C%203.15-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)

The **PyTorch variant** of a personal
[copier](https://copier.readthedocs.io/) template: it bootstraps
deep-learning projects with `torch` / `torchvision` and the Astral
toolchain (`uv`, `ruff`, `ty`) pre-configured.

> This is the **`pytorch` branch**. For the plain base template, see
> `main`.

## 🚀 Quick start

```bash
# One-time: install copier
uv tool install copier

# Generate a new deep-learning project
# (--vcs-ref selects this pytorch branch)
copier copy --vcs-ref pytorch --UNSAFE gh:kaparoo/python-project-template my-ml-project
```

`--UNSAFE` is required because the template runs post-generation tasks
(`git init`, `uv lock`, `uv sync`, and an initial commit). Review
[`copier.yml`](./copier.yml) before trusting it.

Pull later template improvements into an existing project:

```bash
cd my-ml-project
copier update --UNSAFE --vcs-ref pytorch
```

`--vcs-ref pytorch` is required: the variant lives on the `pytorch`
branch, so `copier update` would otherwise jump to the latest Git tag
(which belongs to the base template on `main`).

The `.copier-answers.yml` file in each generated project records the
answers, so `copier update` can re-render against newer template
versions without losing your customizations.

## ⚙️ Options

`copier copy` prompts for the following:

| Question | Type | Default | Notes |
|----------|------|---------|-------|
| `project_name` | str | *(required)* | PEP 503 form: lowercase, hyphens |
| `project_description` | str | `""` | One-line summary |
| `package_name` | str | *derived* | snake_case of `project_name` |
| `author_name` | str | `Jaewoo Park` | Used in pyproject + LICENSE |
| `author_email` | str | `kaparoo2001@gmail.com` | |
| `github_username` | str | `kaparoo` | |
| `repo_name` | str | `{{ project_name }}` | |
| `python_version` | choice | `3.14` | Oldest supported; CI tests it and every newer choice. `3.13` / `3.14` / `3.15` |
| `license_year` | int | `2026` | Copyright year |
| `is_library` | bool | `true` | Adds `[build-system]` + `py.typed` |
| `release_automation` | choice | `manual` | `manual` / `github-oidc`; `github-oidc` ships `publish.yml` (libraries only) |
| `use_testpypi` | bool | `true` | Stage on TestPyPI before PyPI (libraries only) |
| `use_pytest` | bool | `false` | Adds `tests/` + pytest config |
| `coverage_fail_under` | int | `0` | Branch-coverage gate; `0` = off (pytest only) |
| `include_todo` | bool | `true` | Generates `TODO.md` + a README 📋 TODO section |
| `torch_version` | str | `2.12.1` | Minimum `torch` version |
| `torchvision_version` | str | `0.27.1` | Minimum `torchvision` version |
| `compute_backend` | choice | `cuda` | `cpu` / `cuda`; selects the PyTorch index |
| `cuda_version` | choice | `13.0` | `12.6` / `12.8` / `13.0` (asked only for `cuda`) |

`release_automation`, `use_testpypi`, and `coverage_fail_under` are only
asked when their parent feature is enabled (a library, or pytest).

- **`is_library = false`** produces an application (no build system, no
  `py.typed` marker); uv treats it as a non-distributable project.
- **`use_pytest`** defaults to `false` here: deterministic pytest
  workflows are impractical for most deep-learning code.
- **`compute_backend`** routes `torch` / `torchvision` through a
  `[[tool.uv.index]]`: `cpu` works everywhere, `cuda` (default, CUDA
  13.0) needs an NVIDIA GPU.

## 🗂️ Layout

```
.
├── .agents/            ← task guides for AI assistants (not shipped)
├── .github/workflows/  ← CI for this repo (not shipped)
├── copier.yml          ← questions, tasks, after-action messages
├── pyproject.toml      ← workspace dev tooling (copier + pytest + ruff)
├── template/           ← files rendered into generated projects
│   ├── pyproject.toml.jinja
│   ├── {{ package_name }}/
│   └── ...
├── tests/              ← tests for the template itself
├── TODO.md             ← open work on the template
└── AGENTS.md           ← guide for AI assistants working on this repo
```

## 🛠️ Development

```bash
git clone https://github.com/kaparoo/python-project-template
cd python-project-template
uv sync --group dev
uv run pytest          # generation-scenario tests
uv run pytest -m "not slow"  # skip the real-toolchain integration tests
```

[CI](./.github/workflows/ci.yml) runs `ruff` and the same tests on
Ubuntu and Windows for every push to `main` or `pytorch` and every
pull request.

### ✍️ Commit convention

Commits use a Gitmoji, a concrete imperative verb, and the name of what
changed (`` ✨ Add `ensure_dir` to `filesystem.utils` ``). The full rules,
with the emoji table and fixed forms, are in
[`template/.agents/commits.md.jinja`](./template/.agents/commits.md.jinja); this
repository follows them too, with the few differences listed in
[`AGENTS.md`](./AGENTS.md).

## 📋 TODO

See [TODO.md](./TODO.md) for open work on the template.

## 📜 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the template's version history.
The `pytorch` branch keeps an independent variant changelog with its
own `pytorch-v*` tag line.

## ⚖️ License

This project is distributed under the terms of the [MIT](./LICENSE) license.
