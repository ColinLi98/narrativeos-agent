from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from .nosbook import NosbookValidationError, export_nosbook, validate_nosbook_file, write_demo_source


def _load_source_chapters(source_dir: Path) -> list[dict[str, Any]]:
    chapters_dir = source_dir / "chapters"
    chapters: list[dict[str, Any]] = []
    for path in sorted(chapters_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            chapters.append(payload)
    return chapters


def write_preview_html(source_dir: Path | str, output_path: Path | str) -> Path:
    source = Path(source_dir)
    output = Path(output_path)
    if not source.is_dir():
        raise NosbookValidationError("nosbook_source_dir_missing")
    manifest_path = source / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError as exc:
            raise NosbookValidationError("nosbook_json_invalid", details={"file": "manifest.json"}) from exc
    chapters = _load_source_chapters(source)
    if not chapters:
        raise NosbookValidationError("nosbook_chapters_required")
    title = escape(str(manifest.get("title") or "NarrativeOS Local Preview"))
    chapter_html = []
    for chapter in chapters:
        chapter_title = escape(str(chapter.get("title") or "Untitled Chapter"))
        body = escape(str(chapter.get("body") or "")).replace("\n", "<br />")
        chapter_index = escape(str(chapter.get("chapter_index") or len(chapter_html) + 1))
        chapter_html.append(
            "<article class=\"chapter\">"
            f"<p class=\"chapter-index\">Chapter {chapter_index}</p>"
            f"<h2>{chapter_title}</h2>"
            f"<p>{body}</p>"
            "</article>"
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ margin: 0; background: #0b0f17; color: #e5edf7; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 840px; margin: 0 auto; padding: 40px 20px; }}
    h1 {{ font-size: 32px; margin: 0 0 24px; }}
    .chapter {{ border-top: 1px solid rgba(148, 163, 184, 0.24); padding: 28px 0; }}
    .chapter-index {{ color: #67e8f9; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; }}
    h2 {{ font-size: 22px; margin: 8px 0 14px; }}
    p {{ line-height: 1.8; color: #cbd5e1; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    {''.join(chapter_html)}
  </main>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NarrativeOS local agent bundle tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Create a local demo source bundle without platform DB access.")
    generate.add_argument("--out-dir", "--out", dest="out_dir", required=True)
    generate.add_argument("--title", default="Local Agent Demo")

    validate = sub.add_parser("validate", help="Validate a .nosbook bundle.")
    validate.add_argument("bundle")

    export = sub.add_parser("export", help="Export a source directory to .nosbook.")
    export.add_argument("--source-dir", "--source", dest="source_dir", required=True)
    export.add_argument("--out", required=True)

    preview = sub.add_parser("preview", help="Render a local source directory into a standalone HTML preview.")
    preview.add_argument("--source-dir", "--source", dest="source_dir", required=True)
    preview.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            source = write_demo_source(Path(args.out_dir), title=args.title)
            print(json.dumps({"status": "generated", "source_dir": str(source), "platform_db_access": False}, ensure_ascii=False))
            return 0
        if args.command == "validate":
            result = validate_nosbook_file(args.bundle)
            print(json.dumps({"status": "valid", **result.public_summary()}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "export":
            result = export_nosbook(Path(args.source_dir), Path(args.out))
            print(json.dumps({"status": "exported", "bundle": args.out, **result.public_summary()}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "preview":
            output = write_preview_html(Path(args.source_dir), Path(args.out))
            print(json.dumps({"status": "preview_ready", "preview": str(output), "platform_db_access": False}, ensure_ascii=False))
            return 0
    except NosbookValidationError as exc:
        print(json.dumps({"status": "invalid", "code": exc.code, "details": exc.details}, ensure_ascii=False, indent=2))
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
