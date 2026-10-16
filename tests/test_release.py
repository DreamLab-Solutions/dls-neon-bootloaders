import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release', ROOT/'scripts/release.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReleaseTests(unittest.TestCase):
    def test_offline_links_resolve_from_each_document(self):
        r.check_links({'README.md': b'[Guide](docs/INSTALL.md)',
                       'docs/INSTALL.md': b'![Menu](screenshots/menu.png) [Home](../README.md)',
                       'docs/screenshots/menu.png': b'png'})

    def test_missing_nested_image_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Broken offline link'):
            r.check_links({'docs/it/README.md': b'![Menu](../screenshots/missing.png)'})

    def test_external_and_anchor_links_are_not_treated_as_files(self):
        r.check_links({'README.md': b'[Remote](https://example.org/a) [Section](#install)'})

    def fixture(self, extra=None, changed=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name)/'dls-neon-setup-0.5.1.tar.gz'
        files = {name: b'license' for name in ('LICENSE', 'LICENSE-MIT', 'ARTWORK-LICENSE.md')}
        files.update({'README.md': b'Guide', 'VERSION': b'0.5.1\n'})
        manifest = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
        files['manifest.json'] = json.dumps(manifest).encode()
        if changed:
            files['README.md'] = b'corrupted'
        if extra:
            files.update(extra)
        with tarfile.open(path, 'w:gz') as tar:
            for name, data in files.items():
                info = tarfile.TarInfo(path.name.removesuffix('.tar.gz')+'/'+name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        return path

    def test_complete_archive_is_accepted(self):
        r.validate_tar(self.fixture(), '0.5.1')

    def test_corrupted_combined_archive_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Manifest mismatch'):
            r.validate_tar(self.fixture(changed=True), '0.5.1')

    def test_unmanifested_file_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Incomplete combined'):
            r.validate_tar(self.fixture({'untracked.txt': b'extra'}), '0.5.1')

    def test_bootloader_binary_is_excluded(self):
        with self.assertRaisesRegex(RuntimeError, 'Development/private'):
            r.validate_tar(self.fixture({'EFI/test.efi': b'not for runtime'}), '0.5.1')

    def test_reference_material_is_excluded(self):
        with self.assertRaisesRegex(RuntimeError, 'Development/private'):
            r.validate_tar(self.fixture({'assets/reference/concept.png': b'private'}), '0.5.1')

    def test_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Unsafe package'):
            r.validate_tar(self.fixture({'../escape': b'unsafe'}), '0.5.1')

    def test_release_version_must_match_package(self):
        with self.assertRaisesRegex(RuntimeError, 'wrong version'):
            r.validate_tar(self.fixture(), '0.5.2')


if __name__ == '__main__':
    unittest.main()
