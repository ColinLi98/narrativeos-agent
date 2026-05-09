---
name: narrativeos-agent
description: Use when a creator wants Codex to generate, edit, validate, preview, or export a local NarrativeOS .nosbook novel bundle for marketplace upload.
---

# NarrativeOS Agent

Use this skill for local creator workflows only. The agent writes local files, validates `.nosbook` bundles, and exports portable work packages. It must not connect to the hosted platform database or use production marketplace credentials.

## Safety Contract

- Keep all generation and edits local to the user's chosen workspace.
- Do not read or write Neon, Vercel, Stripe, or marketplace production secrets.
- Do not upload a bundle to the hosted marketplace unless the user explicitly asks for upload.
- Validate before upload or handoff.
- Cover images are required for marketplace-ready bundles: PNG, JPEG, or WebP, max 2 MB.
- Do not include `kernel`, `benchmark`, `world_version_id`, DB URLs, tracebacks, tokens, or provider secrets in visible story text or exported metadata.

## Commands

From an installed package:

```bash
narrativeos-agent generate --out ./local_story --title "My Story"
narrativeos-agent preview --source ./local_story --out ./local_story/preview.html
narrativeos-agent export --source ./local_story --out ./my_story.nosbook
narrativeos-agent validate ./my_story.nosbook
```

From the repository without installation:

```bash
PYTHONPATH=src python3 -m narrativeos_agent.cli generate --out ./local_story --title "My Story"
PYTHONPATH=src python3 -m narrativeos_agent.cli export --source ./local_story --out ./my_story.nosbook
PYTHONPATH=src python3 -m narrativeos_agent.cli validate ./my_story.nosbook
```

For derivative works:

```bash
narrativeos-agent generate \
  --out ./derived_story \
  --title "My Licensed Derivative" \
  --derivative-of "<platform-work-ref>" \
  --derivative-license-id "<platform-license-ref>" \
  --no-derivatives
```

## Expected Output

Report:

- source directory path
- `.nosbook` bundle path
- preview HTML path when created
- validation status
- cover status
- derivative permission state
- confirmation that `platform_db_access` is false

## Handoff To Marketplace

The hosted marketplace accepts the exported `.nosbook` through its Creator upload flow. The platform stores uploaded/published content and transaction metadata; the local generation workspace remains on the creator's machine.
