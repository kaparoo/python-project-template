# TODO

Open work on this template that is not done yet: deferred, blocked on
a decision, or a known limitation. Delete an item in the commit that
resolves it.

## Releases and variants

### Python 3.15 on `pytorch`

The variant offers Python 3.13 and 3.14 only: `torch` 2.14.1 and
`torchvision` 0.29.1, the newest releases, ship wheels for cp310 to
cp314 (CPU and CUDA alike). Add `3.15` to the `python_version` choices
and the computed `python_versions` once both ship cp315 wheels, on the
CPU index too, which CI uses.

Revisit when `torch` publishes cp315 wheels.

## Infrastructure

### Dependabot for generated projects

`template/.github/dependabot.yml`: Dependabot updates for generated
projects' `uv` dependencies and GitHub Actions. The minimums inside
`template/*.jinja` stay manual. The user postponed it until the code
style and test rules landed; both are now in.

Revisit when the user takes it up.
