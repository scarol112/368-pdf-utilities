# Working rules for Claude

- **GitHub issues**: when querying GitHub issues (e.g. via `gh`), request/use
  JSON format (`gh issue list --json ...`, `gh issue view --json ...`, etc.)
  rather than the default human-readable text output.
- **Markdown files**: write and edit all Markdown files (`*.md`) using
  Obsidian-flavored Markdown conventions (e.g. `[[wikilinks]]` where a link
  is useful, standard Obsidian callout/formatting conventions) rather than
  plain CommonMark-only syntax.
- **RCS**: this repo dual-tracks files in RCS and git (see `30-source/RCS/`).
  Any time you edit a file that has a corresponding `RCS/<file>,v`, check it
  in afterward (`ci -l -m"description" file`) so RCS isn't left unaware of a
  change already sitting in git.
- **Git commit/push**: never commit or push to GitHub on your own initiative.
  Only do so with the user's explicit, per-instance permission — a prior
  approval does not carry forward to later changes.
