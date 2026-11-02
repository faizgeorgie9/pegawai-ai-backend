import markdown

with open(r"D:\ai_developer\project6\task 3\Hermes_Agent_23_Checklist_Evidence.md", "r", encoding="utf-8") as f:
    md_content = f.read()

html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>23 Checklist Evidence - Hermes Agent (Day 3)</title>
<style>
  body {{
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    line-height: 1.6;
    color: #282828;
    max-width: 900px;
    margin: 40px auto;
    padding: 0 30px;
    background-color: #ffffff;
  }}
  h1 {{
    color: #1B365D;
    font-size: 24px;
    border-bottom: 2px solid #1B365D;
    padding-bottom: 8px;
    margin-top: 10px;
  }}
  h2 {{
    color: #1B365D;
    font-size: 18px;
    margin-top: 25px;
    border-bottom: 1px solid #E1E4E8;
    padding-bottom: 4px;
  }}
  h3 {{
    color: #2D4B73;
    font-size: 15px;
    margin-top: 18px;
  }}
  p, li {{
    font-size: 14px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 13.5px;
  }}
  th, td {{
    border: 1px solid #D0D7DE;
    padding: 8px 12px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #1B365D;
    color: #ffffff;
    font-weight: 600;
  }}
  tr:nth-child(even) {{
    background-color: #F8F9FA;
  }}
  pre, code {{
    font-family: 'Consolas', 'Courier New', monospace;
    background-color: #F6F8FA;
    border-radius: 4px;
  }}
  pre {{
    padding: 12px;
    border: 1px solid #D0D7DE;
    overflow-x: auto;
    font-size: 12.5px;
  }}
  code {{
    padding: 2px 5px;
    font-size: 12.5px;
  }}
  .copy-btn {{
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #1B365D;
    color: white;
    border: none;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
    border-radius: 6px;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }}
  .copy-btn:hover {{
    background-color: #0E2440;
  }}
</style>
</head>
<body>
<button class="copy-btn" onclick="copyForGDocs()">📋 Copy All to Google Docs</button>
<div id="content">
{html_body}
</div>
<script>
function copyForGDocs() {{
  const range = document.createRange();
  range.selectNode(document.getElementById('content'));
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  document.execCommand('copy');
  window.getSelection().removeAllRanges();
  alert('Seluruh bukti 23 checklist berhasil di-copy! Anda bisa langsung tekan Ctrl+V di Google Docs.');
}}
</script>
</body>
</html>
"""

with open(r"D:\ai_developer\project6\task 3\Hermes_Agent_23_Checklist_Evidence.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("HTML generated successfully.")
