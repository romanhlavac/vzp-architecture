# Commit publication privacy

Before any cross-agent state push, inspect the actual immutable candidate commit message, its direct parent, changed paths, and exact state transition. Stop if the message includes an additional attribution or session-link trailer. In cloud Claude Code, also verify the effective project setting `attribution.sessionUrl=false`; a setting alone is not proof. Preserve no-force and non-fast-forward server rules. Never rewrite existing history without explicit approval.
