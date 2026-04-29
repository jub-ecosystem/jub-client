# Cars Observatory — JUB Client v2 Examples

A complete set of runnable examples that exercise every operation of the
JUB API v2 client, organised around a **World Automotive Manufacturing
Observatory** as the domain narrative.

## Domain model

The observatory tracks car production using three STORI dimensions:

| Dimension | Catalog value         | Items (examples)                              |
|-----------|-----------------------|-----------------------------------------------|
| SPATIAL   | `MANUFACTURING_COUNTRY` | MX, DE, JP, US, KR                          |
| TEMPORAL  | `PRODUCTION_YEAR`       | Y2020, Y2021, Y2022, Y2023, Y2024           |
| INTEREST  | `CAR_BRAND`             | TOYOTA, BMW, FORD, HONDA, VW                |
| INTEREST  | `CAR_COLOR`             | RED, BLUE, BLACK, WHITE, SILVER             |
| INTEREST  | `MOTOR_TYPE`            | GASOLINE, ELECTRIC, HYBRID, DIESEL          |

## Folder structure

```
cars/
  common.py                    # shared client factory and helpers
  users/
    example_users.py           # signup, authenticate, profile, settings
  catalogs/
    example_catalogs.py        # create, bulk create, list, get
  catalog_items/
    example_catalog_items.py   # CRUD, aliases, hierarchy, catalog linking
  observatories/
    example_observatories.py   # CRUD, setup flow, catalog/product linking, bulk
  products/
    example_products.py        # CRUD, tags, upload, download
  datasources/
    example_datasources.py     # register, ingest records, DSL query
  search/
    example_search.py          # search, records, plot, observatories, services
  tasks/
    example_tasks.py           # stats, list, get, complete, retry
  notifications/
    example_notifications.py   # list, mark read, clear
  building_blocks/
    example_building_blocks.py # CRUD
  patterns/
    example_patterns.py        # CRUD
  stages/
    example_stages.py          # CRUD
  workflows/
    example_workflows.py       # CRUD, cascade delete
  services/
    example_services.py        # create, index (full tree), CRUD
```

## Setup

```sh
# 1. Install dependencies
pip install poetry && poetry install && poetry shell

# 2. Edit common.py — set API_URL, USERNAME, PASSWORD
#    API_URL = "http://localhost:8000"

# 3. Run a specific example
python examples/v2/cars/catalogs/example_catalogs.py
```

## Recommended run order

Run in this order so that IDs from earlier steps can be pasted into later ones:

1. `users/example_users.py`
2. `catalogs/example_catalogs.py`
3. `catalog_items/example_catalog_items.py`
4. `observatories/example_observatories.py`
5. `products/example_products.py`
6. `datasources/example_datasources.py`
7. `search/example_search.py`
8. `tasks/example_tasks.py`
9. `notifications/example_notifications.py`
10. `building_blocks/example_building_blocks.py`
11. `patterns/example_patterns.py`
12. `stages/example_stages.py`
13. `workflows/example_workflows.py`
14. `services/example_services.py`

## JUB DSL quick reference (Cars domain)

```
# All electric cars made in Germany since 2022
jub.v1.VS(DE).VT(>= 2022).VI(ELECTRIC)

# Toyota or Honda cars from Japan
jub.v1.VS(JP).VI(TOYOTA OR HONDA)

# Count all cars grouped by brand
jub.v1.VO(COUNT()).BY(CAR_BRAND)

# Average engine displacement for gasoline cars in Mexico
jub.v1.VS(MX).VI(GASOLINE).VO(AVG(engine_cc)).BY(CAR_BRAND)
```
