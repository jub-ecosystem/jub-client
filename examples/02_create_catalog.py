import time as T
import sys 
from jub.client import JubClient,LevelCatalog,Catalog
from uuid import uuid4

oca_client = JubClient(
    hostname = "localhost",
    port     = 5000
)


def main():
    catalog = Catalog.from_json("/home/nacho/Programming/Python/oca-client/data/catalogs/sex.json")
    result = oca_client.create_catalog(catalog)
    if result.is_ok:
        cid = result.unwrap()
        print(f"Catalog created with ID: {cid}")
        obid = sys.argv[1]

        catalogs = [
            LevelCatalog(level=0, cid=cid),
        ]
        update_res = oca_client.update_observatory_catalogs(
            obid     = obid,
            catalogs = catalogs
        )
        print("Updating observatory catalogs..", update_res)
    else:
        print(f"Failed to create catalog: {result.unwrap_err()}")


if __name__ == "__main__":
    main()