from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

API_ROOT = "https://data.cms.gov/provider-data/api/1"
HOSPITAL_GENERAL_INFORMATION_ID = "xubh-q36u"


def get_metadata(
    dataset_id: str = HOSPITAL_GENERAL_INFORMATION_ID,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    http = session or requests.Session()
    url = f"{API_ROOT}/metastore/schemas/dataset/items/{dataset_id}"
    response = http.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def select_csv_distribution(metadata: dict[str, Any]) -> dict[str, Any]:
    distributions = metadata.get("distribution") or []
    if isinstance(distributions, dict):
        distributions = [distributions]

    candidates: list[dict[str, Any]] = []
    for item in distributions:
        media = str(item.get("mediaType", "")).lower()
        fmt = str(item.get("format", "")).lower()
        url = str(item.get("downloadURL", ""))
        title = str(item.get("title", "")).lower()
        if not url:
            continue
        is_csv = (
            media in {"text/csv", "application/csv"}
            or fmt == "csv"
            or url.lower().endswith(".csv")
            or "csv" in title
        )
        if is_csv:
            candidates.append(item)

    if not candidates:
        raise RuntimeError("CMS metadata did not contain a CSV download distribution")
    return candidates[0]


def resolve_csv_url(dataset_id: str = HOSPITAL_GENERAL_INFORMATION_ID) -> str:
    metadata = get_metadata(dataset_id)
    return str(select_csv_distribution(metadata)["downloadURL"])


def download_csv(url: str, destination: Path, session: requests.Session | None = None) -> int:
    http = session or requests.Session()
    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with http.get(url, stream=True, timeout=180) as response:
        response.raise_for_status()
        with destination.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                total += len(chunk)
    return total
