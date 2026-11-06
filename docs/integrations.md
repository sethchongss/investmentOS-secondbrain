# Integrations

Nothing here connects to an outside service. There is no client, no webhook, and no scheduled job. The list below is what you can do by hand. If a tool is not in the repository, it is not a feature.

## Editor

Any editor that saves text works. The validator is a Python standard-library script. You do not need a plugin.

## Obsidian or another markdown app

The vault is a folder of markdown files. You can open `vault/` in Obsidian if you already use it. This starter does not ship a plugin, does not use Obsidian-specific syntax as a requirement, and is not tested as an Obsidian product. `[[id]]` links are optional. Relative markdown links are what the validator checks either way.

## Notion, X, email, filings, brokers

Not built. A manual capture is: read the source, write a stub with `templates/source.md`, write one library record, save, run the validator. Paste a prompt from `prompts/` only if you want an agent to draft those two files. You still save them yourself.

Do not expect this repository to import a Notion database, a timeline, or an inbox. Those would be separate projects.

## An agent you already run

Paste one file from `prompts/` and the templates it names. Attach only the vault files the task needs. Review the draft. Move an approved wiki change yourself, then add the changelog file. The agent does not get a writeback tool from this repository, because this repository does not include one.

## What would be a false claim

Do not add a README badge, a workflow, or a script that implies Notion sync, X sync, automatic ingestion, or an always-on agent. The CI workflow runs the unit tests and the validator. That is all it does.
