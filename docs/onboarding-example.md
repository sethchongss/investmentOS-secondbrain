# Fictional onboarding excerpt

This is a sample of the interview in [prompts/onboard.md](../prompts/onboard.md). The person, the desk, and the answers are fictional. It is not a transcript of a client and not a recommended portfolio.

Agent: Institution type is not your investment style. Which apply: SFO, MFO, VC, PE, hedge fund, independent, or other? More than one is fine. Unknown or skip is a complete answer. I will not ask for a firm name.

Person: PE.

Agent: Direct investments, fund selection, or both? I will not assume a PE desk only buys control.

Person: Direct.

Agent: Role, and do you recommend, vote, or decide?

Person: Partner. I vote.

Agent: I'll ask the direct PE subprofile on its own. Ownership: control, minority, or both? Deal type: buyout, growth, both, not a buyout, or unknown?

Person: Both ownership. Both buyout and growth. Don't make it all buyout.

Agent: Earnings quality, cash and debt, and downside: in scope, unknown, or skip? Value creation only if you want it as a question rather than a fact.

Person: All in scope as questions. No company names.

Agent: Geography, sectors, and a size range are optional.

Person: Skip all three.

Agent: Leverage, concentration, and a return target if you want one stated. I will not propose a number.

Person: Leverage limited. No single name above a third of the sleeve. No return target.

Agent: Here is the read-back. Institution PE, activity direct, seat partner, authority vote. One subprofile, kind PE, ownership both, deal type both. Size skipped. Return not stated. This is operating context, not evidence and not advice. I have not written a file. Confirm, or correct a line.

Person: Confirm.

Agent: Save this as `vault/profile/mandate.md` and the subprofile as `vault/profile/strategies/reed-pe.md` only if those paths are absent. Then run `python3 tools/init_mandate.py validate vault/profile`. The script checks the fields. It does not interview you. If you later change ownership, that is a new file under `vault/profile/revisions/` with the old wording under Before. I will not overwrite the old file.

The saved fictional result of a similar confirm is [reed-harbor-direct](../examples/profiles/reed-harbor-direct/mandate.md). A family office that selects funds, instead of this direct desk, is [hearth-lane-office](../examples/profiles/hearth-lane-office/mandate.md).
