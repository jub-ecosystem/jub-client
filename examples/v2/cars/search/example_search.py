"""
Search examples — JUB API v2.

The JUB DSL uses dimension prefixes to filter and aggregate car data:
  VS(<value>)          — Spatial filter  (country where car was built)
  VT(>= <year>)        — Temporal filter (production year range)
  VI(<value> AND/OR …) — Interest filter (brand, color, motor type)
  VO(COUNT()/AVG(x))   — Observable aggregation
  BY(<dimension>)      — Grouping for aggregations

Examples in this file use the Cars Observatory to answer questions like:
  "How many electric cars were produced in Germany since 2022?"
  "Show a bar chart of car counts grouped by brand in Japan."

Covers: search, search_records, generate_plot,
        search_observatories, search_services.

Run:
    python examples/v2/cars/search/example_search.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Optional: scope queries to a specific observatory.
OBSERVATORY_ID = "<your-observatory-id>"  # set to None to search all


async def main():
    client = await get_client()

    # --- 1. Full-text search: electric cars from Germany since 2022 ---
    search_result = await client.search(
        DTO.SearchQueryDTO(
            query="jub.v1.VS(DE).VT(>= 2022).VI(ELECTRIC)",
            observatory_id=OBSERVATORY_ID,
            limit=10,
        )
    )
    print_result("search / VS(DE).VT(>= 2022).VI(ELECTRIC)", search_result)

    # --- 2. Search raw records: Toyota or Honda, Japan, 2022 ----------
    records_result = await client.search_records(
        DTO.SearchQueryDTO(
            query="jub.v1.VS(JP).VT(>= 2022).VI(TOYOTA OR HONDA)",
            observatory_id=OBSERVATORY_ID,
            limit=20,
        )
    )
    print_result("search_records / VS(JP).VT(>= 2022).VI(TOYOTA OR HONDA)", records_result)

    # --- 3. Search across all countries (no spatial filter) -----------
    all_electric = await client.search_records(
        DTO.SearchQueryDTO(
            query="jub.v1.VI(ELECTRIC)",
            limit=50,
        )
    )
    print_result("search_records / VI(ELECTRIC) — all countries", all_electric)

    # --- 4. Generate a bar chart: car count by brand in Japan ---------
    plot_result = await client.generate_plot(
        DTO.PlotQueryDTO(
            query="jub.v1.VS(JP).VO(COUNT()).BY(CAR_BRAND)",
            observatory_id=OBSERVATORY_ID,
            chart_type="bar",
        )
    )
    print_result("generate_plot / VS(JP).VO(COUNT()).BY(CAR_BRAND)", plot_result)

    # --- 5. Generate a pie chart: distribution of motor types worldwide
    motor_pie = await client.generate_plot(
        DTO.PlotQueryDTO(
            query="jub.v1.VO(COUNT()).BY(MOTOR_TYPE)",
            chart_type="pie",
        )
    )
    print_result("generate_plot / VO(COUNT()).BY(MOTOR_TYPE)", motor_pie)

    # --- 6. Search observatories matching Germany (spatial) -----------
    obs_result = await client.search_observatories(
        DTO.SearchQueryDTO(
            query="jub.v1.VS(DE)",
            limit=5,
        )
    )
    print_result("search_observatories / VS(DE)", obs_result)

    # --- 7. Search services by name -----------------------------------
    # Requires at least one service to exist (see services example).
    services_result = await client.search_services(
        DTO.ServiceQueryDTO(
            query="jub.v1.SVC(name=cars)",
            limit=10,
        )
    )
    print_result("search_services / SVC(name=cars)", services_result)


if __name__ == "__main__":
    asyncio.run(main())
