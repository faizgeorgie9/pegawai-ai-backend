import email, glob, os, re
from html.parser import HTMLParser

DIR = os.path.dirname(os.path.abspath(__file__))

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg", "noscript"):
            self.skip += 1
        if tag in ("p","div","h1","h2","h3","h4","li","br","tr","section","span","button","a"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "noscript") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip() + " ")

for path in glob.glob(os.path.join(DIR, "*.mhtml")):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        msg = email.message_from_file(f)
    html = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                html = part.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                html = part.get_payload(decode=True).decode("latin-1", errors="replace")
            break
    ex = TextExtractor()
    ex.feed(html)
    text = re.sub(r"\n\s*\n+", "\n", "".join(ex.parts))
    out = os.path.splitext(path)[0] + ".txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(os.path.basename(out), len(text))
