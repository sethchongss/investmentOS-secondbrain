# Mandate schema

`mandate.schema.json` is the field list `tools/init_mandate.py` loads. This page is the same contract in prose. The research records in [README.md](README.md) are a different file. A mandate is operating context for those records. It is not evidence and not advice.

Ids are lowercase letters, digits, and hyphens. `synthetic` is a boolean. A private profile uses `synthetic: false`. The files under `examples/profiles/` use `synthetic: true` and say they are fictional.

Do not add a firm name, a client name, AUM, holdings, or credentials. Those keys are rejected. Unknown and skipped are allowed values on the questions below.

## mandate (`mandate.md`)

`status` is `draft` or `confirmed`. `revision` starts at 1. `operating_context` is true. `evidence_rule` is `cite_sources`. `human_approval` is `required`. A confirmed file needs `confirmed_on` as a date, `confirmed_by` as a role rather than an email, the sentence "This is operating context, not evidence and not advice.", and at least one strategy id.

`institution_types` is a list: `sfo`, `mfo`, `vc`, `pe`, `hedge_fund`, `independent`, `other`, or unknown/skipped. More than one entry is how "multiple" is stored. The institution is not the strategy.

`activity` is separate: `direct`, `fund_selection`, `both`, or unknown/skipped. A PE institution may select funds. An SFO may invest directly. Confirmed `both` needs one direct subprofile and one `fund_selection` subprofile. They are not collapsed.

`role` and `decision_authority` (`recommend_only`, `vote`, `decide`, or unknown/skipped) describe the seat. Geography, sectors, size range, holding period, liquidity, leverage, and concentration may be skipped. `return_objective` is `not_stated`, `skipped`, or `user_stated`. A stated objective needs the person's words under `## User-stated objective`. The tools do not invent a target.

`client_separation` is `separate_files` for an MFO. This starter does not store a shared client list. Use `not_applicable` when the institution is not an MFO.

`output_formats` names the workflows the person wants. `skipped` means the applicable set in [the map](../docs/mandate-map.md).

## strategy (`strategies/<id>.md`)

`strategy_kind` picks the fields. Other kinds' fields are unknown fields and fail validation.

- `pe`: ownership, deal type (buyout, growth, both, not a buyout, or unknown), value creation, earnings quality, cash and debt, downside.
- `vc`: stage, ownership, follow-on, unit economics.
- `hedge_fund`: style, holding period, exposure, liquidity, catalysts, risk.
- `fund_selection`: GP strategy, team, attribution, terms, repeatability. Each may be in scope, unknown, or skipped.
- `direct_public`, `credit`, `real_assets`, and `other` keep a short focus instead of borrowing one of the lists above.

## revision (`revisions/YYYY-MM-DD-note.md`)

Revision 1 has no `prior_revision`. A later confirm points at a new file with `## Before` and `## After`. The filename starts with the date. The tools refuse to overwrite that file. Raw wording in Before stays.

## What the tools will not do

A draft, a missing file, or an unknown institution or activity maps to generic mode. The interview that fills the file is [prompts/onboard.md](../prompts/onboard.md). The script checks shape, prints the map, and writes a wiki starter only when the destination is absent.
