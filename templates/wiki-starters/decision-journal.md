---
id: wf-decision-journal
type: playbook
title: Decision journal
summary: "Append-only decisions with the constraint check. The mandate is context, not evidence."
synthetic: false
---

Strategies named on the mandate: {{strategy_list}}.

This is the log of what a person decided. It is not the mandate and not a source.

## What a new entry records

The date. The role, not an account id. The strategy id. The constraint check. Any conflict that was left open. The library ids that were cited. Unknown stays unknown.

## What it does not do

It does not edit `vault/profile/mandate.md`. A mandate change is a new file under `vault/profile/revisions/` after the person confirms. Older revision files stay.
