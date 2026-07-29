#!/usr/bin/env python3
"""Build a deterministic KrakenD template from allowlisted connector files.

The compiler does not call external APIs, execute connector code, or read secret
values. Secret headers and query parameters are represented only by environment-
variable names and are resolved by KrakenD Flexible Configuration at runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "krakend.base.json"
SCHEMA_PATH = HERE / "connector.schema.json"
CONNECTORS_DIR = HERE / "connectors"
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
PATH_PLACEHOLDER_RE = re.compile(r"\{([a-z][a-z0-9_]{0,63})\}")
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{12,}|bearer\s+[A-Za-z0-9._~-]{12,}|"
    r"(?:api[_-]?key|client[_-]?secret|password|token)\s*[:=]\s*[^$<{\s][^\s]{7,})"
)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.azure.internal",
    "kubernetes.default",
    "kubernetes.default.svc",
    "instance-data",
}
BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost", ".svc", ".cluster.local")
DANGEROUS_FORWARDED_HEADERS = {
    "authorization",
    "cookie",
    "host",
    "connection",
    "proxy-authorization",
    "proxy-authenticate",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
DEFAULT_CIRCUIT_BREAKER = {
    "interval": 60,
    "timeout": 30,
    "max_errors": 3,
    "log_status_change": True,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def reject_literal_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            reject_literal_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_literal_secrets(item, f"{path}[{index}]")
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        raise ValueError(f"literal secret-like value is forbidden at {path}")


def _blocked_ip(hostname: str) -> str | None:
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return None
    if address.is_loopback:
        return "loopback"
    if address.is_private:
        return "private"
    if address.is_link_local:
        return "link-local"
    if address.is_multicast:
        return "multicast"
    if address.is_reserved:
        return "reserved"
    if address.is_unspecified:
        return "unspecified"
    return None


def validate_backend_host(connector_id: str, host: str, enabled: bool) -> None:
    parsed = urlsplit(host)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"connector {connector_id} has an invalid backend host")
    hostname = parsed.hostname.casefold().rstrip(".")
    loopback_test = hostname in LOOPBACK_HOSTS
    if enabled and parsed.scheme != "https" and not loopback_test:
        raise ValueError(
            f"enabled connector {connector_id} must use HTTPS; "
            "plain HTTP is allowed only for loopback tests"
        )
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise ValueError(
            f"connector {connector_id} targets a blocked internal hostname: {hostname}"
        )
    blocked_kind = _blocked_ip(hostname)
    if blocked_kind and not loopback_test:
        raise ValueError(
            f"connector {connector_id} targets a blocked {blocked_kind} IP address: {hostname}"
        )
    if hostname == "169.254.169.254":
        raise ValueError(f"connector {connector_id} targets a cloud metadata address")


def validate_forwarded_headers(connector_id: str, headers: Any) -> None:
    for raw in headers or []:
        header = str(raw).casefold()
        if header in DANGEROUS_FORWARDED_HEADERS or header.startswith("x-forwarded-"):
            raise ValueError(
                f"connector {connector_id} forwards a forbidden request header: {raw}"
            )


def validate_path_parameter_policy(connector: Mapping[str, Any]) -> None:
    connector_id = str(connector["id"])
    raw_specs = connector.get("path_parameters")
    specs = raw_specs if isinstance(raw_specs, Mapping) else {}
    expected = {str(name) for name in specs}
    endpoint_names = PATH_PLACEHOLDER_RE.findall(str(connector["endpoint"]))
    backend_names = PATH_PLACEHOLDER_RE.findall(str(connector["backend"]["url_pattern"]))
    if len(endpoint_names) != len(set(endpoint_names)):
        raise ValueError(f"connector {connector_id} repeats an endpoint path placeholder")
    if len(backend_names) != len(set(backend_names)):
        raise ValueError(f"connector {connector_id} repeats a backend path placeholder")
    if set(endpoint_names) != expected or set(backend_names) != expected:
        raise ValueError(
            f"connector {connector_id} path placeholders must exactly match path_parameters"
        )
    for name, raw_spec in specs.items():
        pattern = str(raw_spec["pattern"])
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"connector {connector_id} has invalid path regex for {name}: {exc}"
            ) from exc


def validate_method_policy(connector: Mapping[str, Any], enabled: bool) -> None:
    connector_id = str(connector["id"])
    endpoint_method = str(connector["method"])
    backend_method = str(connector["backend"].get("method", endpoint_method))
    if backend_method != endpoint_method:
        raise ValueError(
            f"connector {connector_id} must use the same endpoint and backend method"
        )
    if enabled and endpoint_method == "POST" and connector.get("write_approved") is not True:
        raise ValueError(
            f"enabled POST connector {connector_id} requires write_approved=true"
        )


def validate_secret_policy(connector: Mapping[str, Any]) -> None:
    connector_id = str(connector["id"])
    secret_header = connector.get("secret_header")
    secret_query = connector.get("secret_query")
    if isinstance(secret_header, Mapping) and isinstance(secret_query, Mapping):
        raise ValueError(
            f"connector {connector_id} may use only one secret injection mechanism"
        )
    if isinstance(secret_header, Mapping):
        secret_name = str(secret_header["name"]).casefold()
        forwarded = {
            str(name).casefold() for name in connector.get("input_headers", [])
        }
        if secret_name in forwarded:
            raise ValueError(
                f"connector {connector_id} exposes its secret header to clients"
            )
    if isinstance(secret_query, Mapping):
        secret_name = str(secret_query["name"])
        forwarded = {str(name) for name in connector.get("input_query_strings", [])}
        if secret_name in forwarded:
            raise ValueError(
                f"connector {connector_id} exposes its secret query parameter to clients"
            )


def _circuit_breaker(
    connector: Mapping[str, Any], resilience: Mapping[str, Any]
) -> dict[str, Any]:
    override = resilience.get("circuit_breaker")
    values = copy.deepcopy(DEFAULT_CIRCUIT_BREAKER)
    if isinstance(override, Mapping):
        values.update(override)
    return {
        "interval": int(values["interval"]),
        "timeout": int(values["timeout"]),
        "max_errors": int(values["max_errors"]),
        "name": f"cb-{connector['id']}",
        "log_status_change": bool(values["log_status_change"]),
    }


def _rate_limit(resilience: Mapping[str, Any]) -> dict[str, Any] | None:
    raw = resilience.get("rate_limit")
    if not isinstance(raw, Mapping):
        return None
    max_rate = float(raw["max_rate"])
    capacity = int(raw.get("capacity", max(1, round(max_rate))))
    return {
        "max_rate": max_rate,
        "every": str(raw.get("every", "1s")),
        "capacity": capacity,
    }


def render_endpoint(
    connector: Mapping[str, Any],
) -> tuple[dict[str, Any], str | None, str | None]:
    backend_spec = connector["backend"]
    resilience = backend_spec.get("resilience")
    if not isinstance(resilience, Mapping):
        resilience = {}

    backend_extra: dict[str, Any] = {
        "qos/circuit-breaker": _circuit_breaker(connector, resilience),
    }
    rate_limit = _rate_limit(resilience)
    if rate_limit:
        backend_extra["qos/ratelimit/proxy"] = rate_limit

    backend: dict[str, Any] = {
        "host": [backend_spec["host"]],
        "url_pattern": backend_spec["url_pattern"],
        "method": backend_spec.get("method", connector["method"]),
        "encoding": backend_spec.get("encoding", "json"),
        "extra_config": backend_extra,
    }
    if backend_spec.get("allow"):
        backend["allow"] = list(backend_spec["allow"])

    env_name: str | None = None
    injection: str | None = None
    secret_header = connector.get("secret_header")
    secret_query = connector.get("secret_query")
    if isinstance(secret_header, Mapping):
        env_name = str(secret_header["env"])
        injection = "header"
        if not ENV_NAME_RE.fullmatch(env_name):
            raise ValueError(f"invalid secret environment variable name: {env_name}")
        backend_extra["modifier/martian"] = {
            "header.Modifier": {
                "scope": ["request"],
                "name": secret_header["name"],
                "value": f"__API_CENTER_ENV_{env_name}__",
            }
        }
    elif isinstance(secret_query, Mapping):
        env_name = str(secret_query["env"])
        injection = "query"
        if not ENV_NAME_RE.fullmatch(env_name):
            raise ValueError(f"invalid secret environment variable name: {env_name}")
        backend_extra["modifier/martian"] = {
            "querystring.Modifier": {
                "scope": ["request"],
                "name": secret_query["name"],
                "value": f"__API_CENTER_ENV_{env_name}__",
            }
        }

    endpoint: dict[str, Any] = {
        "endpoint": connector["endpoint"],
        "method": connector["method"],
        "output_encoding": connector.get("output_encoding", "json"),
        "backend": [backend],
    }
    if connector.get("timeout"):
        endpoint["timeout"] = connector["timeout"]
    if connector.get("input_query_strings"):
        endpoint["input_query_strings"] = list(connector["input_query_strings"])
    if connector.get("input_headers"):
        endpoint["input_headers"] = list(connector["input_headers"])
    return endpoint, env_name, injection


def build() -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    base = load_json(BASE_PATH)
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    Draft202012Validator.check_schema(schema)
    reject_literal_secrets(base)

    endpoints: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    env_names: set[str] = set()
    route_keys: set[tuple[str, str]] = set()
    connector_ids: set[str] = set()

    for path in sorted(CONNECTORS_DIR.glob("*.connector.json")):
        connector = load_json(path)
        errors = sorted(
            validator.iter_errors(connector),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            rendered = "; ".join(
                f"{'.'.join(str(item) for item in error.absolute_path) or '$'}: "
                f"{error.message}"
                for error in errors[:20]
            )
            raise ValueError(f"{path.name}: {rendered}")
        reject_literal_secrets(connector)
        connector_id = connector["id"]
        if connector_id in connector_ids:
            raise ValueError(f"duplicate connector id: {connector_id}")
        connector_ids.add(connector_id)
        enabled = bool(connector["enabled"])
        validate_backend_host(connector_id, connector["backend"]["host"], enabled)
        validate_forwarded_headers(connector_id, connector.get("input_headers"))
        validate_path_parameter_policy(connector)
        validate_method_policy(connector, enabled)
        validate_secret_policy(connector)
        row = {
            "id": connector_id,
            "file": f"connectors/{path.name}",
            "enabled": enabled,
            "endpoint": connector["endpoint"],
            "method": connector["method"],
            "path_parameter_names": sorted(
                str(name) for name in (connector.get("path_parameters") or {})
            ),
            "write_approved": bool(connector.get("write_approved")),
            "backend_host": connector["backend"]["host"],
            "secret_environment_variable": None,
            "secret_injection": None,
            "default_circuit_breaker": True,
            "backend_rate_limit": bool(
                connector["backend"].get("resilience", {}).get("rate_limit")
            ),
            "ssrf_static_policy": "public-host-or-loopback-test-only",
            "connector_sha256": sha256(connector),
        }
        if enabled:
            key = (connector["method"], connector["endpoint"])
            if key in route_keys:
                raise ValueError(f"duplicate enabled route: {key[0]} {key[1]}")
            route_keys.add(key)
            endpoint, env_name, injection = render_endpoint(connector)
            endpoints.append(endpoint)
            row["secret_environment_variable"] = env_name
            row["secret_injection"] = injection
            if env_name:
                env_names.add(env_name)
        manifest_rows.append(row)

    result = copy.deepcopy(base)
    result["endpoints"] = endpoints
    return result, manifest_rows, sorted(env_names)


def write_outputs(
    template_path: Path, validation_path: Path, manifest_path: Path
) -> None:
    config, rows, env_names = build()
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    ) + "\n"
    validation = rendered
    for env_name in env_names:
        quoted_placeholder = json.dumps(f"__API_CENTER_ENV_{env_name}__")
        rendered = rendered.replace(
            quoted_placeholder,
            f'{{{{ env "{env_name}" | quote }}}}',
        )
        validation = validation.replace(
            quoted_placeholder,
            json.dumps("VALIDATION_DUMMY_SECRET"),
        )
    template_path.write_text(rendered, encoding="utf-8")
    validation_path.write_text(validation, encoding="utf-8")
    manifest = {
        "version": 4,
        "connector_count": len(rows),
        "enabled_connector_count": sum(bool(row["enabled"]) for row in rows),
        "required_secret_environment_variables": env_names,
        "connector_policy": {
            "default_method": "GET",
            "enabled_post_requires_write_approved": True,
            "put_patch_delete_allowed": False,
            "dangerous_forwarded_headers_allowed": False,
            "client_supplied_secret_parameters_allowed": False,
            "path_parameters_require_regex_and_encoding": True,
            "private_literal_ip_targets_allowed": False,
            "dns_rebinding_requires_runtime_egress_controls": True,
        },
        "connectors": rows,
        "validation_config_sha256": hashlib.sha256(
            validation.encode("utf-8")
        ).hexdigest(),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default=str(HERE / "krakend.tmpl"))
    parser.add_argument("--validation", default=str(HERE / "krakend.validation.json"))
    parser.add_argument("--manifest", default=str(HERE / "connector-manifest.json"))
    args = parser.parse_args()
    write_outputs(Path(args.template), Path(args.validation), Path(args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
