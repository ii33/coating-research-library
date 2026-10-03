import hashlib,json,tempfile,unittest
from pathlib import Path
from reader import verify,EXCLUDED
class IntegrityTests(unittest.TestCase):
    def fixture(self,root,archive=False):
        (root/'data').mkdir();(root/'demo.txt').write_text('tiny local reader')
        originals=[]
        if archive:
            p=root/'sources/originals/example.pdf';p.parent.mkdir(parents=True);p.write_bytes(b'%PDF-local-test')
            originals=[{'path':p.relative_to(root).as_posix(),'bytes':len(p.read_bytes()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]
        (root/'data/local_source_archive_manifest.json').write_text(json.dumps({'files':originals}))
        names=['data/local_source_archive_manifest.json','data/reader_allowlist.json','demo.txt']
        (root/'data/reader_allowlist.json').write_text(json.dumps({'paths':names}))
        entries=[{'path':n,'bytes':len((root/n).read_bytes()),'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in names]
        (root/'freeze_manifest.json').write_text(json.dumps({'excluded_paths':sorted(EXCLUDED),'files':entries,'local_only_originals':originals}))
    def test_valid_payload(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r);self.assertEqual(verify(r,False)['status'],'passed')
    def test_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r);(r/'demo.txt').write_text('changed')
            with self.assertRaises(ValueError):verify(r,False)
    def test_extra_file(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r);(r/'extra.txt').write_text('extra')
            with self.assertRaises(ValueError):verify(r,False)
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r);(r/'link').symlink_to(r/'demo.txt')
            with self.assertRaises(ValueError):verify(r,False)
    def test_unregistered_original(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r);(r/'paper.pdf').write_bytes(b'%PDF-test')
            with self.assertRaises(ValueError):verify(r,False)
    def test_local_archive_optional_for_reader(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);self.fixture(r,True);self.assertEqual(verify(r,False)['local_only_originals_present'],1)
            (r/'sources/originals/example.pdf').unlink()
            self.assertEqual(verify(r,False)['local_only_originals_present'],0)
