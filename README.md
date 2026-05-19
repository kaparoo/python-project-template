# python-project-template

A personal [copier](https://copier.readthedocs.io/) template for bootstrapping
modern Python projects with `uv`, `ruff`, `ty`, and `pytest` pre-configured.

> **Status**: under construction — copier wiring lands incrementally.
> The rendered content lives in [`template/`](./template/); the rest of
> this repo is template-development tooling.

## Quick start (once template is wired)

```bash
# One-time: install copier
uv tool install copier

# Generate a new project
copier copy gh:kaparoo/python-project-template my-new-project

# Later: pull template improvements into an existing project
cd my-new-project
copier update --trust
```

## Layout

```
.                       ← this repo (template source)
├── copier.yml          ← (Phase 2) question definitions
├── template/           ← files rendered into generated projects
└── tests/              ← (Phase 5) tests for the template itself
```

## License

[MIT](./LICENSE)
