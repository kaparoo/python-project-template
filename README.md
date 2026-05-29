# python-project-template

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)

A personal [copier](https://copier.readthedocs.io/) template for bootstrapping
Python projects with the Astral toolchain — `uv`, `ruff`, `ty` — plus `pytest`,
all pre-configured.

## 🚀 Quick start

```bash
# One-time: install copier
uv tool install copier

# Generate a new project
copier copy --UNSAFE gh:kaparoo/python-project-template my-new-project
```

`--UNSAFE` is required because the template runs post-generation tasks
(`git init`, `uv lock`, `uv sync`, and an initial commit). Review
[`copier.yml`](./copier.yml) before trusting it.

Pull later template improvements into an existing project:

```bash
cd my-new-project
copier update --UNSAFE
```

The `.copier-answers.yml` file in each generated project records the
answers, so `copier update` can re-render against newer template
versions without losing your customizations.

## ⚙️ Options

`copier copy` prompts for the following:

| Question | Type | Default | Notes |
|----------|------|---------|-------|
| `project_name` | str | *(required)* | PEP 503 form — lowercase, hyphens |
| `project_description` | str | `""` | One-line summary |
| `package_name` | str | *derived* | snake_case of `project_name` |
| `author_name` | str | `Jaewoo Park` | Used in pyproject + LICENSE |
| `author_email` | str | `kaparoo2001@gmail.com` | |
| `github_username` | str | `kaparoo` | |
| `repo_name` | str | `{{ project_name }}` | |
| `python_version` | choice | `3.14` | `3.12` / `3.13` / `3.14` |
| `license_year` | int | `2026` | Copyright year |
| `is_library` | bool | `true` | Adds `[build-system]` + `py.typed` |
| `use_pytest` | bool | `true` | Adds `tests/` + pytest config |

- **`is_library = false`** produces an application (no build system, no
  `py.typed` marker); uv treats it as a non-distributable project.
- **`use_pytest = false`** omits the entire pytest layer (`tests/`,
  config, ruff `PT` rule) — useful for ML/DL projects where
  deterministic test workflows are impractical.

## 🗂️ Layout

```
.
├── copier.yml          ← questions, tasks, after-action messages
├── pyproject.toml      ← workspace dev tooling (copier + pytest + ruff)
├── template/           ← files rendered into generated projects
│   ├── pyproject.toml.jinja
│   ├── {{ package_name }}/
│   └── ...
├── tests/              ← tests for the template itself
└── AGENTS.md           ← guide for AI assistants working on this repo
```

## 🛠️ Development

```bash
git clone https://github.com/kaparoo/python-project-template
cd python-project-template
uv sync --group dev
uv run pytest          # generation-scenario tests
```

### ✍️ Commit convention

Commit messages use an emoji prefix and wrap package/tool names in
backticks:

```
<emoji> <Imperative summary; tool names in `backticks`>

<Optional body explaining *why*>
```

| Emoji | When |
|-------|------|
| 🔧 | Configuration / settings (catch-all) |
| ✨ | New feature |
| 🔄 | Migration (e.g. `mypy → ty`) |
| 📝 | Documentation |
| ♻️ | Restructure without behavior change |
| 🐛 | Bug fix |
| 🔥 | Remove code or files |
| 🧹 | Cleanup (remove redundancy) |
| 🎨 | Cosmetic (whitespace, alignment) |
| 🙈 | `.gitignore` change |
| 📄 | License / legal text |
| ✅ | Tests added or fixed |
| ⬆️ / ➕ / ➖ | Dependency bump / add / remove |
| 💥 | Breaking change |
| 🎉 | Initial commit |

Keep commits single-purpose, don't rewrite published history, and
don't skip git hooks.

AI coding assistants working on this repository additionally follow
[`AGENTS.md`](./AGENTS.md) for workflow rules and the toolchain
rationale they must respect.

## 📜 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the template's version history.
The `pytorch` branch keeps an independent variant changelog with its
own `pytorch-v*` tag line.

## ⚖️ License

This project is distributed under the terms of the [MIT](./LICENSE) license.
