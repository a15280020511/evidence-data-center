#!/usr/bin/env python3
"""One-time repository migration for the unified Google credential Secret."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

OLD_SECRET = "GOOGLE_CREDENTIALS_JSON"
NEW_SECRET = "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON"


def publish_start_receipt() -> None:
    repository = str(os.getenv("GITHUB_REPOSITORY") or "").strip()
    issue_number = str(os.getenv("ISSUE_NUMBER") or "").strip()
    run_id = str(os.getenv("GITHUB_RUN_ID") or "").strip()
    if not repository or not issue_number:
        return
    body = "\n".join(
        [
            "## GOOGLE_CREDENTIAL_MIGRATION_STARTED",
            "",
            f"- Run ID: `{run_id or 'unknown'}`",
            f"- Target Secret: `{NEW_SECRET}`",
            "- Model calls: `0`",
            "- Secret values exposed: `false`",
        ]
    )
    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{repository}/issues/{issue_number}/comments",
            "-f",
            f"body={body}",
        ],
        check=True,
    )


def install_test_dependencies() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "-r",
            "api-center/google-cloud/requirements.txt",
            "-r",
            "api-center/data-commons/requirements.txt",
        ],
        check=True,
    )


def replace_secret_name() -> None:
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0")
    for raw_path in tracked:
        if not raw_path:
            continue
        path = Path(raw_path.decode("utf-8"))
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        replaced = text.replace(OLD_SECRET, NEW_SECRET)
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")


def support_compact_bundle() -> None:
    path = Path("api-center/google-cloud/unified_google_credentials.py")
    text = path.read_text(encoding="utf-8")
    old_block = '''    service_account = value.get("service_account")
    api_key = str(value.get("data_commons_api_key") or "").strip()
    if not isinstance(service_account, Mapping):
        raise RuntimeError(f"{BUNDLE_ENV}.service_account must be a JSON object")
    required = {
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "token_uri",
    }
    missing = sorted(required - set(service_account))
    if missing:
        raise RuntimeError(
            f"{BUNDLE_ENV}.service_account is missing fields: {missing}"
        )
    if str(service_account.get("type") or "") != "service_account":
        raise RuntimeError(
            f"{BUNDLE_ENV}.service_account.type must be service_account"
        )
    if not api_key:
        raise RuntimeError(f"{BUNDLE_ENV}.data_commons_api_key is required")
    return dict(service_account), api_key
'''
    new_block = '''    nested_service_account = value.get("service_account")
    if isinstance(nested_service_account, Mapping):
        service_account = dict(nested_service_account)
        api_key = str(value.get("data_commons_api_key") or "").strip()
        service_account_path = f"{BUNDLE_ENV}.service_account"
    else:
        service_account = dict(value)
        api_key = str(service_account.pop("data_commons_api_key", "") or "").strip()
        service_account_path = BUNDLE_ENV
    required = {
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "token_uri",
    }
    missing = sorted(required - set(service_account))
    if missing:
        raise RuntimeError(
            f"{service_account_path} is missing service-account fields: {missing}"
        )
    if str(service_account.get("type") or "") != "service_account":
        raise RuntimeError(f"{service_account_path}.type must be service_account")
    if not api_key:
        raise RuntimeError(f"{BUNDLE_ENV}.data_commons_api_key is required")
    return service_account, api_key
'''
    if old_block not in text:
        raise RuntimeError("unified credential parser block did not match expected source")
    path.write_text(text.replace(old_block, new_block), encoding="utf-8")


def add_compact_bundle_test() -> None:
    path = Path("api-center/google-cloud/tests/test_unified_google_credentials.py")
    text = path.read_text(encoding="utf-8")
    anchor = '''    def test_missing_bundle_is_rejected(self) -> None:
'''
    addition = '''    def test_parse_compact_single_secret_object(self) -> None:
        value = json.loads(self.bundle())
        compact = dict(value["service_account"])
        compact["data_commons_api_key"] = value["data_commons_api_key"]
        service_account, api_key = module.parse_bundle(json.dumps(compact))
        self.assertEqual(service_account["project_id"], "valid-project-123")
        self.assertNotIn("data_commons_api_key", service_account)
        self.assertEqual(api_key, "test-placeholder-key")

'''
    if addition in text:
        return
    if anchor not in text:
        raise RuntimeError("test insertion anchor not found")
    path.write_text(text.replace(anchor, addition + anchor), encoding="utf-8")


def main() -> int:
    publish_start_receipt()
    install_test_dependencies()
    replace_secret_name()
    support_compact_bundle()
    add_compact_bundle_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
