import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('privacy',ROOT/'scripts/privacy_check.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class PrivacyTests(unittest.TestCase):
    def test_private_conversation_detected_without_echoing_value(self):
        value=('https://'+'chatgpt.com/c/'+'12345678-1234-1234-1234-123456789abc').encode()
        with self.assertRaisesRegex(RuntimeError,'private conversation URL') as cm:p.check_files({'guide.md':value})
        self.assertNotIn(value.decode(),str(cm.exception))

    def test_named_home_path_is_private(self):
        self.assertIn('named local home path',p.findings('guide.md',('/'+'home/'+'private-user/project').encode()))

    def test_public_business_attribution_is_kept(self):
        self.assertEqual(p.findings('LICENSE-MIT',b'Copyright DreamLab Solutions <info@dreamlab.solutions>'),[])

    def test_reference_is_excluded(self):
        self.assertIn('private/reference file',p.findings('assets/reference/concept.png',b'image'))

    def test_png_metadata_is_rejected(self):
        def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+b'0000'
        data=b'\x89PNG\r\n\x1a\n'+chunk(b'tEXt',b'private metadata')+chunk(b'IEND',b'')
        self.assertIn('PNG metadata',p.findings('image.png',data))

    def test_paths_and_placeholder_fixture_ids_are_allowed(self):
        self.assertEqual(p.findings('guide.md',b'~/Projects/example /boot/limine.conf root=UUID=fake'),[])
