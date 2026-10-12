# TODO

Open work on this template that is not done yet: deferred, blocked on
a decision, or a known limitation. Delete an item in the commit that
resolves it.

## Infrastructure

### Dependabot for generated projects

`template/.github/dependabot.yml`: Dependabot updates for generated
projects' `uv` dependencies and GitHub Actions. The minimums inside
`template/*.jinja` stay manual. The user postponed it until the code
style and test rules landed; both are now in.

Revisit when the user takes it up.

## Rules

### Condense the generated task guides

The core `AGENTS.md` was condensed for `v2.0.0`; the guides it indexes
were moved as they were. `tests/AGENTS.md` (about 1,900 tokens) loads
whenever an agent works in `tests/`, so it gains most from a tighter
wording; `.agents/commits.md`, `changelog.md`, and `readme.md` (about
1,200 to 1,450 tokens each) load only for their task. Keep every
condition the rules carry, and update the phrases `tests/` asserts.

Revisit after `v2.0.0` is tagged, when the user takes it up.
