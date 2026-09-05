import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_USER_AGENT = "JobHunt-Auto/1.0 (+https://github.com/meryemgcl/jobhunt-auto)"
RETRY_STATUSES = (429, 500, 502, 503, 504)


class ResilientHttpClient:
    def __init__(
        self,
        timeout: float | None = None,
        total_retries: int = 3,
        backoff_factor: float = 0.6,
        user_agent: str | None = None,
    ):
        self.timeout = timeout or float(os.getenv("JOBHUNT_HTTP_TIMEOUT", "10"))
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent or os.getenv("JOBHUNT_USER_AGENT", DEFAULT_USER_AGENT),
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            }
        )

        retry = Retry(
            total=total_retries,
            connect=total_retries,
            read=total_retries,
            status=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=RETRY_STATUSES,
            allowed_methods=frozenset({"GET", "POST"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def get_json(self, url: str, **kwargs):
        return self.get(url, **kwargs).json()
