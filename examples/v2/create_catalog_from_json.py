from jub.client.v2 import JubClient


client = JubClient(api_url="http://localhost:5000",username="invitado3", password="invitado")


if __name__ == "__main__":
    import asyncio

    async def main():
        # Create a catalog from a JSON file
        # with open("example_catalog.json", "r") as f:
            # catalog_json = f.read()
        result = await client.create_bulk_catalogs_from_json(json_path="./catalogs.json")
        if result.is_err:
            e = result.unwrap_err()
            print(dir(e))
            print(e.response.content)
            print(f"Error creating catalog: {e}")
        # print(result)

    asyncio.run(main())