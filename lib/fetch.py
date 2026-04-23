"""Browser-mimicking HTTP client.

Academic publisher sites (ASCO/NEJM/OUP/Wiley/Nature) sit behind Cloudflare
or Atypon which reject bare Python user agents. We send a realistic Chrome
header set, keep cookies, and retry once on 403.
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

import httpx

try:
    import h2  # noqa: F401
    HTTP2_AVAILABLE = True
except ImportError:
    HTTP2_AVAILABLE = False

CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

BASE_HEADERS = {
    "User-Agent": CHROME_UA,
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

RETRY_BACKOFF_SECONDS = (2, 5)


def same_origin_referer(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}/"


def build_client(override_headers: dict[str, str] | None = None) -> httpx.Client:
    headers = dict(BASE_HEADERS)
    if override_headers:
        headers.update(override_headers)
    return httpx.Client(
        headers=headers,
        http2=HTTP2_AVAILABLE,
        follow_redirects=True,
        timeout=20,
    )


def fetch_feed(url: str, overrides: dict[str, Any] | None = None) -> bytes:
    """Fetch an RSS/Atom feed, handling Cloudflare 403 with one retry.

    overrides may contain:
      headers: dict[str, str]   additional headers to merge
      referer: str              override same-origin referer
    """
    overrides = overrides or {}
    headers = dict(BASE_HEADERS)
    headers["Referer"] = overrides.get("referer") or same_origin_referer(url)
    if overrides.get("headers"):
        headers.update(overrides["headers"])

    last_error: Exception | None = None
    with httpx.Client(
        headers=headers, http2=HTTP2_AVAILABLE, follow_redirects=True, timeout=25
    ) as client:
        for attempt, backoff in enumerate((0, *RETRY_BACKOFF_SECONDS)):
            if backoff:
                time.sleep(backoff)
            try:
                r = client.get(url)
                if r.status_code == 403 and attempt < len(RETRY_BACKOFF_SECONDS):
                    last_error = httpx.HTTPStatusError(
                        f"403 from {url}", request=r.request, response=r
                    )
                    continue
                r.raise_for_status()
                return r.content
            except httpx.HTTPError as e:
                last_error = e
                if attempt >= len(RETRY_BACKOFF_SECONDS):
                    break
    assert last_error is not None
    raise last_error
