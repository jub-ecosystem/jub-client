# Copyright (C) 2026  Jesus Ignacio Castillo Barrios
#
# This file is part of jub_client (MADTEC-2025-M-478).
#
# jub_client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jub_client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jub_client.  If not, see <https://www.gnu.org/licenses/>.

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