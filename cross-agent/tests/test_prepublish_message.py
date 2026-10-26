import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepublish_message import validate_message


class CommitPrivacyTests(unittest.TestCase):
    def test_plain_message(self):
        self.assertEqual(
            validate_message("cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)\n"),
            "cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)",
        )

    def test_session_trailer_rejected(self):
        with self.assertRaises(ValueError):
            validate_message(
                "cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)\n\n"
                "Claude-Session: https://claude.ai/code/session_example\n"
            )

    def test_coauthor_trailer_rejected(self):
        with self.assertRaises(ValueError):
            validate_message(
                "cross-agent: HANDOFF_OPEN CROSS_AGENT_TEST rev 61 (CLAUDE)\n\n"
                "Co-Authored-By: Claude <noreply@anthropic.com>\n"
            )

    def test_unexpected_line_rejected(self):
        with self.assertRaises(ValueError):
            validate_message("cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)\nsecret\n")

    def test_url_in_subject_rejected(self):
        with self.assertRaises(ValueError):
            validate_message("https://claude.ai/code/session_abc\n")

if __name__ == "__main__":
    unittest.main()
