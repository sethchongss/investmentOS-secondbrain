# Schema

`vault.schema.json` is the field list the research-vault validator loads. A mandate is a different file, checked by `tools/init_mandate.py` against [mandate.schema.json](mandate.schema.json) and described in [mandate.md](mandate.md). `tools/validate_vault.py` skips `profile/` so a private mandate is not mistaken for a source. This page is the research contract in prose. Dates are `YYYY-MM-DD`. `synthetic` is a boolean. Ids are lowercase letters, digits, and hyphens. `conviction` is an integer from 1 to 5.

Paths in frontmatter are relative to the vault root (`raw/note.md`, not `../raw/note.md`). Paths in the markdown body are normal relative links.

## source (`raw/`)

`id`, `type`, `title`, `source`, `author`, `date_posted`, `date_captured`, `link`, `post_id`, `synthetic`.

The stub keeps the excerpt. Later steps do not rewrite it to match a new belief.

## library (`library/`, not `library/relations/`)

Everything on a source, plus `claim`, `specifics` (list), `category`, `tags` (list), `context`, `reading_status`, `source_stub`.

`reading_status`: `unread`, `reading`, `read`, `filed`.

Optional: `claim_status` (`active`, `contested`, `superseded`) and `superseded_by`.

One capture, one library record. `link` and `post_id` must match the stub and must be unique among library records. Further points from the same capture go in `specifics`.

## relation (`library/relations/`)

`id`, `type`, `relation`, `from`, `to`, `note`, `synthetic`. See [relations.md](relations.md). `from` and `to` are library ids.

## principle (`wiki/principles/`)

`thesis`, `conviction`, `evidence_for`, `evidence_against`, `current_belief`, `recall_question`, `recall_answer`, `last_shown`, `maturity`.

`maturity` is `developing` or `recurring`. Recurring needs at least three library ids in `evidence_for`. That bar is not applied to company facts, sector notes, or a developing principle.

## thesis, company, sector, playbook, glossary

- Thesis: `thesis`, `conviction`, `current_belief`, `linked_principles`.
- Company: `company`, `current_belief`, `conviction`. Optional `last_writeback` (a changelog id whose `target` is this file).
- Sector and playbook: `summary`.
- Glossary: `term`, `summary`.

These are the pages a writeback may update in place.

## journal (`wiki/journal/`)

`date`, `append_only: true`. The filename starts with `date`. Add a new file. Do not revise an old one.

## memo, digest, review (`output/`)

- Memo: `date`, `cites` (library ids). Body contains the headings `## Sources` and `## Inference`.
- Digest: `date`, `covers_from`, `covers_to`.
- Review: `date`, `subject` (a principle id).

## writeback proposal (`proposals/`)

`date`, `target`, `status` (`proposed`, `approved`, `rejected`), `proposal_note`.

`target` is an existing wiki page under principles, theses, companies, sectors, playbooks, or glossary. Not raw sources, not the library, not the journal, not output, not another proposal or changelog.

`approved` also requires `human_reviewer` and `review_date`. The reviewer is a name or a role you choose to write down. It is not an account id. This starter does not log into anything.

## changelog (`changelog/`)

`date`, `target`, `proposal`, `approved_by`. The proposal is approved, and the target matches. Body contains `## Before` and `## After`. New file per edit. Append-only.

## Checks that are not extra fields

The validator also checks:

- unique ids
- unique source `link` and `post_id`, and the same for library records
- library provenance matches its stub
- local markdown links and `[[id]]` links resolve inside the vault
- dates are real, and `date_captured` is not earlier than `date_posted`
- superseded and contested records have the matching relation
- a changelog is not earlier than its proposal and does not point at a different target than the proposal
- `last_writeback` points at a changelog for this same file

`--example`, used on `examples/low-oriole-metering`, also requires `synthetic: true`, `synthetic://` links, `syn-` post ids, the word "synthetic" in each source body, and no `http://` or `https://` anywhere in that vault.

Your private `vault/` is checked without `--example`, so real `https` links you captured are allowed. The tool still does not fetch them.
