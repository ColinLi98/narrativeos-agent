# NarrativeOS Agent Codex Contract

This repository is the open-source local agent only.

Codex may:

- help the user create or edit local story source files
- run `narrativeos-agent generate`
- run `narrativeos-agent preview`
- run `narrativeos-agent export`
- run `narrativeos-agent validate`

Codex must not:

- connect to the hosted NarrativeOS production database
- request platform database credentials
- upload a bundle without explicit user instruction
- write provider keys or user secrets into the repository

The output artifact for platform submission is a `.nosbook` file.
