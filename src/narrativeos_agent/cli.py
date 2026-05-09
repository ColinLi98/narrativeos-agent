from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from .longform import DEFAULT_WORLD_PACK, continue_project, generate_project, init_project, validate_project
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

    init = sub.add_parser("init", help="Create a local longform story workspace.")
    init.add_argument("--out", required=True)
    init.add_argument("--title", default="Local Longform Novel")
    init.add_argument("--worldpack", default=DEFAULT_WORLD_PACK)
    init_derivative_group = init.add_mutually_exclusive_group()
    init_derivative_group.add_argument("--allow-derivatives", dest="allow_derivatives", action="store_true", default=True)
    init_derivative_group.add_argument("--no-derivatives", dest="allow_derivatives", action="store_false")
    init.add_argument("--derivative-of", default=None)
    init.add_argument("--derivative-license-id", default=None)

    generate = sub.add_parser("generate", help="Create a local demo source bundle without platform DB access.")
    generate.add_argument("--source", default=None, help="Existing local story workspace to generate into.")
    generate.add_argument("--out-dir", "--out", dest="out_dir", default=None, help="Legacy shortcut: initialize this workspace, then generate.")
    generate.add_argument("--chapters", type=int, default=None, help="Target total chapter count. Use 500 for longform release generation.")
    generate.add_argument("--title", default=None)
    generate.add_argument("--worldpack", default=DEFAULT_WORLD_PACK)
    derivative_group = generate.add_mutually_exclusive_group()
    derivative_group.add_argument("--allow-derivatives", dest="allow_derivatives", action="store_true", default=True)
    derivative_group.add_argument("--no-derivatives", dest="allow_derivatives", action="store_false")
    generate.add_argument("--derivative-of", default=None, help="Original platform work id when preparing a derivative bundle.")
    generate.add_argument("--derivative-license-id", default=None, help="Platform derivative license id for derivative bundles.")

    continue_cmd = sub.add_parser("continue", help="Append chapters to an existing local story workspace.")
    continue_cmd.add_argument("--source", required=True)
    continue_cmd.add_argument("--chapters", type=int, required=True, help="Additional chapters to generate.")

    validate = sub.add_parser("validate", help="Validate a .nosbook bundle.")
    validate.add_argument("bundle", nargs="?")
    validate.add_argument("--source", default=None, help="Validate a local story workspace instead of a .nosbook.")
    validate.add_argument("--profile", default="nosbook", choices=["nosbook", "local", "longform_500"])

    export = sub.add_parser("export", help="Export a source directory to .nosbook.")
    export.add_argument("--source-dir", "--source", dest="source_dir", required=True)
    export.add_argument("--out", required=True)

    preview = sub.add_parser("preview", help="Render a local source directory into a standalone HTML preview.")
    preview.add_argument("--source-dir", "--source", dest="source_dir", required=True)
    preview.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            source = init_project(
                Path(args.out),
                title=args.title,
                worldpack=args.worldpack,
                allow_derivatives=bool(args.allow_derivatives),
                derivative_of=args.derivative_of,
                derivative_license_id=args.derivative_license_id,
            )
            print(json.dumps({"status": "initialized", "source_dir": str(source), "platform_db_access": False}, ensure_ascii=False))
            return 0
        if args.command == "generate":
            if args.source:
                result = generate_project(Path(args.source), target_chapters=int(args.chapters or 3), title=args.title, worldpack=args.worldpack)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            if not args.out_dir:
                raise NosbookValidationError("nosbook_source_dir_missing", details={"hint": "Use --source or --out."})
            if args.chapters and int(args.chapters) > 3:
                source = init_project(
                    Path(args.out_dir),
                    title=args.title or "Local Agent Demo",
                    worldpack=args.worldpack,
                    allow_derivatives=bool(args.allow_derivatives),
                    derivative_of=args.derivative_of,
                    derivative_license_id=args.derivative_license_id,
                )
                result = generate_project(source, target_chapters=int(args.chapters), title=args.title or "Local Agent Demo", worldpack=args.worldpack)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            source = write_demo_source(
                Path(args.out_dir),
                title=args.title or "Local Agent Demo",
                allow_derivatives=bool(args.allow_derivatives),
                derivative_of=args.derivative_of,
                derivative_license_id=args.derivative_license_id,
            )
            print(json.dumps({"status": "generated", "source_dir": str(source), "platform_db_access": False}, ensure_ascii=False))
            return 0
        if args.command == "continue":
            result = continue_project(Path(args.source), additional_chapters=int(args.chapters))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "validate":
            if args.source:
                profile = "longform_500" if args.profile == "nosbook" else args.profile
                summary = validate_project(Path(args.source), profile=profile)
                print(json.dumps({"status": summary.status, **summary.to_dict()}, ensure_ascii=False, indent=2))
                return 0 if summary.ready else 2
            if not args.bundle:
                raise NosbookValidationError("nosbook_required_file_missing", details={"file": ".nosbook"})
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
