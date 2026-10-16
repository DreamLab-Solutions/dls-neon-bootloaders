"""Regression checks for selecting a directory instead of a demo EFI leaf."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import limine_preview as preview
sys.path.pop(0)


class PreviewNavigation(unittest.TestCase):
    def test_flat_demo_selects_second_row_directory(self):
        fixture = b'/Omarchy\n protocol: efi\n/Snapshots\n//snapshot 1\n/Ubuntu\n'
        self.assertEqual(preview.submenu_steps(fixture), 1)

    def test_expanded_real_root_skips_kernel_leaf(self):
        fixture = b'/+Omarchy\n //linux-omarchy\n //Snapshots\n ///snapshot 2\n ////linux-omarchy\n ///snapshot 1\n ////linux-omarchy\n'
        self.assertEqual(preview.submenu_steps(fixture), 2)

    def test_hidden_descendants_are_not_counted(self):
        fixture = b'/Omarchy\n //kernel\n //Snapshots\n ///snapshot\n/Other OS options\n //Other kernel\n'
        self.assertEqual(preview.submenu_steps(fixture), 1)

    def test_missing_directory_is_not_called_a_navigation_pass(self):
        with self.assertRaises(RuntimeError):
            preview.submenu_steps(b'/Omarchy\n/Ubuntu\n')


if __name__ == '__main__':
    unittest.main()
