import os
import base64
import tempfile
from pathlib import Path

from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
WIDTH = 1200
HEIGHT = 800

# ================= HTML TEMPLATE =================
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

# ================= HELPERS =================

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

def render_html(html, out_path):
    # ✅ RENDER-SAFE PLAYWRIGHT CONFIG (REQUIRED ON RENDER)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ],
        )
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(300)
        page.screenshot(path=out_path)
        browser.close()

# ================= API =================

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "DM Image Generator is running"}), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)
    if not data or "script" not in data:
        return jsonify({"error": "No script provided"}), 400

    script = data["script"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        img_path = tmp / "output.png"

        messages = parse_script(script)
        html = build_html(messages)

        try:
            render_html(html, str(img_path))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return send_file(
            img_path,
            mimetype="image/png",
            as_attachment=False
        )

# ================= START =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





