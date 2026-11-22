"""Describe each product photo once with a vision-capable model through Hermes (the configured model; no separate API key).
`uv run python -m bff.product_vision [--limit N] [--dry-run] [--bot rian]`. Idempotent: photos that already have a description are skipped."""
import argparse
import asyncio
import base64
import sys
from collections.abc import Awaitable, Callable

from . import catalog, config, db, hermes, product_images

MAX_CHARS = 600
PROMPT = ("Deskripsikan HANYA apa yang terlihat pada foto produk pakaian ini, dalam bahasa Indonesia, satu paragraf ringkas "
          "(maksimal 80 kata): potongan dan siluet, bahan yang tampak, detail jahitan/kantong/kerah/kancing, dan warna. "
          "Jangan menebak merek, ukuran, harga, atau hal yang tidak terlihat. Nama produk: {name}.")
# shortcut: rough per-photo token use (image ~1.2k + prompt ~0.2k in, ~0.2k out); re-measure with a real run before the full batch.
EST_IN, EST_OUT = 1400, 200

Describer = Callable[[str, str, str], Awaitable[tuple[str, str]]]  # (image_ref, product name, bot) -> (text, model)


def _image_ref(image_url: str) -> str:
    """http(s) CDN urls go as they are; bundled photos are read from disk and sent as a data URI."""
    if image_url.startswith(product_images.LOCAL_PREFIX):
        p = product_images.safe_image_path(image_url.removeprefix(product_images.LOCAL_PREFIX))
        if not p:
            raise ValueError("Foto lokal tidak ditemukan")
        return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
    return image_url


async def describe_with_hermes(image_ref: str, name: str, bot: str) -> tuple[str, str]:
    r = await hermes.call(bot, "POST", "/v1/chat/completions", timeout=180, json_body={
        "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT.format(name=name)},
                                                  {"type": "image_url", "image_url": {"url": image_ref}}]}]})
    if r.status_code != 200:
        raise RuntimeError(f"Hermes menjawab {r.status_code}")
    d = r.json()
    text = (d["choices"][0]["message"]["content"] or "").strip()
    if not text:
        raise RuntimeError("Jawaban kosong")
    return text[:MAX_CHARS], str(d.get("model") or "hermes")


async def describe_all(limit: int | None = None, dry_run: bool = False, bot: str = "rian",
                       describer: Describer = describe_with_hermes) -> dict:
    # local photos first (they are the pilot set), then by url
    todo = await db.q("select i.url, i.image_url, (select name from products where url = i.url limit 1) as name from product_images i "
                      "where i.image_description is null and exists (select 1 from products where url = i.url) "
                      "order by i.image_source <> 'local', i.url")
    if limit:
        todo = todo[:limit]
    if dry_run:
        return {"akan_diproses": len(todo), "estimasi_token_masuk": len(todo) * EST_IN, "estimasi_token_keluar": len(todo) * EST_OUT}
    ok = failed = 0
    for row in todo:
        try:
            text, model = await describer(_image_ref(row["image_url"]), row["name"], bot)
        except Exception as e:  # one bad photo must not stop the batch; the message never contains the key
            print(f"gagal {row['url']}: {type(e).__name__} {e}", file=sys.stderr)
            failed += 1
            continue
        await db.ex("update product_images set image_description = %s, described_at = now(), describer_model = %s "
                    "where url = %s and image_description is null", text, model, row["url"])
        ok += 1
    return {"diproses": ok + failed, "berhasil": ok, "gagal": failed}


async def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bot", default="rian")
    a = ap.parse_args()
    await db.open_pool()
    hermes.start_client()
    try:
        await catalog.sync()
        print(await describe_all(a.limit, a.dry_run, a.bot))
    finally:
        await hermes.stop_client()
        await db.close_pool()


if __name__ == "__main__":
    asyncio.run(_main(), loop_factory=asyncio.SelectorEventLoop)
