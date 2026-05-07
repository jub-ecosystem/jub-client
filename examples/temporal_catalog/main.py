from jub import JubClient,JubClientBuilder
import asyncio

async def main():
    maybe_client = await JubClientBuilder()\
    .with_api_url("http://localhost:5000/api/v2")\
    .with_credentials("invitado","invitado")\
    .build()
    if maybe_client.is_err:
        print("Error creating client:", maybe_client.err())
        return
    client = maybe_client.unwrap()
    result = await client.create_catalog_from_json(
        json_path="./examples/temporal_catalog/temporal_subset.json"
    )
    if result.is_err:
        print("Error creating catalog:", result.err())
    else:
        print("Catalog created successfully:", result.unwrap())


    

if __name__ == "__main__":
    asyncio.run(main())