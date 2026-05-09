# NarrativeOS Agent v0.1.0

Initial open-source local creator package.

## Included

- Local CLI: `generate`, `preview`, `export`, `validate`
- Codex plugin manifest and NarrativeOS Agent skill
- `.nosbook` schema validation
- required cover asset validation for PNG/JPEG/WebP
- derivative-work metadata fields
- sample `.nosbook` bundle
- reproducible release zip script
- GitHub Actions CI

## Not Included

- Hosted platform upload automation
- Production marketplace credentials
- Neon/Vercel/Stripe access
- Hosted generation worker access

## Release Artifact

Build with:

```bash
scripts/build-release-zip
```

Expected output:

```text
release/narrativeos-agent-0.1.0.zip
```
