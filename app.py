import os
import base64
import tempfile
from pathlib import Path

from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

app = Flask(__name__)

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

def apply_rounded_mask(src, dst, radius=20):
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius, fill=255)

    out = Image.new("RGBA", (w, h))
    out.paste(img, (0, 0), mask)
    out.save(dst)

def parse_script(text):
    msgs = []
    y = 50
    for line in text.splitlines():
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

def render_html(html, out):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.set_content(html)
        page.wait_for_timeout(300)
        page.screenshot(path=out)
        browser.close()

# ================= API =================


@app.route("/")
def home():
    return "DM Image Generator is running! Use /generate to generate images."

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    script = data.get("script")

    if not script:
        return jsonify({"error": "No script provided"}), 400

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        img_path = tmp / "output.png"

        messages = parse_script(script)
        html = build_html(messages)

        render_html(html, str(img_path))

        return send_file(img_path, mimetype="image/png")

# ================= START =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

