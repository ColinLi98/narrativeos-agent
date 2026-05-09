# NarrativeOS Agent v1.0.0

Production longform creator release.

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
release/narrativeos-agent-1.0.0.zip
```
