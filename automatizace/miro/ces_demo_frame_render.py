#!/usr/bin/env python3
"""Read-only Miro REST frame -> SVG/PNG approximation.

No private Miro content is logged or written to Git history. Encrypted CMS
envelope is the *only* uploaded artifact. THIS IS NOT A NATIVE MIRO SCREENSHOT.
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from xml.sax.saxutils import escape

BOARD = os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
TOKEN = os.environ["MIRO_DIAGNOSTIC_TOKEN"]
MODE = os.environ.get("RENDER_SCOPE", "pilot")
assert MODE in ("pilot", "all")
BASE = "https://api.miro.com/v2/boards/" + urllib.parse.quote(BOARD, safe="")
FRAMES = {
    "1b_map": "3458764687938964779",
    "1a_bp": "3458764687741774534",
    "1a_dl": "3458764687757375873",
    "1b_e2e": "3458764687942876552",
}
TARGETS = ["1b_map"] if MODE == "pilot" else list(FRAMES)
CERT = pathlib.Path("automatizace/miro/ces_demo_render_recipient.crt")
MAX_ITEMS = 1200
MAX_PIXELS = 4300

def api(path, params=None):
    url = BASE + "/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + TOKEN, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt + 1)
                continue
            raise RuntimeError("REST_READ_FAILED_HTTP_" + str(e.code)) from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < 3:
                time.sleep(2 ** attempt + 1)
                continue
            raise RuntimeError("REST_READ_UNCERTAIN_TRANSPORT") from None

def listing(path, params=None):
    out, cursor = [], None
    for page in range(130):
        query = dict(params or {}, limit=50)
        if cursor:
            query["cursor"] = cursor
        answer = api(path, query)
        out.extend(answer.get("data") or [])
        if len(out) > MAX_ITEMS * 4:
            raise RuntimeError("BOUNDED_INVENTORY_LIMIT")
        cursor = answer.get("cursor") or answer.get("nextCursor")
        if not cursor:
            return out
    raise RuntimeError("PAGINATION_NOT_EXHAUSTED")

def number(x, default=0):
    try:
        y = float(x)
        return y if math.isfinite(y) else default
    except (TypeError, ValueError):
        return default

def get_id(z):
    return str(z.get("id") or "")

def get_parent(z):
    return str((z.get("parent") or {}).get("id") or "")

def bounds(z, parent_w=None, parent_h=None):
    geom, pos = z.get("geometry") or {}, z.get("position") or {}
    w, h = number(geom.get("width"), 270), number(geom.get("height"), 100)
    w, h = max(w, 1), max(h, 1)
    cx, cy = number(pos.get("x")), number(pos.get("y"))
    origin = pos.get("origin") or "center"
    if origin == "top_left":
        return cx, cy, w, h
    return cx - w / 2, cy - h / 2, w, h

def content(z):
    source = str((z.get("data") or {}).get("content") or "")
    source = re.sub(r"(?i)<br\s*/?>", chr(10), source)
    source = re.sub(r"(?i)</(?:p|div|li|h[1-6])>", chr(10), source)
    source = re.sub(r"<[^>]+>", "", source)
    source = html.unescape(source)
    return chr(10).join(s.strip() for s in source.splitlines() if s.strip())

def valid_hex(c, default):
    c = str(c or "").strip()
    return c if re.match(r"^#[0-9a-fA-F]{6}$", c) else default

def color(z, key, default):
    return valid_hex((z.get("style") or {}).get(key), default)

def truncate(w):
    return int(min(MAX_PIXELS, max(1024, w * 1.25)))

def anchor(box, side, target=None):
    x, y, w, h = box
    side = (side or "").lower()
    if side == "left":
        return x, y + h / 2
    if side == "right":
        return x + w, y + h / 2
    if side == "top":
        return x + w / 2, y
    if side == "bottom":
        return x + w / 2, y + h
    mid = (x + w / 2, y + h / 2)
    if target is None:
        return mid
    dx, dy = target[0] - mid[0], target[1] - mid[1]
    return anchor(box, "right" if dx > 0 else "left") if abs(dx) > abs(dy) else anchor(box, "bottom" if dy > 0 else "top")

def svg_text(text, x, y, width, height, style, fill, box_type):
    fs = number(style.get("fontSize"), 27 if box_type == "sticky_note" else 24)
    fs = min(80, max(10, fs))
    if box_type == "sticky_note":
        fs = min(fs, 30)
    char_width = 0.53 * fs
    chars = max(7, int(max(30, width - 24) / char_width))
    lines = []
    for line in text.split(chr(10)):
        words, cur = line.split(), ""
        for word in words:
            if cur and len(cur) + len(word) + 1 > chars:
                lines.append(cur)
                cur = word
            elif cur:
                cur += " " + word
            else:
                cur = word
        lines.append(cur)
    spacing = fs * 1.20
    if len(lines) * spacing > height - 8:
        fs = max(9, min(fs, (height - 8) / max(1, len(lines)) / 1.20))
        spacing = fs * 1.20
    align = str(style.get("textAlign") or "left").lower()
    if align == "center":
        anchor_name, tx = "middle", x + width / 2
    elif align == "right":
        anchor_name, tx = "end", x + width - 10
    else:
        anchor_name, tx = "start", x + 10
    if str(style.get("textAlignVertical") or "").lower() == "middle":
        ty = y + (height - len(lines) * spacing) / 2 + fs
    else:
        ty = y + 11 + fs
    parts = []
    for i, line in enumerate(lines):
        if not line:
            continue
        parts.append(
            '<text x="{:.2f}" y="{:.2f}" font-family="DejaVu Sans,Arial,sans-serif" '
            'font-size="{:.2f}" text-anchor="{}" fill="{}">{}</text>'.format(
                tx, ty + spacing * i, fs, anchor_name, fill, escape(line)))
    return "".join(parts), len(lines)

def render_frame(name, frame_id, root):
    frame = api("items/" + frame_id)
    if frame.get("type") != "frame":
        raise RuntimeError("TARGET_NOT_FRAME")
    _, _, fw, fh = bounds(frame)
    if fw > 90000 or fh > 90000:
        raise RuntimeError("FRAME_UNEXPECTED_SIZE")
    item_list = listing("items", {"parent_item_id": frame_id})
    # Include nested elements, but do not touch other frames.
    queue, seen = list(item_list), {get_id(x) for x in item_list}
    cursor = 0
    while cursor < len(queue):
        z = queue[cursor]
        cursor += 1
        if z.get("type") == "frame":
            for ch in listing("items", {"parent_item_id": get_id(z)}):
                if get_id(ch) not in seen:
                    queue.append(ch)
                    seen.add(get_id(ch))
    if len(queue) > MAX_ITEMS:
        raise RuntimeError("TARGET_SCOPE_TOO_LARGE")
    connectors = listing("connectors")
    # Determine absolute coordinates relative to target frame top-left.
    lookup = {get_id(x): x for x in queue}
    absolute = {}
    def abs_bounds(z):
        zid = get_id(z)
        if zid in absolute:
            return absolute[zid]
        x, y, w, h = bounds(z)
        p = get_parent(z)
        if p == frame_id:
            result = (x, y, w, h)
        elif p in lookup:
            px, py, pw, ph = abs_bounds(lookup[p])
            result = (x + px, y + py, w, h)
        else:
            # Unsupported loose geometry: keep, but report.
            result = (x, y, w, h)
        absolute[zid] = result
        return result
    for z in queue:
        abs_bounds(z)

    chosen = []
    for z in connectors:
        sid = str((z.get("startItem") or {}).get("id") or "")
        eid = str((z.get("endItem") or {}).get("id") or "")
        if sid in absolute and eid in absolute:
            chosen.append(z)

    elements = []
    types = collections.Counter(z.get("type") or "unknown" for z in queue)
    elements.append('<rect x="0" y="0" width="{:.2f}" height="{:.2f}" fill="#ffffff"/>'.format(fw, fh))
    # Draw connectors under their endpoint nodes.
    for z in chosen:
        start, end = z["startItem"], z["endItem"]
        s_id, e_id = str(start["id"]), str(end["id"])
        bb1, bb2 = absolute[s_id], absolute[e_id]
        center2 = (bb2[0] + bb2[2] / 2, bb2[1] + bb2[3] / 2)
        p1 = anchor(bb1, start.get("snapTo"), center2)
        p2 = anchor(bb2, end.get("snapTo"), p1)
        p1 = anchor(bb1, start.get("snapTo"), p2)
        stroke = color(z, "strokeColor", "#536E7B")
        sw = min(7, max(1, number((z.get("style") or {}).get("strokeWidth"), 2)))
        dash = ' stroke-dasharray="13,8"' if "dash" in str((z.get("style") or {}).get("strokeStyle") or "").lower() else ""
        x1, y1 = p1
        x2, y2 = p2
        shape = str(z.get("shape") or "straight")
        if shape in ("curved", "elbowed"):
            bend = max(35, min(300, abs(x2 - x1) * 0.35))
            path = "M {:.2f},{:.2f} C {:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}".format(
                x1, y1, x1 + (bend if x2 >= x1 else -bend), y1,
                x2 - (bend if x2 >= x1 else -bend), y2, x2, y2)
        else:
            path = "M {:.2f},{:.2f} L {:.2f},{:.2f}".format(x1, y1, x2, y2)
        elements.append('<path d="{}" stroke="{}" stroke-width="{:.2f}" fill="none"{} marker-end="url(#arrow)"/>'.format(
            path, stroke, sw, dash))
    text_lines = 0
    unsupported = 0
    for z in queue:
        t = z.get("type") or ""
        if t == "frame":
            continue
        if t not in ("shape", "sticky_note", "text", "card"):
            unsupported += 1
            continue
        x, y, w, h = absolute[get_id(z)]
        style = z.get("style") or {}
        bg = color(z, "fillColor", "#fff1b8" if t == "sticky_note" else "#eaf4f5")
        ink = color(z, "color", "#223943")
        if t != "text":
            radius = 12 if t == "sticky_note" else 6
            elements.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" '
                            'rx="{}" fill="{}" stroke="#9aaeb8" stroke-width="1.6"/>'.format(
                                x, y, w, h, radius, bg))
        body = content(z)
        if body:
            txt, lc = svg_text(body, x, y, w, h, style, ink, t)
            elements.append(txt)
            text_lines += lc
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" height="{:.0f}" '
           'viewBox="0 0 {:.2f} {:.2f}"><defs><marker id="arrow" viewBox="0 0 10 10" '
           'refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           '<path d="M 0 0 L 10 5 L 0 10 Z" fill="#536E7B"/></marker></defs>{}</svg>').format(
               fw, fh, fw, fh, "".join(elements))
    import cairosvg
    from PIL import Image
    import io
    pixw = truncate(fw)
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=pixw,
                           output_height=max(300, int(pixw * fh / fw)))
    im = Image.open(io.BytesIO(png))
    if im.width < 900 or im.height < 250:
        raise RuntimeError("RENDER_DIMENSIONS_FAIL")
    (root / (name + ".svg")).write_text(svg, encoding="utf-8")
    (root / (name + ".png")).write_bytes(png)
    report = {"scope": name, "frame_id": frame_id,
              "frame_size": [fw, fh], "png_size": list(im.size),
              "direct_items": len(item_list), "all_items": len(queue),
              "item_types": types, "connectors": len(chosen),
              "text_lines": text_lines, "unsupported_items": unsupported,
              "kind": "MIRO_REST_SVG_APPROXIMATION", "native_g4": "OPEN"}
    (root / (name + "_report.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    # Output only scalar metrics. Never output board text/identifiers.
    print("RENDER_PROXY_OK", name, "items", len(queue),
          "connectors", len(chosen), "unsupported", unsupported,
          "pixels", im.width, im.height, flush=True)
    return report

def main():
    if not CERT.is_file():
        raise RuntimeError("MISSING_PUBLIC_ENCRYPTION_CERT")
    with tempfile.TemporaryDirectory(prefix="miro-ciread-") as td:
        src = pathlib.Path(td)
        report = {}
        for scope in TARGETS:
            report[scope] = render_frame(scope, FRAMES[scope], src)
        archive = src / "render.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in sorted(src.iterdir()):
                if f.name != archive.name:
                    z.write(f, arcname=f.name)
        out = pathlib.Path("encrypted-render.p7m")
        subprocess.run([
            "openssl", "cms", "-encrypt", "-binary", "-aes-256-cbc",
            "-in", str(archive), "-out", str(out),
            "-outform", "DER", str(CERT)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("ENCRYPTED_ARTIFACT_READY", out.stat().st_size,
              "sha256", hashlib.sha256(out.read_bytes()).hexdigest(),
              "mode", MODE, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Exception details may contain private content: deliberately redact.
        print("RENDER_FAIL", type(exc).__name__, flush=True)
        sys.exit(1)
