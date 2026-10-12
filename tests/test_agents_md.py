from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import prose

if TYPE_CHECKING:
    from tests.helpers import Render

GUIDES = (
    "changelog.md",
    "commits.md",
    "decisions.md",
    "dependencies.md",
    "readme.md",
    "releases.md",
)


def test_agents_md_indexes_task_guides(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Task guides" in agents
    for guide in (*GUIDES, "todo.md"):
        assert f"`.agents/{guide}`" in agents, f"missing {guide} in the index"
        assert (project / ".agents" / guide).is_file(), f"missing .agents/{guide}"
    assert "| write or change a test                  | `tests/AGENTS.md`" in agents
    assert "`tests/AGENTS.md` also loads on its own" in agents
    claude = (project / "tests" / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude == "@AGENTS.md\n"
    for moved in (
        "## Commit convention",
        "## Dependencies",
        "## Tests",
        "## Releases",
        "### `CHANGELOG.md`",
        "### `TODO.md`",
        "### `README.md`",
        "### `docs/decisions/`",
    ):
        assert moved not in agents, f"{moved} still in the core AGENTS.md"


@pytest.mark.parametrize(
    "answers",
    (
        {"use_pytest": False},
        {"include_todo": False},
        {"is_library": False, "use_pytest": False, "include_todo": False},
    ),
)
def test_task_guides_follow_options(render: Render, answers: dict[str, object]) -> None:
    project = render(answers)
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    for guide in GUIDES:
        assert f"`.agents/{guide}`" in agents, f"missing {guide} in the index"
        assert (project / ".agents" / guide).is_file(), f"missing .agents/{guide}"
    has_tests = answers.get("use_pytest", True)
    assert ("tests/AGENTS.md" in agents) is has_tests
    assert (project / "tests" / "AGENTS.md").is_file() is has_tests
    assert (project / "tests" / "CLAUDE.md").is_file() is has_tests
    has_todo = answers.get("include_todo", True)
    assert ("`.agents/todo.md`" in agents) is has_todo
    assert (project / ".agents" / "todo.md").is_file() is has_todo


def test_agents_md_documents_commit_convention(render: Render) -> None:
    project = render({"project_name": "agent-app"})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Commit only when the user asks, then follow `.agents/commits.md`." in agents
    assert "Gitmoji" not in agents
    commits = (project / ".agents" / "commits.md").read_text(encoding="utf-8")
    assert "## Commit convention" in commits
    assert "Gitmoji" in commits
    assert "Co-Authored-By" in commits
    assert "Common prefixes used in this project" not in commits
    assert "Commit messages are written in English." in commits
    assert "<gitmoji> <Verb> <object> [<preposition> <target>]" in commits
    assert "Those take the change's emoji, not one of their own." in prose(commits)
    assert "(`filesystem.utils`, not `agent_app.filesystem.utils`)" in prose(commits)
    assert "aim for about 50 characters and never pass 72" in commits
    assert "never commit work in progress on your own" in prose(commits)
    assert (
        "\N{UPWARDS BLACK ARROW}\N{VARIATION SELECTOR-16} Upgrade `ruff` to 0.17.0"
        in commits
    )
    assert "\N{PARTY POPPER} Initial commit from copier template" in commits
    assert "\N{BOOKMARK} Release version 2.0.0" in commits
    assert "| \N{HEAVY PLUS SIGN} | adding a dependency | Add |" in commits
    assert "| \N{HEAVY MINUS SIGN} | removing a dependency | Remove |" in commits
    for prefix in ("✨", "🐛", "♻️", "📝", "🔖", "🔧"):
        assert prefix in commits, f"missing {prefix} in gitmoji palette"


def test_agents_md_documents_workflow_and_secrets(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Workflow" in agents
    assert (
        "uv run ruff format .\nuv run ruff check --fix .\n"
        "uv run ty check\nuv run pytest\n```"
    ) in agents
    assert "instead of skipping it silently" in agents
    assert "Push only when the user asks" in agents
    assert "Never force-push" in agents
    assert "Create a branch only when" in agents
    assert "### Secrets" in agents
    assert "The credential has to be revoked and replaced" in agents
    assert "(see `tests/AGENTS.md`).\n\n## Task guides" in agents
    commits = (project / ".agents" / "commits.md").read_text(encoding="utf-8")
    assert "# Committing" in commits
    assert "`git stash push --include-untracked -m" in commits
    assert "so each commit passes on its own" in commits
    assert "`git checkout stash@{0} -- <file>`" in commits
    assert "No `git add -p` or other interactive commands." in commits
    assert "Drop a stash only once its changes are back" in commits


def test_agents_md_workflow_gates_follow_options(render: Render) -> None:
    project = render({"use_pytest": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert 'uv run ty check\nuv run python -c "import test_app"\n```' in agents
    assert "uv run pytest\n```" not in agents
    assert "uv run ty check          # type-check\n```\n\n## Task guides" in agents


def test_agents_md_documents_code_style(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Python style" not in agents
    assert "## Conventions" not in agents
    for heading in ("## Code style", "### All Python code", "### Source code"):
        assert f"\n{heading}\n" in agents, f"missing {heading}"
    assert "`ruff` enforces the import groups and order" in prose(agents)
    assert "the 88-column limit (`E501`)" in agents
    assert "1. `from __future__ import annotations`, except in an `__init__.py`." in (
        agents
    )
    assert "2. `__all__` as a tuple" in agents
    assert "the blank lines around imports and definitions" in prose(agents)
    assert "One blank line between `__all__` and the imports" in agents
    assert "two before a function or class" not in prose(agents)
    assert "with `# noqa: TID252` and the reason" in agents
    assert "Define a private helper above its first caller" in agents
    assert "takes one argument per line" in agents
    assert "a body of one or two lines has none" in prose(agents)
    assert "blank line before the final" not in agents
    assert "never `TypeVar`, `TypeAlias`, `Optional`, or `Union`" in prose(agents)
    assert "30 columns wide" in prose(agents)
    assert "use no em dash and no ` -- `" in agents
    assert "double backticks only when the content holds a backtick" in prose(agents)
    assert "PEP 723" in agents
    assert "A module takes no docstring unless the user asks for one." in agents
    assert "annotated `Final`" in agents
    assert "then `__init__` (or `__post_init__`) and `__repr__`" in agents
    assert "Mark every override with `@override`" in agents
    assert "`@dataclass(frozen=True, slots=True)`" in agents
    assert "starts lower-case and ends without a period" in agents
    assert "never split the string" in prose(agents)
    assert "Name the valid set or the fix" in agents
    assert "Google style" in agents
    assert "*intent and contracts, not mechanism*" in prose(agents)
    assert "Type Parameters:" in agents
    assert "family map" in agents
    assert "self-explainable" in agents
    assert "leave `__init__` bare" in agents
    assert "Keep a comment to one line, three at most" in agents
    assert "Fill docstring and comment prose toward 88 columns" in agents


def test_agents_md_documents_test_conventions_with_pytest(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "`tests/AGENTS.md` says what tests do differently" in prose(agents)
    code_style = agents.split("## Code style", 1)[1].split("## Documentation", 1)[0]
    assert "pytest" not in code_style
    tests = (project / "tests" / "AGENTS.md").read_text(encoding="utf-8")
    assert tests.startswith("# Test guide: `test-app`\n")
    for heading in (
        "## Layout",
        "## Test data",
        "## Writing tests",
        "## Skipped tests",
        "## Coverage and speed",
    ):
        assert f"\n{heading}\n" in tests, f"missing {heading}"
    assert "Don't mix the two styles" in tests
    assert "verify it with a spy" in tests
    assert "live in `tests/assets/`" in tests
    assert "`tests/assets/local/`" in tests
    assert "one `test_<module>.py` per source module" in prose(tests)
    assert "`tests/<sub>/fixtures/` for one subpackage" in tests
    assert "pytest honors `pytest_plugins` in the root `conftest.py`" in tests
    assert "Add a `conftest.py` or a `helpers.py` wherever tests need one" in tests
    assert "If the project has a module named `assets`" in prose(tests)
    assert "record it below the marker in the root `AGENTS.md`" in prose(tests)
    assert "does so under pytest's `tmp_path`" in tests
    assert "Add no docstrings or comments to test functions and classes" in tests
    assert "`from tests.<pkg>.helpers import ...`" in tests
    assert "Type annotations are optional in tests" in tests
    assert '`pytest.param(..., id="empty-source")`' in tests
    assert "Tests are independent of each other and of their order." in tests
    assert "never a global seed" in prose(tests)
    assert "`numpy.testing.assert_allclose` for arrays" in tests
    assert "`# noqa: SLF001` on that line" in prose(tests)
    assert "Tests never touch the network or an outside service" in tests
    assert "`pytest.warns(Category, match=...)`" in tests
    assert "`record.getMessage()`" in tests
    assert "not `unittest.mock`" in prose(tests)
    assert "A bug fix starts with a test that fails on the bug." in tests
    assert '`pytest.importorskip("<module>")`' in tests
    assert "`tests/marks.py`" in tests
    assert "When CI cannot run the tests" in tests
    assert "Never lower `fail_under`" in tests
    assert "tests cover the public API" in tests
    assert '`uv run pytest -m "not slow"`' in tests

    no_pytest = render({"use_pytest": False})
    agents_np = (no_pytest / "AGENTS.md").read_text(encoding="utf-8")
    assert "tests/AGENTS.md" not in agents_np
    assert "verify it with a spy" not in agents_np


def test_agents_md_documents_dependency_rules(render: Render) -> None:
    project = render()
    deps = (project / ".agents" / "dependencies.md").read_text(encoding="utf-8")
    assert deps.startswith("# Dependencies and Python versions\n")
    assert "`uv add --group dev <pkg>`" in deps
    assert "`uv add --optional <extra> <pkg>`" in deps
    assert "Commit `pyproject.toml` and `uv.lock`" in deps
    assert "`uv lock --upgrade-package <pkg>`" in deps
    assert "Raising `ruff`'s minimum also raises `[tool.ruff] required-version`" in deps
    assert "\n## Supported Python versions\n" in deps
    for place in (
        "`requires-python` in `pyproject.toml`",
        "`[tool.ty.environment] python-version`",
        "`Programming Language :: Python :: X.Y` classifier",
        "`.python-version`",
        "the requirement line in 📦 Installation",
    ):
        assert place in deps, f"missing {place}"
    assert "`copier update -d python_version=X.Y`" in deps
    assert "the *Project* line of `AGENTS.md`" in prose(deps)
    assert "the `python-version` list in `.github/workflows/ci.yml`" in deps
    assert "drop it from the classifiers, the CI list, and the badge" in prose(deps)


def test_agents_md_dependency_rules_follow_options(render: Render) -> None:
    project = render({"is_library": False, "use_pytest": False})
    deps = (project / ".agents" / "dependencies.md").read_text(encoding="utf-8")
    assert "--optional" not in deps
    assert "the requirement line in 📦 Setup" in deps
    releases = (project / ".agents" / "releases.md").read_text(encoding="utf-8")
    assert "--isolated" not in releases


def test_agents_md_documents_doc_upkeep_rules(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Documentation" in agents
    assert "Write a new document in English" in prose(agents)
    assert "keeps that language" in agents
    assert "This project keeps no `TODO.md`" not in agents
    assert "| that README → `## Contents`, if present" in agents
    assert "### `AGENTS.md`" in agents
    assert "the guides in `.agents/` and `tests/AGENTS.md` too" in prose(agents)
    guides = project / ".agents"
    changelog = (guides / "changelog.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Writing `CHANGELOG.md`\n")
    assert "| `Deprecated` |" in changelog
    assert "never invent new ones" in changelog
    assert "imports the library" in changelog
    assert "Internal refactoring stays out" in changelog
    assert "`Added` and `Removed` lead with *what*" in changelog
    assert "**Breaking:**" in changelog
    assert "`DeprecationWarning`" in changelog
    assert "Cut a release only when the user asks" in changelog
    assert "https://github.com/kaparoo/test-app/compare/vX.Y.Z...HEAD" in changelog
    todo = (guides / "todo.md").read_text(encoding="utf-8")
    assert todo.startswith("# Writing `TODO.md`\n")
    assert "holds **open work only**" in todo
    assert "`TODO.md` is the only place for it: `ruff` rejects `TODO`" in prose(todo)
    assert "`Revisit when ...`" in todo
    assert 'no "Done" section' in todo
    assert "Before starting a task, read the items" in todo
    assert "brought in line once" in todo
    readme = (guides / "readme.md").read_text(encoding="utf-8")
    assert readme.startswith("# Writing `README.md`\n")
    assert "The root `README.md` is the landing page" in readme
    assert "word for word the `description` in `pyproject.toml`" in prose(readme)
    for lead in ("📦 Installation:", "🚀 Quick start:", "🧩 Modules:"):
        assert lead in readme, f"missing lead section {lead}"
    assert "5. Project-specific sections" in readme
    assert "📋 TODO, 📜 Changelog, ⚖️ License." in readme
    assert 'No hand-written table of contents and no "back to top"' in readme
    assert "https://github.com/kaparoo/test-app/blob/main/<path>" in readme
    assert "\n## Sub-READMEs\n" in readme
    assert "so it has no fixed sections" in readme
    assert "never folded into `<details>`" in prose(readme)
    assert "Keep `## Contents` in step with the headings" in readme
    assert "`#resolving-conflicts-on_conflict`" in readme
    assert "only the root README reaches PyPI" in readme
    assert "📦 Setup:" not in readme
    assert "🗂️ Layout" not in readme
    decisions = (guides / "decisions.md").read_text(encoding="utf-8")
    assert decisions.startswith("# Recording decisions in `docs/decisions/`\n")
    assert "`docs/decisions/NNNN-title-with-dashes.md`" in decisions
    assert "superseded by NNNN" in decisions


def test_agents_md_doc_upkeep_rules_follow_options(render: Render) -> None:
    project = render({"is_library": False, "include_todo": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "This project keeps no `TODO.md`" in agents
    assert "| `README.md` → 🚀 Usage" in agents
    assert "🧩 Modules" not in agents
    guides = project / ".agents"
    changelog = (guides / "changelog.md").read_text(encoding="utf-8")
    assert "runs the application" in changelog
    assert "a command, an option, or a configuration" in changelog
    assert "DeprecationWarning" not in changelog
    readme = (guides / "readme.md").read_text(encoding="utf-8")
    assert "📋 TODO" not in readme
    assert "🧩 Modules" not in readme
    assert "PyPI" not in readme
    for lead in ("📦 Setup:", "🚀 Usage:", "🗂️ Layout, once"):
        assert lead in readme, f"missing lead section {lead}"
    assert "in this order: 📜 Changelog, ⚖️ License." in prose(readme)
    assert "A directory whose use outgrows its 🗂️ Layout entry" in readme
    assert "\n## Sub-READMEs\n" in readme
    assert (guides / "decisions.md").is_file()


def test_agents_md_documents_readme_upkeep_details(render: Render) -> None:
    project = render()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Every document wraps prose at 72 columns" in agents
    assert "`[project.scripts]` | `README.md` → ⌨️ CLI" in agents
    assert "| that README → the link" in agents
    readme = (project / ".agents" / "readme.md").read_text(encoding="utf-8")
    assert "(`[project.scripts]`) comes first among them" in readme
    assert "A badge for a dependency" in readme
    assert "Links stay valid" in readme


def test_agents_md_readme_upkeep_details_follow_options(render: Render) -> None:
    project = render({"is_library": False})
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "[project.scripts]" not in agents
    assert "Every document wraps prose at 72 columns" in agents
    readme = (project / ".agents" / "readme.md").read_text(encoding="utf-8")
    assert "[project.scripts]" not in readme
    assert "Links stay valid" in readme
