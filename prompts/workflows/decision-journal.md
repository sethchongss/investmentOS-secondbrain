# Prompt: decision journal

Write one new journal entry about a decision a person already made, or about a decision they are explicitly recording now. You do not decide for them.

## Mandate

Load `vault/profile/mandate.md` and the strategy id they name. If the mandate is missing or not confirmed, say you are in generic mode, point at `prompts/onboard.md`, and do not invent why they decided. The profile is operating context, not evidence and not a source.

## What the entry contains

A new file under `vault/wiki/journal/` whose name starts with the date. `append_only: true`. The role they choose to write, not an email address. The strategy id. Which constraints you checked. Any conflict you showed and left open. The library ids cited. Fields they skipped stay skipped.

## What the entry does not do

It does not edit `vault/profile/mandate.md`. It does not edit an older journal file or an older file in `vault/profile/revisions/`. A change to the mandate is a new revision file from `templates/mandate/revision.md`, and only after they confirm the Before and After. Run `python3 tools/init_mandate.py check-new` on that path before saving it. The script refuses an existing path. It does not rewrite history.

The decision journal stays on the workflow map even when they named a shorter output list, because the decision should not live only in chat.
