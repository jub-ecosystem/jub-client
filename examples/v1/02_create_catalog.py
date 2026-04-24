# Copyright 2026 MADTEC-2025-M-478 Project Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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