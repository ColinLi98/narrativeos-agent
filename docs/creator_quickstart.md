# NarrativeOS Agent Creator Quickstart

This quickstart is for creators who want to write locally with Codex and upload a finished `.nosbook` to the NarrativeOS marketplace.

## 1. Install

```bash
git clone https://github.com/ColinLi98/narrativeos-agent.git
cd narrativeos-agent
python3 -m pip install --user .
```

For development or editing the agent source:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
```

## 2. Generate A Local Longform Story Workspace

```bash
narrativeos-agent init --out ./local_story --title "My First Local Novel" --worldpack urban_mystery_lotus_lane
narrativeos-agent generate --source ./local_story --chapters 500
narrativeos-agent validate --source ./local_story --profile longform_500
```

This creates local JSON source files only. It checkpoints every completed chapter and does not connect to the NarrativeOS platform database. If generation is interrupted, rerun `generate` with the same `--source` and target chapter count, or append chapters with:

```bash
narrativeos-agent continue --source ./local_story --chapters 50
```

You can edit:

- `manifest.json`
- `chapters/*.json`
- `rights_attestation.json`
- `provenance.json`
- `cover/cover.png`

## 3. Preview

```bash
narrativeos-agent preview --source ./local_story --out ./local_story/preview.html
```

Open `preview.html` in your browser and revise the local chapter files until the work is ready.

## 4. Export And Validate

```bash
narrativeos-agent export --source ./local_story --out ./my_story.nosbook
narrativeos-agent validate ./my_story.nosbook
```

A valid marketplace bundle includes:

- `manifest.json`
- `chapters/*.json`
- `quality_report.json`
- `rights_attestation.json`
- `provenance.json`
- `content_hashes.json`
- `cover/cover.png`, `cover.jpg`, `cover.jpeg`, or `cover.webp`

Cover requirements:

- PNG, JPEG, or WebP only
- max 2 MB
- no SVG in v1

## 5. Derivative Works

If you licensed an existing marketplace work for derivative creation, include the platform work and license references:

```bash
narrativeos-agent init \
  --out ./derived_story \
  --title "My Licensed Derivative" \
  --derivative-of "<platform-work-ref>" \
  --derivative-license-id "<platform-license-ref>" \
  --no-derivatives
narrativeos-agent generate --source ./derived_story --chapters 500
narrativeos-agent validate --source ./derived_story --profile longform_500
```

The exported bundle records the original work and derivative license in `rights_attestation.json` and `provenance.json`.

## 6. Upload To Marketplace

After validation, go to:

[https://pilot.lixidol.com/marketplace](https://pilot.lixidol.com/marketplace)

Use the Creator upload flow to submit the `.nosbook` for review. The platform handles review, publishing, purchases, royalties, support, and takedown governance.

## Local Boundary

The agent is local-first:

- no platform Neon access
- no hosted generation worker
- no automatic upload
- no platform secrets

Only the final `.nosbook` that you explicitly upload enters the marketplace review pipeline.
