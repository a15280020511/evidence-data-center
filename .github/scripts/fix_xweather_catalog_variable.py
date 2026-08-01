#!/usr/bin/env python3
"""Teach the unified catalog to preserve non-secret repository variables."""
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "api-center/build_catalog.py"
text = path.read_text(encoding="utf-8")
old = '''                "optional_secret_environment_variable_name": str(
                    raw_provider.get("optional_secret_environment_variable") or ""
                ),
                "secret_value_exposed": False,
'''
new = '''                "optional_secret_environment_variable_name": str(
                    raw_provider.get("optional_secret_environment_variable") or ""
                ),
                "required_repository_variable": str(
                    raw_provider.get("required_repository_variable") or ""
                ),
                "secret_value_exposed": False,
'''
if text.count(old) != 1:
    raise RuntimeError("managed provider normalization anchor not found exactly once")
text = text.replace(old, new, 1)
old = '''            "- Secret环境变量名："
            f"`{provider['required_secret_environment_variable_name'] or '无'}`（仅名称）",
            f"- 提供方SHA-256：`{provider['provider_sha256']}`",
'''
new = '''            "- Secret环境变量名："
            f"`{provider['required_secret_environment_variable_name'] or '无'}`（仅名称）",
            "- Repository Variable名："
            f"`{provider.get('required_repository_variable') or '无'}`（仅名称）",
            f"- 提供方SHA-256：`{provider['provider_sha256']}`",
'''
if text.count(old) != 1:
    raise RuntimeError("managed provider markdown anchor not found exactly once")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("PASS: unified catalog now preserves required_repository_variable")
