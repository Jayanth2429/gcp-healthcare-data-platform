# Data Sources

## CMS Hospital General Information

- **Publisher:** Centers for Medicare & Medicaid Services (CMS)
- **Catalog:** CMS Provider Data Catalog
- **Dataset:** Hospital General Information
- **Stable dataset identifier:** `xubh-q36u`
- **Public access level:** public
- **Catalog page:** https://data.cms.gov/provider-data/dataset/xubh-q36u
- **Metadata API root used by this project:** `https://data.cms.gov/provider-data/api/1`

CMS describes this dataset as a list of hospitals registered with Medicare and includes fields such as address, hospital type, ownership, emergency services, and overall hospital rating.

The project does **not** commit the source CSV. At runtime it resolves the current CSV distribution from CMS metadata, which avoids pinning the code to a rotating download URL.

This repository is an independent portfolio project and is not affiliated with or endorsed by CMS.
