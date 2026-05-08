from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from narrativeos_agent.cli import main
from narrativeos_agent.nosbook import export_nosbook, validate_nosbook_file, write_demo_source


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


if __name__ == "__main__":
    unittest.main()
