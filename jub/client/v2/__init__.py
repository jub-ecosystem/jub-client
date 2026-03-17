
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
import requests as R
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
        # self.base_url = "https://{}/v2".format(hostname) if port == -1 else "http://{}:{}/v2".format(hostname,port)
        self.base_url = "{}/v2".format(api_url)
        self.observatories_url = "{}/observatories".format(self.base_url)
        self.catalogs_url = "{}/catalogs".format(self.base_url)
        self.products_url = "{}/products".format(self.base_url)
        pass
    def create_observatory(self,observatory : Observatory) -> Result[str,Exception]:
        """
        Receives a 
        
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
            response = R.post(self.observatories_url,json=observatory.model_dump())
            response.raise_for_status()
            return Ok(response)
        except Exception as e:
            return Err(e)
        