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