# Writing `TODO.md`

`TODO.md` holds **open work only**: work deliberately deferred (out of
scope for the current change, blocked on a decision, or a limitation
found along the way). It is not a design document, a progress log, or a
record of what is done: decisions go to `docs/decisions/`, finished
work to git history and `CHANGELOG.md`.

- Before starting a task, read the items that touch the code it
  changes: one may already describe the problem, or be resolved by the
  change.
- An item is one bullet by default: what needs doing and why, led by
  the relevant path in backticks when there is one, as in
  "`io/reader.py`: stream large files instead of reading them whole
  (memory spikes above ~1 GB)."
- Only when one line cannot carry it, give the item a `### <what needs
  doing>` heading and a short body: the problem (a code snippet may show
  it), why it was deferred, and a closing `Revisit when ...` line naming
  what should reopen it: a use case that needs it, a measurement that
  would justify it, or the decision it waits on. A body that grows past
  a few short paragraphs is a design question: settle it in a
  `docs/decisions/` record and keep only the remaining work here.
- Items sit under `## Open`, most important first. Once the list
  outgrows a screen, replace `## Open` with `##` headings by area (a
  package or a topic), most important first within each. Headings
  carry no emoji, so their anchors stay plain.
- No owners, dates, status markers, checkboxes, or "last updated"
  lines: git history records who and when.
- Add an item only for work the current change does not finish.
  `TODO.md` is the only place for it: `ruff` rejects `TODO`, `FIXME`,
  `XXX`, and `HACK` comments (its `FIX` rules), so deferred work
  cannot hide in the code.
- Delete an item in the commit that resolves it (no "Done" section, no
  strikethrough), and add a `CHANGELOG.md` entry if users can see the
  result. An item dropped without being done is deleted the same way,
  with the reason in the commit message. Restore `_No entries yet._`
  when the list becomes empty.
- A `TODO.md` written before these rules is brought in line once: move
  settled decisions to `docs/decisions/`, delete finished and
  struck-through items, and keep the remaining work as items.
