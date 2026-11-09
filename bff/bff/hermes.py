"""Thin client for the Hermes gateway. Keys are read from the profile .env at call time and never logged."""
import json
import re
from typing import AsyncIterator

import httpx

from . import config
from .errors import ApiError

_SLUG = re.compile(r"^[a-z0-9]{1,24}$")
client: httpx.AsyncClient | None = None


def start_client() -> None:
    global client
    client = httpx.AsyncClient(base_url=config.HERMES_API_URL,
                               timeout=httpx.Timeout(30, read=None), limits=httpx.Limits(max_connections=50))


async def stop_client() -> None:
    if client:
        await client.aclose()


def profile_dir(bot: str):
    if not _SLUG.match(bot):
        raise ApiError(404, "Bot tidak ditemukan")
    return config.HERMES_HOME / "profiles" / bot


def bot_key(bot: str) -> str:
    env = profile_dir(bot) / ".env"
    try:
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("API_SERVER_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    raise ApiError(502, "Bot belum siap dipakai")


def _headers(bot: str, extra: dict | None = None) -> dict:
    return {"Authorization": f"Bearer {bot_key(bot)}", **(extra or {})}


async def call(bot: str, method: str, path: str, *, json_body=None, headers=None, timeout=30) -> httpx.Response:
    """Request /p/<bot><path>. Network failure becomes a 502 in Indonesian."""
    try:
        return await client.request(method, f"/p/{bot}{path}", json=json_body,
                                    headers=_headers(bot, headers), timeout=timeout)
    except httpx.HTTPError:
        raise ApiError(502, "Tidak bisa menghubungi Hermes. Pastikan gateway berjalan.")


async def events(bot: str, hermes_run_id: str, last_seq: int) -> AsyncIterator[tuple[int, dict]]:
    """Yield (seq, event) from the run's SSE stream. Raises httpx errors on disconnect."""
    h = _headers(bot, {"Accept": "text/event-stream"})
    if last_seq > 0:
        h["Last-Event-ID"] = str(last_seq)
    async with client.stream("GET", f"/p/{bot}/v1/runs/{hermes_run_id}/events", headers=h,
                             timeout=httpx.Timeout(30, read=60)) as r:
        if r.status_code != 200:
            raise httpx.HTTPStatusError("events", request=r.request, response=r)
        seq, data = 0, []
        async for line in r.aiter_lines():
            if line.startswith("id:"):
                try:
                    seq = int(line[3:].strip())
                except ValueError:
                    pass
            elif line.startswith("data:"):
                data.append(line[5:].strip())
            elif line == "" and data:
                try:
                    ev = json.loads("\n".join(data))
                    yield int(ev.get("seq", seq)), ev
                except ValueError:
                    pass
                seq, data = 0, []


async def alive() -> bool:
    try:
        r = await client.get("/health", timeout=3)
        return r.status_code == 200
    except httpx.HTTPError:
        return False
