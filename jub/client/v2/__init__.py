
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
import os

import httpx
import jub.config as CX
import logging
from option import Err, Ok, Result
from jub.dto.v2 import Observatory
from jub.log import Log

log = Log(
    name                   = __name__ ,
    path                   = CX.JUB_CLIENT_LOG_PATH ,
    file_handler_filter    = lambda record: record.levelno == logging.INFO
)

class JubClient(object):

    def __init__(self,api_url:str):
        self.base_url = "{}/api/v2".format(api_url)
        self.observatories_url = "{}/observatories".format(self.base_url)
        self.catalogs_url = "{}/catalogs".format(self.base_url)
        self.products_url = "{}/products".format(self.base_url)
        self.parse_url = "{}/code".format(self.base_url)
    
    async def create_from_code(self, file_path: str = None, yaml_string: str = None) -> Result[bool, Exception]:
        """
        Sends YAML data to the server-side parser.
        Accepts either a physical file path or a raw YAML string.
        """
        if not file_path and not yaml_string:
            return Err(ValueError("You must provide either 'file_path' or 'yaml_string'."))

        try:
            # 1. Prepare the file data and filename
            if file_path:
                if not os.path.exists(file_path):
                    return Err(FileNotFoundError(f"Could not find file at {file_path}"))
                
                with open(file_path, "rb") as f:
                    file_content = f.read()
                filename = os.path.basename(file_path)
            else:
                # Convert the raw string into bytes so httpx treats it like a file
                file_content = yaml_string.encode('utf-8')
                filename = "payload.yml"

            # 2. Structure the multipart/form-data payload
            # Format: {"field_name": ("file_name", file_bytes, "content_type")}
            files = {
                "file": (filename, file_content, "application/x-yaml")
            }

            # 3. Send the request
            async with httpx.AsyncClient(verify=False) as http_client:
                response = await http_client.post(self.parse_url, files=files)
                response.raise_for_status()
                
            return Ok(True)

        except Exception as e:
            return Err(e)    

    async def create_observatory(self, observatory: Observatory) -> Result[str, Exception]:
        """
        Creates a new observatory resource asynchronously.
        
        Args:
            observatory (Observatory):
                A valid V2 Observatory model instance.
                
        Returns:
            Ok(str):
                The generated or provided observatory ID if the
                request completes successfully.

            Err(Exception):
                Wraps any exception raised during request executing,
                including network errors and HTTP status validation failures (e.g. 4xx or 5xx responses).
        """
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(self.observatories_url, json=observatory.model_dump())
                response.raise_for_status()
                # Assuming the API returns the observatory ID in a JSON body or string
                return Ok(response.text) 
        except Exception as e:
            return Err(e)