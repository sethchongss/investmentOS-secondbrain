# Low Oriole Metering (synthetic example)

This folder is a finished tiny vault. **Low Oriole Metering is not a real company.** Brack Flags is not a real product. The towns, the ledger, the desk notes, and the people are fictional. Every figure is made up for the example. Links use `synthetic://` and are not addresses on the web.

This is not investment advice and not a record of anyone's portfolio.

## Read it in this order

1. [The company page as it stands now](wiki/companies/low-oriole-metering.md)
2. [The changelog, with the before and after](changelog/2026-03-21-backlog-correction.md)
3. [The proposal the human edited before approving](proposals/2026-03-20-backlog-correction.md)
4. [The January stub, which still says $180 million](raw/src-lom-20260114.md)
5. [The superseded library record](library/lib-lom-001.md) and [the ledger record](library/lib-lom-003.md)
6. [Supersedes](library/relations/rel-lom-001.md), [contradicts](library/relations/rel-lom-002.md), and [duplicates](library/relations/rel-lom-005.md)
7. [The memo, sources separate from inference](output/memos/2026-03-21-low-oriole-backlog.md)
8. [The compiled principle](wiki/principles/backlog-definition.md)
9. [The 15 Jan journal](wiki/journal/2026-01-15-first-pass.md) and [the 21 Mar journal](wiki/journal/2026-03-21-after-approval.md)

The January journal is wrong relative to March, on purpose. It was not rewritten.

Validate this folder with:

```bash
python3 tools/validate_vault.py examples/low-oriole-metering --example
```

Run that from the repository root. `--example` rejects ordinary web links and requires `synthetic: true`. Your private `vault/` is validated without that flag.
