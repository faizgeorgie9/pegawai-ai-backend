import pytest

from bff import kb
from bff.errors import ApiError


def test_text_file_is_normalised_and_measured():
    text, pages = kb.extract("catatan.md", "Baris satu.\r\n\r\n\r\n\r\nBaris dua.".encode())
    assert text == "Baris satu.\n\nBaris dua." and pages is None


def test_unsupported_and_empty_files_are_refused():
    with pytest.raises(ApiError) as e:
        kb.extract("gambar.png", b"x")
    assert e.value.status == 400
    with pytest.raises(ApiError):
        kb.extract("kosong.txt", b"   ")


def test_html_keeps_visible_text_and_drops_scripts():
    title, text = kb.html_to_text(
        b"<html><head><title>Kebijakan Retur</title><style>.x{}</style></head>"
        b"<body><script>alert(1)</script><h1>Retur 14 hari</h1><p>Barang harus utuh.</p></body></html>")
    assert title == "Kebijakan Retur"
    assert "Retur 14 hari" in text and "Barang harus utuh." in text
    assert "alert" not in text and ".x{}" not in text


def test_chunks_cover_the_text_with_overlap():
    text = ("Kalimat uji. " * 400).strip()
    parts = kb.chunks(text, size=400, overlap=50)
    assert len(parts) > 1 and all(len(p) <= 420 for p in parts)
    head = {p[:40] for p in parts}
    assert len(head) > 1


def test_short_text_is_one_chunk_and_blank_is_none():
    assert kb.chunks("satu paragraf") == ["satu paragraf"]
    assert kb.chunks("   ") == []


def source(title, content, sid="11111111-2222-3333-4444-555555555555"):
    return {"id": sid, "title": title, "kind": "file", "url": None, "created_at": "2026-11-13",
            "content": content}


def test_rank_matches_plural_and_ignores_unrelated_documents():
    sources = [
        source("Kebijakan retur", "Pengembalian barang maksimal 14 hari setelah diterima."),
        source("Panduan stok", "Stok gudang Jakarta dikirim setiap Senin."),
    ]
    hits = kb.rank("berapa lama pengembalian barang?", sources)
    assert hits and hits[0]["title"] == "Kebijakan retur"
    assert kb.rank("resep kue bolu", sources) == []


def test_rank_counts_a_title_word_as_evidence():
    sources = [source("Kebijakan retur", "Barang boleh dikembalikan dalam 14 hari setelah diterima.")]
    hits = kb.rank("berapa lama batas retur", sources)
    assert hits and hits[0]["title"] == "Kebijakan retur"
    assert hits[0]["score"] == 1


def test_compose_marks_uploaded_documents_and_builds_refs():
    hits = [{"source_id": "abcdef12-0000-0000-0000-000000000000", "title": "Kebijakan retur", "kind": "file",
             "url": None, "created_at": "2026-11-13", "chunk": 0, "score": 3, "text": "Retur 14 hari."}]
    text, refs = kb.compose(hits)
    assert "Dokumen pengetahuan tambahan" in text and "Retur 14 hari." in text
    assert "bukan data live" in text
    assert refs == [{"type": "knowledge", "id": "KB-abcdef12", "title": "Kebijakan retur",
                     "classification": "Uploaded Document", "source_id": None, "url": None,
                     "accessed_date": "2026-11-13"}]


def test_private_addresses_are_blocked():
    assert kb._private_host("127.0.0.1") is True
    assert kb._private_host("10.1.2.3") is True
    assert kb._private_host("192.168.1.5") is True
