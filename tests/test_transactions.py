import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('manager',Path(__file__).resolve().parents[1]/'scripts/theme_manager.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir()
        (self.source/'theme-1080p.txt').write_text('title-text: ""\n')
        (self.source/'manifest.json').write_text(json.dumps(m.tree_digest(self.source)))
        self.cfg=self.root/m.CONFIG;self.cfg.parent.mkdir(parents=True)
        self.before="set default=0\nmenuentry 'Ubuntu' {\n linux /kernel root=UUID=original\n}\nsubmenu 'Advanced' {\n menuentry 'Recovery' { true; }\n}\n"
        self.cfg.write_text(self.before)
        defaults=self.root/'etc/default/grub';defaults.parent.mkdir(parents=True);defaults.write_text('GRUB_TIMEOUT=0\n')
        (self.root/'etc/grub.d').mkdir()
        self.fail=None;self.calls=[]
        self.manager=m.Manager(self.root,self.runner)

    def tearDown(self):self.temp.cleanup()

    def runner(self,command,check=True,**kwargs):
        self.calls.append(command[0])
        if self.fail==command[0]:raise subprocess.CalledProcessError(1,command)
        if command[0]=='grub-probe':return SimpleNamespace(stdout='ABCD-1234\n')
        if command[0]=='grub-mkrelpath':return SimpleNamespace(stdout='/@/boot/grub/themes/'+Path(command[-1]).name+'\n')
        if command[0]=='grub-script-check' and self.fail=='concurrent':self.cfg.write_text(self.before+'# another writer\n')
        return SimpleNamespace(stdout='')

    def install(self):return self.manager.install(self.source,'1080p',8)

    def test_install_restore_keeps_all_original_bytes_and_backup(self):
        record=self.install()
        self.assertTrue(self.cfg.read_bytes().startswith(self.before.encode()))
        self.assertTrue((self.root/m.HOOK).is_file())
        self.assertEqual(m.boot_entries(self.before),m.boot_entries(self.cfg.read_text()))
        self.assertNotIn('grub-mkconfig',self.calls);self.assertNotIn('os-prober',self.calls)
        self.manager.restore();self.assertEqual(self.cfg.read_text(),self.before)
        self.assertFalse((self.root/m.HOOK).exists())
        self.assertTrue((self.root/record['backup']/'grub.cfg').is_file())
        self.assertTrue((self.root/record['theme']).is_dir())
        self.assertEqual((self.root/'etc/default/grub').read_text(),'GRUB_TIMEOUT=0\n')
        self.install()

    def test_reviewed_baseline_change_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Reviewed GRUB'):self.manager.install(self.source,'1080p',8,expected_config='0'*64)
        self.assertEqual(self.cfg.read_text(),self.before);self.assertFalse((self.root/m.HOOK).exists())

    def test_matching_reviewed_baseline_accepted(self):
        record=self.manager.install(self.source,'1080p',8,expected_config=m.digest(self.cfg))
        self.assertEqual(record['status'],'active');self.manager.restore()
        self.assertEqual(self.cfg.read_text(),self.before)

    def test_failed_probe_rolls_back(self):
        self.fail='grub-probe'
        with self.assertRaises(subprocess.CalledProcessError):self.install()
        self.assertEqual(self.cfg.read_text(),self.before)
        self.assertFalse((self.root/m.HOOK).exists());self.assertFalse((self.root/m.STATE/'active.json').exists())

    def test_failed_syntax_check_rolls_back(self):
        self.fail='grub-script-check'
        with self.assertRaises(subprocess.CalledProcessError):self.install()
        self.assertEqual(self.cfg.read_text(),self.before);self.assertFalse((self.root/m.HOOK).exists())

    def test_concurrent_config_preserved(self):
        self.fail='concurrent'
        with self.assertRaisesRegex(RuntimeError,'concurrently'):self.install()
        self.assertIn('another writer',self.cfg.read_text());self.assertFalse((self.root/m.HOOK).exists())

    def test_restore_refuses_later_kernel_update(self):
        self.install();updated=self.cfg.read_text()+'# kernel update\n';self.cfg.write_text(updated)
        with self.assertRaisesRegex(RuntimeError,'changed after'):self.manager.restore()
        self.assertEqual(self.cfg.read_text(),updated);self.assertTrue((self.root/m.HOOK).exists())

    def test_existing_legacy_dropin_not_overwritten(self):
        p=self.root/m.DROPIN;p.parent.mkdir(exist_ok=True);p.write_text('# preserve\n')
        with self.assertRaisesRegex(RuntimeError,'already exists'):self.install()
        self.assertEqual(p.read_text(),'# preserve\n')

    def test_existing_hook_not_overwritten(self):
        p=self.root/m.HOOK;p.write_text('# someone else\n')
        with self.assertRaisesRegex(RuntimeError,'already exists'):self.install()
        self.assertEqual(p.read_text(),'# someone else\n')

    def test_corrupt_asset_aborts(self):
        (self.source/'theme-1080p.txt').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'checksums'):self.install()

    def test_asset_symlink_rejected(self):
        (self.source/'link').symlink_to(self.cfg)
        with self.assertRaisesRegex(RuntimeError,'symlinks'):self.install()

    def test_corrupt_backup_not_restored(self):
        record=self.install();(self.root/record['backup']/'grub.cfg').write_text('corrupt')
        with self.assertRaisesRegex(RuntimeError,'Backup checksum'):self.manager.restore()

    def test_modified_hook_not_removed(self):
        self.install();(self.root/m.HOOK).write_text('modified')
        with self.assertRaisesRegex(RuntimeError,'changed after'):self.manager.restore()
        self.assertEqual((self.root/m.HOOK).read_text(),'modified')

    def test_btrfs_and_separate_boot_paths_use_uuid_and_grub_relative_path(self):
        self.install();text=self.cfg.read_text()
        self.assertIn('--fs-uuid --set=dls_theme_root ABCD-1234',text)
        self.assertIn('($dls_theme_root)/@/boot/grub/themes/',text)
        self.assertNotIn(str(self.root),text)

    def test_bls_dynamic_menu_is_preserved_without_static_menuentries(self):
        self.before='set default=saved\ninsmod blscfg\nblscfg\n'
        self.cfg.write_text(self.before)
        self.install()
        self.assertTrue(self.cfg.read_bytes().startswith(self.before.encode()))
        self.manager.restore();self.assertEqual(self.cfg.read_text(),self.before)

    def test_grub2_layout_restore(self):
        cfg=self.root/'boot/grub2/grub.cfg';cfg.parent.mkdir();cfg.write_text(self.before)
        manager=m.Manager(self.root,self.runner,config='boot/grub2/grub.cfg')
        record=manager.install(self.source,'1080p',8)
        self.assertTrue(record['theme'].startswith('boot/grub2/themes/'))
        manager.restore();self.assertEqual(cfg.read_text(),self.before)

    def test_legacy_record_restore_is_still_supported(self):
        record=self.install();(self.root/m.HOOK).unlink()
        control=self.root/m.DROPIN;control.parent.mkdir(exist_ok=True);control.write_text('# legacy\n')
        for key in ['hook','hook_hash','config','mode']:record.pop(key)
        record['dropin_hash']=m.digest(control)
        (self.root/m.STATE/'active.json').write_text(json.dumps(record))
        self.manager.restore();self.assertEqual(self.cfg.read_text(),self.before);self.assertFalse(control.exists())

    def test_failed_publication_cleans_only_owned_assets(self):
        with patch.object(m.os,'replace',side_effect=OSError('failed publish')):
            with self.assertRaises(OSError):self.install()
        self.assertEqual(self.cfg.read_text(),self.before);self.assertFalse((self.root/m.HOOK).exists())

    def test_generator_hook_emits_only_the_literal_appearance_block(self):
        self.install()
        emitted=subprocess.check_output(['/bin/sh',str(self.root/m.HOOK)])
        native=self.cfg.read_bytes()
        self.assertEqual(emitted,native[native.index(m.BEGIN.encode()):])
        self.assertIn(b'$dls_theme_root',emitted)
        self.assertNotIn(b'menuentry',emitted)

    def test_real_grub_parser_accepts_the_patched_multiboot_configuration(self):
        checker=shutil.which('grub-script-check') or shutil.which('grub2-script-check')
        if not checker:self.skipTest('Real parser is exercised in the isolated build and CI')
        self.install()
        subprocess.run([checker,str(self.cfg)],check=True)

    def test_original_private_config_mode_survives_apply_and_restore(self):
        self.cfg.chmod(0o640)
        self.install();self.assertEqual(self.cfg.stat().st_mode & 0o777,0o640)
        self.manager.restore();self.assertEqual(self.cfg.stat().st_mode & 0o777,0o640)

    def test_config_without_final_newline_is_preserved(self):
        self.before=self.before.rstrip('\n');self.cfg.write_text(self.before)
        self.install();self.assertTrue(self.cfg.read_bytes().startswith(self.before.encode()))
        self.manager.restore();self.assertEqual(self.cfg.read_text(),self.before)


if __name__=='__main__':unittest.main()
