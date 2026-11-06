# Privacy and security

This starter stores research as markdown files on disk. It has no accounts, no telemetry, and no server.

## Your notes and the example

`examples/low-oriole-metering/` is fictional and meant to be readable by anyone who has the repository.

`vault/` is the private working folder. Git is configured to ignore notes there and to keep the folder layout. Ignoring a file is not encryption. `git add -f` will override it. Do not force-add `vault/`.

If you publish the repository, publish the starter and the example, not a copy of your private vault. Run [publication-checklist.md](publication-checklist.md) first.

## Do not file

- Material nonpublic information. The glossary entry in the example states the fence and does not illustrate it.
- Account numbers, customer lists, credentials, API keys, tokens, or private keys.
- A full copyrighted article, transcript, or filing. Keep a short excerpt you have the right to keep, plus the link and the date, in the private vault. The starter's license does not give you or anyone else rights in that material.

## What the tools do

`tools/validate_vault.py` reads markdown and prints errors. It does not phone home, and it does not rewrite files. The prompts do nothing until you paste them into a separate agent. Anything you paste is then in that agent's context. Paste the excerpt you mean to paste, not a folder of unrelated private files.

## Names in the changelog

`human_reviewer` and `approved_by` are words you choose so a later reader knows a person approved the edit. Use a role ("research lead") if you do not want a legal name in a repository you might publish. Do not put an account id, an employee id, or a customer id there.
