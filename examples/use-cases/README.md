# JUB Client — Use Cases

Practical, runnable examples for the five most common indexing workflows.

---

## Prerequisites

```sh
pip install poetry
poetry install
poetry shell
```

Set your connection details as environment variables (or let the scripts fall back to the defaults):

```sh
export JUB_API_URL="http://localhost:5000"
export JUB_USERNAME="invitado"
export JUB_PASSWORD="invitado"
```

---

## Overview

| Script | What it does |
|--------|-------------|
| `1_full_observatory_setup.py` | Full async provisioning: setup → catalogs → products → upload → complete |
| `2_catalog_indexing.py` | Create catalogs in bulk (from code or from `catalogs.json`) and assign to an existing observatory |
| `3_product_indexing.py` | Add products in bulk to an existing observatory and upload their chart files |
| `4_datasource_and_records.py` | Register a data source, ingest records (from `records.json`), and query with the DSL |
| `5_service_indexing.py` | Index a full service tree (building block → pattern → stage → workflow → service) |

---

## Use Case 1 — Full Observatory Setup

Observatories are **created in disabled state** so that their catalogs and products can be
indexed before they appear to end users. The setup task acts as a gate: the observatory
only becomes active after you call `complete_task` with `success=True`.

```
setup_observatory()          →  observatory created (disabled) + task_id returned
bulk_assign_catalogs()       →  spatial, interest, and temporal catalogs created and linked
bulk_assign_products()       →  products created with catalog item tags
upload_product() × N         →  chart/report files attached to each product
complete_task(success=True)  →  observatory enabled and visible to users
```

**Run:**

```sh
python 1_full_observatory_setup.py
```

When to use this pattern: any time you are provisioning a brand-new observatory from scratch.

---

## Use Case 2 — Catalog Indexing

Creates one or more catalogs and links them to an **already existing** observatory.
Useful when extending an observatory with new dimensions (a new geographic level,
a new interest group, a new time series).

You can define catalogs directly in code **or** load them from `catalogs.json`:

```sh
python 2_catalog_indexing.py                     # loads catalogs.json
python 2_catalog_indexing.py --from-code         # uses inline Python definitions
```

`catalogs.json` contains three catalogs: biological sex, age groups, and report years.
Edit it to match your own data model.

---

## Use Case 3 — Product Indexing

Adds products to an **already existing** observatory in bulk, then uploads a chart or
report file for each product. Use this after your catalogs are already in place.

```sh
python 3_product_indexing.py
```

The script also shows how to add extra catalog item tags to an existing product after
it has been created.

---

## Use Case 4 — Data Source Registration and Record Ingestion

Registers a CSV or database data source, ingests records in batch, and shows how to
query them using the JUB DSL.

Records can be loaded from `records.json` (edit the `spatial_id`, `temporal_id`, and
`interest_ids` fields to match the catalog item IDs from your observatory).

```sh
python 4_datasource_and_records.py
```

### DSL quick reference

| Prefix | Purpose | Example |
|--------|---------|---------|
| `VS` | Spatial filter | `VS(CDMX)` |
| `VT` | Temporal filter | `VT(>= 2020)` |
| `VI` | Interest filter | `VI(C_MAMA AND MUJER)` |
| `VO` | Metric / aggregation | `VO(AVG(TASA_100K))` |
| `BY` | Group-by dimension | `BY(CIE10_CANCER)` |
| `SVC` | Service search | `SVC(name=cancer,public=true)` |

---

## Use Case 5 — Service Indexing

Creates the full service hierarchy (building block → pattern → stage → workflow → service)
in a **single one-shot request** using `index_service`. Alternatively, the script shows
the equivalent step-by-step construction if you need to reuse existing components.

```sh
python 5_service_indexing.py
```

Services are discoverable via `search_services()` using the `SVC()` DSL operator.
