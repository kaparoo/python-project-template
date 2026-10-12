from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import prose

if TYPE_CHECKING:
    from tests.helpers import Render


def test_agents_md_documents_commit_convention(render: Render) -> None:
    project = render({"project_name": "agent-app"})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "agent-app" in agents
    assert "## Commit convention" in agents
    assert "Gitmoji" in agents
    assert "Co-Authored-By" in agents
    assert "Common prefixes used in this project" in agents
    for prefix in ("✨", "🐛", "♻️", "📝", "🔖", "🔧"):
        assert prefix in agents, f"missing {prefix} in gitmoji palette"


def test_agents_md_documents_workflow_and_secrets(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Workflow" in agents
    assert (
        "uv run ruff format .\nuv run ruff check --fix .\n"
        "uv run ty check\nuv run pytest\n```"
    ) in agents
    assert "instead of skipping it silently" in agents
    assert "Commit only when the user asks; see *Committing* below." in agents
    assert "### Committing" in agents
    assert "`git stash push --include-untracked -m" in agents
    assert "so each commit passes on its own" in agents
    assert "`git checkout stash@{0} -- <file>`" in agents
    assert "No `git add -p` or other interactive commands." in agents
    assert "Drop a stash only once its changes are back" in agents
    assert "Push only when the user asks" in agents
    assert "Never force-push" in agents
    assert "Create a branch only when" in agents
    assert "### Secrets" in agents
    assert "The credential has to be revoked and replaced" in agents


def test_agents_md_workflow_gates_follow_options(render: Render) -> None:
    project = render({"use_pytest": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert 'uv run ty check\nuv run python -c "import test_app"\n```' in agents
    assert "uv run pytest\n```" not in agents


def test_agents_md_documents_code_style(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Python style" not in agents
    assert "## Conventions" not in agents
    for heading in ("## Code style", "### All Python code", "### Source code"):
        assert f"\n{heading}\n" in agents, f"missing {heading}"
    assert "from __future__ import annotations" in agents
    assert "except in an `__init__.py`, which does not need it" in agents
    assert "2. `__all__` as a tuple" in agents
    assert "Two blank lines follow the import section" in prose(agents)
    assert "carries `# noqa: TID252`" in agents
    assert "Define a private helper above its first caller" in agents
    assert "(ruff `E501`)" in agents
    assert "takes one argument per line" in agents
    assert "a body of one or two lines has none" in prose(agents)
    assert "blank line before the final" not in agents
    assert "never `TypeVar`, `TypeAlias`, `Optional`, or `Union`" in agents
    assert "30 columns wide" in prose(agents)
    assert "uses no em dash" in agents
    assert "double backticks only when the content holds a backtick" in agents
    assert "PEP 723" in agents
    assert "A module takes no docstring unless the user asks for one." in agents
    assert "annotated `Final`" in agents
    assert "then `__init__` (or `__post_init__`) and `__repr__`" in agents
    assert "Mark every override with `@override`" in agents
    assert "`@dataclass(frozen=True, slots=True)`" in agents
    assert "starts lower-case and ends without a period" in agents
    assert "never split the string" in agents
    assert "Google style" in agents
    assert "intent and contracts" in agents
    assert "Type Parameters:" in agents
    assert "family map" in agents
    assert "self-explainable" in agents
    assert "Literal option values get backticks" in agents
    assert "leave `__init__` bare" in agents
    assert "Keep a comment to one line, three at most" in agents
    assert "Fill docstring and comment prose toward 88 columns" in agents


def test_agents_md_documents_error_message_content(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Name the valid set or the fix" in agents


def test_agents_md_documents_test_conventions_with_pytest(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    for heading in (
        "## Tests",
        "### Layout",
        "### Test data",
        "### Writing tests",
        "### Skipped tests",
        "### Coverage and speed",
    ):
        assert f"\n{heading}\n" in agents, f"missing {heading}"
    assert "Don't mix the two styles" in agents
    assert "verify it with a spy" in agents
    assert "live in `tests/assets/`" in agents
    assert "`tests/assets/local/`" in agents
    assert "one `test_<module>.py` per source module" in prose(agents)
    assert "`tests/<sub>/fixtures/` for one subpackage" in agents
    assert "pytest honors `pytest_plugins` in the root `conftest.py`" in agents
    assert "Add a `conftest.py` or a `helpers.py` wherever tests need one" in agents
    assert "If the project has a module named `assets`" in prose(agents)
    assert "does so under pytest's `tmp_path`" in agents
    assert "Add no docstrings or comments to test functions and classes" in agents
    assert "`from tests.<pkg>.helpers import ...`" in agents
    assert "Type annotations are optional in tests" in agents
    assert '`pytest.param(..., id="empty-source")`' in agents
    assert "Tests are independent of each other and of their order." in agents
    assert "never a global seed" in prose(agents)
    assert "`numpy.testing.assert_allclose` for arrays" in agents
    assert "`# noqa: SLF001` on that line" in prose(agents)
    assert "Tests never touch the network or an outside service" in agents
    assert "(for tests, see *Tests*)" in agents
    assert "`pytest.warns(Category, match=...)`" in agents
    assert "`record.getMessage()`" in agents
    assert "not `unittest.mock`" in prose(agents)
    assert "A bug fix starts with a test that fails on the bug." in agents
    assert '`pytest.importorskip("<module>")`' in agents
    assert "`tests/marks.py`" in agents
    assert "When CI cannot run the tests" in agents
    assert "Never lower `fail_under`" in agents
    assert "tests cover the public API" in agents
    assert '`uv run pytest -m "not slow"`' in agents
    code_style = agents.split("## Code style", 1)[1].split("## Tests", 1)[0]
    assert "pytest" not in code_style

    no_pytest = render({"use_pytest": False})
    agents_np = (no_pytest / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Tests" not in agents_np
    assert "see *Tests*" not in agents_np
    assert "verify it with a spy" not in agents_np
    assert "Don't mix the two styles" not in agents_np


def test_agents_md_documents_dependency_rules(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Dependencies" in agents
    assert "`uv add --group dev <pkg>`" in agents
    assert "`uv add --optional <extra> <pkg>`" in agents
    assert "Commit `pyproject.toml` and `uv.lock`" in agents
    assert "`uv lock --upgrade-package <pkg>`" in agents
    assert (
        "Raising `ruff`'s minimum also raises `[tool.ruff] required-version`" in agents
    )
    assert "### Supported Python versions" in agents
    for place in (
        "`requires-python` in `pyproject.toml`",
        "`[tool.ty.environment] python-version`",
        "`Programming Language :: Python :: X.Y` classifier",
        "`.python-version`",
        "the requirement line in 📦 Installation",
    ):
        assert place in agents, f"missing {place}"
    assert "`copier update -d python_version=X.Y`" in agents
    assert "the `python-version` list in `.github/workflows/ci.yml`" in agents
    assert "drop it from the classifiers, the CI list, and the badge" in prose(agents)
    assert "| \N{HEAVY PLUS SIGN}     | Add a dependency" in agents
    assert "| \N{HEAVY MINUS SIGN}     | Remove a dependency" in agents


def test_agents_md_dependency_rules_follow_options(render: Render) -> None:
    project = render({"is_library": False, "use_pytest": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Dependencies" in agents
    assert "--optional" not in agents
    assert "the requirement line in 📦 Setup" in agents
    assert "--isolated" not in agents


def test_agents_md_documents_doc_upkeep_rules(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Documentation" in agents
    assert "### `CHANGELOG.md`" in agents
    assert "| `Deprecated` |" in agents
    assert "never invent new ones" in agents
    assert "imports the library" in agents
    assert "Internal refactoring stays out" in agents
    assert "`Added` and `Removed` lead with *what*" in agents
    assert "**Breaking:**" in agents
    assert "`DeprecationWarning`" in agents
    assert "Cut a release only when the user asks" in agents
    assert "https://github.com/kaparoo/test-app/compare/vX.Y.Z...HEAD" in agents
    assert "### `TODO.md`" in agents
    assert "holds **open work only**" in agents
    assert "`Revisit when ...`" in agents
    assert 'no "Done" section' in agents
    assert "Before starting a task, read the items" in agents
    assert "brought in line once" in agents
    assert "document already written in another language" in agents
    assert "This project keeps no `TODO.md`" not in agents
    assert "### `README.md`" in agents
    assert "The root `README.md` is the landing page" in agents
    assert "word for word the `description` in `pyproject.toml`" in prose(agents)
    for lead in ("📦 Installation:", "🚀 Quick start:", "🧩 Modules:"):
        assert lead in agents, f"missing lead section {lead}"
    assert "5. Project-specific sections" in agents
    assert "📋 TODO, 📜 Changelog, ⚖️ License." in agents
    assert 'No hand-written table of contents and no "back to top"' in agents
    assert "https://github.com/kaparoo/test-app/blob/main/<path>" in agents
    assert "#### Sub-READMEs" in agents
    assert "so it has no fixed sections" in agents
    assert "never folded into `<details>`" in prose(agents)
    assert "Keep `## Contents` in step with the headings" in agents
    assert "`#resolving-conflicts-on_conflict`" in agents
    assert "| that README → `## Contents`, if present" in agents
    assert "only the root README reaches PyPI" in agents
    assert "📦 Setup:" not in agents
    assert "🗂️ Layout" not in agents
    assert "### `docs/decisions/`" in agents
    assert "`docs/decisions/NNNN-title-with-dashes.md`" in agents
    assert "superseded by NNNN" in agents
    assert "### `AGENTS.md`" in agents


def test_agents_md_doc_upkeep_rules_follow_options(render: Render) -> None:
    project = render({"is_library": False, "include_todo": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Documentation" in agents
    assert "### `CHANGELOG.md`" in agents
    assert "runs the application" in agents
    assert "a command, an option, or a configuration" in agents
    assert "DeprecationWarning" not in agents
    assert "This project keeps no `TODO.md`" in agents
    assert "### `TODO.md`" not in agents
    assert "📋 TODO" not in agents
    assert "🧩 Modules" not in agents
    assert "PyPI" not in agents
    for lead in ("📦 Setup:", "🚀 Usage:", "🗂️ Layout, once"):
        assert lead in agents, f"missing lead section {lead}"
    assert "| `README.md` → 🚀 Usage" in agents
    assert "in this order: 📜 Changelog, ⚖️ License." in prose(agents)
    assert "A directory whose use outgrows its 🗂️ Layout entry" in agents
    assert "#### Sub-READMEs" in agents
    assert "### `docs/decisions/`" in agents


def test_agents_md_documents_readme_upkeep_details(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "All of them wrap prose at 72 columns" in agents
    assert "(`[project.scripts]`) comes first among them" in agents
    assert "`[project.scripts]` | `README.md` → ⌨️ CLI" in agents
    assert "A badge for a dependency" in agents
    assert "Links stay valid" in agents
    assert "| that README → the link" in agents


def test_agents_md_readme_upkeep_details_follow_options(render: Render) -> None:
    project = render({"is_library": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "[project.scripts]" not in agents
    assert "Links stay valid" in agents
    assert "All of them wrap prose at 72 columns" in agents
