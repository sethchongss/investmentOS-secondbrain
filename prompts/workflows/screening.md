# Prompt: screening

Screen one name against one strategy subprofile. You do not give investment advice or a rating that pretends to be a decision.

## Mandate

Read `vault/profile/mandate.md` and only the strategy file for the id in front of you. If the mandate is missing or `status` is not `confirmed`, stop tailoring. Say you are in generic mode and point at `prompts/onboard.md`. Do not guess the institution.

The mandate is operating context, not evidence and not a source. Cite a library record for every claim about an issuer or a manager. If the request conflicts with leverage, concentration, holding period, liquidity, or decision authority, write the conflict and leave the mandate as confirmed.

Use the block that matches `strategy_kind`. Do not paste the other blocks into the note.

## PE

Ask control or minority as stated, buyout or growth as stated, earnings quality, cash, debt, and downside.

Do not ask seed follow-on reserves or a GP's fund terms.

## VC

Ask stage, ownership, follow-on, and unit economics.

Do not ask buyout debt or a manager's carry.

## Hedge fund

Ask style, holding period, exposures, liquidity, catalysts, and what would falsify the book.

Do not ask control buyout covenants or GP fundraising terms.

## Fund selection

Ask GP strategy, team, attribution, terms, and repeatability.

Do not ask portfolio-company debt or venture unit economics unless a separate direct subprofile is the file you opened.

## Output

A short note with Sources and Inference. Unknown fields stay unknown. The script `python3 tools/init_mandate.py map` can name this prompt. It does not write the screen.
