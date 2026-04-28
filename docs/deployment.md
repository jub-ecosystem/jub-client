# Deployment

Running `deploy.sh` starts the services required by the client:

```bash
chmod +x deploy.sh
./deploy.sh
```

This spins up two Docker containers:

| Container | Default port | Configured via |
|---|---|---|
| **JUB API** | `5000` | `JUB_PORT` in `.env.dev` |
| **MongoDB** | `27017` | `JUB_MONGODB_PORT` in `.env.dev` |

---

## Connecting the client

Pass the API base URL when creating `JubClient`. The client appends `/api/v2` automatically.

```python
from jub.client.v2 import JubClient

client = JubClient(
    api_url  = "http://localhost:5000",
    username = "admin",
    password = "secret",
)
await client.authenticate()
```

Given `api_url="http://localhost:5000"`, the resolved endpoints are:

- Observatories → `http://localhost:5000/api/v2/observatories`
- Catalogs → `http://localhost:5000/api/v2/catalogs`
- Products → `http://localhost:5000/api/v2/products`
- … and so on for every resource group.

!!! note "HTTPS"
    The client uses HTTP by default. To use HTTPS, provide the full URL including `https://` and ensure the server has a valid certificate or configure `verify=False` in the underlying httpx client.

---

## Using JubClientBuilder

`JubClientBuilder` is a convenience builder that authenticates during construction and returns an already-authenticated client:

```python
from jub.client.v2 import JubClientBuilder
import os

result = await JubClientBuilder(
    api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
    username = os.environ.get("JUB_USERNAME", "admin"),
    password = os.environ.get("JUB_PASSWORD", "secret"),
).build()

if result.is_ok:
    client = result.unwrap()
else:
    raise result.unwrap_err()
```

The builder calls `authenticate()` internally. If authentication fails, `.build()` returns `Err(Exception)`.
