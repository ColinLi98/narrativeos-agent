from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .nosbook import DEFAULT_COVER_PNG, NOSBOOK_SCHEMA_VERSION, NosbookValidationError


AGENT_VERSION = "1.0.1"
LONGFORM_PROFILE = "longform_500"
DEFAULT_WORLD_PACK = "urban_mystery_lotus_lane"
SUPPORTED_WORLDPACKS = {
    "urban_mystery_lotus_lane": {
        "genre": "urban_mystery",
        "premise": "A sealed harbor district hides a debt ledger that changes hands every night.",
        "lead": "Mara",
        "counterpart": "Ren",
        "setting": "Lotus Lane",
    },
    "xianxia_forgotten_vow": {
        "genre": "xianxia",
        "premise": "A broken vow binds a wandering cultivator to a mountain archive.",
        "lead": "Yun",
        "counterpart": "Lio",
        "setting": "Cloudroot Pass",
    },
    "jade_court_exam": {
        "genre": "court_exam",
        "premise": "A scholar enters the palace exam while factions trade answers for silence.",
        "lead": "Lin",
        "counterpart": "Shao",
        "setting": "Jade Court",
    },
    "jade_court_romance": {
        "genre": "court_romance",
        "premise": "Two court rivals protect a forbidden archive while pretending not to care.",
        "lead": "Mei",
        "counterpart": "An",
        "setting": "Jade Court",
    },
}
ENGINEERING_LEAK_TERMS = (
    "kernel",
    "benchmark",
    "world_version_id",
    "database_url",
    "traceback",
    "synthetic_min_pack",
    "bearer ",
)
BROKEN_SLOT_PATTERNS = (
    re.compile(r"[，,、]\s*[，,、]"),
    re.compile(r"\bNone\b|\bnull\b|\{\{|\}\}|\[[A-Z_]+]"),
)
OBJECTS = [
    "brass key",
    "rain map",
    "ink ledger",
    "cracked cup",
    "blue lantern",
    "sealed letter",
    "salt-stained coat",
    "ivory token",
    "paper compass",
    "silver bell",
    "folded warrant",
    "green ribbon",
]
SOUNDS = [
    "a shutter knocked once",
    "rain clicked against the sill",
    "a cart wheel scraped stone",
    "a bell trembled behind the wall",
    "water hissed in the gutter",
    "paper rasped under a thumb",
    "footsteps paused beyond the door",
    "a match flared and died",
]
ACTIONS = [
    "turned the token over",
    "moved the lamp away from the window",
    "marked the map with a wet fingertip",
    "locked the drawer before answering",
    "pushed the ledger beneath a loose board",
    "lifted the cup and found the note beneath it",
    "stepped into the narrow passage",
    "tore one corner from the letter",
]
ANCHORS = [
    "promise",
    "receipt",
    "witness",
    "threshold",
    "signal",
    "debt",
    "choice",
    "return",
    "bargain",
    "silence",
]
CHOICES = [
    "Follow the new evidence before anyone else notices.",
    "Press the witness for one concrete detail.",
    "Protect the fragile alliance for one more scene.",
    "Trade a small secret to uncover the larger debt.",
    "Return to the place where the clue first changed meaning.",
    "Refuse the easy answer and test the contradiction.",
    "Move quietly, but leave one sign for an ally.",
    "Confront the person who benefits from the delay.",
    "Hide the proof, then watch who reaches for it.",
    "Ask the question that makes retreat impossible.",
]


@dataclass(frozen=True)
class ValidationSummary:
    status: str
    ready: bool
    profile: str
    completed_chapters: int
    target_chapters: int
    hard_fail_count: int
    issue_counts: Dict[str, int]
    blockers: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "narrativeos_agent_quality/v1",
            "status": self.status,
            "ready": self.ready,
            "profile": self.profile,
            "completed_chapters": self.completed_chapters,
            "target_chapters": self.target_chapters,
            "hard_fail_count": self.hard_fail_count,
            "issue_counts": dict(self.issue_counts),
            "blockers": list(self.blockers),
            "generated_at": _now(),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _chapter_paths(source: Path) -> List[Path]:
    return sorted((source / "chapters").glob("*.json"))


def _load_chapters(source: Path) -> List[Dict[str, Any]]:
    chapters: List[Dict[str, Any]] = []
    for path in _chapter_paths(source):
        payload = _read_json(path)
        if payload:
            chapters.append(payload)
    return chapters


def _worldpack(worldpack_id: str) -> Dict[str, str]:
    return dict(SUPPORTED_WORLDPACKS.get(worldpack_id) or SUPPORTED_WORLDPACKS[DEFAULT_WORLD_PACK])


def init_project(
    source_dir: Path | str,
    *,
    title: str,
    worldpack: str = DEFAULT_WORLD_PACK,
    allow_derivatives: bool = True,
    derivative_of: Optional[str] = None,
    derivative_license_id: Optional[str] = None,
) -> Path:
    source = Path(source_dir)
    world = _worldpack(worldpack)
    (source / "chapters").mkdir(parents=True, exist_ok=True)
    (source / "quality").mkdir(parents=True, exist_ok=True)
    (source / "state").mkdir(parents=True, exist_ok=True)
    (source / "cover").mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": NOSBOOK_SCHEMA_VERSION,
        "title": title,
        "creator_display_name": "Local Creator",
        "genre": world["genre"],
        "worldpack": worldpack if worldpack in SUPPORTED_WORLDPACKS else DEFAULT_WORLD_PACK,
        "chapter_count": len(_chapter_paths(source)),
        "price_credits": 9,
        "agent_version": AGENT_VERSION,
        "longform_profile": LONGFORM_PROFILE,
    }
    rights = {
        "rights_holder": "Local Creator",
        "can_publish": True,
        "ai_assisted": True,
        "allow_derivatives": bool(allow_derivatives),
        "derivative_terms": "Derivative works require a platform license. Sales split: derivative creator 50%, original creator 20%, platform 30%.",
        **({"derivative_of": derivative_of} if derivative_of else {}),
        **({"derivative_license_id": derivative_license_id} if derivative_license_id else {}),
    }
    provenance = {
        "generator": "narrativeos-agent",
        "agent_version": AGENT_VERSION,
        "renderer_provider": "local",
        "platform_db_access": False,
        "worldpack": manifest["worldpack"],
        **({"original_work_id": derivative_of} if derivative_of else {}),
        **({"derivative_license_id": derivative_license_id} if derivative_license_id else {}),
    }
    _write_json(source / "project.json", {"title": title, "worldpack": manifest["worldpack"], "created_at": _now()})
    _write_json(source / "manifest.json", manifest)
    _write_json(source / "rights_attestation.json", rights)
    _write_json(source / "provenance.json", provenance)
    _write_json(
        source / "state" / "checkpoint.json",
        {
            "schema_version": "narrativeos_agent_checkpoint/v1",
            "last_completed_chapter": len(_chapter_paths(source)),
            "target_chapters": 0,
            "platform_db_access": False,
            "updated_at": _now(),
        },
    )
    _write_quality_report(source, _validate_source(source, target_chapters=max(1, len(_chapter_paths(source))), profile="local"))
    if not (source / "cover" / "cover.png").exists():
        (source / "cover" / "cover.png").write_bytes(DEFAULT_COVER_PNG)
    return source


def _render_chapter(index: int, *, title: str, worldpack: str) -> Dict[str, Any]:
    world = _worldpack(worldpack)
    obj = OBJECTS[(index * 5) % len(OBJECTS)]
    obj2 = OBJECTS[(index * 7 + 3) % len(OBJECTS)]
    sound = SOUNDS[(index * 3) % len(SOUNDS)]
    action = ACTIONS[(index * 4) % len(ACTIONS)]
    anchor = ANCHORS[index % len(ANCHORS)]
    lead = world["lead"]
    counterpart = world["counterpart"]
    setting = world["setting"]
    phase = ((index - 1) % 50) + 1
    arc = ((index - 1) // 50) + 1
    scene_goal = [
        "find proof",
        "protect a witness",
        "test a false confession",
        "move an ally through danger",
        "make the hidden bargain visible",
    ][index % 5]
    body = "\n\n".join(
        [
            f"Chapter {index} opened in {setting} with {lead} holding the {obj}. {sound}, and the room answered with a small change: the shadow near the door showed fresh mud instead of dust. {lead} {action}, then counted three breaths before speaking.",
            f"\"You saw the {anchor} before I did,\" {lead} said. {counterpart} touched the {obj2} and shook their head. \"I saw who moved it. That is worse.\" The answer gave the scene a shape: {scene_goal}, but do it before the street learned their names.",
            f"They crossed the room one object at a time. The {obj} stayed wrapped in cloth, the {obj2} stayed visible, and every step changed what the previous clue meant. Outside, {sound}; inside, {counterpart} blocked the easy exit and made {lead} choose a narrower path.",
            f"In arc {arc}, scene {phase}, the decision became physical instead of abstract. {lead} left one sign for an ally, hid one sign from an enemy, and carried the remaining question forward without closing the larger case.",
        ]
    )
    choice_start = index % len(CHOICES)
    choices = [
        {"id": f"c{index}_a", "text": CHOICES[choice_start]},
        {"id": f"c{index}_b", "text": CHOICES[(choice_start + 3) % len(CHOICES)]},
    ]
    return {
        "chapter_index": index,
        "title": f"Chapter {index}",
        "body": body,
        "choices": choices,
        "metadata": {
            "arc_index": arc,
            "scene_index": phase,
            "renderer_provider": "local",
            "quality_status": "passed",
        },
    }


def generate_project(source_dir: Path | str, *, target_chapters: int, title: Optional[str] = None, worldpack: Optional[str] = None) -> Dict[str, Any]:
    source = Path(source_dir)
    if not (source / "manifest.json").exists():
        init_project(source, title=title or "Local Longform Novel", worldpack=worldpack or DEFAULT_WORLD_PACK)
    manifest = _read_json(source / "manifest.json")
    resolved_title = str(title or manifest.get("title") or "Local Longform Novel")
    resolved_worldpack = str(worldpack or manifest.get("worldpack") or DEFAULT_WORLD_PACK)
    existing = _load_chapters(source)
    completed = max([int(item.get("chapter_index") or 0) for item in existing] or [0])
    target = max(int(target_chapters), completed)
    for index in range(completed + 1, target + 1):
        chapter = _render_chapter(index, title=resolved_title, worldpack=resolved_worldpack)
        issues = _chapter_issues(chapter)
        if issues:
            raise NosbookValidationError("longform_chapter_quality_failed", details={"chapter_index": index, "issues": issues})
        _write_json(source / "chapters" / f"{index:04d}.json", chapter)
        _write_json(
            source / "state" / "checkpoint.json",
            {
                "schema_version": "narrativeos_agent_checkpoint/v1",
                "last_completed_chapter": index,
                "target_chapters": target,
                "platform_db_access": False,
                "updated_at": _now(),
            },
        )
    _refresh_manifest(source, target_chapters=target, title=resolved_title, worldpack=resolved_worldpack)
    summary = _validate_source(source, target_chapters=target, profile=LONGFORM_PROFILE if target >= 500 else "local_longform")
    _write_quality_report(source, summary)
    return {
        "status": "generated",
        "source_dir": str(source),
        "completed_chapters": summary.completed_chapters,
        "target_chapters": target,
        "quality_ready": summary.ready,
        "platform_db_access": False,
    }


def continue_project(source_dir: Path | str, *, additional_chapters: int) -> Dict[str, Any]:
    source = Path(source_dir)
    if not (source / "manifest.json").exists():
        raise NosbookValidationError("nosbook_source_dir_missing")
    completed = len(_chapter_paths(source))
    return generate_project(source, target_chapters=completed + int(additional_chapters))


def validate_project(source_dir: Path | str, *, profile: str = LONGFORM_PROFILE) -> ValidationSummary:
    source = Path(source_dir)
    if not source.is_dir():
        raise NosbookValidationError("nosbook_source_dir_missing")
    target = 500 if profile == LONGFORM_PROFILE else max(1, len(_chapter_paths(source)))
    summary = _validate_source(source, target_chapters=target, profile=profile)
    _write_quality_report(source, summary)
    return summary


def _refresh_manifest(source: Path, *, target_chapters: int, title: str, worldpack: str) -> None:
    manifest = _read_json(source / "manifest.json")
    manifest.update(
        {
            "schema_version": NOSBOOK_SCHEMA_VERSION,
            "title": title,
            "worldpack": worldpack,
            "chapter_count": len(_chapter_paths(source)),
            "agent_version": AGENT_VERSION,
            "longform_profile": LONGFORM_PROFILE if target_chapters >= 500 else "local_longform",
        }
    )
    _write_json(source / "manifest.json", manifest)


def _chapter_issues(chapter: Dict[str, Any]) -> List[str]:
    text = "\n".join(
        [
            str(chapter.get("title") or ""),
            str(chapter.get("body") or ""),
            json.dumps(chapter.get("choices") or [], ensure_ascii=False),
        ]
    )
    lowered = text.lower()
    issues: List[str] = []
    if not str(chapter.get("body") or "").strip():
        issues.append("Q05_empty_chapter")
    if any(term in lowered for term in ENGINEERING_LEAK_TERMS):
        issues.append("Q01_engineering_leak")
    if any(pattern.search(text) for pattern in BROKEN_SLOT_PATTERNS):
        issues.append("Q01_broken_slot")
    detail_hits = sum(1 for item in OBJECTS + SOUNDS + ACTIONS if item.lower() in lowered)
    if detail_hits < 3:
        issues.append("Q05_detail_density_floor")
    if any(phrase in lowered for phrase in ("the end", "case closed", "finally solved")):
        issues.append("Q09_premature_ending")
    return issues


def _validate_source(source: Path, *, target_chapters: int, profile: str) -> ValidationSummary:
    chapters = _load_chapters(source)
    blockers: List[Dict[str, Any]] = []
    issue_counts: Counter[str] = Counter({"Q03": 0, "Q04": 0, "Q05": 0, "Q09": 0, "Q01": 0})
    seen_indexes: set[int] = set()
    choice_counter: Counter[str] = Counter()
    anchor_counter: Counter[str] = Counter()
    body_hashes: Counter[str] = Counter()
    for chapter in chapters:
        index = int(chapter.get("chapter_index") or 0)
        if index <= 0 or index in seen_indexes:
            issue_counts["Q07"] += 1
            blockers.append({"code": "chapter_sequence_invalid", "chapter_index": index})
        seen_indexes.add(index)
        issues = _chapter_issues(chapter)
        for issue in issues:
            issue_counts[issue.split("_", 1)[0]] += 1
            blockers.append({"code": issue, "chapter_index": index})
        for choice in list(chapter.get("choices") or []):
            choice_counter[str(choice.get("text") or "").strip()] += 1
        lowered_body = str(chapter.get("body") or "").lower()
        for anchor in ANCHORS:
            if anchor in lowered_body:
                anchor_counter[anchor] += 1
        body_hashes[str(chapter.get("body") or "").strip()] += 1
    completed = len(chapters)
    if completed < target_chapters:
        blockers.append({"code": "chapter_target_incomplete", "completed": completed, "target": target_chapters})
    if profile == LONGFORM_PROFILE and completed >= 1:
        top_choice_count = max(choice_counter.values() or [0])
        if top_choice_count / max(1, completed) > 0.30:
            issue_counts["Q08"] += 1
            blockers.append({"code": "choice_repetition_budget_exceeded", "top_choice_count": top_choice_count})
        top_anchor_count = max(anchor_counter.values() or [0])
        if top_anchor_count / max(1, completed) > 0.45:
            issue_counts["Q03"] += 1
            blockers.append({"code": "anchor_repetition_budget_exceeded", "top_anchor_count": top_anchor_count})
        repeated_bodies = sum(count - 1 for count in body_hashes.values() if count > 1)
        if repeated_bodies:
            issue_counts["Q03"] += repeated_bodies
            blockers.append({"code": "duplicate_chapter_body", "count": repeated_bodies})
    hard_fail_count = len(blockers)
    ready = hard_fail_count == 0
    return ValidationSummary(
        status="passed" if ready else "blocked",
        ready=ready,
        profile=profile,
        completed_chapters=completed,
        target_chapters=target_chapters,
        hard_fail_count=hard_fail_count,
        issue_counts={key: int(value) for key, value in sorted(issue_counts.items())},
        blockers=blockers,
    )


def _write_quality_report(source: Path, summary: ValidationSummary) -> None:
    payload = {
        "schema_version": "narrativeos_agent_quality_report/v1",
        "status": summary.status,
        "profile": summary.profile,
        "issue_counts": summary.issue_counts,
        "longform_500_summary": summary.to_dict(),
        "platform_db_access": False,
        "generated_at": _now(),
    }
    _write_json(source / "quality_report.json", payload)
    _write_json(source / "quality" / "longform_500_summary.json", summary.to_dict())
