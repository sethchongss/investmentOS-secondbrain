# Fictional mandate profiles

These are saved answers, not interviews and not books of record. Every file is fictional. None of them names a real firm, a client, a deal, a holding, or a credential. Links are not web addresses. Do not copy the choices into a private vault as if they were yours.

| Profile | Institution | Activity | What the map should do |
| --- | --- | --- | --- |
| [reed-harbor-direct](reed-harbor-direct/mandate.md) | PE | direct | PE diligence. Ownership is both control and minority. Deal type is both buyout and growth. A dated revision kept the earlier "unknown". |
| [hearth-lane-office](hearth-lane-office/mandate.md) | SFO | fund selection | Manager diligence. Not PE company diligence. An SFO is not assumed to allocate only. |
| [glass-keel](glass-keel/mandate.md) | hedge fund | direct | Long/short monitoring. Not buyout covenants. |
| [wicket-seed](wicket-seed/mandate.md) | VC | direct | Stage, follow-on, unit economics. The seat recommends only, so no IC memo is invented. |
| [split-oak](split-oak/mandate.md) | independent | both | Two subprofiles. The IC request conflicts with recommend-only and stays visible. |
| [two-lamp-mfo](two-lamp-mfo/mandate.md) | MFO | fund selection | Separate client files. No client is named. Not a direct book. |

Check them from the repository root:

```bash
python3 tools/init_mandate.py validate-all
```

A private mandate belongs in `vault/profile/`, which git ignores. These examples are the only profiles that belong in the commit.
