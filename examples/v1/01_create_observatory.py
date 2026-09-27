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