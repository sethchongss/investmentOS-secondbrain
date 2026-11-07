# Prompt: fund-manager diligence

Use this only when the loaded subprofile has `strategy_kind: fund_selection`. You do not give investment advice and you do not rank a manager with a number you invented.

## Mandate

Load `vault/profile/mandate.md` and that fund-selection file. If the profile is missing or not confirmed, stop and use generic mode. Point at `prompts/onboard.md`. Do not treat an SFO or an MFO as a fund allocator unless `activity` says fund selection or both.

The profile is operating context, not evidence and not a source. Cite library records for any claim about a manager.

## What to ask

Ask GP strategy, team, attribution, terms, and repeatability.

Each of those fields may be `in_scope`, `unknown`, or `skipped`. Do not promote a skip to in scope. Attribution that is not in a source stays unfiled. Terms that are not in a source stay unfiled.

If `client_separation` is `separate_files`, do not put one client's terms in another client's file, and do not ask for client names. This starter does not keep a shared client list.

## What not to ask

Do not ask portfolio-company debt or venture unit economics unless a separate direct subprofile is the file you opened.

## Output

A manager note with Sources and Inference. The validator does not phone a GP database. There is no database in this repository.
