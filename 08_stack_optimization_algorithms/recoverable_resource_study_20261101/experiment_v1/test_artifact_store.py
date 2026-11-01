import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import artifact_store as store


class ArtifactStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_idempotent_and_conflict_preserves_original(self):
        target = store.write_immutable_json(self.root, "artifacts/x.json", {"b": 2, "a": 1})
        original = target.read_bytes()
        store.write_immutable_json(self.root, "artifacts/x.json", {"a": 1, "b": 2})
        self.assertEqual(original, b'{"a":1,"b":2}\n')
        with self.assertRaises(FileExistsError):
            store.write_immutable_json(self.root, "artifacts/x.json", {"a": 4})
        self.assertEqual(target.read_bytes(), original)

    def test_nonfinite_values_rejected_before_creating_file(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                store.write_immutable_json(self.root, "bad.json", {"value": value})
        self.assertFalse((self.root / "bad.json").exists())

    def test_path_escape_and_symlinks_rejected(self):
        for path in ("../escape", "/absolute", "x/../escape", "x//y", "./x", "C:/escape", "x\\y"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                store.write_immutable_json(self.root, path, {})
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / "link").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(ValueError):
                store.write_immutable_json(self.root, "link/escape", {})
            self.assertFalse((Path(outside) / "escape").exists())

    def test_interrupted_write_cleans_temp_and_does_not_publish(self):
        with mock.patch.object(store.os, "fsync", side_effect=OSError("injected failure")):
            with self.assertRaisesRegex(OSError, "injected failure"):
                store.write_immutable_json(self.root, "partial.json", {"x": 1})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_replace_failure_cleans_temp_and_preserves_previous_manifest(self):
        (self.root / "data").mkdir()
        store.write_manifest(self.root, "data")
        before = (self.root / "manifest.json").read_bytes()
        with mock.patch.object(store.os, "replace", side_effect=OSError("injected replace failure")):
            with self.assertRaisesRegex(OSError, "injected replace failure"):
                store.write_manifest(self.root, "data")
        self.assertEqual((self.root / "manifest.json").read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["data", "manifest.json"])

    def test_manifest_inventory_size_hash_exclusions_and_tampering(self):
        store.write_immutable_bytes(self.root, "data/nested/a.bin", b"abc")
        for rel in ("data/scratch.tmp", "data/local.log", "data/__pycache__/x.pyc", "data/logs/debug.json", "data/tmp/work.json", "data/rotated.log.1"):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"not public")
        result = store.write_manifest(self.root, "data", "data/manifest.json")
        self.assertEqual(result["files"], [{"path": "data/nested/a.bin", "bytes": 3,
                                           "sha256": hashlib.sha256(b"abc").hexdigest()}])
        self.assertTrue(store.verify_manifest(self.root, "data/manifest.json"))
        (self.root / "data/nested/a.bin").write_bytes(b"xyz")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            store.verify_manifest(self.root, "data/manifest.json")
        (self.root / "data/nested/a.bin").write_bytes(b"abc!")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            store.verify_manifest(self.root, "data/manifest.json")
        (self.root / "data/nested/a.bin").write_bytes(b"abc")
        (self.root / "data/new.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            store.verify_manifest(self.root, "data/manifest.json")

    def test_root_inventory(self):
        store.write_immutable_bytes(self.root, "a.json", b"{}")
        manifest = store.write_manifest(self.root, ".")
        self.assertEqual([e["path"] for e in manifest["files"]], ["a.json"])
        self.assertTrue(store.verify_manifest(self.root))

    def test_manifest_rejects_traversal(self):
        (self.root / "manifest.json").write_text(json.dumps({"version": 1, "directory": "../outside", "files": []}))
        with self.assertRaises(ValueError):
            store.verify_manifest(self.root)


if __name__ == "__main__":
    unittest.main()
