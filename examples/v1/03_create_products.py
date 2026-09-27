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
import sys 
from jub.client import JubClient,LevelCatalog,Product,Level
from uuid import uuid4

oca_client = JubClient(
    hostname = "localhost",
    port     = 5000
)


def main():
    obid = sys.argv[1]
    cid = sys.argv[2]
    p = Product(
            pid         = uuid4().hex.replace("-",""),
            description = "No description yet.",
            level_path  = "CIE10.SEX.PLOT_TYPE",
            levels      = [
                Level(
                    cid   = cid,
                    index = 0,
                    kind  = "INTEREST",
                    value = "HOMBRE",
                )
            ],
            product_name = "Test Product",
            product_type = "PRODUCT_TYPE",
            profile      = "HOMBRE",
            tags         = [obid],
            url          = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzFsdnlsNGY3ZGFwNjhmeTRhYWU3eG1jMDMxZ2t2dmE3Yjg2NjFoZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/VbnUQpnihPSIgIXuZv/giphy.gif",
    )
    
    result = oca_client.create_products(products=[p])
    if result.is_ok:
        print("Products created successfully")
    else:
        print(f"Failed to create products: {result.unwrap_err()}")


if __name__ == "__main__":
    main()