from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import nexus_release as nexus


class NexusReleaseTests(unittest.TestCase):
    def test_source_must_match_peeled_canonical_tag(self):
        source_commands = [
            "",
            "reviewed",
            "tag-object refs/tags/v1.2.3\nreviewed refs/tags/v1.2.3^{}",
            "reviewed",
        ]
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            (checkout / "VERSION").write_text("1.2.3\n")
            with patch.object(nexus, "ROOT", checkout), patch.object(nexus, "git", side_effect=source_commands):
                self.assertEqual(nexus.release_source()["sourceCommit"], "reviewed")
            source_commands[2] = "other refs/tags/v1.2.3"
            with patch.object(nexus, "ROOT", checkout), patch.object(nexus, "git", side_effect=source_commands):
                with self.assertRaisesRegex(ValueError, "canonical release tag"):
                    nexus.release_source()

    def test_bundle_binds_the_four_assets_to_checksums_and_source(self):
        source = {"version": "1.2.3", "sourceCommit": "first"}
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            files = {name: name.encode() for name in nexus.asset_names(source["version"])}
            files["SHA256SUMS"] = nexus.release_checksums(files, source["version"])
            files["RELEASE-NOTES.md"] = b"Release notes"
            for name, content in files.items():
                (stage / name).write_bytes(content)
            payload = nexus.build_bundle(stage, source)
            self.assertEqual(payload, nexus.build_bundle(stage, source))
            nexus.verify_bundle(payload, source)
            with self.assertRaisesRegex(ValueError, "canonical source"):
                nexus.verify_bundle(payload, dict(source, sourceCommit="different"))
            (stage / next(iter(files))).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
                nexus.build_bundle(stage, source)

    def test_publish_and_verify_absent_digest(self):
        request = Mock(side_effect=[None, b"", b"archive"])
        self.assertEqual(nexus.publish(b"archive", request), "published")
        self.assertEqual(request.call_args_list, [call(), call(b"archive"), call()])

    def test_never_replace_confirmed_existing_digest(self):
        request = Mock(return_value=b"archive")
        self.assertEqual(nexus.publish(b"archive", request), "already-present")
        request.assert_called_once_with()
        request = Mock(return_value=b"unexpected")
        with self.assertRaisesRegex(ValueError, "different bytes"):
            nexus.publish(b"archive", request)
        request.assert_called_once_with()

    def test_readback_catches_failure_and_recovers_uncertain_put(self):
        request = Mock(side_effect=[None, b"", b"unexpected"])
        with self.assertRaisesRegex(ValueError, "readback differs"):
            nexus.publish(b"archive", request)
        request = Mock(side_effect=[None, OSError("interrupted"), b"archive"])
        self.assertEqual(nexus.publish(b"archive", request), "already-present")
        self.assertEqual(request.call_args_list, [call(), call(b"archive"), call()])
