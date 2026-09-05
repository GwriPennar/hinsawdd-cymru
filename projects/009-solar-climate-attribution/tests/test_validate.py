"""Integrity tests only: these do not verify scientific claims."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("project009_validate", ROOT / "validate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestRegisters(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in list(ROOT.glob("*.json")) + list(ROOT.glob("*.md")):
            shutil.copy2(path, self.root / path.name)

    def change(self, name, transform):
        path = self.root / name
        obj = json.loads(path.read_text(encoding="utf-8"))
        transform(obj)
        path.write_text(json.dumps(obj), encoding="utf-8")

    def test_valid_baseline(self):
        result = module.validate(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["sources"], 19)
        self.assertEqual(result["claims"], 10)
        self.assertEqual(result["acquired_datasets"], 0)

    def test_duplicate_source(self):
        self.change("sources.json", lambda o: o["sources"].append(o["sources"][0].copy()))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_unknown_claim_reference(self):
        self.change("claims.json", lambda o: o["claims"][0].update(sources=["S99"]))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_bad_url(self):
        self.change("sources.json", lambda o: o["sources"][0].update(url="not-a-url"))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_missing_locator(self):
        self.change("sources.json", lambda o: o["sources"][0].update(locator=""))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_invalid_assessment(self):
        self.change("claims.json", lambda o: o["claims"][0].update(assessment="proved_forever"))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_unrecorded_download_rejected(self):
        self.change("datasets.json", lambda o: o["datasets"][0].update(status="acquired"))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_different_review_date(self):
        self.change("claims.json", lambda o: o.update(review_date="2026-09-04"))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_unknown_markdown_citation(self):
        (self.root / "extra.md").write_text("Unsupported citation [S99].", encoding="utf-8")
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_duplicate_doi(self):
        self.change("sources.json", lambda o: o["sources"][0].update(doi=o["sources"][1]["doi"]))
        with self.assertRaises(ValueError):
            module.validate(self.root)

    def test_catalogue_deterministic(self):
        self.assertEqual(module.catalogue(self.root), module.catalogue(self.root))
        self.assertIn("S05", module.catalogue(self.root))
        self.assertIn("abstract_only", module.catalogue(self.root))

    def test_supportive_literature_retained(self):
        obj = json.loads((self.root / "sources.json").read_text(encoding="utf-8"))
        roles = {s["role"] for s in obj["sources"]}
        self.assertIn("supports_solar_origin", roles)
        self.assertIn("supports_solar_influence", roles)
        self.assertIn("challenges_solar_origin", roles)


if __name__ == "__main__":
    unittest.main()
