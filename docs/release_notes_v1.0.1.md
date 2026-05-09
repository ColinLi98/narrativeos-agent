# NarrativeOS Agent v1.0.1

Patch release for the local 500-chapter creator Agent.

## Fixed

- `generate --source` now preserves the worldpack selected by `init`.
- A workspace initialized with `--worldpack jade_court_romance` no longer falls back to `urban_mystery_lotus_lane` during generation.
- Added regression coverage for preserving genre, setting, and lead character across the `init -> generate --source` flow.

## Included

- Local 500-chapter generation through `init`, `generate`, and `continue`
- Per-chapter checkpointing in `state/checkpoint.json`
- `longform_500` validation with hard-fail, repetition, detail, leak, and pacing checks
- `.nosbook` export with chapter bodies, cover asset, rights, provenance, hashes, and quality report
- Local HTML preview
- Codex plugin instructions for longform generation and marketplace-ready export

## Boundary

- No platform Neon access
- No hosted worker access
- No Vercel, Stripe, or Marketplace secrets
- No automatic upload

## Release Artifact

Build with:

```bash
scripts/build-release-zip
```

Expected output:

```text
release/narrativeos-agent-1.0.1.zip
```
