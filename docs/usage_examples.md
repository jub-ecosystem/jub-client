#Usage examples

<h2>Create a catalog</h2>
First,create an instance of the Jub Client:
```python
from jub.client import JubClient

jub_client = JubClient(
    hostname = "localhost",
    port     = 5000
)
```
Next, define the `Catalog` model :

```python
from jub.dto import Catalog

catalog = Catalog(
    display_name = "Test catalog",
    items = [],
    kind = "Temporal",
)

```
Now create the catalog using the client : 

```python
result = jub_client.create_catalog(catalog=catalog)

if result.is_ok:
    catalog_id = result.unwrap()
    print(f"Catalog created with id: {catalog_id}")
else:
    error = result.unwrap_err()
    print(f"Failed to create catalog: {error}")
```

<h2>Register an Observatory</h2>
First, create an `Observatory` instance : 
```python
from jub.dto import Observatory
observatory = Observatory(
    title = "Observatory 1",
    description = "This is an observatory",
    catalogs = [] 
)
```
Then call the client method `create_observatory()`: 
```python
result = jub_client.create_observatory(observatory=observatory)
if result.is_ok:
    observatory_id = result.unwrap()
    print(f"Observatory succesfuly created with ID : {observatory_id}")
else:
    error = result.unwrap_err()
    print(f"Failed to create the observatory: {error}")
```

<h2>Indexing Products</h2>
We can create and init a collection of products for future storage : 
```python
from jub.dto import Product
products = [
     Product(
                pid="product1",
                description="Some description",
                level_path="iz33bpdsfepc3jejsgfll.producttypex",
                levels=[
                    Level(
                        index=0,
                        cid="iz33bpdsfepc3jejsgfll",
                        value="C00",
                        kind="INTEREST"
                    ),
                    Level(
                        index=1,
                        cid="producttypex",
                        value="MAP",
                        kind="INTEREST"
                    )
                ],
                product_name="Product 1",
                profile="C00.MAP",
                product_type="PRODUCT",
            )    
            # .....
]
```
Then we can call the client method `create_products()` : 

```python
result = jub_client.create_products(prodcuts = products)

if result.is_ok:
    success = result.unwrap()
    print("The products were created succesful")
else:
    error = result.unwrap_err()
    print(f"Failed to create the products: {error}")
```
