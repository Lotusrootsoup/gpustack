import asyncio
import json
from typing import Any, Callable, Dict, Optional

import httpx
from gpustack.api.exceptions import raise_if_response_error
from gpustack.server.bus import Event
from gpustack.schemas import *

from .generated_http_client import HTTPClient


class ModelInstanceClient:
    def __init__(self, client: HTTPClient):
        self._client = client
        self._url = f"{client._base_url}/v1/model-instances"

    def list(self, params: Dict[str, Any] = None) -> ModelInstancesPublic:
        response = self._client.get_httpx_client().get(self._url, params=params)
        raise_if_response_error(response)

        return ModelInstancesPublic.model_validate(response.json())

    def watch(
        self,
        callback: Callable[[Event], None],
        stop_condition: Optional[Callable[[Event], bool]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        if params is None:
            params = {}
        params["watch"] = "true"

        if stop_condition is None:
            stop_condition = lambda event: False

        with self._client.get_httpx_client().stream(
            "GET", self._url, params=params, timeout=None
        ) as response:
            raise_if_response_error(response)
            for line in response.iter_lines():
                if line:
                    event_data = json.loads(line)
                    event = Event(**event_data)
                    callback(event)
                    if stop_condition(event):
                        break

    async def awatch(
        self,
        callback: Callable[[Event], None],
        stop_condition: Optional[Callable[[Event], bool]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        if params is None:
            params = {}
        params["watch"] = "true"

        if stop_condition is None:
            stop_condition = lambda event: False

        async with self._client.get_async_httpx_client().stream(
            "GET",
            self._url,
            params=params,
            timeout=httpx.Timeout(connect=10, read=None, write=10, pool=10),
        ) as response:
            raise_if_response_error(response)
            lines = response.aiter_lines()
            while True:
                try:
                    line = await asyncio.wait_for(lines.__anext__(), timeout=45)
                    if line:
                        event_data = json.loads(line)
                        event = Event(**event_data)
                        callback(event)
                        if stop_condition(event):
                            break
                except asyncio.TimeoutError:
                    raise Exception("watch timeout")

    def get(self, id: int) -> ModelInstancePublic:
        response = self._client.get_httpx_client().get(f"{self._url}/{id}")
        raise_if_response_error(response)
        return ModelInstancePublic.model_validate(response.json())

    def create(self, model_create: ModelInstanceCreate):
        response = self._client.get_httpx_client().post(
            self._url,
            content=model_create.model_dump_json(),
            headers={"Content-Type": "application/json"},
        )
        raise_if_response_error(response)
        return ModelInstancePublic.model_validate(response.json())

    def update(self, id: int, model_update: ModelInstanceUpdate):
        response = self._client.get_httpx_client().put(
            f"{self._url}/{id}",
            content=model_update.model_dump_json(),
            headers={"Content-Type": "application/json"},
        )
        raise_if_response_error(response)
        return ModelInstancePublic.model_validate(response.json())

    def delete(self, id: int):
        response = self._client.get_httpx_client().delete(f"{self._url}/{id}")
        raise_if_response_error(response)
