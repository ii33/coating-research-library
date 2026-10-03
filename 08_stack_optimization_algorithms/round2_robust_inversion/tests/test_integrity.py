import json,shutil,tempfile,unittest
from pathlib import Path
from reader import verify,payload_paths
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'freeze_manifest.json').exists(),'requires final manifest')
class IntegrityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='t08-integrity-');self.root=Path(self.tmp.name)
  for name in payload_paths(ROOT)+['freeze_manifest.json']:
   target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 def tearDown(self):self.tmp.cleanup()
 def test_exact_payload_no_originals(self):
  self.assertEqual(verify(self.root)['status'],'passed');self.assertFalse((self.root/'sources/originals').exists())
 def test_changed_bytes_rejected(self):
  (self.root/'README.md').write_text('modified')
  with self.assertRaises(ValueError):verify(self.root)
 def test_missing_rejected(self):
  (self.root/'README.md').unlink()
  with self.assertRaises(ValueError):verify(self.root)
 def test_extra_rejected(self):
  (self.root/'unexpected.txt').write_text('extra')
  with self.assertRaises(ValueError):verify(self.root)
if __name__=='__main__':unittest.main()
