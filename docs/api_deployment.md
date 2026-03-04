# API Deployment

When running `deploy.sh`, two Docker containers are created :

* Jub API
    The API service listens on port 5000 by default.
* A Mongo database
    The database service listens on port 27017 by default

Both ports can be configured in the `.env.dev` file through the variables `JUB_PORT` and `JUB_MONGODB_PORT`.

<h2>Base URL</h2>
When a `JubClient` instance is created , it builds a base URL using the provided initialization parameters.

Example :

```python
from jub import JubClient
client = JubClient(hostname = "localhost",port = 5000)
``` 
Given these parameters, the client constructs the base URL in the following format : 

`http://localhost:5000`

The client uses the [**HTTP**](https://en.wikipedia.org/wiki/HTTP) scheme by default. If [**HTTPS**](https://en.wikipedia.org/wiki/HTTPS) is required, this must be explicitly configured (for example, passing a full base URL)

All endpoint URLs are derived from this base URL. For example :

* Observatories
    `http://localhost:5000/observatories`

* Catalogs
    `http://localhost:5000/catalogs`

* Products
    `http://localhost:5000/products`

<h2>Sending a request</h2>

For this request example we will create a new Observatory, first initalize the corresponding DTO :

```python
from jub.dto import Observatory
obs = Observatory(
    title="Test Observatory",
    description="This is a test observatory",
    catalogs=[]
)
```
Then call the `create_observatory()` method : 
```python
response = client.create_observatory(observatory=obs)
```

Internally, this method:

1. Serializes the observatory model using `model_dump()`.
2. Performs an HTTP POST request to `/observatories`.
3. Sends the serialiezd model as the JSON body of the request.

The method returns the API response, the ID of the Observatory created.