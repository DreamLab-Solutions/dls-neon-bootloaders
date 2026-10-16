import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    import tkinter as tk
except ImportError:
    tk = None

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('setup', ROOT/'scripts/dls_setup.py')
s = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(s)


class Fixture:

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name)
        self.catalog={}
        for name in ['dls-neon-setup','grub_manager.py','limine_manager.py']:
            (self.base/name).write_text('# trusted test fixture\n')
        for slug in s.THEMES:
            item={'title':slug,'preview':{}}
            for backend in ('grub','limine'):
                folder=self.base/backend/'themes'/slug;folder.mkdir(parents=True)
                (folder/'background.png').write_bytes(b'background')
                (folder/'manifest.json').write_text(json.dumps({'background.png':s.sha(b'background')}))
                item[backend]=str(folder.relative_to(self.base))
                preview=self.base/'previews'/backend/(slug+'.png');preview.parent.mkdir(parents=True,exist_ok=True)
                preview.write_bytes((ROOT/'docs/screenshots/limine-synaptic-cosmos-1080p.png').read_bytes())
                item['preview'][backend]=str(preview.relative_to(self.base))
            self.catalog[slug]=item
        (self.base/'catalog.json').write_text(json.dumps(self.catalog))
        self.rehash()

    def rehash(self):
        (self.base/'manifest.json').write_text(json.dumps({str(p.relative_to(self.base)):s.sha(p.read_bytes())
             for p in self.base.rglob('*') if p.is_file() and p != self.base/'manifest.json'}))

    def tearDown(self): self.temp.cleanup()



class Bundle(Fixture, unittest.TestCase):
    def test_catalog_and_all_previews_verified(self):
        self.assertEqual(set(s.verify_bundle(self.base)),set(s.THEMES))

    def test_modified_preview_rejected(self):
        (self.base/'previews/grub/synaptic-cosmos.png').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'modificato'):s.verify_bundle(self.base)

    def test_modified_manager_rejected(self):
        (self.base/'grub_manager.py').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'modificato'):s.verify_bundle(self.base)

    def test_missing_preview_coverage_rejected(self):
        p=self.base/'manifest.json';m=json.loads(p.read_text());m.pop('previews/grub/synaptic-cosmos.png');p.write_text(json.dumps(m))
        with self.assertRaisesRegex(RuntimeError,'non verificabile'):s.verify_bundle(self.base)

    def test_catalog_cannot_redirect_source(self):
        self.catalog['synaptic-cosmos']['grub']='../../outside'
        (self.base/'catalog.json').write_text(json.dumps(self.catalog));self.rehash()
        with self.assertRaisesRegex(RuntimeError,'inatteso'):s.verify_bundle(self.base)

    def test_manifest_cannot_read_outside(self):
        p=self.base/'manifest.json';m=json.loads(p.read_text());m['../outside']='x';p.write_text(json.dumps(m))
        with self.assertRaisesRegex(RuntimeError,'Percorso'):s.verify_bundle(self.base)

    def test_symlink_rejected(self):
        p=self.base/'grub_manager.py';p.unlink();p.symlink_to(self.base/'limine_manager.py')
        with self.assertRaisesRegex(RuntimeError,'collegamento'):s.verify_bundle(self.base)

    def test_detection_does_not_infer_bootloader_from_files(self):
        root=self.base/'root';(root/'etc').mkdir(parents=True)
        for identity,expected in [('omarchy','limine'),('ubuntu','grub'),('debian','grub')]:
            (root/'etc/os-release').write_text('ID="'+identity+'"\n')
            self.assertEqual(s.detected_backend(root),expected)
        (root/'etc/os-release').write_text('ID=fedora\nID_LIKE=ubuntu\n')
        with self.assertRaisesRegex(RuntimeError,'non qualificato'):s.detected_backend(root)

    def test_standard_os_release_symlink_is_supported(self):
        root=self.base/'osroot';(root/'etc').mkdir(parents=True);(root/'usr/lib').mkdir(parents=True)
        (root/'usr/lib/os-release').write_text('ID=debian\n')
        (root/'etc/os-release').symlink_to('../usr/lib/os-release')
        self.assertEqual(s.detected_backend(root),'grub')

    def test_os_release_cannot_redirect_elsewhere(self):
        root=self.base/'osroot';(root/'etc').mkdir(parents=True)
        (root/'elsewhere').write_text('ID=ubuntu\n');(root/'etc/os-release').symlink_to('../elsewhere')
        with self.assertRaises((RuntimeError,OSError)):s.detected_backend(root)

    def test_plan_rejects_other_bootloader_before_manager(self):
        with patch.object(s,'detected_backend',return_value='limine'),patch.object(s,'load_manager') as load:
            with self.assertRaisesRegex(RuntimeError,'nessuna migrazione'):s.plan(self.base,'grub','synaptic-cosmos','1080p',8)
            load.assert_not_called()

    def test_no_approval_never_calls_plan(self):
        args=argparse.Namespace(action='apply',approve_boot_write=False,recovery_confirmed=True)
        with patch.object(s.os,'geteuid',return_value=0),patch.object(s,'plan') as plan:
            with self.assertRaisesRegex(RuntimeError,'approvazione'):s.operation(self.base,args)
            plan.assert_not_called()

    def test_missing_recovery_never_calls_plan(self):
        args=argparse.Namespace(action='restore',approve_boot_write=True,recovery_confirmed=False)
        with patch.object(s.os,'geteuid',return_value=0),patch.object(s,'plan') as plan:
            with self.assertRaisesRegex(RuntimeError,'recovery'):s.operation(self.base,args)
            plan.assert_not_called()

    def test_changed_review_refuses_write(self):
        args=argparse.Namespace(action='apply',approve_boot_write=True,recovery_confirmed=True,backend='limine',theme='synaptic-cosmos',profile='1080p',timeout=8,expected_review='old')
        with patch.object(s.os,'geteuid',return_value=0),patch.object(s,'plan',return_value={'review_sha256':'changed'}),patch.object(s,'load_manager') as manager:
            with self.assertRaisesRegex(RuntimeError,'cambiato'):s.operation(self.base,args)
            manager.assert_not_called()

    def test_unprivileged_operation_refused(self):
        with patch.object(s.os,'geteuid',return_value=1000),patch.object(s,'plan') as plan:
            with self.assertRaisesRegex(RuntimeError,'amministratore'):s.operation(self.base,Mock())
            plan.assert_not_called()

    def test_grub_active_efi_partition_must_match(self):
        boot='BootCurrent: 0001\nBoot0001* ubuntu HD(1,GPT,aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,0,1)/File(\\EFI\\ubuntu\\shimx64.efi)\n'
        def output(command,**kwargs):
            if command[0]=='efibootmgr':return boot
            if command[0]=='findmnt':return json.dumps({'filesystems':[{'fstype':'vfat','source':'/dev/fake'}]})
            return '11111111-2222-3333-4444-555555555555\n'
        with patch.object(Path,'is_dir',return_value=True),patch.object(s.os,'uname',return_value=argparse.Namespace(machine='x86_64')),patch.object(s.subprocess,'check_output',side_effect=output):
            with self.assertRaisesRegex(RuntimeError,'non corrisponde'):s.grub_guard()

    def test_grub_guard_rejects_active_limine(self):
        with patch.object(Path,'is_dir',return_value=True),patch.object(s.os,'uname',return_value=argparse.Namespace(machine='x86_64')),patch.object(s.subprocess,'check_output',return_value='BootCurrent: 0001\nBoot0001* Limine HD(1,GPT,abc,0,1)/File(\\EFI\\limine\\limine_x64.efi)\n'):
            with self.assertRaisesRegex(RuntimeError,'non identifica'):s.grub_guard()


@unittest.skipUnless(os.environ.get('DISPLAY') and tk is not None,'Tk UI requires Tk and an isolated display')
class Gui(Fixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        import tkinter as tk
        self.window=tk.Tk()
        with patch.object(s,'detected_backend',return_value='limine'):
            self.ui=s.Wizard(self.window,self.base)
        self.window.update()

    def tearDown(self):
        self.ui.close();super().tearDown()

    def test_apply_needs_plan_and_recovery(self):
        self.assertEqual(str(self.ui.apply['state']),'disabled')
        self.ui.review={'can_apply':True,'can_restore':False,'review_sha256':'abc'};self.ui.buttons()
        self.assertEqual(str(self.ui.apply['state']),'disabled')
        self.ui.recovery.set(True);self.ui.buttons()
        self.assertEqual(str(self.ui.apply['state']),'normal')
        self.ui.theme.set('sentient-atlas');self.ui.change()
        self.assertIsNone(self.ui.review)
        self.assertEqual(str(self.ui.apply['state']),'disabled')

    def test_preview_can_change_without_changing_install_target(self):
        self.ui.preview_backend.set('grub');self.ui.show_preview()
        self.assertEqual(self.ui.backend,'limine')
        self.assertIn('GRUB',self.ui.caption['text'])
        self.assertGreater(self.ui.image.width(),0)

    def test_cancel_does_not_start_privileged_operation(self):
        self.ui.review={'title':'Synaptic Cosmos'};self.ui.recovery.set(True)
        with patch.object(self.ui.messagebox,'askyesno',return_value=False),patch.object(self.ui,'start') as start:
            self.ui.confirm('apply');start.assert_not_called()

    def test_authentication_command_is_fixed_and_review_bound(self):
        self.ui.review={'review_sha256':'abc'}
        cmd=self.ui.execute('apply')
        self.assertEqual(cmd[:2],['pkexec','/usr/bin/python3'])
        self.assertIn('--approve-boot-write',cmd)
        self.assertEqual(cmd[-2:],['--expected-review','abc'])


if __name__=='__main__':unittest.main()
