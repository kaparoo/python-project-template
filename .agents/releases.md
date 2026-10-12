# Releasing the template

This workspace itself is versioned with SemVer (see
[`CHANGELOG.md`](../CHANGELOG.md)):

- `MAJOR`: changes that break `copier update` for an existing
  generated project: a removed question or choice, or anything that
  needs a `_migrations` entry in `copier.yml` to update across.
- `MINOR`: new copier options, new generated files, new sections in
  generated docs.
- `PATCH`: fixes, doc tweaks, behavior-preserving cleanup.

## Cutting a release

For both branches the procedure is the same shape; only the tag form
differs (`vX.Y.Z` on `main`, `pytorch-vX.Y.Z` on `pytorch`).

1. Land all changes in `[Unreleased]` first. Verify with
   `uv run pytest` on a clean tree.
2. Promote: rename `## [Unreleased]` content to a dated
   `## [X.Y.Z] - YYYY-MM-DD` heading, add a fresh empty
   `## [Unreleased]` above, append the new comparison link at the
   bottom of the file.
3. Commit: `🔖 Release version X.Y.Z` (body summarizes the bundle).
4. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Push: `git push origin <branch>` then `git push origin vX.Y.Z`.

For shared work, the order is **main first, then `pytorch`**:
release `vX.Y.Z` on `main`, merge `main` into `pytorch` (resolving
the CHANGELOG conflict per below), then promote pytorch's own
`[Unreleased]` to `[X.Y.Z]` and tag `pytorch-vX.Y.Z`. The two
version sequences are **independent**: `pytorch-v1.1.0` is not
required to mirror `v1.1.0` numerically once they diverge.

## Merging `main` into `pytorch`

After every `main` change cycle, merge forward:

```bash
git switch pytorch
git merge main --no-ff -m "🔀 Merge \`main\` into \`pytorch\`"
```

**Recurring `CHANGELOG.md` conflict**: pytorch keeps a variant-only
changelog (it does NOT mirror `main`'s release history). Resolution
principle:

- **Take** main's new `[Unreleased]` bullets (Added / Changed / Fixed):
  the underlying template change applies to both branches.
- **Drop** main's `## [X.Y.Z]` heading and any base `v*` comparison
  links: pytorch has its own release line.
- **Keep** pytorch's existing `## [X.Y.Z]` headings (the variant's
  prior releases) and the `pytorch-v*` comparison links at the
  bottom.

The tests in `tests/` may also conflict when the default values
diverge (notably `use_pytest`): keep pytorch's `{"use_pytest": True}`
override in tests that assume the pytest layer; keep pytorch's
expected-files list (no `tests/__init__.py` when use_pytest is
default-false there).
