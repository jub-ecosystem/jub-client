# Jub Client

<div align="center">
    <img src="assets/logo.svg" alt="Jub Client Logo" width="260" />
    <p><em>Official async Python client for the JUB API v2</em></p>
</div>

**jub_client** gives you a fully-typed, async Python interface to the JUB national data hub. It follows the STORI model — organising information into **Observatories**, **Catalogs**, and **Products** across Spatial, Temporal, Observable, Reference, and Interest dimensions.

---

## What you can do

- Authenticate once and let the client attach the JWT to every request automatically.
- Create and manage Observatories, Catalogs, Catalog Items, and Products.
- Ingest, query, and search data records via the JUB DSL.
- Build automated pipelines with Services, Workflows, Stages, Patterns, and Building Blocks.
- Get back strongly-typed Pydantic models — or `Err(exception)` if something goes wrong.

## Design principles

Every client method returns `Result[T, Exception]` from the [`option`](https://pypi.org/project/option/) library. The client **never raises**; callers always check `.is_ok` or `.is_err`.

```python
result = await client.list_catalogs()
if result.is_ok:
    catalogs = result.unwrap()   # List[CatalogSummaryDTO]
else:
    error = result.unwrap_err()  # Exception
```

## Documentation

<div class="grid cards" markdown>

-   **Installation**

    Get the library running on your machine.

    [Go to Installation](installation.md)

-   **Getting Started**

    Authenticate and make your first API call in minutes.

    [Go to Getting Started](getting-started.md)

-   **API Reference**

    Full documentation for every client method and DTO.

    [Go to API Reference](api-reference.md)

-   **Examples**

    Complete, runnable code for common workflows.

    [Go to Examples](usage_examples.md)

</div>
