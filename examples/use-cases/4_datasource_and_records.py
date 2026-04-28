"""
Use Case 4 — Data Source Registration and Record Ingestion

Shows how to:
  1. Register a data source (CSV, database, or S3-backed)
  2. Ingest data records in batch from records.json
  3. Query the records using the JUB DSL
  4. Generate an aggregated ECharts plot

Records in records.json use placeholder strings like "<catalog_item_id:CDMX>"
for spatial_id, temporal_id, and interest_ids. Replace those with real catalog
item IDs from your observatory before running.

Run:
    python 4_datasource_and_records.py

Environment variables (optional):
    JUB_API_URL   — API base URL    (default: http://localhost:5000)
    JUB_USERNAME  — Login username  (default: invitado)
    JUB_PASSWORD  — Login password  (default: invitado)
"""

import asyncio
import os

from jub.client.v2 import JubClient, JubClientBuilder
import jub.dto.v2 as DTO
from dotenv import load_dotenv

JUB_CLIENT_ENV_FILE_PATH = os.environ.get("JUB_CLIENT_ENV_FILE_PATH", ".env")
if os.path.exists(JUB_CLIENT_ENV_FILE_PATH):
    load_dotenv(JUB_CLIENT_ENV_FILE_PATH)
    print(f"Loaded environment variables from {JUB_CLIENT_ENV_FILE_PATH!r}")


# ── Step 1: Register a data source ───────────────────────────────────────────

async def register_datasource(client: JubClient) -> str:
    """
    POST /api/v2/datasources

    Registers a new data source. The format field tells the API how records
    are stored (csv, json, postgres, mysql, mongodb).

    connection_uri is optional. Use it for database-backed sources. For file
    sources (csv, json) the data is pushed via the /records endpoint instead.

    Returns the source_id.
    """
    print("\n[Step 1] Registering data source...")

    result = await client.register_data_source(DTO.DataSourceCreateDTO(
        name           = "Cancer Mortality Records — Mexico 2018–2023",
        description    = (
            "Row-level mortality data disaggregated by state, year, biological sex, "
            "and CIE-10 diagnosis group. Source: SINAIS / INCAN."
        ),
        format         = "csv",
        # connection_uri = "s3://my-bucket/cancer/mortality.csv",  # uncomment for S3
    ))

    if result.is_err:
        raise RuntimeError(f"register_data_source failed: {result.unwrap_err()}")

    source = result.unwrap()
    print(f"  Data source ID : {source.source_id}")
    print(f"  Name           : {source.name}")
    print(f"  Format         : {source.format}")
    return source.source_id


# ── Step 2: Ingest records ────────────────────────────────────────────────────

async def ingest_records(client: JubClient, source_id: str) -> None:
    """
    POST /api/v2/datasources/{source_id}/records

    Ingests a batch of data records from records.json. Each record is identified
    by a deterministic record_id so that re-ingestion is idempotent.

    For large datasets split the data into batches of 1 000–10 000 records
    and call this endpoint once per batch.
    """
    print("\n[Step 2] Ingesting records from records.json...")

    json_path = os.path.join(os.path.dirname(__file__), "records.json")

    result = await client.ingest_records_from_json(source_id, json_path=json_path)
    if result.is_err:
        raise RuntimeError(f"ingest_records failed: {result.unwrap_err()}")

    print(f"  Inserted : {result.unwrap().inserted} record(s)")


async def ingest_records_from_code(client: JubClient, source_id: str) -> None:
    """
    POST /api/v2/datasources/{source_id}/records  (inline variant)

    Same as above but defines records directly in Python. Use this when your
    records are generated from a database query or a pandas DataFrame.
    """
    print("\n[Step 2] Ingesting records from code...")

    result = await client.ingest_records(source_id, [
        DTO.DataRecordCreateDTO(
            # record_id must be deterministic so that re-runs are idempotent
            record_id               = "rec_cdmx_2022_mujer_mama",
            # Replace with the real catalog_item_id values from your observatory
            spatial_id              = "<catalog_item_id:CDMX>",
            temporal_id             = "2022-01-01T00:00:00Z",
            interest_ids            = ["<catalog_item_id:MUJER>", "<catalog_item_id:C_MAMA>"],
            numerical_interest_ids  = {"TASA_100K": 28.4, "CASOS": 1842},
            raw_payload             = {"estado": "CDMX", "anio": 2022, "dx_cie10": "C50"},
        ),
        DTO.DataRecordCreateDTO(
            record_id               = "rec_jalisco_2022_mujer_mama",
            spatial_id              = "<catalog_item_id:JALISCO>",
            temporal_id             = "2022-01-01T00:00:00Z",
            interest_ids            = ["<catalog_item_id:MUJER>", "<catalog_item_id:C_MAMA>"],
            numerical_interest_ids  = {"TASA_100K": 24.7, "CASOS": 2103},
            raw_payload             = {"estado": "Jalisco", "anio": 2022, "dx_cie10": "C50"},
        ),
    ])

    if result.is_err:
        raise RuntimeError(f"ingest_records failed: {result.unwrap_err()}")

    print(f"  Inserted : {result.unwrap().inserted} record(s)")


# ── Step 3: Query records ─────────────────────────────────────────────────────

async def query_records(client: JubClient, source_id: str) -> None:
    """
    POST /api/v2/datasources/{source_id}/query

    Runs a JUB DSL filter query against the records of this data source.
    Returns raw record dicts (no hydration, no aggregation).

    DSL reference:
      VS(<item>)           spatial filter
      VT(>= <year>)        temporal filter (also <, <=, >, =)
      VI(<item>)           interest filter (supports AND / OR)
    """
    print("\n[Step 3] Querying records with DSL...")

    result = await client.query_records(
        source_id,
        DTO.DataSourceQueryDTO(
            query = "jub.v1.VS(CDMX).VT(>= 2021).VI(C_MAMA)",
            limit = 50,
            skip  = 0,
        ),
    )
    if result.is_err:
        raise RuntimeError(f"query_records failed: {result.unwrap_err()}")

    records = result.unwrap()
    print(f"  Records returned : {len(records)}")
    if records:
        print(f"  First record     : {records[0]}")


# ── Step 4: Generate a plot ───────────────────────────────────────────────────

async def generate_plot(client: JubClient) -> None:
    """
    POST /api/v2/search/plot

    Runs a DSL aggregation query across all data sources visible to your
    account and returns an ECharts-compatible JSON configuration. Feed this
    directly into an ECharts instance in the browser.

    DSL aggregation operators:
      VO(COUNT())           count records in each group
      VO(AVG(<field>))      average of a numerical_interest_id field
      VO(SUM(<field>))      sum
      BY(<catalog_value>)   group-by dimension
    """
    print("\n[Step 4] Generating aggregated plot...")

    result = await client.generate_plot(DTO.PlotQueryDTO(
        query      = "jub.v1.VS(MX).VI(C_MAMA OR C_OVARIO).VO(AVG(TASA_100K)).BY(CIE10_CANCER)",
        chart_type = "bar",
    ))
    if result.is_err:
        raise RuntimeError(f"generate_plot failed: {result.unwrap_err()}")

    chart_config = result.unwrap()
    print(f"  ECharts config keys : {list(chart_config.keys())}")
    # Pass chart_config to an ECharts instance:
    # echarts.init(dom).setOption(chart_config)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    result = await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "invitado"),
        password = os.environ.get("JUB_PASSWORD", "invitado"),
    ).build()
    if result.is_err:
        raise result.unwrap_err()

    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")

    source_id = await register_datasource(client)
    await ingest_records(client, source_id)         # from JSON file
    # await ingest_records_from_code(client, source_id)  # alternative: inline
    await query_records(client, source_id)
    await generate_plot(client)

    print(f"\nDone. Data source ID: {source_id}")


if __name__ == "__main__":
    asyncio.run(main())
