import time as T
from jub.client import JubClient,Observatory
from uuid import uuid4

oca_client = JubClient(
    hostname = "localhost",
    port     = 5000
)


def main():
    observatory = Observatory(
        obid        = uuid4().hex,
        title       = "Test Observatory",
        description = "This is a test observatory",
        image_url   = "",
        catalogs    = []
    )
    result = oca_client.create_observatory(observatory)
    if result.is_ok:
        print(f"Observatory created with ID: {result.unwrap()}")
    else:
        print(f"Failed to create observatory: {result.unwrap_err()}")


if __name__ == "__main__":
    main()