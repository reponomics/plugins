"""Remote normalization retained for Scorecard."""

from pathlib import Path
import sys
import unittest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "plugins/badge-buddy/scripts")
)
from ossf_review.remotes import github_repository_url, normalize_github_remote


class NormalizeGithubRemoteTest(unittest.TestCase):
    def test_supported_spellings_have_one_identity(self) -> None:
        remotes = (
            "https://github.com/OpenSSF/Best-Practices-Badge.git",
            "https://github.com/OpenSSF/Best-Practices-Badge/",
            "http://github.com/OpenSSF/Best-Practices-Badge/",
            "ssh://git@github.com/OpenSSF/Best-Practices-Badge.git",
            "git@github.com:OpenSSF/Best-Practices-Badge.git",
            "github.com/OpenSSF/Best-Practices-Badge",
        )

        identities = {normalize_github_remote(remote) for remote in remotes}

        self.assertEqual(
            {"github.com/openssf/best-practices-badge"},
            identities,
        )
        self.assertEqual(
            {"https://github.com/OpenSSF/Best-Practices-Badge"},
            {github_repository_url(remote) for remote in remotes},
        )

    def test_preserved_url_and_lowercase_key_remain_distinct(self) -> None:
        remote = "ssh://git@GitHub.com/Reponomics/PolicyChecks.git"
        self.assertEqual(
            "https://github.com/Reponomics/PolicyChecks", github_repository_url(remote)
        )
        self.assertEqual(
            "github.com/reponomics/policychecks", normalize_github_remote(remote)
        )

    def test_non_repository_remote_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_github_remote("https://gitlab.com/OpenSSF/project")
        with self.assertRaises(ValueError):
            normalize_github_remote("https://github.com/OpenSSF/project/issues")
