# Templates

Copy a template into your private `vault/` (or into a scratch copy of the example) and replace every `REPLACE_ME`. The validator treats that token as unfinished.

Templates are not a vault. Point the validator at `vault/` or at `examples/low-oriole-metering`, not at this folder.

| File | Becomes |
| --- | --- |
| `source.md` | `raw/` stub, kept as captured |
| `library-record.md` | one claim record for that capture |
| `relation.md` | `library/relations/` |
| `principle.md`, `thesis.md`, `company.md`, `sector.md`, `playbook.md`, `glossary.md` | wiki pages, changed only through a proposal |
| `journal-entry.md` | `wiki/journal/YYYY-MM-DD-slug.md` |
| `memo.md`, `digest.md`, `review.md` | `output/` |
| `writeback-proposal.md` | `proposals/` |
| `changelog-entry.md` | `changelog/` after a person approves |

`synthetic: false` is the default for real notes. The shipped example uses `synthetic: true` and is checked with `--example`.
