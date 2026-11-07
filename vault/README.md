# Private vault

This folder is yours. The example under `examples/low-oriole-metering/` is the synthetic demonstration. Do your real filing here.

Git ignores markdown you add under this tree and keeps the directory layout. That is not a lock. Do not `git add -f` these notes. Do not put material nonpublic information, account numbers, or secrets here if this repository might ever be published. See `docs/privacy-and-security.md`.

## Mandate first

Your investment mandate is operating context, not a source. Git ignores it with the rest of this tree.

```bash
python3 tools/init_mandate.py init
```

That copies `templates/mandate/mandate.md` only if `vault/profile/mandate.md` is absent. Fill it by pasting `prompts/onboard.md` into an agent you already use, then:

```bash
python3 tools/init_mandate.py validate vault/profile
python3 tools/init_mandate.py map vault/profile
python3 tools/init_mandate.py scaffold vault/profile
```

Do not put a real firm name, client list, deal, AUM, holding, or credential in the profile. Unknown and skipped are valid. An MFO does not get a shared client file. If the mandate is missing or unconfirmed, prompts stay generic.

## Research notes

From the repository root:

```bash
cp templates/journal-entry.md vault/wiki/journal/2026-01-01-start.md
```

Edit the copy. Replace every `REPLACE_ME`. Keep `append_only: true`. The filename already starts with the date in the template. Then:

```bash
python3 tools/validate_vault.py vault
```

Do not pass `--example` for this folder. `--example` is only for the fictional demonstration, where web links are forbidden. Real `https` links you captured are allowed here. The validator still does not open them.

Copy `templates/source.md` into `vault/raw/` and `templates/library-record.md` into `vault/library/` when you file a capture. One source, one library record, matching `link` and `post_id`.

Wiki edits go through `vault/proposals/` and, after you approve one, `vault/changelog/`. The prompts in `prompts/` are optional paste text for an agent you already use.
