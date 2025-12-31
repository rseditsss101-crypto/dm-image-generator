import tempfile
from pathlib import Path

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

WIDTH = 1200
HEIGHT = 800

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
body {{
  margin: 0;
  background: black;
  display: flex;
  justify-content: center;
  align-items: center;
}}
.chat {{
  width: {w}px;
  height: {h}px;
  background: black;
  font-family: Arial, sans-serif;
  color: white;
  position: relative;
}}
.bubble {{
  position: absolute;
  max-width: 45%;
  padding: 16px 24px;
  font-size: 26px;
  border-radius: 30px;
}}
.me {{
  background: #a439ff;
  right: 40px;
}}
.them {{
  background: #2b2b2f;
  left: 40px;
}}
</style>
</head>
<body>
<div class="chat">
{bubbles}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return jsonify({"status": "DM Image Generator is running"})

def parse_script(text):
    msgs = []
    y = 50
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("R) "):
            msgs.append(("me", line[3:], y))
            y += 90
        elif line.startswith("L) "):
            msgs.append(("them", line[3:], y))
            y += 90
    return msgs

def build_html(messages):
    bubbles = []
    for side, txt, y in messages:
        bubbles.append(
            f'<div class="bubble {side}" style="top:{y}px">{txt}</div>'
        )
    return HTML_TEMPLATE.format(
        w=WIDTH, h=HEIGHT, bubbles="\n".join(bubbles)
    )

def render_html(html_content, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--single-process',
                '--no-zygote',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
        page.set_content(html_content)
        page.screenshot(path=output_path, full_page=False)
        browser.close()



@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)
    if not data or "script" not in data:
        return jsonify({"error": "No script provided"}), 400

    script = data["script"]

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "output.png"
        messages = parse_script(script)
        html = build_html(messages)
        render_html(html, str(img_path))
        return send_file(img_path, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)







