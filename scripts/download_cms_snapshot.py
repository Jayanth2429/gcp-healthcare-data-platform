#!/usr/bin/env python3
"""Download a live CMS hospital snapshot locally without requiring GCP."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.platform.cms import HOSPITAL_GENERAL_INFORMATION_ID, get_metadata, select_csv_distribution, download_csv
from src.platform.hashing import sha256_file

metadata = get_metadata(HOSPITAL_GENERAL_INFORMATION_ID)
distribution = select_csv_distribution(metadata)
source_url = str(distribution["downloadURL"])
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
destination = Path("data/raw") / f"hospital_general_information_{stamp}.csv"
size = download_csv(source_url, destination)
print(f"saved: {destination}")
print(f"bytes: {size}")
print(f"sha256: {sha256_file(destination)}")
print(f"source: {source_url}")
