"""Knowledge Base: SSRF guard, link intent, chunking, extraction, size/type rejection, search ranking, user scoping.
The tests marked with_db need TEST_DATABASE_URL (see test_scheduler.py)."""
import asyncio
import io
import uuid
import zipfile

import httpx
import pytest
from test_scheduler import with_db

from bff import kb
from bff.errors import ApiError


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def dns(monkeypatch):
    """Fake resolver: host -> addresses (a literal IP resolves to itself)."""
    table: dict[str, list[str]] = {}

    async def resolve(host, port):
        if host in table:
            return table[host]
        return [host]  # literal IPs; an unknown name would fail in getaddrinfo, here it fails ip parsing
    monkeypatch.setattr(kb, "_resolve", resolve)
    return table


# ---------- SSRF guard ----------

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://10.0.0.5/x", "http://192.168.1.1/", "http://172.16.0.1/", "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/", "http://[::ffff:127.0.0.1]/", "http://100.64.0.1/", "http://0.0.0.0/", "http://[fe80::1]/", "http://[fd00::1]/",
])
def test_private_addresses_are_blocked(dns, url):
    with pytest.raises(kb.Blocked, match="internal"):
        run(kb.check_url(url))


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/x", "gopher://example.com", "javascript:alert(1)", "http:///x"])
def test_non_http_schemes_are_blocked(dns, url):
    with pytest.raises(kb.Blocked):
        run(kb.check_url(url))


def test_credentials_in_url_are_blocked(dns):
    with pytest.raises(kb.Blocked):
        run(kb.check_url("http://user:pw@example.com/"))


def test_hostname_resolving_to_private_is_blocked_even_if_one_address_is_public(dns):
    dns["evil.example"] = ["93.184.216.34", "10.0.0.1"]
    with pytest.raises(kb.Blocked):
        run(kb.check_url("https://evil.example/"))
    dns["ok.example"] = ["93.184.216.34"]
    run(kb.check_url("https://ok.example/"))  # public: allowed


def client_for(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


def test_redirect_to_private_address_is_blocked(dns):
    dns["ok.example"] = ["93.184.216.34"]

    def handler(req: httpx.Request):
        if req.url.host == "ok.example":
            return httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data/"})
        raise AssertionError("the private address must never be requested")
    with pytest.raises(kb.Blocked, match="internal"):
        run(kb.fetch("https://ok.example/start", client_for(handler)))


def test_redirect_chain_is_capped(dns):
    dns["ok.example"] = ["93.184.216.34"]
    hits = []

    def handler(req):
        hits.append(1)
        return httpx.Response(302, headers={"location": "/again"})
    with pytest.raises(kb.Blocked, match="dialihkan"):
        run(kb.fetch("https://ok.example/", client_for(handler)))
    assert len(hits) == kb.MAX_REDIRECTS + 1


def test_fetch_follows_a_safe_redirect_and_caps_size(dns, monkeypatch):
    dns["ok.example"] = ["93.184.216.34"]

    def handler(req):
        if req.url.path == "/":
            return httpx.Response(301, headers={"location": "/page"})
        return httpx.Response(200, text="<p>halo</p>", headers={"content-type": "text/html"})
    r, body = run(kb.fetch("https://ok.example/", client_for(handler)))
    assert r.status_code == 200 and body == b"<p>halo</p>"
    monkeypatch.setattr(kb, "MAX_PAGE_BYTES", 5)
    with pytest.raises(kb.Blocked, match="terlalu besar"):
        run(kb.fetch("https://ok.example/page", client_for(handler)))


# ---------- link intent ----------

@pytest.mark.parametrize("text", [
    "tolong simpan https://example.com/a", "Pelajari link ini https://example.com", "baca dan jadikan knowledge: https://x.co",
    "please save this https://example.com", "read this and learn it https://example.com", "masukkan ke knowledge base https://x.co/p",
])
def test_intent_detected(text):
    assert kb.wants_save(text) and kb.urls_in(text)


@pytest.mark.parametrize("text", ["lihat https://example.com/simpan-hemat", "apa kabar", "bandingkan https://example.com dan https://b.co"])
def test_no_intent_without_words(text):
    assert not kb.wants_save(text)  # an intent word inside the URL itself does not count


def test_urls_in_strips_punctuation_and_dedups():
    assert kb.urls_in("simpan (https://a.co/x). dan https://a.co/x, juga https://b.co/y?z=1!") == ["https://a.co/x", "https://b.co/y?z=1"]


# ---------- extraction, chunking ----------

def docx_bytes(paras):
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paras) + "</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def test_extract_text_md_csv_docx_and_bad_files():
    assert kb.extract("a.md", "# Judul\n\nisi".encode()) == "# Judul\n\nisi"
    assert "kolom" in kb.extract("a.csv", "kolom,nilai\n1,2".encode())
    assert kb.extract("a.docx", docx_bytes(["Satu", "Dua"])) == "Satu\nDua"
    with pytest.raises(ValueError, match="Word"):
        kb.extract("a.docx", b"not a zip")
    with pytest.raises(ValueError, match="PDF"):
        kb.extract("a.pdf", b"%PDF-broken")
    with pytest.raises(ValueError, match="kosong"):
        kb.extract("a.txt", b"  \n ")


def test_html_to_text_drops_scripts_and_nav():
    html = ("<html><head><title>Judul  Situs</title><style>x{}</style></head><body><nav>menu</nav><script>var a=1</script>"
            "<h1>Halo</h1><p>Paragraf satu.</p><p>Dua &amp; tiga</p><footer>kaki</footer></body></html>")
    title, text = kb.html_to_text(html)
    assert title == "Judul Situs" and text == "Halo\n\nParagraf satu.\n\nDua & tiga"


def test_chunks_respect_size_and_keep_all_text():
    text = "\n\n".join(f"Paragraf nomor {i}. " + "kata " * 60 for i in range(12))
    pieces = kb.chunk(text, 500)
    assert len(pieces) > 3 and all(len(p) <= 500 for p in pieces)
    assert "nomor 0" in pieces[0] and "nomor 11" in pieces[-1]
    long = "kalimat panjang. " * 200  # one paragraph far over the size is cut, not dropped
    assert all(len(p) <= 500 for p in kb.chunk(long, 500)) and sum(len(p) for p in kb.chunk(long, 500)) > 3000


def test_tsquery_uses_content_words_only():
    assert kb.tsquery("Tolong simpan https://example.com/x dan jelaskan harga kaos polos") == "jelaskan | harga | kaos | polos"
    assert kb.tsquery("di ke dan") is None
    assert kb.tsquery("a'; drop table kb_items; --") == "drop | table | kb_items"  # \w words only: nothing to inject


def test_drive_targets():
    assert kb.drive_target("https://docs.google.com/document/d/AbC_1-x/edit?usp=sharing") == ("https://docs.google.com/document/d/AbC_1-x/export?format=txt", "Google Docs")
    assert kb.drive_target("https://docs.google.com/spreadsheets/d/S1/edit#gid=77")[0].endswith("/S1/export?format=csv&gid=77")
    assert kb.drive_target("https://drive.google.com/file/d/F1/view")[0] == "https://drive.google.com/uc?export=download&id=F1"
    assert kb.drive_target("https://drive.google.com/open?id=F2")[0].endswith("id=F2")
    assert kb.drive_target("https://drive.google.com/drive/folders/xyz")[0] == "folder"
    assert kb.drive_target("https://example.com/document/d/x") is None


def test_block_cites_names_failures_and_stays_bounded():
    saved = [{"status": "ready", "name": "toko.co", "source": "https://toko.co"},
             {"status": "failed", "name": "x", "source": "https://x.co", "error": "Alamat ini tidak ditemukan."}]
    chunks = [{"name": "Panduan", "text": "a" * 2500}, {"name": "Harga", "text": "b" * 2500}, {"name": "Lain", "text": "c" * 2500}]
    b = kb.block(saved, chunks)
    assert "Tersimpan: toko.co" in b and "GAGAL disimpan: https://x.co" in b and "Alamat ini tidak ditemukan" in b
    assert "[Panduan]" in b and "[Harga]" in b and "[Lain]" not in b and len(b) < kb.CONTEXT_CHARS + 1500
    assert kb.block([], []) is None


# ---------- size / type rejection ----------

@pytest.mark.parametrize("name, size, status", [("x.exe", 10, 415), ("x", 10, 415), ("x.pdf", 0, 400), ("x.txt", kb.MAX_FILE_BYTES + 1, 413)])
def test_file_rejections(name, size, status):
    with pytest.raises(ApiError) as e:
        kb.check_file(name, size)
    assert e.value.status == status and e.value.message
    for ok in kb.FILE_TYPES:
        kb.check_file("Laporan" + ok.upper(), 100)


# ---------- database: ingest, search ranking, scoping ----------

def uid():
    return f"u-{uuid.uuid4().hex[:8]}"


@with_db
async def test_ingest_file_then_search_ranks_the_matching_chunk_first(db):
    u = uid()
    md = ("# Katalog\n\nKaos polos katun combed 30s tersedia warna hitam dan putih dengan harga 89 ribu.\n\n"
          "Pengiriman memakai kurir reguler dan estimasi tiba tiga hari kerja.\n\n"
          "Kebijakan retur berlaku tujuh hari setelah barang diterima dalam kondisi baik.").encode()
    item = await kb.ingest_file(u, "katalog.md", md)
    assert item["status"] == "ready" and item["kind"] == "file" and item["chars"] and item["size_bytes"] == len(md)
    hits = await kb.search(u, "berapa harga kaos katun?")
    assert hits and "89 ribu" in hits[0]["text"] and hits[0]["name"] == "katalog.md"
    assert await kb.search(u, "zzzz tidak ada") == []
    assert await kb.search(u, "di ke dan") == []


@with_db
async def test_search_ranks_better_match_above_weaker(db):
    u = uid()
    await kb.ingest_file(u, "a.txt", b"Cerita soal kucing dan anjing di taman kota yang ramai.")
    await kb.ingest_file(u, "b.txt", b"Kucing kucing kucing: perawatan kucing, makanan kucing, dan vaksin kucing.")
    hits = await kb.search(u, "kucing vaksin")
    assert [h["name"] for h in hits][:2] == ["b.txt", "a.txt"]


@with_db
async def test_items_are_scoped_to_the_user(db):
    a, b = uid(), uid()
    item = await kb.ingest_file(a, "rahasia.txt", b"nomor rahasia proyek bernama pelangi")
    assert await kb.search(b, "rahasia pelangi") == []
    assert await kb.list_items(b) == [] and [i["id"] for i in await kb.list_items(a)] == [item["id"]]
    assert await kb.attached(b, [item["id"]]) == [] and await kb.owned_ids(b, [item["id"]]) == []
    with pytest.raises(ApiError) as e:
        await kb.delete_item(b, item["id"])
    assert e.value.status == 404
    assert await kb.search(a, "rahasia pelangi")  # still there
    await kb.delete_item(a, item["id"])
    assert await kb.search(a, "rahasia pelangi") == []
    assert not await db.q1("select 1 as x from kb_chunks where item_id = %s", item["id"])  # chunks go with the item


@with_db
async def test_unreadable_file_is_saved_as_failed_with_a_reason(db):
    u = uid()
    item = await kb.ingest_file(u, "rusak.docx", b"bukan zip")
    assert item["status"] == "failed" and "Word" in item["error"]
    assert await kb.search(u, "rusak") == []


@with_db
async def test_ingest_url_ready_failed_and_private_drive(db):
    u = uid()
    html = "<html><head><title>Toko Kami</title></head><body><p>Kami menjual kaos polos berkualitas dengan harga terjangkau.</p></body></html>"

    async def fake_fetch(url, client=None):
        if "drive.google.com" in url or "docs.google.com" in url:
            return httpx.Response(200, headers={"content-type": "text/html"}, request=httpx.Request("GET", "https://accounts.google.com/x")), b"<html>Sign in</html>"
        if "gone" in url:
            raise kb.Blocked("Alamat ini mengarah ke jaringan internal dan tidak diizinkan.")
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, request=httpx.Request("GET", url)), html.encode()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(kb, "fetch", fake_fetch)
    ok = await kb.ingest_url(u, "https://toko.example/produk")
    assert ok["status"] == "ready" and ok["name"] == "Toko Kami" and ok["kind"] == "url" and ok["source"] == "https://toko.example/produk"
    again = await kb.ingest_url(u, "https://toko.example/produk")  # same link again refreshes instead of duplicating
    assert len(await kb.list_items(u)) == 1 and again["id"] != ok["id"]
    bad = await kb.ingest_url(u, "https://gone.example/")
    assert bad["status"] == "failed" and "internal" in bad["error"]
    drive = await kb.ingest_url(u, "https://docs.google.com/document/d/ABC/edit")
    assert drive["status"] == "failed" and drive["kind"] == "gdrive" and "Google Drive" in drive["error"]
    with pytest.raises(ApiError):
        await kb.ingest_url(u, "ftp://x.example/a")


@with_db
async def test_prepare_saves_only_on_intent_and_builds_context(db):
    u = uid()

    async def fake_fetch(url, client=None):
        return (httpx.Response(200, headers={"content-type": "text/plain"}, request=httpx.Request("GET", url)),
                "Jam buka toko adalah pukul sembilan sampai lima sore setiap hari kerja.".encode())
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(kb, "fetch", fake_fetch)
    assert await kb.save_links(u, "lihat https://toko.example/jam") == [] and await kb.list_items(u) == []
    saved = await kb.save_links(u, "tolong simpan https://toko.example/jam")
    assert [s["status"] for s in saved] == ["ready"]
    text = await kb.retrieve(u, "jam buka toko kapan?", [], saved)
    assert "Tersimpan: " in text and "Jam buka toko" in text
    assert "Jam buka toko" in await kb.retrieve(u, "jam buka toko kapan?", [], [])  # later messages find it by keywords
