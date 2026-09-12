import logging
import time
from collections.abc import Iterator
from typing import Any, Self

import httpx

logger = logging.getLogger(__name__)


class MercadoLivreAPIError(RuntimeError):
    pass


class MercadoLivreClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        rate_limit_seconds: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.rate_limit_seconds = rate_limit_seconds
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout_seconds,
            headers={
                "Accept": "application/json",
                "User-Agent": "mercado-intelligence-ai/0.1.0",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def get_authenticated(
        self,
        endpoint: str,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request(
            "GET",
            endpoint,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.request(method, path, params=params, headers=headers)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise MercadoLivreAPIError(
                        f"HTTP {response.status_code} from Mercado Livre: {response.text[:300]}"
                    )
                response.raise_for_status()
                time.sleep(self.rate_limit_seconds)
                return response.json()
            except (httpx.HTTPError, MercadoLivreAPIError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                sleep_seconds = min(2**attempt, 10)
                logger.warning(
                    "Retrying Mercado Livre request",
                    extra={
                        "pipeline": "ingestion",
                        "task": "http_get",
                        "status": "retry",
                    },
                )
                time.sleep(sleep_seconds)

        raise MercadoLivreAPIError(f"Request failed for {path}") from last_error

    def paginate_search(
        self,
        query: str,
        site_id: str,
        limit: int = 50,
        max_pages: int = 1,
        extra_params: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        params = {"q": query, "limit": limit, "offset": 0}
        if extra_params:
            params.update(extra_params)

        for page in range(max_pages):
            params["offset"] = page * limit
            payload = self.get(f"/sites/{site_id}/search", params=params)
            if not isinstance(payload, dict):
                raise MercadoLivreAPIError("Search payload is not a JSON object")
            results = payload.get("results", [])
            if not isinstance(results, list):
                raise MercadoLivreAPIError("Search payload does not contain a results list")
            for item in results:
                if isinstance(item, dict):
                    yield item
            paging = payload.get("paging", {})
            total = int(paging.get("total", 0)) if isinstance(paging, dict) else 0
            if (page + 1) * limit >= total or not results:
                break
