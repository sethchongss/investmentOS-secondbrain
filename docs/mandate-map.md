# Mandate map

`schema/mandate.schema.json` is the field list. `tools/mandate.py` reads it and chooses prompts. This page is the same map in prose. The profile is operating context, not evidence and not advice. A missing or unconfirmed profile selects nothing tailored.

Institution type and activity are different questions. A PE institution can select funds. An SFO can invest directly. The map follows `activity` and `strategy_kind`, not the institution label alone.

## When the mode is generic

- No `vault/profile/mandate.md`.
- `status` is not `confirmed`.
- Institution is only `unknown` or `skipped`.
- Activity is `unknown` or `skipped`.
- The profile does not validate.

Generic mode points at [prompts/onboard.md](../prompts/onboard.md). It does not guess a checklist.

## What a confirmed profile selects

`output_formats: skipped` or `unknown` means the applicable set below. A named list keeps only those workflows, plus the decision journal.

| Workflow | Prompt | When |
| --- | --- | --- |
| Screening | [screening.md](../prompts/workflows/screening.md) | One note per strategy id |
| Thesis and counterthesis | [thesis-counterthesis.md](../prompts/workflows/thesis-counterthesis.md) | One pair per strategy id |
| PE diligence | [pe-diligence.md](../prompts/workflows/pe-diligence.md) | `strategy_kind: pe` only |
| Fund-manager diligence | [fund-manager-diligence.md](../prompts/workflows/fund-manager-diligence.md) | `strategy_kind: fund_selection` only |
| Monitoring | [portfolio-monitoring.md](../prompts/workflows/portfolio-monitoring.md) | One watch list per strategy id |
| IC memo | [ic-memo.md](../prompts/workflows/ic-memo.md) | The seat votes or decides, or they asked for `ic_memo` |
| Decision journal | [decision-journal.md](../prompts/workflows/decision-journal.md) | Always, so the decision is not left in chat |

Wiki starters under `templates/wiki-starters/` use the same split. `scaffold` fills one playbook per selected row and skips any path that already exists.

## How the checklists differ

The phrases live in `emphasis` inside the schema. Screening, thesis, diligence, and monitoring each quote the phrase for that kind and refuse the others.

- PE asks control or minority as stated, buyout or growth as stated, earnings quality, cash, debt, and downside. It does not ask seed follow-on or GP terms. Monitoring watches cash, debt, and whether the stated value-creation plan happened. The counterthesis is earnings quality or debt service, not a different multiple.
- VC asks stage, ownership, follow-on, and unit economics. It does not ask buyout debt or carry. Monitoring watches the follow-on reserve and unit economics since the last source.
- A hedge fund asks style, holding period, exposures, liquidity, catalysts, and what would falsify the book. It does not ask buyout covenants or GP fundraising. Monitoring watches exposures, liquidity, and the catalyst clock.
- Fund selection asks GP strategy, team, attribution, terms, and repeatability. It does not ask portfolio-company debt or venture unit economics unless that other subprofile is the file you opened. Monitoring watches manager reports, team changes, and terms.

If `activity` is `both`, the map emits one row per subprofile. It does not merge the PE list with the GP list.

## Conflicts that stay visible

The map does not rewrite the mandate.

- `ic_memo` with `decision_authority: recommend_only` still produces the memo prompt, and the memo must say it does not decide.
- An output they asked for, with no subprofile of that kind, is named and not added.
- `constraint_conflicts` in `tools/mandate.py` compares a request with leverage, holding period, concentration, and authority. It returns sentences. It does not edit the file.
- An MFO confirmation requires `client_separation: separate_files`. The validator rejects a shared client list instead of storing one.

A revision above 1 requires a new file under `revisions/` with Before and After. The initializer will not overwrite that file or the mandate.
