import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("manager", Path(__file__).resolve().parents[1] / "scripts/theme_manager.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "theme-1080p.txt").write_text('title-text: ""\n')
        (self.source / "manifest.json").write_text(json.dumps(m.tree_digest(self.source)))
        self.cfg = self.root / m.CONFIG
        self.cfg.parent.mkdir(parents=True)
        self.before = "menuentry 'Ubuntu' {\n true\n}\nsubmenu 'Advanced options for Ubuntu' {\n true\n}\n"
        self.cfg.write_text(self.before)
        defaults = self.root / "etc/default/grub"
        defaults.parent.mkdir(parents=True)
        defaults.write_text("GRUB_TIMEOUT=0\n")
        self.fail = None
        self.calls = []
        self.manager = m.Manager(self.root, self.runner)

    def tearDown(self):
        self.temp.cleanup()

    def runner(self, command, check):
        self.calls.append(command[0])
        if self.fail == command[0]:
            raise subprocess.CalledProcessError(1, command)
        if command[0] == "grub-mkconfig":
            dropin = (self.root / m.DROPIN).read_text()
            theme = next(line.split("=", 1)[1] for line in dropin.splitlines() if line.startswith("GRUB_THEME="))
            text = f"insmod gfxmenu\nset theme={theme}\n" + self.before
            if self.fail == "entries":
                text = text.replace("menuentry 'Ubuntu'", "menuentry 'Changed'")
            if self.fail == "theme":
                text = self.before
            if self.fail == "concurrent":
                self.cfg.write_text(self.before + "# another writer\n")
            Path(command[2]).write_text(text)

    def install(self):
        return self.manager.install(self.source, "1080p", 8)

    def test_install_restore_keeps_original_and_backup(self):
        record = self.install()
        self.assertIn("insmod gfxmenu", self.cfg.read_text())
        self.assertTrue((self.root / m.DROPIN).exists())
        self.assertEqual(m.boot_entries(self.before), m.boot_entries(self.cfg.read_text()))
        self.manager.restore()
        self.assertEqual(self.cfg.read_text(), self.before)
        self.assertFalse((self.root / m.DROPIN).exists())
        self.assertTrue((self.root / record["backup"] / "grub.cfg").exists())
        self.assertTrue((self.root / record["theme"]).exists())
        self.assertEqual((self.root / "etc/default/grub").read_text(), "GRUB_TIMEOUT=0\n")
        self.install()  # A restored theme can be installed again without deleting its archive.

    def test_reviewed_baseline_must_still_match_inside_transaction(self):
        with self.assertRaisesRegex(RuntimeError, "Reviewed GRUB configuration changed"):
            self.manager.install(self.source, "1080p", 8, expected_config="0" * 64)
        self.assertEqual(self.cfg.read_text(), self.before)
        self.assertFalse((self.root / m.DROPIN).exists())
        self.assertFalse((self.root / m.STATE / "active.json").exists())

    def test_matching_reviewed_baseline_accepted(self):
        record = self.manager.install(self.source, "1080p", 8, expected_config=m.digest(self.cfg))
        self.assertEqual(record["status"], "active")
        self.manager.restore()
        self.assertEqual(self.cfg.read_text(), self.before)

    def test_failed_generator_rolls_back(self):
        self.fail = "grub-mkconfig"
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertEqual(self.cfg.read_text(), self.before)
        self.assertFalse((self.root / m.DROPIN).exists())
        self.assertFalse((self.root / m.STATE / "active.json").exists())

    def test_failed_syntax_check_rolls_back(self):
        self.fail = "grub-script-check"
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertEqual(self.cfg.read_text(), self.before)

    def test_changed_entries_abort(self):
        self.fail = "entries"
        with self.assertRaisesRegex(RuntimeError, "Boot entries changed"):
            self.install()
        self.assertEqual(self.cfg.read_text(), self.before)
        backup = next((self.root / m.STATE / "backups").iterdir())
        self.assertIn("'Changed'", (backup / "candidate-grub.cfg").read_text())
        self.assertIn("-menuentry 'Ubuntu'", (backup / "boot-entry-changes.diff").read_text())
        record = json.loads((backup / "transaction.json").read_text())
        self.assertEqual(record["status"], "aborted")
        self.assertTrue(record["config_unchanged"])

    def test_missing_theme_aborts(self):
        self.fail = "theme"
        with self.assertRaisesRegex(RuntimeError, "did not activate"):
            self.install()

    def test_concurrent_config_preserved(self):
        self.fail = "concurrent"
        with self.assertRaisesRegex(RuntimeError, "concurrently"):
            self.install()
        self.assertIn("another writer", self.cfg.read_text())

    def test_restore_refuses_later_kernel_update(self):
        self.install()
        updated = self.cfg.read_text() + "# later update\n"
        self.cfg.write_text(updated)
        with self.assertRaisesRegex(RuntimeError, "changed after"):
            self.manager.restore()
        self.assertEqual(self.cfg.read_text(), updated)
        self.assertTrue((self.root / m.DROPIN).exists())

    def test_existing_dropin_not_overwritten(self):
        dropin = self.root / m.DROPIN
        dropin.parent.mkdir()
        dropin.write_text("# preserve\n")
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            self.install()
        self.assertEqual(dropin.read_text(), "# preserve\n")

    def test_corrupt_asset_aborts(self):
        (self.source / "theme-1080p.txt").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "checksums"):
            self.install()

    def test_asset_symlink_rejected(self):
        (self.source / "link").symlink_to(self.cfg)
        with self.assertRaisesRegex(RuntimeError, "symlinks"):
            self.install()

    def test_corrupt_backup_not_restored(self):
        record = self.install()
        (self.root / record["backup"] / "grub.cfg").write_text("bad")
        with self.assertRaisesRegex(RuntimeError, "Backup checksum"):
            self.manager.restore()


if __name__ == "__main__":
    unittest.main()
