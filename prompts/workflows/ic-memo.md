# Prompt: IC memo

Prepare a memo a person will read. You do not hold the seat, and you do not approve the memo by writing it.

## Mandate

Load `vault/profile/mandate.md`. If it is missing or not confirmed, stop. Generic mode. Point at `prompts/onboard.md`. Do not invent a committee, a cadence, or a return target.

Name one strategy id from `strategies`. Load only that file. Do not blend a second subprofile into the same checklist.

The profile is operating context, not evidence and not a source.

## Authority

Read `decision_authority`.

- `vote` or `decide`: the memo can frame a decision. It still says a person approves any wiki change.
- `recommend_only`: the memo must say it does not decide. Do not rewrite the mandate so the seat becomes `decide`.
- `unknown` or `skipped`: the memo must not assume this seat decides.

If `return_objective` is `not_stated` or `skipped`, write that the target is not stated. If it is `user_stated`, quote `return_objective_words` and do not raise them.

## Shape

The question. The constraint check against leverage, concentration, holding period, and liquidity. Sources with library ids and dates. Inference, labeled as inference. What would change the view. The decision left open.

Show a conflict between the request and the mandate in the open. Do not drop the constraint to make the memo cleaner.
