# Publication checklist

Use this before you put the starter in a public repository. The files in this workspace are a project you can publish. Publishing is a separate step you do yourself.

- [ ] `python3 tools/validate_vault.py examples/low-oriole-metering --example` passes.
- [ ] `python3 -m unittest discover -s tests -v` passes.
- [ ] `vault/` has no notes in the commit. `git status` does not list private markdown. Do not `git add -f` that folder.
- [ ] The example is still labeled synthetic, or you removed it. It has no `http://` or `https://` links and no real citation dressed up as a source.
- [ ] You added no material nonpublic information, credentials, account numbers, customer lists, or employer documents.
- [ ] Excerpts you added are short and you have the right to keep them. Full posts, filings, and articles are not republished here.
- [ ] `human_reviewer` and `approved_by` values are names or roles you are willing to show. No account ids.
- [ ] `LICENSE` is still present, including the notice that user notes and third-party sources are not covered by it.
- [ ] The README still says this is not investment advice and that no sync or background agent ships with the repo.
- [ ] You read every wiki page you changed. The validator does not check truth.

If a changelog entry describes a real position, a real issuer, or a real nonpublic fact, it does not belong in the public copy. Keep that history in the private vault.
