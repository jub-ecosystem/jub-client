
# Copyright 2026 MADTEC-2025-M-478 Project Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Full async client for the JUB API v2.

Usage:
    client = JubClient("http://localhost:8000", username="admin", password="secret")
    await client.authenticate()
    catalogs = await client.list_catalogs()
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Union

import httpx
from option import Ok, Err, Result
import jub.dto.v2 as DTO
from functools import wraps
from uuid import uuid4


class JubClientBuilder:
    """
    Builder for JubClient that handles asynchronous authentication during construction.

    Example:
        client = await JubClientBuilder(
            api_url="http://localhost:8000",
            username="admin",
            password="secret"
        ).build()
    """

    def __init__(self, api_url: Optional[str] = "", username: Optional[str] ="", password: Optional[str]=""):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.client = JubClient(api_url, username, password)
    
    def with_api_url(self, api_url: str) -> JubClientBuilder:
        self.api_url = api_url
        return self
    def with_credentials(self, username: str,password:str) -> JubClientBuilder:
        self.username = username 
        self.password = password
        return self
    async def build(self) -> Result[JubClient, Exception]:
        client = JubClient(self.api_url, self.username, self.password)
        auth_result = await client.authenticate()
        if auth_result.is_ok:
            return Ok(client)
        else:
            return Err(Exception(f"Authentication failed: {auth_result.unwrap_err()}"))

def check_auth(func):
    @wraps(func)
    async def __inner(self, *args, **kwargs):
        if self._token is None:
            return Err(Exception("Client is not authenticated. Call authenticate() first."))
        return await func(self, *args, **kwargs)
    return __inner

class JubClient:
    """
    Async HTTP client for the JUB API v2.

    Authenticates on construction and attaches the JWT to every subsequent
    request via the Authorization header. All methods return Result[T, Exception],
    where Ok wraps the parsed JSON and Err wraps the raised exception.

    Example:
        client = JubClient("http://localhost:8000", "admin", "secret")
        await client.authenticate()
        result = await client.list_catalogs()
        if result.is_ok:
            print(result.unwrap())
    """

    def __init__(self, api_url: str, username: str, password: str,scope:Optional[str]=None, token_expiration:Optional[str]=None, renew_token:bool=True):
        base = f"{api_url.rstrip('/')}/api/v2"
        self.base_url = base
        self._username = username
        self._password = password
        self._token: Optional[str] = None

        self._users_url = f"{base}/users"
        self._catalogs_url = f"{base}/catalogs"
        self._catalog_items_url = f"{base}/catalog-items"
        self._datasources_url = f"{base}/datasources"
        self._search_url = f"{base}/search"
        self._observatories_url = f"{base}/observatories"
        self._products_url = f"{base}/products"
        self._tasks_url = f"{base}/tasks"
        self._notifications_url = f"{base}/notifications"
        self._building_blocks_url = f"{base}/building-blocks"
        self._patterns_url = f"{base}/patterns"
        self._stages_url = f"{base}/stages"
        self._workflows_url = f"{base}/workflows"
        self._services_url = f"{base}/services"
        self._code_url = f"{base}/code"
        self.user_id = None
        self.temporal_secret_key = None
        self.__scope = scope or "jub"
        self.__token_expiration = token_expiration or "1h"
        self.__renew_token = renew_token  # Automatically renew token on expiration

    # ── Internal helpers ───────────────────────────────────────

    def _validated(self, cls, response: Result) -> Result:
        """Parse a raw-dict Ok result into a typed DTO, or pass through Err."""
        if response.is_err:
            return response
        try:
            return Ok(cls.model_validate(response.unwrap()))
        except Exception as e:
            return Err(e)

    def _validated_list(self, cls, response: Result) -> Result:
        """Parse a raw-list Ok result into List[DTO], or pass through Err."""
        if response.is_err:
            return response
        try:
            return Ok([cls.model_validate(x) for x in response.unwrap()])
        except Exception as e:
            return Err(e)

    def _headers(self,headers:Dict[str,str]=None) -> Dict[str, str]:
        if headers is None:
            headers = {"Content-Type": "application/json"}

        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self.temporal_secret_key:
            headers["Temporal-Secret-Key"] = self.temporal_secret_key

        return headers

    def _client(self,headers:Dict[str,str]=None) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers(headers), verify=False)

    async def _get(self, url: str, params: Dict = None) -> Result[Any, Exception]:
        try:
            async with self._client() as c:
                r = await c.get(url, params=params)
                r.raise_for_status()
                return Ok(r.json())
        except Exception as e:
            return Err(e)

    async def _post(self, url: str, payload: Any = None, files: Any = None,headers:Dict[str,str]=None) -> Result[Any, Exception]:
        try:
            async with self._client(headers) as c:
                r = await c.post(url, json=payload, files=files)
                r.raise_for_status()
                return Ok(r.json())
        except Exception as e:
            print(e.response.text)
            return Err(e)

    async def _put(self, url: str, payload: Dict) -> Result[Any, Exception]:
        try:
            async with self._client() as c:
                r = await c.put(url, json=payload)
                r.raise_for_status()
                return Ok(r.json())
        except Exception as e:
            return Err(e)

    async def _delete(self, url: str, params: Dict = None) -> Result[Any, Exception]:
        try:
            async with self._client() as c:
                r = await c.delete(url, params=params)
                r.raise_for_status()
                return Ok(r.json())
        except Exception as e:
            return Err(e)

    async def _delete_no_content(self, url: str, params: Dict = None) -> Result[bool, Exception]:
        try:
            async with self._client() as c:
                r = await c.delete(url, params=params)
                r.raise_for_status()
                return Ok(True)
        except Exception as e:
            return Err(e)

    async def _put_no_content(self, url: str, payload: Dict) -> Result[bool, Exception]:
        try:
            async with self._client() as c:
                r = await c.put(url, json=payload)
                r.raise_for_status()
                return Ok(True)
        except Exception as e:
            return Err(e)

    async def _patch(self, url: str, payload: Dict) -> Result[Any, Exception]:
        try:
            async with self._client() as c:
                r = await c.patch(url, json=payload)
                r.raise_for_status()
                return Ok(r.json())
        except Exception as e:
            return Err(e)

    # ── Users  /users ──────────────────────────────────────────

    async def authenticate(self) -> Result[bool, Exception]:
        """
        POST /users/auth

        Logs in with the credentials provided at construction and stores the
        JWT token for all subsequent requests.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        try:
            async with httpx.AsyncClient(verify=False) as c:
                r = await c.post(
                    f"{self._users_url}/auth",
                    json={
                        "username": self._username, 
                        "password": self._password,
                        "scope": self.__scope,
                        "expiration": self.__token_expiration,
                        "renew_token": self.__renew_token
                    },
                )
                r.raise_for_status()
                response_json = r.json()
                # print(response_json)
                self.temporal_secret_key = response_json.get("temporal_secret_key")
                self._token = response_json.get("access_token")
                self.user_id = response_json.get("user_profile",{}).get("user_id",None)
                return Ok(True)
        except Exception as e:
            return Err(e)

    async def signup(self, dto: DTO.SignUpDTO) -> Result[DTO.AuthResponseDTO, Exception]:
        """
        POST /users/signup

        Creates a new user account via the external Xolo auth service.

        Args:
            dto: User registration payload.

        Returns:
            Ok(AuthResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.AuthResponseDTO, await self._post(f"{self._users_url}/signup", dto.model_dump()))

    @check_auth
    async def get_current_user(self) -> Result[DTO.UserProfileDTO, Exception]:
        """
        GET /users/me

        Returns the profile of the currently authenticated user.

        Returns:
            Ok(UserProfileDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.UserProfileDTO, await self._get(f"{self._users_url}/me"))

    async def get_user_settings(self, user_id: str) -> Result[DTO.UserPreferencesDTO, Exception]:
        """
        GET /users/{user_id}/settings

        Returns the preferences for the given user. Users can only access
        their own settings.

        Args:
            user_id: Target user identifier.

        Returns:
            Ok(UserPreferencesDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.UserPreferencesDTO, await self._get(f"{self._users_url}/{user_id}/settings"))

    async def update_user_settings(
        self, user_id: str, prefs: DTO.UserPreferencesDTO
    ) -> Result[DTO.UserPreferencesDTO, Exception]:
        """
        PUT /users/{user_id}/settings

        Replaces the preferences for the given user.

        Args:
            user_id: Target user identifier.
            prefs: New preferences payload.

        Returns:
            Ok(UserPreferencesDTO) on success, Err(exception) on failure.
        """
        return self._validated(
            DTO.UserPreferencesDTO,
            await self._put(f"{self._users_url}/{user_id}/settings", prefs.model_dump()),
        )

    # ── Catalogs  /catalogs ────────────────────────────────────

    async def create_catalog(
        self,
        dto: Union[DTO.CatalogCreateDTO, Dict],
    ) -> Result[DTO.CatalogCreatedResponseDTO, Exception]:
        """
        POST /catalogs

        Creates a single catalog with nested items, aliases, and hierarchy.

        Args:
            dto: CatalogCreateDTO instance or plain dict matching its schema.

        Returns:
            Ok(CatalogCreatedResponseDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.CatalogCreateDTO) else dto
        return self._validated(DTO.CatalogCreatedResponseDTO, await self._post(self._catalogs_url, payload))

    async def create_catalog_from_json(
        self,
        json_path: Optional[str] = None,
        json_string: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Result[DTO.CatalogCreatedResponseDTO, Exception]:
        """
        POST /catalogs (from JSON source)

        Convenience wrapper that loads a catalog payload from a file path,
        a raw JSON string, or an already-parsed dict.

        Args:
            json_path: Path to a JSON file containing the catalog payload.
            json_string: Raw JSON string containing the catalog payload.
            data: Already-parsed dict matching CatalogCreateDTO schema.

        Returns:
            Ok(CatalogCreatedResponseDTO) on success, Err(exception) on failure.
        """
        if data is not None:
            payload = data
        elif json_string is not None:
            payload = json.loads(json_string)
        elif json_path is not None:
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            return Err(ValueError("Provide json_path, json_string, or data."))
        return self._validated(DTO.CatalogCreatedResponseDTO, await self._post(self._catalogs_url, payload))

    async def create_bulk_catalogs_from_json(
        self,
        json_path: Optional[str] = None,
        json_string: Optional[str] = None,
        data: Optional[List[Dict]] = None,
    ) -> Result[DTO.CatalogCreatedBulkResponseDTO, Exception]:
        """
        POST /catalogs/bulk (from JSON source)

        Convenience wrapper that loads a list of catalog payloads from a file
        path, a raw JSON string, or an already-parsed list of dicts.

        Args:
            json_path: Path to a JSON file containing a list of catalog payloads.
            json_string: Raw JSON string containing a list of catalog payloads.
            data: Already-parsed list of dicts matching CatalogCreateDTO schema.

        Returns:
            Ok(CatalogCreatedBulkResponseDTO) on success, Err(exception) on failure.
        """
        if data is not None:
            payload = data
        elif json_string is not None:
            payload = json.loads(json_string)
        elif json_path is not None:
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            return Err(ValueError("Provide json_path, json_string, or data."))
        return self._validated(DTO.CatalogCreatedBulkResponseDTO, await self._post(f"{self._catalogs_url}/bulk", payload))

    async def list_catalogs(self) -> Result[List[DTO.CatalogSummaryDTO], Exception]:
        """
        GET /catalogs

        Returns a lightweight list of all catalogs.

        Returns:
            Ok(List[CatalogSummaryDTO]) on success, Err(exception) on failure.
        """
        return self._validated_list(DTO.CatalogSummaryDTO, await self._get(self._catalogs_url))

    async def get_catalog(self, catalog_id: str) -> Result[DTO.CatalogResponseDTO, Exception]:
        """
        GET /catalogs/{catalog_id}

        Returns the full catalog including its items and aliases.

        Args:
            catalog_id: Unique identifier of the catalog.

        Returns:
            Ok(CatalogResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.CatalogResponseDTO, await self._get(f"{self._catalogs_url}/{catalog_id}"))

    # ── Catalog items  /catalog-items ─────────────────────────

    async def create_catalog_item(
        self,
        dto: Union[DTO.CatalogItemStandaloneCreateDTO, Dict],
    ) -> Result[DTO.CatalogItemXResponseDTO, Exception]:
        """POST /catalog-items — Creates a standalone catalog item."""
        payload = (
            dto.model_dump()
            if isinstance(dto, DTO.CatalogItemStandaloneCreateDTO)
            else dto
        )
        return self._validated(DTO.CatalogItemXResponseDTO, await self._post(self._catalog_items_url, payload))

    async def list_catalog_items(
        self, limit: int = 100
    ) -> Result[List[DTO.CatalogItemXResponseDTO], Exception]:
        """GET /catalog-items — Returns a paginated list of catalog items."""
        return self._validated_list(DTO.CatalogItemXResponseDTO, await self._get(self._catalog_items_url, params={"limit": limit}))

    async def get_catalog_item(
        self, catalog_item_id: str
    ) -> Result[DTO.CatalogItemXResponseDTO, Exception]:
        """GET /catalog-items/{id} — Returns a single catalog item."""
        return self._validated(DTO.CatalogItemXResponseDTO, await self._get(f"{self._catalog_items_url}/{catalog_item_id}"))

    async def update_catalog_item(
        self,
        catalog_item_id: str,
        dto: Union[DTO.CatalogItemUpdateDTO, Dict],
    ) -> Result[DTO.CatalogItemXResponseDTO, Exception]:
        """PUT /catalog-items/{id} — Updates mutable fields."""
        payload = (
            dto.model_dump() if isinstance(dto, DTO.CatalogItemUpdateDTO) else dto
        )
        return self._validated(DTO.CatalogItemXResponseDTO, await self._put(f"{self._catalog_items_url}/{catalog_item_id}", payload))

    async def delete_catalog_item(
        self, catalog_item_id: str
    ) -> Result[DTO.CatalogItemDeleteResponseDTO, Exception]:
        """DELETE /catalog-items/{id} — Deletes a catalog item and its relationships."""
        return self._validated(DTO.CatalogItemDeleteResponseDTO, await self._delete(f"{self._catalog_items_url}/{catalog_item_id}"))

    async def list_catalog_item_aliases(
        self, catalog_item_id: str
    ) -> Result[List[DTO.CatalogItemAliasXResponseDTO], Exception]:
        """GET /catalog-items/{id}/aliases — Returns all aliases for an item."""
        return self._validated_list(DTO.CatalogItemAliasXResponseDTO, await self._get(f"{self._catalog_items_url}/{catalog_item_id}/aliases"))

    async def add_catalog_item_alias(
        self,
        catalog_item_id: str,
        dto: Union[DTO.CatalogItemAliasCreateDTO, Dict],
    ) -> Result[DTO.CatalogItemAliasXResponseDTO, Exception]:
        """POST /catalog-items/{id}/aliases — Adds an alias to an item."""
        payload = (
            dto.model_dump()
            if isinstance(dto, DTO.CatalogItemAliasCreateDTO)
            else dto
        )
        return self._validated(DTO.CatalogItemAliasXResponseDTO, await self._post(f"{self._catalog_items_url}/{catalog_item_id}/aliases", payload))

    async def delete_catalog_item_alias(self, catalog_item_id: str, alias_id: str) -> Result[bool, Exception]:
        """DELETE /catalog-items/{id}/aliases/{alias_id} — Removes an alias (204 No Content)."""
        return await self._delete_no_content(f"{self._catalog_items_url}/{catalog_item_id}/aliases/{alias_id}")

    async def list_catalog_item_children(self, catalog_item_id: str) -> Result[List[DTO.CatalogItemXResponseDTO], Exception]:
        """GET /catalog-items/{id}/children — Returns child items in the hierarchy."""
        return self._validated_list(DTO.CatalogItemXResponseDTO, await self._get(f"{self._catalog_items_url}/{catalog_item_id}/children"))

    async def link_catalog_item_child(
        self,
        catalog_item_id: str,
        dto: Union[DTO.CatalogItemChildLinkCreateDTO, Dict],
    ) -> Result[DTO.CatalogItemChildLinkResponseDTO, Exception]:
        """POST /catalog-items/{id}/children — Links a child item to this item."""
        payload = dto.model_dump() if isinstance(dto, DTO.CatalogItemChildLinkCreateDTO) else dto
        return self._validated(DTO.CatalogItemChildLinkResponseDTO, await self._post(f"{self._catalog_items_url}/{catalog_item_id}/children", payload))

    async def unlink_catalog_item_child(self, catalog_item_id: str, child_item_id: str) -> Result[bool, Exception]:
        """DELETE /catalog-items/{id}/children/{child_id} — Removes a child relationship (204 No Content)."""
        return await self._delete_no_content(f"{self._catalog_items_url}/{catalog_item_id}/children/{child_item_id}")

    async def list_catalogs_for_item(self, catalog_item_id: str) -> Result[List[DTO.CatalogXDTO], Exception]:
        """GET /catalog-items/{id}/catalogs — Returns catalogs that contain this item."""
        return self._validated_list(DTO.CatalogXDTO, await self._get(f"{self._catalog_items_url}/{catalog_item_id}/catalogs"))

    async def link_item_to_catalog(
        self,
        catalog_item_id: str,
        dto: Union[DTO.CatalogItemCatalogLinkCreateDTO, Dict],
    ) -> Result[DTO.CatalogItemCatalogLinkResponseDTO, Exception]:
        """POST /catalog-items/{id}/catalogs — Links this item to a catalog."""
        payload = dto.model_dump() if isinstance(dto, DTO.CatalogItemCatalogLinkCreateDTO) else dto
        return self._validated(DTO.CatalogItemCatalogLinkResponseDTO, await self._post(f"{self._catalog_items_url}/{catalog_item_id}/catalogs", payload))

    async def unlink_item_from_catalog(self, catalog_item_id: str, catalog_id: str) -> Result[bool, Exception]:
        """DELETE /catalog-items/{id}/catalogs/{catalog_id} — Removes item from a catalog (204 No Content)."""
        return await self._delete_no_content(f"{self._catalog_items_url}/{catalog_item_id}/catalogs/{catalog_id}")

    async def list_products_for_item(self, catalog_item_id: str) -> Result[DTO.ItemProductsDTO, Exception]:
        """GET /catalog-items/{id}/products — Returns product IDs tagged with this item."""
        return self._validated(DTO.ItemProductsDTO, await self._get(f"{self._catalog_items_url}/{catalog_item_id}/products"))

    # ── DataSources  /datasources ──────────────────────────────

    async def register_data_source(
        self,
        dto: Union[DTO.DataSourceCreateDTO, Dict],
    ) -> Result[DTO.DataSourceDTO, Exception]:
        """
        POST /datasources

        Registers a new data source and returns its DataSourceDTO with the
        system-generated source_id.

        Args:
            dto: DataSourceCreateDTO instance or plain dict.

        Returns:
            Ok(DataSourceDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.DataSourceCreateDTO) else dto
        response = await self._post(self._datasources_url, payload)
        if response.is_err:
            return response
        return Ok(DTO.DataSourceDTO.model_validate(response.unwrap()))

    async def register_data_source_from_json(
        self,
        json_path: Optional[str] = None,
        json_string: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Result[DTO.DataSourceDTO, Exception]:
        """
        POST /datasources (from JSON source)

        Convenience wrapper that loads a data source payload from a file path,
        a raw JSON string, or an already-parsed dict.

        Args:
            json_path: Path to a JSON file containing the DataSourceCreateDTO payload.
            json_string: Raw JSON string containing the DataSourceCreateDTO payload.
            data: Already-parsed dict matching DataSourceCreateDTO schema.

        Returns:
            Ok(DataSourceDTO) on success, Err(exception) on failure.
        """
        if data is not None:
            payload = data
        elif json_string is not None:
            payload = json.loads(json_string)
        elif json_path is not None:
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            return Err(ValueError("Provide json_path, json_string, or data."))
        return self._validated(DTO.DataSourceDTO, await self._post(self._datasources_url, payload))

    async def list_data_sources(self) -> Result[List[DTO.DataSourceDTO], Exception]:
        """GET /datasources — Returns all registered data sources."""
        return self._validated_list(DTO.DataSourceDTO, await self._get(self._datasources_url))

    async def get_data_source(self, source_id: str) -> Result[DTO.DataSourceDTO, Exception]:
        """GET /datasources/{id} — Returns a single data source."""
        return self._validated(DTO.DataSourceDTO, await self._get(f"{self._datasources_url}/{source_id}"))

    async def delete_data_source(self, source_id: str) -> Result[DTO.DataSourceDeleteResponseDTO, Exception]:
        """DELETE /datasources/{id} — Deletes a data source and all its records."""
        return self._validated(DTO.DataSourceDeleteResponseDTO, await self._delete(f"{self._datasources_url}/{source_id}"))

    async def ingest_records(
        self,
        source_id: str,
        records: List[Union[DTO.DataRecordCreateDTO, Dict]],
    ) -> Result[DTO.IngestResponseDTO, Exception]:
        """
        POST /datasources/{source_id}/records

        Ingests a batch of data records into the given data source.

        Args:
            source_id: Unique identifier of the target data source.
            records: List of DataRecordCreateDTO instances or plain dicts.

        Returns:
            Ok(IngestResponseDTO) on success, Err(exception) on failure.
        """
        payload = [
            r.model_dump() if isinstance(r, DTO.DataRecordCreateDTO) else r
            for r in records
        ]
        return self._validated(
            DTO.IngestResponseDTO,
            await self._post(f"{self._datasources_url}/{source_id}/records", payload),
        )

    async def ingest_records_from_json(
        self,
        source_id: str,
        json_path: Optional[str] = None,
        json_string: Optional[str] = None,
        data: Optional[List[Dict]] = None,
    ) -> Result[DTO.IngestResponseDTO, Exception]:
        """
        POST /datasources/{source_id}/records (from JSON source)

        Loads a JSON list of DataRecordCreateDTO dicts and ingests them.

        Args:
            source_id: Unique identifier of the target data source.
            json_path: Path to a JSON file containing a list of record payloads.
            json_string: Raw JSON string containing a list of record payloads.
            data: Already-parsed list of dicts matching DataRecordCreateDTO schema.

        Returns:
            Ok(IngestResponseDTO) on success, Err(exception) on failure.
        """
        if data is not None:
            payload = data
        elif json_string is not None:
            payload = json.loads(json_string)
        elif json_path is not None:
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            return Err(ValueError("Provide json_path, json_string, or data."))
        return self._validated(
            DTO.IngestResponseDTO,
            await self._post(f"{self._datasources_url}/{source_id}/records", payload),
        )

    async def query_records(
        self, source_id: str, dto: DTO.DataSourceQueryDTO
    ) -> Result[Any, Exception]:
        """
        POST /datasources/{source_id}/query

        Runs a JUB DSL query against the records of the given data source.

        Args:
            source_id: Unique identifier of the target data source.
            dto: Query payload with DSL string and pagination parameters.

        Returns:
            Ok(list of matching record dicts) on success, Err(exception) on failure.
        """
        return await self._post(
            f"{self._datasources_url}/{source_id}/query",
            dto.model_dump(),
        )

    # ── Observatories  /observatories ─────────────────────────

    async def create_observatory(
        self,
        dto: Union[DTO.ObservatoryCreateDTO, Dict],
    ) -> Result[DTO.ObservatoryXDTO, Exception]:
        """POST /observatories — Creates an immediately-enabled observatory."""
        payload = (
            dto.model_dump() if isinstance(dto, DTO.ObservatoryCreateDTO) else dto
        )
        return self._validated(DTO.ObservatoryXDTO, await self._post(self._observatories_url, payload))

    async def setup_observatory(
        self,
        dto: Union[DTO.ObservatorySetupDTO, Dict],
    ) -> Result[DTO.ObservatorySetupResponseDTO, Exception]:
        """
        POST /observatories/setup

        Creates a disabled observatory and queues a background setup task.
        The observatory is enabled only after the task completes successfully
        via complete_task().

        Args:
            dto: ObservatorySetupDTO instance or plain dict.

        Returns:
            Ok(ObservatorySetupResponseDTO) on success, Err(exception) on failure.
        """
        payload: Dict[str, Any] = dto.model_dump() if isinstance(dto, DTO.ObservatorySetupDTO) else dto
        payload["user_id"] = self.user_id
        payload["observatory_id"] = payload.get("observatory_id") or f"obs-{uuid4().hex[:8]}"
        return self._validated(DTO.ObservatorySetupResponseDTO, await self._post(f"{self._observatories_url}/setup", payload))

    async def list_observatories(
        self, page_index: int = 0, limit: int = 10
    ) -> Result[List[DTO.ObservatoryXDTO], Exception]:
        """GET /observatories — Returns a paginated list of observatories."""
        return self._validated_list(
            DTO.ObservatoryXDTO,
            await self._get(self._observatories_url, params={"page_index": page_index, "limit": limit}),
        )

    async def get_observatory(self, observatory_id: str) -> Result[DTO.ObservatoryXDTO, Exception]:
        """GET /observatories/{id} — Returns a single observatory."""
        return self._validated(DTO.ObservatoryXDTO, await self._get(f"{self._observatories_url}/{observatory_id}"))

    async def update_observatory(
        self,
        observatory_id: str,
        dto: Union[DTO.ObservatoryUpdateDTO, Dict],
    ) -> Result[DTO.ObservatoryXDTO, Exception]:
        """PUT /observatories/{id} — Updates mutable fields on an observatory."""
        payload = (
            dto.model_dump() if isinstance(dto, DTO.ObservatoryUpdateDTO) else dto
        )
        return self._validated(DTO.ObservatoryXDTO, await self._put(f"{self._observatories_url}/{observatory_id}", payload))

    async def delete_observatory(
        self, observatory_id: str
    ) -> Result[DTO.ObservatoryDeleteResponseDTO, Exception]:
        """DELETE /observatories/{id} — Deletes an observatory and its linked relationships."""
        return self._validated(DTO.ObservatoryDeleteResponseDTO, await self._delete(f"{self._observatories_url}/{observatory_id}"))

    async def link_catalog_to_observatory(
        self,
        observatory_id: str,
        dto: Union[DTO.LinkCatalogDTO, Dict],
    ) -> Result[DTO.ObservatoryCatalogLinkResponseDTO, Exception]:
        """
        POST /observatories/{observatory_id}/catalogs

        Links an existing catalog to the given observatory.

        Args:
            observatory_id: Unique identifier of the observatory.
            dto: LinkCatalogDTO with the catalog_id and display level.

        Returns:
            Ok(ObservatoryCatalogLinkResponseDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.LinkCatalogDTO) else dto
        return self._validated(
            DTO.ObservatoryCatalogLinkResponseDTO,
            await self._post(f"{self._observatories_url}/{observatory_id}/catalogs", payload),
        )

    async def list_observatory_catalogs(
        self, observatory_id: str
    ) -> Result[List[DTO.CatalogXDTO], Exception]:
        """GET /observatories/{id}/catalogs — Lists all linked catalogs."""
        return self._validated_list(
            DTO.CatalogXDTO,
            await self._get(f"{self._observatories_url}/{observatory_id}/catalogs"),
        )

    async def unlink_catalog_from_observatory(
        self, observatory_id: str, catalog_id: str
    ) -> Result[bool, Exception]:
        """
        DELETE /observatories/{observatory_id}/catalogs/{catalog_id}

        Removes the link between the given catalog and observatory (204 No Content).

        Args:
            observatory_id: Unique identifier of the observatory.
            catalog_id: Unique identifier of the catalog to unlink.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        return await self._delete_no_content(
            f"{self._observatories_url}/{observatory_id}/catalogs/{catalog_id}"
        )

    async def bulk_assign_catalogs(
        self,
        observatory_id: str,
        dto: Union[DTO.BulkCatalogsDTO, Dict],
    ) -> Result[DTO.BulkCatalogsResponseDTO, Exception]:
        """
        POST /observatories/{observatory_id}/catalogs/bulk

        Creates multiple catalogs and links each to the observatory in one request.

        Args:
            observatory_id: Unique identifier of the observatory.
            dto: BulkCatalogsDTO with a list of CatalogCreateDTO payloads.

        Returns:
            Ok(bulk_result_dict) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.BulkCatalogsDTO) else dto
        response = await self._post(
            f"{self._observatories_url}/{observatory_id}/catalogs/bulk", payload
        )
        if response.is_err:
            # Log error
            return response
        x = response.unwrap() 
        return Ok(DTO.BulkCatalogsResponseDTO.model_validate(x))


    async def list_observatory_products(
        self, observatory_id: str
    ) -> Result[List[DTO.ProductSimpleDTO], Exception]:
        """GET /observatories/{id}/products — Lists all linked products."""
        return self._validated_list(
            DTO.ProductSimpleDTO,
            await self._get(f"{self._observatories_url}/{observatory_id}/products"),
        )

    async def link_product_to_observatory(
        self,
        observatory_id: str,
        dto: Union[DTO.LinkProductDTO, Dict],
    ) -> Result[DTO.ObservatoryProductLinkResponseDTO, Exception]:
        """
        POST /observatories/{observatory_id}/products

        Links an existing product to the given observatory.

        Args:
            observatory_id: Unique identifier of the observatory.
            dto: LinkProductDTO with the product_id to link.

        Returns:
            Ok(ObservatoryProductLinkResponseDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.LinkProductDTO) else dto
        return self._validated(
            DTO.ObservatoryProductLinkResponseDTO,
            await self._post(f"{self._observatories_url}/{observatory_id}/products", payload),
        )

    async def unlink_product_from_observatory(
        self, observatory_id: str, product_id: str
    ) -> Result[bool, Exception]:
        """
        DELETE /observatories/{observatory_id}/products/{product_id}

        Removes the link between the given product and observatory (204 No Content).

        Args:
            observatory_id: Unique identifier of the observatory.
            product_id: Unique identifier of the product to unlink.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        return await self._delete_no_content(
            f"{self._observatories_url}/{observatory_id}/products/{product_id}"
        )

    async def bulk_assign_products(
        self,
        observatory_id: str,
        dto: Union[DTO.BulkProductsDTO, Dict],
    ) -> Result[DTO.BulkProductsResponseDTO, Exception]:
        """
        POST /observatories/{observatory_id}/products/bulk

        Creates multiple products and links each to the observatory in one request.

        Args:
            observatory_id: Unique identifier of the observatory.
            dto: BulkProductsDTO with a list of ProductCreateDTO payloads.

        Returns:
            Ok(bulk_result_dict) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.BulkProductsDTO) else dto
        response = await self._post(
            f"{self._observatories_url}/{observatory_id}/products/bulk", payload
        )
        if response.is_err:
            # Log error
            return response
        x = response.unwrap() 
        return Ok(DTO.BulkProductsResponseDTO.model_validate(x))

    # ── Products  /products ────────────────────────────────────

    async def create_product(
        self,
        dto: Union[DTO.ProductCreateDTO, Dict],
    ) -> Result[DTO.ProductSimpleDTO, Exception]:
        """POST /products — Creates a product linked to an observatory."""
        payload = dto.model_dump() if isinstance(dto, DTO.ProductCreateDTO) else dto
        return self._validated(DTO.ProductSimpleDTO, await self._post(self._products_url, payload,))

    async def list_products(self, limit: int = 100) -> Result[List[DTO.ProductSimpleDTO], Exception]:
        """GET /products — Returns a paginated list of products."""
        return self._validated_list(DTO.ProductSimpleDTO, await self._get(self._products_url, params={"limit": limit}))

    async def get_product(self, product_id: str) -> Result[DTO.ProductSimpleDTO, Exception]:
        """GET /products/{id} — Returns a single product."""
        return self._validated(DTO.ProductSimpleDTO, await self._get(f"{self._products_url}/{product_id}"))

    async def update_product(
        self,
        product_id: str,
        dto: Union[DTO.ProductUpdateDTO, Dict],
    ) -> Result[DTO.ProductSimpleDTO, Exception]:
        """PUT /products/{id} — Updates mutable fields on a product."""
        payload = dto.model_dump() if isinstance(dto, DTO.ProductUpdateDTO) else dto
        return self._validated(DTO.ProductSimpleDTO, await self._put(f"{self._products_url}/{product_id}", payload))

    async def delete_product(self, product_id: str) -> Result[DTO.ProductDeleteResponseDTO, Exception]:
        """DELETE /products/{id} — Deletes a product and its relationships."""
        return self._validated(DTO.ProductDeleteResponseDTO, await self._delete(f"{self._products_url}/{product_id}"))

    async def get_product_tags(self, product_id: str) -> Result[DTO.ProductTagsResponseDTO, Exception]:
        """
        GET /products/{product_id}/tags

        Returns the catalog item IDs associated with the given product.

        Args:
            product_id: Unique identifier of the product.

        Returns:
            Ok(ProductTagsResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.ProductTagsResponseDTO, await self._get(f"{self._products_url}/{product_id}/tags"))

    async def add_product_tags(
        self,
        product_id: str,
        dto: Union[DTO.TagProductDTO, Dict],
    ) -> Result[DTO.ProductTagsResponseDTO, Exception]:
        """
        POST /products/{product_id}/tags

        Associates catalog items with a product for search and filtering.

        Args:
            product_id: Unique identifier of the product.
            dto: TagProductDTO with list of catalog_item_ids to add.

        Returns:
            Ok(ProductTagsResponseDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.TagProductDTO) else dto
        return self._validated(DTO.ProductTagsResponseDTO, await self._post(f"{self._products_url}/{product_id}/tags", payload))

    async def remove_product_tag(
        self, product_id: str, catalog_item_id: str
    ) -> Result[bool, Exception]:
        """
        DELETE /products/{product_id}/tags/{catalog_item_id}

        Removes a catalog item tag from a product (204 No Content).

        Args:
            product_id: Unique identifier of the product.
            catalog_item_id: Unique identifier of the catalog item to detag.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        return await self._delete_no_content(
            f"{self._products_url}/{product_id}/tags/{catalog_item_id}"
        )

    async def upload_product(self, product_id: str, file_path: Union[str, bytes]) -> Result[DTO.ProductUploadResponseDTO, Exception]:
        """
        POST /products/{product_id}/upload

        Queues a file for background ingestion linked to the given product.

        Args:
            product_id: Unique identifier of the product.
            file_path: Path to the file to upload, or raw bytes.

        Returns:
            Ok(ProductUploadResponseDTO) on success, Err(exception) on failure.
        """
        if isinstance(file_path, bytes):
            file_content = file_path
            filename = f"{product_id}_upload"
        else:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                file_content = file.read()

        files = {"file": (filename, file_content, "application/octet-stream")}
        return self._validated(
            DTO.ProductUploadResponseDTO,
            await self._post(url=f"{self._products_url}/{product_id}/upload", files=files, headers={}),
        )

    async def get_product_tag_details(self, product_id: str) -> Result[List[DTO.CatalogItemXResponseDTO], Exception]:
        """GET /products/{product_id}/tags/details — Returns full catalog items for each tag."""
        return self._validated_list(DTO.CatalogItemXResponseDTO, await self._get(f"{self._products_url}/{product_id}/tags/details"))

    async def download_product(self, product_id: str) -> Result[bytes, Exception]:
        """GET /products/{product_id}/download — Downloads the product file as raw bytes."""
        try:
            async with self._client() as c:
                r = await c.get(f"{self._products_url}/{product_id}/download")
                r.raise_for_status()
                return Ok(r.content)
        except Exception as e:
            return Err(e)


    # ── Search  /search ────────────────────────────────────────

    async def search(self, dto: DTO.SearchQueryDTO) -> Result[Any, Exception]:
        """
        POST /search

        Runs a JUB DSL query and returns hydrated product results.

        Args:
            dto: SearchQueryDTO with DSL query and optional observatory scope.

        Returns:
            Ok(list of product dicts) on success, Err(exception) on failure.
        """
        return await self._post(self._search_url, dto.model_dump())

    async def search_records(
        self, dto: DTO.SearchQueryDTO
    ) -> Result[Any, Exception]:
        """
        POST /search/records

        Translates a JUB DSL query to a MongoDB filter and returns matching
        data records.

        Args:
            dto: SearchQueryDTO with DSL query and optional observatory scope.

        Returns:
            Ok(list of data record dicts) on success, Err(exception) on failure.
        """
        return await self._post(f"{self._search_url}/records", dto.model_dump())

    async def generate_plot(self, dto: DTO.PlotQueryDTO) -> Result[Any, Exception]:
        """
        POST /search/plot

        Runs a JUB DSL aggregation query and returns an ECharts-compatible
        JSON object. Use VO operators (COUNT, AVG, SUM) and BY for grouping.

        Example DSL:
            jub.v1.VS(MX).VI(C_MAMA OR C_OVARIO).VO(AVG(TASA_100K)).BY(CIE10_CANCER)

        Args:
            dto: PlotQueryDTO with DSL aggregation query and optional chart type.

        Returns:
            Ok(echarts_config_dict) on success, Err(exception) on failure.
        """
        return await self._post(f"{self._search_url}/plot", dto.model_dump())

    async def search_observatories(
        self, dto: DTO.SearchQueryDTO
    ) -> Result[Any, Exception]:
        """
        POST /search/observatories

        Runs a JUB DSL query scoped to the observatory dimension.

        Args:
            dto: SearchQueryDTO with DSL query.

        Returns:
            Ok(list of observatory dicts) on success, Err(exception) on failure.
        """
        return await self._post(
            f"{self._search_url}/observatories", dto.model_dump()
        )

    async def search_services(self, dto: DTO.ServiceQueryDTO) -> Result[List[DTO.ServiceDTO], Exception]:
        """
        POST /search/services

        Searches services using the JUB SVC() DSL operator.

        Args:
            dto: ServiceQueryDTO with DSL query and pagination parameters.

        Returns:
            Ok(List[ServiceDTO]) on success, Err(exception) on failure.
        """
        return self._validated_list(DTO.ServiceDTO, await self._post(f"{self._search_url}/services", dto.model_dump()))

    # ── Tasks  /tasks ──────────────────────────────────────────

    async def get_task_stats(self) -> Result[DTO.TasksStatsDTO, Exception]:
        """GET /tasks/stats — Returns task counts grouped by status."""
        return self._validated(DTO.TasksStatsDTO, await self._get(f"{self._tasks_url}/stats"))

    async def list_my_tasks(
        self, limit: int = 50
    ) -> Result[List[DTO.TaskXDTO], Exception]:
        """GET /tasks — Returns recent background tasks for the authenticated user."""
        return self._validated_list(DTO.TaskXDTO, await self._get(self._tasks_url, params={"limit": limit}))

    async def get_task(self, task_id: str) -> Result[DTO.TaskXDTO, Exception]:
        """GET /tasks/{id} — Returns details of a single background task."""
        return self._validated(DTO.TaskXDTO, await self._get(f"{self._tasks_url}/{task_id}"))

    async def complete_task(
        self,
        task_id: str,
        dto: Union[DTO.TaskCompleteDTO, Dict],
    ) -> Result[DTO.TaskCompleteResponseDTO, Exception]:
        """POST /tasks/{id}/complete — Marks a task done and enables its observatory on success."""
        payload = dto.model_dump() if isinstance(dto, DTO.TaskCompleteDTO) else dto
        return self._validated(DTO.TaskCompleteResponseDTO, await self._post(f"{self._tasks_url}/{task_id}/complete", payload))

    async def retry_task(self, task_id: str) -> Result[bool, Exception]:
        """PUT /tasks/{task_id}/retry — Retries a failed task (204 No Content)."""
        return await self._put_no_content(f"{self._tasks_url}/{task_id}/retry", {})

    # ── Code / YAML seed  /code ────────────────────────────────

    async def create_from_code(
        self,
        file_path: Optional[str] = None,
        yaml_string: Optional[str] = None,
    ) -> Result[bool, Exception]:
        """
        POST /code

        Uploads a YAML file to fully seed the database with catalogs, observatories,
        and products in a single request. The YAML is validated against the JubFile
        Pydantic schema on the server.

        Args:
            file_path: Path to a .yml or .yaml file on disk.
            yaml_string: Raw YAML string to upload directly.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        if not file_path and not yaml_string:
            return Err(ValueError("Provide file_path or yaml_string."))
        try:
            if file_path:
                if not os.path.exists(file_path):
                    return Err(FileNotFoundError(f"File not found: {file_path}"))
                with open(file_path, "rb") as f:
                    content = f.read()
                filename = os.path.basename(file_path)
            else:
                content = yaml_string.encode("utf-8")
                filename = "payload.yml"

            files = {"file": (filename, content, "application/x-yaml")}
            auth_headers = (
                {"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            async with httpx.AsyncClient(headers=auth_headers, verify=False) as c:
                r = await c.post(self._code_url, files=files)
                r.raise_for_status()
            return Ok(True)
        except Exception as e:
            return Err(e)

    # ── Notifications  /notifications ──────────────────────────

    async def list_notifications(
        self, unread_only: bool = False, limit: int = 50
    ) -> Result[List[DTO.NotificationDTO], Exception]:
        """
        GET /notifications

        Returns the current user's notifications.

        Args:
            unread_only: When True, returns only unread notifications.
            limit: Maximum number of notifications to return (default 50).

        Returns:
            Ok(List[NotificationDTO]) on success, Err(exception) on failure.
        """
        return self._validated_list(
            DTO.NotificationDTO,
            await self._get(self._notifications_url, params={"unread_only": unread_only, "limit": limit}),
        )

    async def mark_notification_read(self, notification_id: str) -> Result[bool, Exception]:
        """
        PUT /notifications/{notification_id}/read

        Marks a single notification as read (204 No Content).

        Args:
            notification_id: Unique identifier of the notification.

        Returns:
            Ok(True) on success, Err(exception) on failure.
        """
        return await self._put_no_content(f"{self._notifications_url}/{notification_id}/read", {})

    async def mark_all_notifications_read(self) -> Result[DTO.NotificationReadAllResponseDTO, Exception]:
        """
        PUT /notifications/read-all

        Marks all unread notifications as read for the current user.

        Returns:
            Ok(NotificationReadAllResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.NotificationReadAllResponseDTO, await self._put(f"{self._notifications_url}/read-all", {}))

    async def clear_read_notifications(self) -> Result[DTO.NotificationClearReadResponseDTO, Exception]:
        """
        DELETE /notifications/clear-read

        Deletes all previously read notifications for the current user.

        Returns:
            Ok(NotificationClearReadResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(DTO.NotificationClearReadResponseDTO, await self._delete(f"{self._notifications_url}/clear-read"))

    # ── Building blocks  /building-blocks ─────────────────────

    async def create_building_block(
        self,
        dto: Union[DTO.BuildingBlockCreateDTO, Dict],
    ) -> Result[DTO.BuildingBlockDTO, Exception]:
        """POST /building-blocks — Creates a new containerised unit of work."""
        payload = dto.model_dump() if isinstance(dto, DTO.BuildingBlockCreateDTO) else dto
        return self._validated(DTO.BuildingBlockDTO, await self._post(self._building_blocks_url, payload))

    async def list_building_blocks(
        self, skip: int = 0, limit: int = 100
    ) -> Result[List[DTO.BuildingBlockDTO], Exception]:
        """GET /building-blocks — Returns a paginated list of building blocks."""
        return self._validated_list(
            DTO.BuildingBlockDTO,
            await self._get(self._building_blocks_url, params={"skip": skip, "limit": limit}),
        )

    async def get_building_block(self, building_block_id: str) -> Result[DTO.BuildingBlockDTO, Exception]:
        """GET /building-blocks/{id} — Returns a single building block."""
        return self._validated(DTO.BuildingBlockDTO, await self._get(f"{self._building_blocks_url}/{building_block_id}"))

    async def update_building_block(
        self,
        building_block_id: str,
        dto: Union[DTO.BuildingBlockUpdateDTO, Dict],
    ) -> Result[DTO.BuildingBlockDTO, Exception]:
        """PATCH /building-blocks/{id} — Updates mutable fields on a building block."""
        payload = dto.model_dump() if isinstance(dto, DTO.BuildingBlockUpdateDTO) else dto
        return self._validated(DTO.BuildingBlockDTO, await self._patch(f"{self._building_blocks_url}/{building_block_id}", payload))

    async def delete_building_block(self, building_block_id: str) -> Result[bool, Exception]:
        """DELETE /building-blocks/{id} — Deletes a building block (204 No Content)."""
        return await self._delete_no_content(f"{self._building_blocks_url}/{building_block_id}")

    # ── Patterns  /patterns ────────────────────────────────────

    async def create_pattern(
        self,
        dto: Union[DTO.PatternCreateDTO, Dict],
    ) -> Result[DTO.PatternDTO, Exception]:
        """POST /patterns — Creates a new execution pattern for a building block."""
        payload = dto.model_dump() if isinstance(dto, DTO.PatternCreateDTO) else dto
        return self._validated(DTO.PatternDTO, await self._post(self._patterns_url, payload))

    async def list_patterns(self, skip: int = 0, limit: int = 100) -> Result[List[DTO.PatternDTO], Exception]:
        """GET /patterns — Returns a paginated list of patterns."""
        return self._validated_list(
            DTO.PatternDTO,
            await self._get(self._patterns_url, params={"skip": skip, "limit": limit}),
        )

    async def get_pattern(self, pattern_id: str) -> Result[DTO.PatternDTO, Exception]:
        """GET /patterns/{id} — Returns a single pattern."""
        return self._validated(DTO.PatternDTO, await self._get(f"{self._patterns_url}/{pattern_id}"))

    async def update_pattern(
        self,
        pattern_id: str,
        dto: Union[DTO.PatternUpdateDTO, Dict],
    ) -> Result[DTO.PatternDTO, Exception]:
        """PATCH /patterns/{id} — Updates mutable fields on a pattern."""
        payload = dto.model_dump() if isinstance(dto, DTO.PatternUpdateDTO) else dto
        return self._validated(DTO.PatternDTO, await self._patch(f"{self._patterns_url}/{pattern_id}", payload))

    async def delete_pattern(self, pattern_id: str) -> Result[bool, Exception]:
        """DELETE /patterns/{id} — Deletes a pattern (204 No Content)."""
        return await self._delete_no_content(f"{self._patterns_url}/{pattern_id}")

    # ── Stages  /stages ────────────────────────────────────────

    async def create_stage(
        self,
        dto: Union[DTO.StageCreateDTO, Dict],
    ) -> Result[DTO.StageDTO, Exception]:
        """POST /stages — Creates a new processing step in a workflow (source → sink)."""
        payload = dto.model_dump() if isinstance(dto, DTO.StageCreateDTO) else dto
        return self._validated(DTO.StageDTO, await self._post(self._stages_url, payload))

    async def list_stages(self, skip: int = 0, limit: int = 100) -> Result[List[DTO.StageDTO], Exception]:
        """GET /stages — Returns a paginated list of stages."""
        return self._validated_list(
            DTO.StageDTO,
            await self._get(self._stages_url, params={"skip": skip, "limit": limit}),
        )

    async def get_stage(self, stage_id: str) -> Result[DTO.StageDTO, Exception]:
        """GET /stages/{id} — Returns a single stage."""
        return self._validated(DTO.StageDTO, await self._get(f"{self._stages_url}/{stage_id}"))

    async def update_stage(
        self,
        stage_id: str,
        dto: Union[DTO.StageUpdateDTO, Dict],
    ) -> Result[DTO.StageDTO, Exception]:
        """PATCH /stages/{id} — Updates mutable fields on a stage."""
        payload = dto.model_dump() if isinstance(dto, DTO.StageUpdateDTO) else dto
        return self._validated(DTO.StageDTO, await self._patch(f"{self._stages_url}/{stage_id}", payload))

    async def delete_stage(self, stage_id: str) -> Result[bool, Exception]:
        """DELETE /stages/{id} — Deletes a stage (204 No Content)."""
        return await self._delete_no_content(f"{self._stages_url}/{stage_id}")

    # ── Workflows  /workflows ──────────────────────────────────

    async def create_workflow(
        self,
        dto: Union[DTO.WorkflowCreateDTO, Dict],
    ) -> Result[DTO.WorkflowDTO, Exception]:
        """POST /workflows — Creates a workflow from an ordered list of stages."""
        payload = dto.model_dump() if isinstance(dto, DTO.WorkflowCreateDTO) else dto
        return self._validated(DTO.WorkflowDTO, await self._post(self._workflows_url, payload))

    async def list_workflows(self, skip: int = 0, limit: int = 100) -> Result[List[DTO.WorkflowDTO], Exception]:
        """GET /workflows — Returns a paginated list of workflows."""
        return self._validated_list(
            DTO.WorkflowDTO,
            await self._get(self._workflows_url, params={"skip": skip, "limit": limit}),
        )

    async def get_workflow(self, workflow_id: str) -> Result[DTO.WorkflowDTO, Exception]:
        """GET /workflows/{id} — Returns a single workflow."""
        return self._validated(DTO.WorkflowDTO, await self._get(f"{self._workflows_url}/{workflow_id}"))

    async def update_workflow(
        self,
        workflow_id: str,
        dto: Union[DTO.WorkflowUpdateDTO, Dict],
    ) -> Result[DTO.WorkflowDTO, Exception]:
        """PATCH /workflows/{id} — Updates mutable fields on a workflow."""
        payload = dto.model_dump() if isinstance(dto, DTO.WorkflowUpdateDTO) else dto
        return self._validated(DTO.WorkflowDTO, await self._patch(f"{self._workflows_url}/{workflow_id}", payload))

    async def delete_workflow(
        self, workflow_id: str, cascade: bool = False
    ) -> Result[DTO.WorkflowDeleteResponseDTO, Exception]:
        """
        DELETE /workflows/{workflow_id}

        Deletes a workflow. When cascade=True, also deletes all linked stages.

        Args:
            workflow_id: Unique identifier of the workflow.
            cascade: When True, cascade-deletes the workflow's stages.

        Returns:
            Ok(WorkflowDeleteResponseDTO) on success, Err(exception) on failure.
        """
        return self._validated(
            DTO.WorkflowDeleteResponseDTO,
            await self._delete(f"{self._workflows_url}/{workflow_id}", params={"cascade": cascade}),
        )

    # ── Services  /services ────────────────────────────────────

    async def create_service(
        self,
        dto: Union[DTO.ServiceCreateDTO, Dict],
    ) -> Result[DTO.ServiceDTO, Exception]:
        """POST /services — Creates a new service with an optional workflow reference."""
        payload = dto.model_dump() if isinstance(dto, DTO.ServiceCreateDTO) else dto
        return self._validated(DTO.ServiceDTO, await self._post(self._services_url, payload))

    async def index_service(
        self,
        dto: Union[DTO.ServiceIndexDTO, Dict],
    ) -> Result[DTO.ServiceIndexResponseDTO, Exception]:
        """
        POST /services/index

        One-shot endpoint that creates the full Service -> Workflow -> Stages ->
        Patterns -> BuildingBlocks tree in a single request.

        Args:
            dto: ServiceIndexDTO instance or plain dict.

        Returns:
            Ok(ServiceIndexResponseDTO) on success, Err(exception) on failure.
        """
        payload = dto.model_dump() if isinstance(dto, DTO.ServiceIndexDTO) else dto
        return self._validated(DTO.ServiceIndexResponseDTO, await self._post(f"{self._services_url}/index", payload))

    async def list_services(self, skip: int = 0, limit: int = 100) -> Result[List[DTO.ServiceDTO], Exception]:
        """GET /services — Returns a paginated list of services."""
        return self._validated_list(
            DTO.ServiceDTO,
            await self._get(self._services_url, params={"skip": skip, "limit": limit}),
        )

    async def get_service(self, service_id: str) -> Result[DTO.ServiceDTO, Exception]:
        """GET /services/{id} — Returns a single service."""
        return self._validated(DTO.ServiceDTO, await self._get(f"{self._services_url}/{service_id}"))

    async def update_service(
        self,
        service_id: str,
        dto: Union[DTO.ServiceUpdateDTO, Dict],
    ) -> Result[DTO.ServiceDTO, Exception]:
        """PATCH /services/{id} — Updates mutable fields on a service."""
        payload = dto.model_dump() if isinstance(dto, DTO.ServiceUpdateDTO) else dto
        return self._validated(DTO.ServiceDTO, await self._patch(f"{self._services_url}/{service_id}", payload))

    async def delete_service(self, service_id: str) -> Result[DTO.ServiceDeleteResponseDTO, Exception]:
        """DELETE /services/{id} — Deletes a service and returns a cascade summary."""
        return self._validated(DTO.ServiceDeleteResponseDTO, await self._delete(f"{self._services_url}/{service_id}"))
