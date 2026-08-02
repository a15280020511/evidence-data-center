#!/usr/bin/env python3
"""Bounded public-only Hugging Face Hub intelligence provider."""
from __future__ import annotations

import dataclasses
import json
import re
import signal
import sys
import time
from contextlib import contextmanager
from datetime import date, datetime
from enum import Enum
from itertools import islice
from pathlib import Path
from typing import Any, Mapping

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    bytes_sha,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
HUB_ORIGIN = "https://huggingface.co"
REPO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,95})?$")
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$")
SORT_MODELS = {"trendingScore", "downloads", "likes", "createdAt", "lastModified"}
SORT_DATASETS = SORT_MODELS
SORT_SPACES = {"trendingScore", "likes", "createdAt", "lastModified"}
REPO_TYPES = {"model", "dataset", "space"}


class OperationTimeout(TimeoutError):
    """Raised when the bounded Hub call exceeds the ticket timeout."""


@contextmanager
def bounded_call(seconds: int):
    def handler(_signum: int, _frame: Any) -> None:
        raise OperationTimeout(f"Hugging Face Hub call exceeded {seconds} seconds")

    previous = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def text(
    parameters: Mapping[str, Any],
    name: str,
    maximum: int,
    *,
    required: bool = False,
) -> str | None:
    raw = parameters.get(name)
    if raw in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    value = str(raw).strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValueError(f"{name} is invalid")
    return value


def repo_id(parameters: Mapping[str, Any]) -> str:
    value = str(text(parameters, "repo_id", 193, required=True))
    if not REPO_ID_RE.fullmatch(value):
        raise ValueError("repo_id must be a valid public Hugging Face repository id")
    return value


def repo_type(parameters: Mapping[str, Any]) -> str:
    value = str(text(parameters, "repo_type", 16, required=True)).lower()
    if value not in REPO_TYPES:
        raise ValueError("repo_type must be model, dataset, or space")
    return value


def revision(parameters: Mapping[str, Any]) -> str | None:
    value = text(parameters, "revision", 100)
    if value is not None and not REVISION_RE.fullmatch(value):
        raise ValueError("revision is invalid")
    return value


def safe_path(value: Any, *, required: bool = False) -> str | None:
    if value in (None, ""):
        if required:
            raise ValueError("path is required")
        return None
    rendered = str(value)
    if len(rendered) > 300 or rendered.startswith("/") or any(ord(char) < 32 for char in rendered):
        raise ValueError("path is invalid")
    parts = rendered.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path must be normalized and relative")
    return rendered


def to_plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return to_plain(value.value)
    if isinstance(value, Path):
        return str(value)
    if dataclasses.is_dataclass(value):
        return to_plain(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_plain(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return to_plain(value.to_dict())
        except TypeError:
            pass
    if hasattr(value, "__dict__"):
        return {
            str(key): to_plain(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    if hasattr(value, "item"):
        try:
            return to_plain(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return to_plain(value.tolist())
        except Exception:
            pass
    return str(value)


def ensure_public(value: Any) -> None:
    plain = to_plain(value)
    rows = plain if isinstance(plain, list) else [plain]
    for row in rows:
        if isinstance(row, Mapping) and row.get("private") is True:
            raise RuntimeError("private Hugging Face repositories are forbidden by this provider")


def optional_sort(parameters: Mapping[str, Any], allowed: set[str]) -> str | None:
    value = text(parameters, "sort", 32)
    if value is not None and value not in allowed:
        raise ValueError("sort is not allowlisted")
    return value


def execute_operation(
    api: HfApi,
    operation: str,
    parameters: Mapping[str, Any],
    timeout: int,
) -> tuple[Any, str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return {"provider": provider_row(CATALOG_PATH)}, "local-catalog"

    with bounded_call(timeout):
        if operation == "models-search":
            limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
            result = list(
                islice(
                    api.list_models(
                        search=text(parameters, "query", 100),
                        author=text(parameters, "author", 96),
                        pipeline_tag=text(parameters, "task", 80),
                        library=text(parameters, "library", 80),
                        sort=optional_sort(parameters, SORT_MODELS),
                        limit=limit,
                        gated=parameters.get("gated") if isinstance(parameters.get("gated"), bool) else None,
                        token=False,
                    ),
                    limit,
                )
            )
            ensure_public(result)
            return result, "list_models"

        if operation == "model-info":
            result = api.model_info(
                repo_id(parameters),
                revision=revision(parameters),
                files_metadata=False,
                token=False,
                timeout=timeout,
            )
            ensure_public(result)
            return result, "model_info"

        if operation == "model-security":
            result = api.model_info(
                repo_id(parameters),
                revision=revision(parameters),
                securityStatus=True,
                files_metadata=False,
                token=False,
                timeout=timeout,
            )
            ensure_public(result)
            return result, "model_info_securityStatus"

        if operation == "datasets-search":
            limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
            result = list(
                islice(
                    api.list_datasets(
                        search=text(parameters, "query", 100),
                        author=text(parameters, "author", 96),
                        language=text(parameters, "language", 32),
                        task_categories=text(parameters, "task_category", 80),
                        sort=optional_sort(parameters, SORT_DATASETS),
                        limit=limit,
                        gated=parameters.get("gated") if isinstance(parameters.get("gated"), bool) else None,
                        token=False,
                    ),
                    limit,
                )
            )
            ensure_public(result)
            return result, "list_datasets"

        if operation == "dataset-info":
            result = api.dataset_info(
                repo_id(parameters),
                revision=revision(parameters),
                files_metadata=False,
                token=False,
                timeout=timeout,
            )
            ensure_public(result)
            return result, "dataset_info"

        if operation == "spaces-search":
            limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
            result = list(
                islice(
                    api.list_spaces(
                        search=text(parameters, "query", 100),
                        author=text(parameters, "author", 96),
                        sort=optional_sort(parameters, SORT_SPACES),
                        limit=limit,
                        token=False,
                    ),
                    limit,
                )
            )
            ensure_public(result)
            return result, "list_spaces"

        if operation == "space-info":
            result = api.space_info(
                repo_id(parameters),
                revision=revision(parameters),
                files_metadata=False,
                token=False,
                timeout=timeout,
            )
            ensure_public(result)
            return result, "space_info"

        if operation == "repo-tree":
            limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=100, name="limit")
            path = safe_path(parameters.get("path"))
            result = list(
                islice(
                    api.list_repo_tree(
                        repo_id(parameters),
                        path_in_repo=path,
                        recursive=False,
                        expand=False,
                        revision=revision(parameters),
                        repo_type=repo_type(parameters),
                        token=False,
                    ),
                    limit,
                )
            )
            return result, "list_repo_tree"

        if operation == "repo-refs":
            result = api.list_repo_refs(
                repo_id(parameters),
                repo_type=repo_type(parameters),
                include_pull_requests=False,
                token=False,
            )
            return result, "list_repo_refs"

        if operation == "repo-paths-info":
            raw_paths = parameters.get("paths")
            if not isinstance(raw_paths, list) or not 1 <= len(raw_paths) <= 20:
                raise ValueError("paths must contain 1 to 20 entries")
            paths = [str(safe_path(item, required=True)) for item in raw_paths]
            if len(paths) != len(set(paths)):
                raise ValueError("paths must be unique")
            result = api.get_paths_info(
                repo_id(parameters),
                paths,
                repo_type=repo_type(parameters),
                revision=revision(parameters),
                expand=bool(parameters.get("expand", False)),
                token=False,
            )
            return result, "get_paths_info"

    raise ValueError(f"unsupported operation: {operation}")


def row_count(value: Any) -> int:
    plain = to_plain(value)
    if isinstance(plain, list):
        return len(plain)
    if isinstance(plain, Mapping):
        return 1
    return 0


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_HUGGINGFACE_FAILED"
    failure: dict[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "official_origin": HUB_ORIGIN,
        "public_repositories_only": True,
        "authentication_used": False,
        "secret_values_exposed": False,
        "hub_method_calls_per_ticket_max": 1,
        "automatic_pagination": False,
        "recursive_repository_listing": False,
        "inference_or_training": False,
        "operation": operation,
    }
    try:
        api = HfApi(
            endpoint=HUB_ORIGIN,
            token=False,
            library_name="intelligence-center-huggingface",
            library_version="1",
        )
        result, method_name = execute_operation(api, operation, parameters, timeout)
        plain = to_plain(result)
        snapshot = {
            "provider": "huggingface-hub",
            "operation": operation,
            "row_count": row_count(plain),
            "data": plain,
        }
        raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        if len(raw) > max_bytes:
            raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
        metadata.update(
            {
                "upstream_called": operation != "catalog-capabilities",
                "hub_method": method_name,
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "row_count": row_count(plain),
            }
        )
        status = "INTEL_HUGGINGFACE_COMPLETED"
    except HfHubHTTPError as exc:
        response = getattr(exc, "response", None)
        failure = {
            "type": type(exc).__name__,
            "message": str(exc)[:1800],
            "http_status": getattr(response, "status_code", None),
        }
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="huggingface-hub",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-huggingface]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="huggingface-hub-ticket-status-v1",
            display_name="Hugging Face Hub",
        )
    )
