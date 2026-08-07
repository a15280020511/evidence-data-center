from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import oauth_bootstrap as bootstrap  # noqa: E402
import oauth_refresh as refresh  # noqa: E402


class ConsensusOAuthBridgeTests(unittest.TestCase):
    def test_public_client_is_pkce_native_without_secret(self) -> None:
        client = bootstrap.load_client()
        self.assertEqual(client["client_id"], "ee123d14-833d-428c-bc28-e796c2e4b25f")
        self.assertEqual(client["redirect_uri"], "http://127.0.0.1:8765/callback")
        self.assertEqual(client["token_endpoint_auth_method"], "none")
        self.assertEqual(client["pkce_method"], "S256")
        self.assertFalse(client["contains_secret"])

    def test_pkce_verifier_and_challenge(self) -> None:
        verifier, challenge = bootstrap.make_pkce()
        self.assertGreaterEqual(len(verifier), 43)
        self.assertGreaterEqual(len(challenge), 43)
        self.assertNotEqual(verifier, challenge)
        self.assertNotIn("=", verifier)
        self.assertNotIn("=", challenge)

    @patch("oauth_refresh.requests.post")
    def test_stable_refresh_injects_only_runner_access_token(self, post: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "access-secret-value",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "search",
        }
        post.return_value = response
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "env"
            output_file = Path(tmp) / "output"
            with patch.dict(os.environ, {
                "CONSENSUS_MCP_REFRESH_TOKEN": "refresh-secret-value",
                "CONSENSUS_MCP_BEARER_TOKEN": "",
                "GITHUB_ENV": str(env_file),
                "GITHUB_OUTPUT": str(output_file),
            }, clear=False):
                report = refresh.resolve(20)
            self.assertEqual(report["status"], "pass")
            self.assertFalse(report["refresh_token_rotated"])
            env_text = env_file.read_text(encoding="utf-8")
            self.assertIn("CONSENSUS_MCP_BEARER_TOKEN=access-secret-value", env_text)
            self.assertNotIn("refresh-secret-value", env_text)
            output_text = output_file.read_text(encoding="utf-8")
            self.assertIn("credential_mode=free-account-refresh-token", output_text)
            self.assertNotIn("access-secret-value", output_text)
            self.assertNotIn("refresh-secret-value", output_text)

    @patch("oauth_refresh.requests.post")
    def test_rotating_refresh_token_fails_closed(self, post: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "access-secret-value",
            "refresh_token": "new-refresh-secret",
            "token_type": "Bearer",
        }
        post.return_value = response
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "env"
            output_file = Path(tmp) / "output"
            with patch.dict(os.environ, {
                "CONSENSUS_MCP_REFRESH_TOKEN": "old-refresh-secret",
                "CONSENSUS_MCP_BEARER_TOKEN": "",
                "GITHUB_ENV": str(env_file),
                "GITHUB_OUTPUT": str(output_file),
            }, clear=False):
                with self.assertRaisesRegex(refresh.OAuthRefreshError, "rotated"):
                    refresh.resolve(20)
            self.assertFalse(env_file.exists() and env_file.read_text(encoding="utf-8").strip())
            output_text = output_file.read_text(encoding="utf-8")
            self.assertIn("refresh_token_rotated=true", output_text)
            self.assertNotIn("new-refresh-secret", output_text)

    def test_secure_local_token_file_is_not_repo_default(self) -> None:
        default = Path.home() / ".config" / "evidence-data-center" / "consensus-oauth-token.json"
        self.assertNotEqual(default.resolve().parent, ROOT.resolve())


if __name__ == "__main__":
    unittest.main()
