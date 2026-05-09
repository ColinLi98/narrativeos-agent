from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from narrativeos_agent.cli import main
from narrativeos_agent.nosbook import NosbookValidationError, export_nosbook, validate_nosbook_file, write_demo_source


class AgentCliTests(unittest.TestCase):
    def test_generate_preview_export_validate(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "story.nosbook"
            preview = root / "preview.html"

            self.assertEqual(main(["generate", "--out", str(source), "--title", "Local Test"]), 0)
            self.assertEqual(main(["preview", "--source", str(source), "--out", str(preview)]), 0)
            self.assertEqual(main(["export", "--source", str(source), "--out", str(bundle)]), 0)
            self.assertEqual(main(["validate", str(bundle)]), 0)
            self.assertTrue(bundle.is_file())
            self.assertIn("Local Test", preview.read_text(encoding="utf-8"))
            validation = validate_nosbook_file(bundle)
            self.assertEqual(validation.cover_asset.file_name, "cover/cover.png")
            self.assertEqual(validation.cover_asset.content_type, "image/png")
            self.assertIn("cover/cover.png", validation.file_hashes)

    def test_export_rejects_engineering_leaks(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            write_demo_source(source, title="Leak Test")
            chapter_path = source / "chapters" / "0001.json"
            payload = json.loads(chapter_path.read_text(encoding="utf-8"))
            payload["body"] += "\ninternal kernel world_version_id benchmark trace"
            chapter_path.write_text(json.dumps(payload), encoding="utf-8")
            bundle = root / "leaky.nosbook"

            self.assertEqual(main(["export", "--source", str(source), "--out", str(bundle)]), 2)

    def test_exported_bundle_schema(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "story.nosbook"
            write_demo_source(source, title="Schema Test")
            result = export_nosbook(source, bundle)
            validation = validate_nosbook_file(bundle)

            self.assertEqual(result.public_summary()["schema_version"], "nosbook/v1")
            self.assertEqual(validation.manifest["title"], "Schema Test")
            self.assertEqual(len(validation.chapters), 3)
            self.assertTrue(validation.rights_attestation["allow_derivatives"])
            self.assertEqual(validation.cover_asset.content_type, "image/png")

    def test_missing_cover_is_rejected(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "story.nosbook"
            write_demo_source(source, title="Missing Cover")
            (source / "cover" / "cover.png").unlink()

            with self.assertRaises(NosbookValidationError) as raised:
                export_nosbook(source, bundle)
            self.assertEqual(raised.exception.code, "nosbook_cover_required")

    def test_unsupported_cover_is_rejected(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "story.nosbook"
            write_demo_source(source, title="Bad Cover")
            (source / "cover" / "cover.png").unlink()
            (source / "cover" / "cover.svg").write_text("<svg></svg>", encoding="utf-8")

            with self.assertRaises(NosbookValidationError) as raised:
                export_nosbook(source, bundle)
            self.assertEqual(raised.exception.code, "nosbook_cover_type_unsupported")

    def test_generate_derivative_metadata(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "derivative.nosbook"

            self.assertEqual(
                main(
                    [
                        "generate",
                        "--out",
                        str(source),
                        "--title",
                        "Derivative Test",
                        "--no-derivatives",
                        "--derivative-of",
                        "work_redacted",
                        "--derivative-license-id",
                        "license_redacted",
                    ]
                ),
                0,
            )
            result = export_nosbook(source, bundle)
            summary = result.public_summary()
            self.assertFalse(summary["rights"]["allow_derivatives"])
            self.assertTrue(summary["rights"]["is_derivative"])
            self.assertEqual(result.provenance["original_work_id"], "work_redacted")

    def test_zip_with_unsupported_cover_is_rejected(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            bundle = root / "manual.nosbook"
            write_demo_source(source, title="Manual Bad Cover")
            (source / "cover" / "cover.png").unlink()
            (source / "cover" / "cover.svg").write_text("<svg></svg>", encoding="utf-8")
            file_hashes: dict[str, str] = {}
            for path in source.rglob("*"):
                if path.is_file() and path.name != "content_hashes.json":
                    file_hashes[path.relative_to(source).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            (source / "content_hashes.json").write_text(
                json.dumps({"files": file_hashes}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            with ZipFile(bundle, "w") as zip_file:
                for path in source.rglob("*"):
                    if path.is_file():
                        zip_file.write(path, path.relative_to(source).as_posix())

            with self.assertRaises(NosbookValidationError) as raised:
                validate_nosbook_file(bundle)
            self.assertEqual(raised.exception.code, "nosbook_cover_type_unsupported")


if __name__ == "__main__":
    unittest.main()
