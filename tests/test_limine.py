import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('limine_manager', Path(__file__).resolve().parents[1] / 'scripts/limine_manager.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
build_spec = importlib.util.spec_from_file_location('limine_build', Path(__file__).resolve().parents[1] / 'scripts/limine_build.py')
b = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(b)
BASE = b'# original\ntimeout: 0\ndefault_entry: 2\nterm_background: 1a1b26\ninterface_branding: Omarchy\nhash_mismatch_panic: no\n/Omarchy\n  protocol: efi\n  path: boot():/EFI/Linux/omarchy_linux.efi\n//Snapshots\n  comment: unchanged\n/Ubuntu\n  protocol: efi\n  path: guid(example):/EFI/ubuntu/shimx64.efi\n'


class LimineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'boot').mkdir()
        self.manager = m.Manager(self.root)
        self.manager.config.write_bytes(BASE)
        self.source = self.root / 'source'
        self.source.mkdir()
        image = b'fixture image'
        self.asset = m.sha(image)[:16]
        (self.source / 'background.png').write_bytes(image)
        (self.source / 'appearance.conf').write_text(b.appearance(self.asset))
        self.manifest()

    def manifest(self):
        (self.source / 'manifest.json').write_text(json.dumps({p.name: m.sha(p.read_bytes()) for p in self.source.iterdir() if p.name != 'manifest.json'}))

    def alternative(self, name):
        source = self.root / name
        source.mkdir()
        image = ('fixture-' + name).encode()
        (source / 'background.png').write_bytes(image)
        (source / 'appearance.conf').write_text(b.appearance(m.sha(image)[:16], name))
        (source / 'manifest.json').write_text(json.dumps({p.name: m.sha(p.read_bytes()) for p in source.iterdir()}))
        return source

    def test_multiboot_windows_macos_linux_and_custom_entries_are_unchanged(self):
        extra=b'/Windows\n protocol: efi\n path: guid(example):/EFI/Microsoft/Boot/bootmgfw.efi\n/macOS via OpenCore\n protocol: efi\n path: guid(example):/EFI/OC/OpenCore.efi\n/Fedora\n protocol: linux\n kernel_path: boot():/vmlinuz\n/Custom network rescue\n protocol: efi\n path: boot():/custom.efi\n'
        original=BASE+extra;self.manager.config.write_bytes(original)
        self.manager.install(self.source)
        updated=self.manager.config.read_bytes()
        self.assertEqual(original[original.index(b'/Omarchy'):],updated[updated.index(b'/Omarchy'):])
        self.manager.restore();self.assertEqual(self.manager.config.read_bytes(),original)

    def test_switch_plan_read_only_and_entries_preserved(self):
        self.manager.install(self.source)
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        alt = self.alternative('synaptic')
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        old, new, _, _ = self.manager.plan(alt, replace=True)
        self.assertEqual(old, self.manager.config.read_bytes())
        self.assertEqual(old[old.index(b'/Omarchy'):], new[new.index(b'/Omarchy'):])
        self.assertIn(b'default_entry: 2\n', new)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_switch_restore_previous_then_original(self):
        self.manager.install(self.source)
        first = self.manager.config.read_bytes()
        meta = json.loads(self.manager.active.read_bytes())
        self.manager.install(self.alternative('synaptic'), expected=m.sha(first), replace=True)
        self.assertTrue((self.root / 'boot/dls-neon-limine' / self.asset).is_dir())
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), first)
        self.assertEqual(json.loads(self.manager.active.read_bytes()), meta)
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), BASE)
        self.assertFalse(self.manager.active.exists())

    def test_uninstall_unwinds_all_themes(self):
        self.manager.install(self.source)
        for name in ['quantum', 'atlas', 'synaptic']:
            self.manager.install(self.alternative(name), replace=True)
        self.manager.uninstall()
        self.assertEqual(self.manager.config.read_bytes(), BASE)
        self.assertFalse(self.manager.active.exists())
        self.assertFalse(list((self.root / 'boot/dls-neon-limine').iterdir()))
        self.assertEqual(len(list(self.manager.state.glob('backup-*'))), 4)

    def test_switch_requires_active_theme(self):
        with self.assertRaises(RuntimeError): self.manager.install(self.source, replace=True)
        self.assertEqual(self.manager.config.read_bytes(), BASE)

    def test_switch_updated_config_refused(self):
        self.manager.install(self.source)
        changed = self.manager.config.read_bytes() + b'# kernel update\n'
        self.manager.config.write_bytes(changed)
        with self.assertRaises(RuntimeError): self.manager.install(self.alternative('synaptic'), replace=True)
        self.assertEqual(self.manager.config.read_bytes(), changed)
        self.assertFalse(self.manager.pending.exists())

    def test_switch_wrong_reviewed_hash_refused(self):
        self.manager.install(self.source)
        before = self.manager.config.read_bytes()
        with self.assertRaises(RuntimeError): self.manager.install(self.alternative('synaptic'), expected='0'*64, replace=True)
        self.assertEqual(self.manager.config.read_bytes(), before)
        self.assertFalse(self.manager.pending.exists())

    def test_switch_edited_previous_asset_refused(self):
        self.manager.install(self.source)
        (self.root / 'boot/dls-neon-limine' / self.asset / 'background.png').write_bytes(b'admin')
        with self.assertRaises(RuntimeError): self.manager.install(self.alternative('synaptic'), replace=True)
        self.assertFalse(self.manager.pending.exists())

    def test_restore_refuses_edited_previous_asset(self):
        self.manager.install(self.source)
        self.manager.install(self.alternative('synaptic'), replace=True)
        current = self.manager.config.read_bytes()
        (self.root / 'boot/dls-neon-limine' / self.asset / 'background.png').write_bytes(b'admin')
        with self.assertRaises(RuntimeError): self.manager.restore()
        self.assertEqual(current, self.manager.config.read_bytes())

    def test_switch_failure_before_config_restores_prior_state(self):
        self.manager.install(self.source)
        first = self.manager.config.read_bytes()
        state = self.manager.active.read_bytes()
        alt = self.alternative('synaptic')
        atomic = m.atomic
        def fail(path, data):
            if path.name == 'background.png': raise OSError('full ESP')
            atomic(path, data)
        with patch.object(m, 'atomic', side_effect=fail):
            with self.assertRaises(OSError): self.manager.install(alt, replace=True)
        self.assertTrue(self.manager.active.exists())
        self.assertTrue(self.manager.pending.exists())
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), first)
        self.assertEqual(json.loads(self.manager.active.read_bytes()), json.loads(state))
        self.assertFalse(self.manager.pending.exists())

    def test_switch_failure_after_config_restores_prior_state(self):
        self.manager.install(self.source)
        first = self.manager.config.read_bytes()
        state = json.loads(self.manager.active.read_bytes())
        alt = self.alternative('synaptic')
        atomic = m.atomic
        def fail(path, data):
            if path == self.manager.active: raise OSError('state write failed')
            atomic(path, data)
        with patch.object(m, 'atomic', side_effect=fail):
            with self.assertRaises(OSError): self.manager.install(alt, replace=True)
        self.assertNotEqual(self.manager.config.read_bytes(), first)
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), first)
        self.assertEqual(json.loads(self.manager.active.read_bytes()), state)

    def test_switch_after_active_commit_interruption_restores_prior(self):
        self.manager.install(self.source)
        first = self.manager.config.read_bytes()
        alt = self.alternative('synaptic')
        unlink = Path.unlink
        def fail(path, *args, **kwargs):
            if path == self.manager.pending: raise OSError('interruption clearing journal')
            return unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', fail):
            with self.assertRaises(OSError): self.manager.install(alt, replace=True)
        self.assertTrue(self.manager.pending.exists())
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), first)
        self.assertTrue(self.manager.active.exists())

    def test_ancestor_destination_cannot_be_reclaimed(self):
        self.manager.install(self.source)
        self.manager.install(self.alternative('synaptic'), replace=True)
        current = self.manager.config.read_bytes()
        with self.assertRaises(RuntimeError): self.manager.install(self.source, replace=True)
        self.assertEqual(current, self.manager.config.read_bytes())
        self.assertFalse(self.manager.pending.exists())

    def test_previous_checkpoint_corruption_refused(self):
        self.manager.install(self.source)
        self.manager.install(self.alternative('synaptic'), replace=True)
        meta = json.loads(self.manager.active.read_text())
        meta['previous']['after'] = '0' * 64
        self.manager.active.write_text(json.dumps(meta))
        current = self.manager.config.read_bytes()
        with self.assertRaises(RuntimeError): self.manager.restore()
        self.assertEqual(current, self.manager.config.read_bytes())

    def test_reviewed_baseline_change_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'Reviewed configuration changed'):
            self.manager.install(self.source, '0' * 64)
        self.assertEqual(self.manager.config.read_bytes(), BASE)
        self.assertFalse(self.manager.pending.exists())

    def test_lock_conflict_refused(self):
        with self.manager.lock():
            with self.assertRaises(BlockingIOError): self.manager.install(self.source)
        self.assertEqual(self.manager.config.read_bytes(), BASE)

    def test_config_symlink_refused(self):
        target = self.root / 'real-config'
        self.manager.config.rename(target)
        self.manager.config.symlink_to(target)
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_asset_path_traversal_refused(self):
        (self.source / 'manifest.json').write_text(json.dumps({'../bad': '0' * 64}))
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_host_guard_refuses_non_root(self):
        with patch.object(m.Path, 'read_text', return_value='ID=omarchy\n'), patch.object(m.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'requires root'): m.host_guard()

    def test_host_guard_refuses_other_platform(self):
        from types import SimpleNamespace
        with patch.object(m.os,'uname',return_value=SimpleNamespace(machine='aarch64')):
            with self.assertRaisesRegex(RuntimeError,'x86-64'):m.host_guard()

    def test_host_guard_does_not_require_omarchy_label_or_pacman(self):
        from types import SimpleNamespace
        boot='BootCurrent: 0001\nBoot0001* Custom Linux HD(1,GPT,fake,0,1)/File(\\EFI\\limine\\limine_x64.efi)\n'
        def run(command,**kwargs):
            if command[0]=='efibootmgr':return SimpleNamespace(stdout=boot)
            if command[0]=='findmnt':return SimpleNamespace(stdout=json.dumps({'filesystems':[{'fstype':'vfat','options':'rw,relatime'}]}))
            raise AssertionError('Unexpected distro-specific command: '+str(command))
        with patch.object(m.os,'geteuid',return_value=0),patch.object(m.Path,'is_dir',return_value=True),patch.object(m.subprocess,'run',side_effect=run),patch.object(m,'regular',return_value=b'\x00'*5),patch.object(m,'sha',return_value='3fe0de87c13a12998b3c785b0c57ddfbcd6fc57251c1b0628604583ec8e9a5ff'),patch.object(m.Path,'glob',side_effect=lambda _: [m.Path('/fake')]):
            m.host_guard()

    def test_host_guard_refuses_other_active_loader(self):
        with patch.object(m.Path, 'read_text', return_value='ID=omarchy\n'), patch.object(m.os, 'geteuid', return_value=0), patch.object(m.Path, 'is_dir', return_value=True), patch.object(m.subprocess, 'run') as run:
            run.return_value.stdout = 'BootCurrent: 0006\nBoot0006* Ubuntu\n'
            with self.assertRaisesRegex(RuntimeError, 'not identified as Limine'): m.host_guard()

    def test_indented_entry_section_preserved(self):
        source = BASE.replace(b'/Omarchy', b'    /Omarchy').replace(b'/Ubuntu', b'    /Ubuntu')
        self.manager.config.write_bytes(source)
        _, new, _, _ = self.manager.plan(self.source)
        self.assertEqual(new[new.index(b'    /Omarchy'):], source[source.index(b'    /Omarchy'):])

    def test_indented_appearance_in_entries_refused(self):
        self.manager.config.write_bytes(BASE + b'    term_background: 000000\n')
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_no_entries_refused(self):
        self.manager.config.write_bytes(b'timeout: 0\n')
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_state_path_symlink_refused(self):
        target = self.root / 'var/lib'
        target.mkdir(parents=True)
        self.manager.state.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(RuntimeError): self.manager.install(self.source)
        self.assertEqual(self.manager.config.read_bytes(), BASE)

    def test_plan_is_read_only_and_preserves_entries_defaults_security(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        old, new, _, _ = self.manager.plan(self.source)
        self.assertEqual(old, BASE)
        self.assertEqual(new[new.index(b'/Omarchy'):], BASE[BASE.index(b'/Omarchy'):])
        for line in [b'timeout: 0\n', b'default_entry: 2\n', b'hash_mismatch_panic: no\n']:
            self.assertIn(line, new)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_install_uninstall_exact_roundtrip(self):
        self.manager.install(self.source)
        self.assertTrue(self.manager.active.exists())
        self.assertFalse(self.manager.pending.exists())
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), BASE)
        self.assertFalse(self.manager.active.exists())
        self.assertTrue(list(self.manager.state.glob('backup-*')))

    def test_repeat_install_refused_without_mutation(self):
        self.manager.install(self.source)
        current = self.manager.config.read_bytes()
        with self.assertRaises(RuntimeError): self.manager.install(self.source)
        self.assertEqual(current, self.manager.config.read_bytes())

    def test_later_kernel_or_snapshot_update_refuses_restore(self):
        self.manager.install(self.source)
        newer = self.manager.config.read_bytes() + b'/new kernel\n  path: boot():/new.efi\n'
        self.manager.config.write_bytes(newer)
        with self.assertRaises(RuntimeError): self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), newer)

    def test_corrupted_backup_refused(self):
        self.manager.install(self.source)
        backup = next(self.manager.state.glob('backup-*'))
        (backup / 'before.conf').write_bytes(b'corrupt')
        with self.assertRaises(RuntimeError): self.manager.restore()
        self.assertTrue(self.manager.active.exists())

    def test_edited_assets_not_deleted(self):
        self.manager.install(self.source)
        target = self.root / 'boot/dls-neon-limine' / self.asset / 'background.png'
        target.write_bytes(b'admin edit')
        with self.assertRaises(RuntimeError): self.manager.restore()
        self.assertEqual(target.read_bytes(), b'admin edit')

    def test_corrupt_source_rejected_before_state_creation(self):
        (self.source / 'background.png').write_bytes(b'bad')
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)
        self.assertFalse(self.manager.state.exists())

    def test_source_symlink_refused(self):
        path = self.source / 'background.png'
        path.unlink()
        path.symlink_to(self.manager.config)
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_destination_symlink_refused(self):
        (self.root / 'boot/dls-neon-limine').symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(RuntimeError): self.manager.install(self.source)
        self.assertEqual(self.manager.config.read_bytes(), BASE)

    def test_security_option_in_asset_refused(self):
        with (self.source / 'appearance.conf').open('a') as stream: stream.write('hash_mismatch_panic: no\n')
        self.manifest()
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_appearance_after_entry_refused(self):
        self.manager.config.write_bytes(BASE + b'term_background: 000000\n')
        with self.assertRaises(RuntimeError): self.manager.plan(self.source)

    def test_preexisting_destination_not_owned(self):
        target = self.root / 'boot/dls-neon-limine' / self.asset
        target.mkdir(parents=True)
        (target / 'private').write_bytes(b'keep')
        with self.assertRaises(RuntimeError): self.manager.install(self.source)
        self.assertEqual((target / 'private').read_bytes(), b'keep')

    def test_interrupted_copy_is_recoverable(self):
        atomic = m.atomic
        def fail(path, data):
            if path.name == 'background.png': raise OSError('simulated full ESP')
            atomic(path, data)
        with patch.object(m, 'atomic', side_effect=fail):
            with self.assertRaises(OSError): self.manager.install(self.source)
        self.assertTrue(self.manager.pending.exists())
        self.assertEqual(self.manager.config.read_bytes(), BASE)
        self.manager.restore()
        self.assertFalse(self.manager.pending.exists())

    def test_interruption_after_config_commit_recoverable(self):
        atomic = m.atomic
        def fail(path, data):
            if path == self.manager.active: raise OSError('state write failed')
            atomic(path, data)
        with patch.object(m, 'atomic', side_effect=fail):
            with self.assertRaises(OSError): self.manager.install(self.source)
        self.assertNotEqual(self.manager.config.read_bytes(), BASE)
        self.manager.restore()
        self.assertEqual(self.manager.config.read_bytes(), BASE)

    def test_concurrent_change_refused(self):
        atomic = m.atomic
        def interfere(path, data):
            atomic(path, data)
            if path.name == 'background.png': self.manager.config.write_bytes(BASE + b'# changed\n')
        with patch.object(m, 'atomic', side_effect=interfere):
            with self.assertRaises(RuntimeError): self.manager.install(self.source)
        self.assertEqual(self.manager.config.read_bytes(), BASE + b'# changed\n')


if __name__ == '__main__': unittest.main()
