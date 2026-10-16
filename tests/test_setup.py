import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

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

    def test_detection_uses_active_efi_instead_of_distribution(self):
        root=self.base/'osroot';(root/'sys/firmware/efi').mkdir(parents=True)
        for file,expected in [('\\EFI\\fedora\\shimx64.efi','grub'),('\\EFI\\custom\\grubx64.efi','grub'),('\\EFI\\limine\\limine_x64.efi','limine')]:
            boot='BootCurrent: 0001\nBoot0001* Whatever HD(1,GPT,aaaa,0,1)/File('+file+')\n'
            with patch.object(s.subprocess,'check_output',return_value=boot):
                self.assertEqual(s.detected_backend(root),expected)

    def test_windows_native_loader_is_not_misidentified_as_grub(self):
        root=self.base/'osroot';(root/'sys/firmware/efi').mkdir(parents=True)
        boot='BootCurrent: 0001\nBoot0001* Windows HD(1,GPT,aaaa,0,1)/File(\\EFI\\Microsoft\\Boot\\bootmgfw.efi)\n'
        with patch.object(s.subprocess,'check_output',return_value=boot):
            with self.assertRaisesRegex(RuntimeError,'non è GRUB/Limine'):s.detected_backend(root)

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

    def test_grub_guard_accepts_other_linux_vendor_and_grub2_layout(self):
        boot='BootCurrent: 0001\nBoot0001* Fedora HD(1,GPT,aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,0,1)/File(\\EFI\\fedora\\shimx64.efi)\n'
        def output(command,**kwargs):
            if command[0]=='efibootmgr':return boot
            if command[0]=='findmnt':return json.dumps({'filesystems':[{'fstype':'vfat','source':'/dev/fake','target':'/efi'}]})
            return 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\n'
        with patch.object(Path,'is_dir',return_value=True),patch.object(s.os,'uname',return_value=argparse.Namespace(machine='x86_64')),patch.object(s.subprocess,'check_output',side_effect=output),patch.object(s,'regular',return_value=b'efi'),patch.object(s.shutil,'which',side_effect=lambda name: '/usr/bin/'+name if name.startswith('grub2-') else None):
            # Explicitly provide one unambiguous native configuration.
            with patch.object(Path,'is_file',autospec=True,side_effect=lambda path: str(path)=='/boot/grub2/grub.cfg'):
                info=s.grub_guard()
            self.assertEqual(info['config'],'boot/grub2/grub.cfg')
            self.assertTrue(info['tools']['check'].endswith('grub2-script-check'))

    def test_grub_guard_rejects_active_limine(self):
        with patch.object(Path,'is_dir',return_value=True),patch.object(s.os,'uname',return_value=argparse.Namespace(machine='x86_64')),patch.object(s.subprocess,'check_output',return_value='BootCurrent: 0001\nBoot0001* Limine HD(1,GPT,abc,0,1)/File(\\EFI\\limine\\limine_x64.efi)\n'):
            with self.assertRaisesRegex(RuntimeError,'GRUB attivo'):s.grub_guard()


class ConsoleTests(Fixture,unittest.TestCase):
    def scripted(self, answers, execute=None):
        lines=[];previews=[];iterator=iter(answers)
        reader=lambda prompt: next(iterator)
        run=execute or Mock(side_effect=AssertionError('Unexpected privileged action'))
        ui=s.Console(self.base,read=reader,write=lines.append,execute=run,preview=previews.append)
        ui.run();return ui,run,lines,previews

    def reviewer(self,action,extra=()):
        if action=='detect':return {'backend':'grub'}
        if action=='plan':return {'backend':'grub','title':'Synaptic Cosmos','config_path':'boot/grub2/grub.cfg','entries':['Windows Boot Manager','macOS','Fedora','Custom rescue'],'reason':'','can_apply':True,'can_restore':True,'review_sha256':'reviewed'}
        return {'result':'Completed in fixture'}

    def test_browsing_and_preview_never_request_privileges(self):
        ui,run,lines,previews=self.scripted(['2','p','b','p','q'])
        run.assert_not_called();self.assertEqual(len(previews),2)
        self.assertIn('quantum-fabric.png',str(previews[0]));self.assertNotEqual(previews[0],previews[1])

    def test_plan_lists_every_os_without_filtering(self):
        run=Mock(side_effect=self.reviewer)
        _,_,lines,_=self.scripted(['v','q'],run)
        rendered='\n'.join(lines)
        import test_transactions as tx
        actual=s.menu_titles(tx.m,"blscfg --entry linux\nmenuentry 'Windows' {\n true\n}\n")
        self.assertIn('Windows',actual)
        self.assertTrue(any(title.startswith('BLS:') for title in actual))
        for name in ['Windows Boot Manager','macOS','Fedora','Custom rescue']:self.assertIn(name,rendered)
        self.assertEqual([c.args[0] for c in run.call_args_list],['detect','plan'])

    def test_apply_without_plan_is_not_executed(self):
        _,run,_,_=self.scripted(['a','q']);run.assert_not_called()

    def test_recovery_refusal_cancels_write(self):
        run=Mock(side_effect=self.reviewer)
        self.scripted(['v','a','n','q'],run)
        self.assertEqual([c.args[0] for c in run.call_args_list],['detect','plan'])

    def test_exact_final_confirmation_required(self):
        run=Mock(side_effect=self.reviewer)
        self.scripted(['v','a','s','yes','q'],run)
        self.assertEqual([c.args[0] for c in run.call_args_list],['detect','plan'])

    def test_review_and_approval_bound_to_apply(self):
        run=Mock(side_effect=self.reviewer)
        ui,_,_,_=self.scripted(['v','a','s','APPLICA','q'],run)
        self.assertEqual(run.call_args_list[-1].args,('apply',['--approve-boot-write','--recovery-confirmed','--expected-review','reviewed']))
        self.assertIsNone(ui.review)

    def test_theme_change_invalidates_review(self):
        run=Mock(side_effect=self.reviewer)
        ui,_,_,_=self.scripted(['v','2','a','q'],run)
        self.assertIsNone(ui.review)
        self.assertEqual([c.args[0] for c in run.call_args_list],['detect','plan'])

    def test_detection_failure_does_not_end_browsing(self):
        run=Mock(side_effect=RuntimeError('Unsupported active loader'))
        _,_,lines,previews=self.scripted(['d','3','p','q'],run)
        self.assertEqual(len(previews),1);self.assertIn('Puoi continuare','\n'.join(lines))

    def test_restore_requires_its_own_confirmation(self):
        run=Mock(side_effect=self.reviewer)
        self.scripted(['v','r','s','APPLICA','r','s','RIPRISTINA','q'],run)
        self.assertEqual([c.args[0] for c in run.call_args_list],['detect','plan','restore'])

    def test_invalid_settings_preserve_previous_values(self):
        ui,run,_,_=self.scripted(['o','4k','999','q'])
        self.assertEqual((ui.profile,ui.timeout),('1080p',8));run.assert_not_called()


if __name__=='__main__':unittest.main()
