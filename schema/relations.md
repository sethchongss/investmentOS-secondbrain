# Relations

Five relation values are accepted. Anything else fails the validator.

| Value | `from` | `to` | Use it when |
| --- | --- | --- | --- |
| `supports` | the confirming record | the record it confirms | A second capture, with its own link, agrees on the same claim. |
| `contradicts` | the challenger | the record it challenges | The records disagree. Say which sentence, not just which file. |
| `extends` | the case | the broader record | A specific episode is an instance of a general claim. |
| `supersedes` | the newer claim | the claim it replaces | The later record replaces a stated figure or definition. The old sentence stays in the old file. |
| `duplicates` | the later copy | the canonical record | Same claim, new link or post id, no new fact. Do not count it as extra evidence. |

Same `link` or same `post_id` never gets this far. The validator rejects the second file. `duplicates` is the judgment you still make when the identifiers differ, as with a syndication clip.

`claim_status: superseded` on a library record requires `superseded_by` and a `supersedes` relation from that id to this one. `claim_status: contested` requires a `contradicts` relation that touches the record. The relation note is where you limit the scope, for example "the backlog total only, not the attach comment."

Do not use a relation to paper over a missing source. No relation is a valid outcome.
