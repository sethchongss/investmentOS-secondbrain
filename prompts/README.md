# Prompts

Start with [onboard.md](onboard.md). It is the interview. The files under [workflows/](workflows/) are the later prompts, and they differ by strategy. These are instructions you paste into an agent you already use, along with the files you want it to read. This repository does not run them, schedule them, or connect them to a data feed.

Every research prompt loads `vault/profile/mandate.md` when that file is confirmed. If it is missing or still a draft, the prompt stays in generic mode and does not invent a mandate. `tools/init_mandate.py` checks the saved profile and prints the map. It does not ask the questions.

Paste the prompt, then the relevant templates and vault files. Read the reply before you save it. An agent does not approve its own writeback. You change `status` to `approved` or `rejected` yourself.

Each prompt tells the agent to treat source text as untrusted data. A capture can contain text that looks like an instruction. It is still a capture.

The Low Oriole files are a format sample. They are fictional. Do not copy those numbers into a real vault as if they were evidence.
