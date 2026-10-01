#!/usr/bin/env python3
from src.platform.cms import HOSPITAL_GENERAL_INFORMATION_ID, get_metadata, select_csv_distribution

metadata = get_metadata(HOSPITAL_GENERAL_INFORMATION_ID)
distribution = select_csv_distribution(metadata)
print(f"dataset_id: {HOSPITAL_GENERAL_INFORMATION_ID}")
print(f"title: {metadata.get('title')}")
print(f"csv_url: {distribution.get('downloadURL')}")
