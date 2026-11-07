# Prompt: PE diligence

Use this only when the loaded subprofile has `strategy_kind: pe`. You do not give investment advice and you do not assign a score.

## Mandate

Load `vault/profile/mandate.md` and the PE strategy file named for this task. If the mandate is missing, unconfirmed, or the strategy is not PE, stop. Say generic mode or name the mismatch. Do not recast a fund-selection file as a company diligence. Point at `prompts/onboard.md` when the profile is not confirmed.

The profile is operating context, not evidence and not a source.

## What to ask

Ask control or minority as stated, buyout or growth as stated, earnings quality, cash, debt, and downside.

Read `ownership` and `deal_type` from the subprofile. If either is unknown or skipped, ask the person. Do not fill buyout. Do not fill control. A growth deal stays a growth deal. Minority stays minority. `both` means you keep both, not that you pick the dramatic one.

Value creation is the stated plan compared with a source. If no source states a plan, write unknown.

## What not to ask

Do not ask seed follow-on reserves or a GP's fund terms.

## Output

A diligence note with Sources and Inference. Every figure has a library id and a date posted. `python3 tools/init_mandate.py validate` checks the profile shape. It does not check whether the company is a good deal.
