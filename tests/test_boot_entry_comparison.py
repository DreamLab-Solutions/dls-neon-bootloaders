"""Regression: Linux NVMe enumeration changed, Windows EFI UUID did not."""
import unittest

import test_transactions as tx

m = tx.m


def windows(device="nvme0n1p1", hint="hd0,gpt1", uuid="ABCD-1234", loader="/efi/Microsoft/Boot/bootmgfw.efi"):
    return f'''menuentry 'Windows Boot Manager (on /dev/{device})' --class windows --class os $menuentry_id_option 'osprober-efi-{uuid}' {{
  insmod part_gpt
  insmod fat
  set root='{hint}'
  if [ x$feature_platform_search_hint = xy ]; then
    search --no-floppy --fs-uuid --set=root --hint-bios={hint} --hint-efi={hint} --hint-baremetal=ahci0,gpt1 {uuid}
  else
    search --no-floppy --fs-uuid --set=root {uuid}
  fi
  chainloader {loader}
}}
'''


class BootEntryComparison(unittest.TestCase):
    def setUp(self):
        self.linux = "menuentry 'Ubuntu' $menuentry_id_option 'gnulinux-simple-example' {\n true\n}\n"
        self.before = self.linux + windows()
        self.after = self.linux + windows("nvme1n1p1", "hd1,gpt1")

    def test_nvme_rename_with_same_uuid_and_loader_is_accepted(self):
        self.assertTrue(m.compatible_boot_entries(self.before, self.after))

    def test_changed_uuid_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("ABCD-1234", "FFFF-5678")))

    def test_changed_chainloader_with_same_header_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.before.replace("bootmgfw.efi", "different.efi")))

    def test_changed_search_uuid_with_unchanged_id_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("gpt1 ABCD-1234", "gpt1 FFFF-5678")))

    def test_uuid_search_missing_rejected(self):
        changed = "\n".join(line for line in self.after.splitlines() if "search --" not in line)
        self.assertFalse(m.compatible_boot_entries(self.before, changed))

    def test_uuid_search_changed_to_label_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("--fs-uuid", "--label")))

    def test_entry_removed_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.linux))

    def test_entry_order_changed_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, windows() + self.linux))

    def test_submenu_changed_to_entry_rejected(self):
        before = self.before + "submenu 'Advanced' {\n true\n}\n"
        self.assertFalse(m.compatible_boot_entries(before, before.replace("submenu 'Advanced'", "menuentry 'Advanced'")))

    def test_renamed_os_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("Windows Boot Manager", "Another OS")))

    def test_custom_efi_entry_without_uuid_not_normalized(self):
        before = self.before.replace("osprober-efi-ABCD-1234", "custom-windows")
        after = self.after.replace("osprober-efi-ABCD-1234", "custom-windows")
        self.assertFalse(m.compatible_boot_entries(before, after))

    def test_extra_boot_command_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("  chainloader", "  set root=elsewhere\n  chainloader")))

    def test_unknown_body_format_rejected(self):
        self.assertFalse(m.compatible_boot_entries(self.before, self.after.replace("{\n  insmod", "{ insmod")))

    def test_braced_id_variable_not_truncated(self):
        text = self.before.replace("$menuentry_id_option", "${menuentry_id_option}")
        self.assertIn("osprober-efi-ABCD-1234", m.boot_entries(text)[-1])


class RenameTransaction(unittest.TestCase):
    setUp = tx.Transactions.setUp
    tearDown = tx.Transactions.tearDown
    install = tx.Transactions.install

    def runner(self, command, check):
        tx.Transactions.runner(self, command, check)
        if command[0] == "grub-mkconfig" and self.fail == "rename":
            from pathlib import Path
            path = Path(command[2])
            path.write_text(path.read_text().replace(windows(), windows("nvme1n1p1", "hd1,gpt1")))

    def test_rename_install_then_exact_restore(self):
        self.before += windows()
        self.cfg.write_text(self.before)
        self.fail = "rename"
        self.install()
        self.assertIn("/dev/nvme1n1p1", self.cfg.read_text())
        self.manager.restore()
        self.assertEqual(self.cfg.read_text(), self.before)
