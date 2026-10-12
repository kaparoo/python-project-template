# Recording decisions in `docs/decisions/`

Record a design decision (a choice between real alternatives that
later work should respect rather than reopen) as an Architecture
Decision Record: one file per decision at
`docs/decisions/NNNN-title-with-dashes.md`, numbered in sequence from
`0001` and never renumbered. Create the directory with the first record.
A rule for how code is written is not a decision record; it goes to
`AGENTS.md`.

Use the [MADR](https://adr.github.io/madr/) shape, kept short:

```markdown
# <Decision, stated as a short sentence>

- Status: accepted
- Date: YYYY-MM-DD

## Context and problem statement

## Considered options

## Decision outcome

## Consequences
```

- Write the record in the commit that implements the decision, or in
  its own `📝` commit when the decision comes first.
- A record is history: once accepted, change it only to fix a factual
  error. When a later decision reverses it, write a new record and set
  the old one's status to `superseded by NNNN`.
