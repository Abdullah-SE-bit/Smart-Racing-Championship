"""Small, serial GitHub client for coordination tooling; credentials stay in memory."""

import json
import os
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GitHubError(RuntimeError):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"GitHub HTTP {status}: {message}")


class GitHub:
    def __init__(self, repo: str):
        self.repo = repo
        self.token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            self.token = subprocess.check_output(
                ["gh", "auth", "token"], text=True, stderr=subprocess.PIPE
            ).strip()
        self.last_write = 0.0

    def request(self, method: str, path: str, body=None):
        if not path.startswith("/"):
            path = f"/repos/{self.repo}" + ("/" + path if path else "")
        if method != "GET":
            time.sleep(max(0, 1.1 - (time.monotonic() - self.last_write)))
        request = Request(
            "https://api.github.com" + path,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            method=method,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "smart-racing-coordination",
            },
        )
        for attempt in range(5):
            try:
                with urlopen(request, timeout=45) as response:
                    data = response.read()
                    if method != "GET":
                        self.last_write = time.monotonic()
                    return json.loads(data) if data else None
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                limited = error.code == 429 or (
                    error.code == 403 and "rate limit" in detail.lower()
                )
                if limited and attempt < 4:
                    delay = int(error.headers.get("Retry-After", "60"))
                    if error.headers.get("X-RateLimit-Remaining") == "0":
                        delay = max(delay, int(error.headers.get("X-RateLimit-Reset", "0")) - int(time.time()) + 1)
                    delay = max(delay, 60 * 2**attempt)
                    print(f"Rate limited; retrying after {delay}s. Progress is resumable.", flush=True)
                    while delay > 0:
                        time.sleep(min(30, delay))
                        delay -= 30
                    continue
                raise GitHubError(error.code, detail) from error
        raise RuntimeError("GitHub retry budget exhausted")

    def pages(self, path: str):
        items = []
        page = 1
        separator = "&" if "?" in path else "?"
        while True:
            batch = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ValueError(f"Expected paginated list: {path}")
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1

    def file(self, path: str, ref: str):
        import base64

        result = self.request("GET", f"contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}")
        return base64.b64decode(result["content"]).decode("utf-8-sig")
