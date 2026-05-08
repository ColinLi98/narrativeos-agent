from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from zipfile import ZIP_DEFLATED, ZipFile


NOSBOOK_SCHEMA_VERSION = "nosbook/v1"
REQUIRED_FILES = {
    "manifest.json",
    "quality_report.json",
    "rights_attestation.json",
    "provenance.json",
    "content_hashes.json",
}
ENGINEERING_LEAK_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bkernel\b",
        r"\bbenchmark\b",
        r"\bworld_version_id\b",
        r"\bDATABASE_URL\b",
        r"\bbearer\s+[a-z0-9._-]+",
        r"\btraceback\b",
        r"\bsynthetic_min_pack\b",
    )
]


class NosbookValidationError(ValueError):
    def __init__(self, code: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(code)
        self.code = code
        self.details = details or {}


@dataclass(frozen=True)
class NosbookChapter:
    chapter_index: int
    title: str
    body: str
    payload: Dict[str, Any]
    file_name: str
    sha256: str


@dataclass(frozen=True)
class NosbookValidationResult:
    manifest: Dict[str, Any]
    quality_report: Dict[str, Any]
    rights_attestation: Dict[str, Any]
    provenance: Dict[str, Any]
    content_hashes: Dict[str, str]
    chapters: List[NosbookChapter]
    file_hashes: Dict[str, str]

    def public_summary(self) -> Dict[str, Any]:
        return {
            "schema_version": NOSBOOK_SCHEMA_VERSION,
            "title": str(self.manifest.get("title") or ""),
            "creator_display_name": str(self.manifest.get("creator_display_name") or ""),
            "genre": str(self.manifest.get("genre") or ""),
            "chapter_count": len(self.chapters),
            "word_count": sum(len(chapter.body.split()) for chapter in self.chapters),
            "quality_issue_counts": dict(self.quality_report.get("issue_counts") or {}),
            "rights": {
                "can_publish": bool(self.rights_attestation.get("can_publish")),
                "is_derivative": bool(self.rights_attestation.get("derivative_of")),
            },
        }


def _load_json(zip_file: ZipFile, file_name: str) -> Dict[str, Any]:
    try:
        payload = json.loads(zip_file.read(file_name).decode("utf-8"))
    except KeyError as exc:
        raise NosbookValidationError("nosbook_required_file_missing", details={"file": file_name}) from exc
    except json.JSONDecodeError as exc:
        raise NosbookValidationError("nosbook_json_invalid", details={"file": file_name}) from exc
    if not isinstance(payload, dict):
        raise NosbookValidationError("nosbook_json_object_required", details={"file": file_name})
    return payload


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _scan_engineering_leaks(text: str) -> List[str]:
    hits: List[str] = []
    for pattern in ENGINEERING_LEAK_PATTERNS:
        if pattern.search(text or ""):
            hits.append(pattern.pattern)
    return hits


def _chapter_files(names: Iterable[str]) -> List[str]:
    chapters = [name for name in names if name.startswith("chapters/") and name.endswith(".json") and not name.endswith("/")]
    return sorted(chapters)


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    if str(manifest.get("schema_version") or "") not in {"", NOSBOOK_SCHEMA_VERSION}:
        raise NosbookValidationError("nosbook_schema_version_unsupported")
    if not str(manifest.get("title") or "").strip():
        raise NosbookValidationError("nosbook_title_required")
    if "price_credits" in manifest and float(manifest.get("price_credits") or 0) < 0:
        raise NosbookValidationError("nosbook_price_invalid")


def _validate_rights(rights: Mapping[str, Any]) -> None:
    if not bool(rights.get("can_publish")):
        raise NosbookValidationError("nosbook_rights_publish_attestation_required")
    if not str(rights.get("rights_holder") or "").strip():
        raise NosbookValidationError("nosbook_rights_holder_required")


def validate_nosbook_bytes(raw: bytes) -> NosbookValidationResult:
    with io.BytesIO(raw) as temp:
        with ZipFile(temp) as zip_file:
            names = set(zip_file.namelist())
            missing = sorted(REQUIRED_FILES - names)
            if missing:
                raise NosbookValidationError("nosbook_required_files_missing", details={"missing": missing})
            manifest = _load_json(zip_file, "manifest.json")
            quality_report = _load_json(zip_file, "quality_report.json")
            rights = _load_json(zip_file, "rights_attestation.json")
            provenance = _load_json(zip_file, "provenance.json")
            content_hashes = _load_json(zip_file, "content_hashes.json")
            hashes_payload = dict(content_hashes.get("files") or content_hashes)
            _validate_manifest(manifest)
            _validate_rights(rights)
            chapter_names = _chapter_files(names)
            if not chapter_names:
                raise NosbookValidationError("nosbook_chapters_required")
            chapters: List[NosbookChapter] = []
            file_hashes: Dict[str, str] = {}
            for file_name in sorted(names):
                if file_name.endswith("/"):
                    continue
                raw_file = zip_file.read(file_name)
                file_hashes[file_name] = _sha256(raw_file)
                expected_hash = hashes_payload.get(file_name)
                if expected_hash and str(expected_hash) != file_hashes[file_name]:
                    raise NosbookValidationError("nosbook_hash_mismatch", details={"file": file_name})
            for file_name in chapter_names:
                chapter = _load_json(zip_file, file_name)
                body = str(chapter.get("body") or "").strip()
                title = str(chapter.get("title") or "").strip() or f"Chapter {len(chapters) + 1}"
                chapter_index = int(chapter.get("chapter_index") or len(chapters) + 1)
                if chapter_index <= 0:
                    raise NosbookValidationError("nosbook_chapter_index_invalid", details={"file": file_name})
                if not body:
                    raise NosbookValidationError("nosbook_chapter_body_required", details={"file": file_name})
                leak_hits = _scan_engineering_leaks("\n".join([title, body, json.dumps(chapter.get("choices") or [], ensure_ascii=False)]))
                if leak_hits:
                    raise NosbookValidationError("nosbook_engineering_leak_detected", details={"file": file_name, "patterns": leak_hits})
                chapters.append(
                    NosbookChapter(
                        chapter_index=chapter_index,
                        title=title,
                        body=body,
                        payload=chapter,
                        file_name=file_name,
                        sha256=file_hashes[file_name],
                    )
                )
            declared_count = int(manifest.get("chapter_count") or len(chapters))
            if declared_count != len(chapters):
                raise NosbookValidationError(
                    "nosbook_chapter_count_mismatch",
                    details={"declared": declared_count, "actual": len(chapters)},
                )
            return NosbookValidationResult(
                manifest=dict(manifest),
                quality_report=dict(quality_report),
                rights_attestation=dict(rights),
                provenance=dict(provenance),
                content_hashes={str(k): str(v) for k, v in hashes_payload.items()},
                chapters=chapters,
                file_hashes=file_hashes,
            )


def validate_nosbook_file(path: Path | str) -> NosbookValidationResult:
    return validate_nosbook_bytes(Path(path).read_bytes())


def _iter_bundle_files(source_dir: Path) -> List[Path]:
    files = [
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.name != "content_hashes.json" and "__MACOSX" not in path.parts
    ]
    return sorted(files)


def export_nosbook(source_dir: Path | str, output_path: Path | str) -> NosbookValidationResult:
    source = Path(source_dir)
    output = Path(output_path)
    if not source.is_dir():
        raise NosbookValidationError("nosbook_source_dir_missing")
    file_hashes: Dict[str, str] = {}
    for path in _iter_bundle_files(source):
        rel = path.relative_to(source).as_posix()
        file_hashes[rel] = _sha256(path.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as zip_file:
        for path in _iter_bundle_files(source):
            zip_file.write(path, path.relative_to(source).as_posix())
        zip_file.writestr("content_hashes.json", json.dumps({"files": file_hashes}, ensure_ascii=False, indent=2))
    return validate_nosbook_file(output)


def write_demo_source(source_dir: Path | str, *, title: str = "Local Agent Demo") -> Path:
    source = Path(source_dir)
    (source / "chapters").mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": NOSBOOK_SCHEMA_VERSION,
        "title": title,
        "creator_display_name": "Local Creator",
        "genre": "original",
        "chapter_count": 3,
        "price_credits": 9,
    }
    chapters = [
        {
            "chapter_index": index,
            "title": f"Chapter {index}",
            "body": f"The room changed after choice {index}. A cup rang softly on the table, and the character made one concrete decision before the scene turned.",
            "choices": [{"id": f"c{index}", "text": "Continue the investigation"}],
        }
        for index in range(1, 4)
    ]
    files = {
        "manifest.json": manifest,
        "quality_report.json": {"issue_counts": {"Q03": 0, "Q04": 0, "Q05": 0, "Q09": 0}, "status": "local_agent_sample"},
        "rights_attestation.json": {"rights_holder": "Local Creator", "can_publish": True, "ai_assisted": True},
        "provenance.json": {"generator": "narrativeos-agent", "renderer_provider": "local"},
    }
    for file_name, payload in files.items():
        (source / file_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for chapter in chapters:
        (source / "chapters" / f"{chapter['chapter_index']:04d}.json").write_text(
            json.dumps(chapter, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return source
