from bff.redact import MASK, redact


def test_secret_patterns():
    assert MASK in redact("key sk-abcdefghijklmnop1234")
    assert redact("Authorization: Bearer abc.def").endswith(MASK)
    assert redact("api_key=hunter2 ok") == f"api_key={MASK} ok"
    assert redact('{"password": "x1"}').startswith('{"password": ' + MASK)
    assert redact("eyJhbGciOi.eyJzdWIi.sig_nature") == MASK
    assert redact("id " + "a1" * 20) == f"id {MASK}"


def test_pii_masks():
    assert redact("kirim ke kevin@example.com") == "kirim ke k***@example.com"
    assert redact("telp 081234567890") == "telp *********890"
    assert redact("wa +6281234567890") == "wa ***********890"


def test_paths_shortened():
    assert redact(r"baca C:\Users\kevin\proj\notes.txt") == "baca …/notes.txt"
    assert redact("baca /home/kevin/proj/notes.txt") == "baca …/notes.txt"
    assert redact("https://example.com/home/page") == "https://example.com/home/page"


def test_plain_text_and_truncate():
    assert redact("hasil pencarian: tren AI 2026") == "hasil pencarian: tren AI 2026"
    assert redact("") == "" and redact(None) == ""
    out = redact("x" * 5000)
    assert len(out) == 2048 and out.endswith("…")
