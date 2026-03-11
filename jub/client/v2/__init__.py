from option import Err, Ok, Result
import requests as R

from jub.dto.v2 import Observatory
class JubClient(object):

    def __init__(self,hostname:str, port:int=-1):
        self.base_url = "https://{}/v2".format(hostname) if port == -1 else "http://{}:{}/v2".format(hostname,port)
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
        