# NarrativeOS Agent

NarrativeOS Agent is the local-first creator tool for writing, validating, previewing, and exporting novels as `.nosbook` bundles.

This repository is intentionally separate from the hosted NarrativeOS marketplace. It does not connect to the platform database, does not use platform workers, and does not upload anything unless the user explicitly takes a bundle to the website.

## Install

```bash
git clone https://github.com/ColinLi98/narrativeos-agent.git
cd narrativeos-agent
python3 -m pip install --user .
```

If your Python/pip does not put console scripts on `PATH`, use:

```bash
python3 -m narrativeos_agent.cli --help
```

## Use with Codex

Open this repo in Codex and ask it to run the agent commands for your story workspace. A typical local flow is:

```bash
narrativeos-agent generate --out ./local_story --title "My Story"
narrativeos-agent preview --source ./local_story --out ./local_story/preview.html
narrativeos-agent export --source ./local_story --out ./my_story.nosbook
narrativeos-agent validate ./my_story.nosbook
```

You can edit the JSON files in `local_story/chapters/` directly or ask Codex to revise them before exporting again.

## Bundle Contract

A `.nosbook` contains:

- `manifest.json`
- `chapters/*.json`
- `quality_report.json`
- `rights_attestation.json`
- `provenance.json`
- `content_hashes.json`
- optional cover/media files

The hosted marketplace accepts `.nosbook` bundles for review and publishing. Large chapter bodies and bundle archives belong in object storage on the platform side; the platform database should only keep metadata, hashes, purchases, royalties, review status, and audit records.

## Local Data Boundary

The agent is local-first:

- no platform database connection
- no hosted generation worker dependency
- no automatic upload
- no platform secret required

Users may configure their own model tools or ask Codex to edit the local story files. The final export remains a portable `.nosbook` bundle.

## License

AGPL-3.0-or-later. Commercial licensing is available separately.
