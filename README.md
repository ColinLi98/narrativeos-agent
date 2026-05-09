# NarrativeOS Agent

NarrativeOS Agent is the local-first creator tool for writing, validating, previewing, and exporting novels as `.nosbook` bundles.

This repository is intentionally separate from the hosted NarrativeOS marketplace. It does not connect to the platform database, does not use platform workers, and does not upload anything unless the user explicitly takes a bundle to the website.

## What Is Included

- installable Python CLI: `narrativeos-agent`
- Codex plugin manifest and skill
- local generate / preview / export / validate commands
- `.nosbook` cover asset validation
- derivative-work metadata support
- sample `.nosbook` bundle under `examples/`
- release zip builder under `scripts/build-release-zip`

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

Open this repo in Codex and ask it to run the NarrativeOS Agent skill for your story workspace. A typical local flow is:

```bash
narrativeos-agent generate --out ./local_story --title "My Story"
narrativeos-agent preview --source ./local_story --out ./local_story/preview.html
narrativeos-agent export --source ./local_story --out ./my_story.nosbook
narrativeos-agent validate ./my_story.nosbook
```

You can edit the JSON files in `local_story/chapters/` directly or ask Codex to revise them before exporting again.

For derivative works after receiving a platform license:

```bash
narrativeos-agent generate \
  --out ./derived_story \
  --title "My Licensed Derivative" \
  --derivative-of "<platform-work-ref>" \
  --derivative-license-id "<platform-license-ref>" \
  --no-derivatives
```

## Bundle Contract

A `.nosbook` contains:

- `manifest.json`
- `chapters/*.json`
- `quality_report.json`
- `rights_attestation.json`
- `provenance.json`
- `content_hashes.json`
- `cover/cover.png`, `cover.jpg`, `cover.jpeg`, or `cover.webp`

Cover requirements:

- PNG, JPEG, or WebP
- max 2 MB
- SVG is intentionally blocked in v1

The hosted marketplace accepts `.nosbook` bundles for review and publishing. The agent does not write platform data; the website extracts the uploaded bundle into its own storage, review, purchase, royalty, and audit records.

## Creator Quickstart

Read [docs/creator_quickstart.md](docs/creator_quickstart.md) for the full creator flow:

1. install
2. generate a local story
3. preview
4. export and validate
5. upload to [pilot.lixidol.com/marketplace](https://pilot.lixidol.com/marketplace)

## Codex Plugin

This repository is also a Codex plugin package. The plugin entry is:

- `.codex-plugin/plugin.json`
- `skills/narrativeos-agent/SKILL.md`
- `scripts/narrativeos-agent`
- `scripts/smoke-test`

After installing or opening the repo in Codex, ask:

> 用 NarrativeOS Agent 在本地生成一本小说，并导出 marketplace-ready `.nosbook`。

## Release Zip

Build a release archive:

```bash
scripts/build-release-zip
```

The output is written to `release/narrativeos-agent-0.1.0.zip`.

The archive excludes `.git`, virtualenvs, local env files, build caches, and generated release zips.

## Local Data Boundary

The agent is local-first:

- no platform database connection
- no hosted generation worker dependency
- no automatic upload
- no platform secret required

Users may configure their own model tools or ask Codex to edit the local story files. The final export remains a portable `.nosbook` bundle.

## License

AGPL-3.0-or-later. Commercial licensing is available separately.
