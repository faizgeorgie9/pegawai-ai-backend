"""Ingatan: Hermes MEMORY.md / USER.md format, lock and BFF endpoints."""
import threading
import time

import pytest

from bff import config, main, memory
from bff.errors import ApiError


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A throwaway HERMES_HOME with one owned profile."""
    monkeypatch.setattr(config, "HERMES_HOME", tmp_path)
    (tmp_path / "profiles" / "rian" / "memories").mkdir(parents=True)
    return tmp_path


def write_store(home, store: str, text: str):
    path = home / "profiles" / "rian" / "memories" / memory.STORE_FILES[store]
    path.write_text(text, encoding="utf-8")
    return path


def owned(monkeypatch, allowed="rian"):
    async def get_bot(user_id, bot_id):
        if bot_id != allowed:
            raise ApiError(404, "Bot tidak ditemukan")
        return {"id": bot_id, "user_id": user_id}

    monkeypatch.setattr(main.bots, "get_bot", get_bot)


# ---------- format ----------

def test_parse_matches_hermes_format():
    raw = "  satu  \n§\n\n§\ndua\n§\ntiga\n"
    assert memory.parse_entries(raw) == ["satu", "dua", "tiga"]
    assert memory.parse_entries("") == []
    # A bare section sign is text, not a delimiter (Hermes splits on the full delimiter only).
    assert memory.parse_entries("a § b") == ["a § b"]


def test_item_ids_are_stable_and_store_scoped():
    one = memory.item_id("memory", "Suka kopi tanpa gula")
    assert one == memory.item_id("memory", "Suka kopi tanpa gula")
    assert one.startswith("m-") and len(one) == 18
    assert memory.item_id("user", "Suka kopi tanpa gula").startswith("u-")
    assert memory.item_id("memory", "Suka kopi tanpa gula") != memory.item_id("memory", "Suka teh")


# ---------- read ----------

def test_snapshot_reads_both_stores(home):
    write_store(home, "memory", "Fakta satu\n§\nFakta dua")
    write_store(home, "user", "Pemilik Colorbox")
    snap = memory.snapshot("rian")
    assert [i["text"] for i in snap["items"]] == ["Fakta satu", "Fakta dua"]
    assert [i["text"] for i in snap["about_you"]] == ["Pemilik Colorbox"]
    assert snap["items"][0]["id"] == memory.item_id("memory", "Fakta satu")
    assert snap["limit"] == {"used": len("Fakta satu\n§\nFakta dua"), "max": memory.DEFAULT_MEMORY_LIMIT}
    assert snap["about_limit"] == {"used": len("Pemilik Colorbox"), "max": memory.DEFAULT_USER_LIMIT}


def test_snapshot_missing_files_is_empty(home):
    snap = memory.snapshot("rian")
    assert snap == {"items": [], "about_you": [],
                    "limit": {"used": 0, "max": memory.DEFAULT_MEMORY_LIMIT},
                    "about_limit": {"used": 0, "max": memory.DEFAULT_USER_LIMIT}}


def test_limits_follow_the_profile_config(home):
    (home / "profiles" / "rian" / "config.yaml").write_text(
        "memory:\n  memory_char_limit: 500\n  user_char_limit: 250\n", encoding="utf-8")
    assert memory.limits("rian") == (500, 250)


def test_bom_is_stripped_like_hermes(home):
    write_store(home, "memory", "\ufeffFakta ber-BOM")
    assert memory.snapshot("rian")["items"][0]["text"] == "Fakta ber-BOM"


def test_write_survives_a_transient_reader(home):
    """Windows refuses os.replace over an open handle; a short-lived reader must not fail the delete."""
    path = write_store(home, "memory", "Satu")
    ready = threading.Event()

    def reader():
        with path.open("r", encoding="utf-8") as fh:
            fh.read(1)
            ready.set()
            time.sleep(0.15)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    assert ready.wait(2)
    memory.write_entries(path, ["Dua"])
    thread.join(2)
    assert path.read_text(encoding="utf-8") == "Dua"


# ---------- delete one ----------

def test_delete_item_removes_only_that_entry(home):
    path = write_store(home, "memory", "Satu\n§\nDua\n§\nTiga")
    target = memory.item_id("memory", "Dua")
    memory.delete_item("rian", target)
    assert path.read_text(encoding="utf-8") == "Satu\n§\nTiga"


def test_delete_item_works_for_about_you(home):
    path = write_store(home, "user", "Pemilik Colorbox")
    memory.delete_item("rian", memory.item_id("user", "Pemilik Colorbox"))
    assert path.read_text(encoding="utf-8") == ""


def test_delete_last_entry_leaves_an_empty_store(home):
    path = write_store(home, "memory", "Hanya satu")
    memory.delete_item("rian", memory.item_id("memory", "Hanya satu"))
    assert path.read_bytes() == b""
    assert memory.snapshot("rian")["items"] == []


def test_delete_stale_id_is_409(home):
    write_store(home, "memory", "Satu\n§\nDua")
    stale = memory.item_id("memory", "Dua")
    write_store(home, "memory", "Satu")  # Hermes (or another tab) already removed it
    with pytest.raises(ApiError) as e:
        memory.delete_item("rian", stale)
    assert e.value.status == 409


def test_delete_unknown_but_valid_id_is_409(home):
    write_store(home, "memory", "Satu")
    with pytest.raises(ApiError) as e:
        memory.delete_item("rian", "m-" + "0" * 16)
    assert e.value.status == 409


def test_delete_malformed_id_is_404(home):
    write_store(home, "memory", "Satu")
    for bad in ("", "x", "m", "m-", "m-zzzz", "z-" + "0" * 16):
        with pytest.raises(ApiError) as e:
            memory.delete_item("rian", bad)
        assert e.value.status == 404


def test_delete_missing_file_is_409(home):
    with pytest.raises(ApiError) as e:
        memory.delete_item("rian", "m-" + "0" * 16)
    assert e.value.status == 409


# ---------- clear all ----------

def test_clear_all_empties_both_stores(home):
    memory_path = write_store(home, "memory", "Satu\n§\nDua")
    user_path = write_store(home, "user", "Tentang Anda")
    memory.clear_all("rian")
    assert memory_path.read_bytes() == b""
    assert user_path.read_bytes() == b""


def test_clear_all_leaves_missing_files_missing(home):
    write_store(home, "memory", "Satu")
    memory.clear_all("rian")
    assert not (home / "profiles" / "rian" / "memories" / "USER.md").exists()


# ---------- lock ----------

def test_delete_waits_for_the_hermes_lock(home):
    path = write_store(home, "memory", "Satu\n§\nDua")
    target = memory.item_id("memory", "Dua")
    started, done = threading.Event(), threading.Event()
    failure: list[BaseException] = []

    def worker():
        started.set()
        try:
            memory.delete_item("rian", target)
        except BaseException as e:  # noqa: BLE001 - surfaced by the assertion below
            failure.append(e)
        finally:
            done.set()

    with memory.file_lock(path):
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        assert started.wait(2)
        time.sleep(0.2)
        assert not done.is_set(), "delete must not write while Hermes holds the lock"
        assert path.read_text(encoding="utf-8") == "Satu\n§\nDua"
    thread.join(5)
    assert not thread.is_alive()
    assert failure == []
    assert path.read_text(encoding="utf-8") == "Satu"


# ---------- endpoints ----------

@pytest.mark.anyio
async def test_endpoints_require_ownership(home, monkeypatch):
    owned(monkeypatch)
    with pytest.raises(ApiError) as e:
        await main.bot_memory("mira")
    assert e.value.status == 404
    with pytest.raises(ApiError) as e:
        await main.delete_memory_item("mira", "m-" + "0" * 16)
    assert e.value.status == 404
    with pytest.raises(ApiError) as e:
        await main.clear_bot_memory("mira", _Body({}), confirm=True)
    assert e.value.status == 404


@pytest.mark.anyio
async def test_get_and_delete_endpoints(home, monkeypatch):
    owned(monkeypatch)
    write_store(home, "memory", "Satu\n§\nDua")
    snap = await main.bot_memory("rian")
    assert [i["text"] for i in snap["items"]] == ["Satu", "Dua"]
    await main.delete_memory_item("rian", snap["items"][0]["id"])
    assert [i["text"] for i in (await main.bot_memory("rian"))["items"]] == ["Dua"]


class _Body:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


@pytest.mark.anyio
async def test_clear_needs_confirmation(home, monkeypatch):
    owned(monkeypatch)
    path = write_store(home, "memory", "Satu")
    with pytest.raises(ApiError) as e:
        await main.clear_bot_memory("rian", _Body({}))
    assert e.value.status == 400
    assert path.read_text(encoding="utf-8") == "Satu"
    await main.clear_bot_memory("rian", _Body({"confirm": True}))
    assert path.read_bytes() == b""


@pytest.mark.anyio
async def test_clear_accepts_the_query_flag(home, monkeypatch):
    owned(monkeypatch)
    path = write_store(home, "memory", "Satu")
    await main.clear_bot_memory("rian", _Body({}), confirm=True)
    assert path.read_bytes() == b""
