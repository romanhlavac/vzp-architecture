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
assert MODE in ("pilot", "pilot_bp", "all")
BASE = "https://api.miro.com/v2/boards/" + urllib.parse.quote(BOARD, safe="")
FRAMES = {
    "1b_map": "3458764687938964779",
    "1a_bp": "3458764687741774534",
    "1a_dl": "3458764687757375873",
    "1b_e2e": "3458764687942876552",
}
TARGETS = ["1b_map"] if MODE == "pilot" else (["1a_bp"] if MODE == "pilot_bp" else list(FRAMES))
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

# Miro REST may expose named sticky-note colors, not just CSS hex values.
# Primary event orange is calibrated against an authorized native Miro reference.
NATIVE_COLORS = {
    "orange": "#FFBC83", "light_orange": "#FFBC83", "light orange": "#FFBC83",
    "light_yellow": "#FFF1B8", "yellow": "#FFF1B8",
    "light_green": "#BFE3A4", "green": "#BFE3A4",
    "light_blue": "#BDE6F4", "blue": "#BDE6F4",
    "purple": "#C9B4EF", "light_purple": "#DCCBF7",
    "pink": "#F7B5D0", "red": "#F5A0A0", "gray": "#E6E6E6",
    "grey": "#E6E6E6", "black": "#263238", "white": "#FFFFFF"
}

def valid_hex(c, default):
    c = str(c or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", c):
        return c.upper()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", c):
        return "#" + "".join(v * 2 for v in c[1:]).upper()
    return NATIVE_COLORS.get(c.lower(), default)

def color(z, key, default):
    return valid_hex((z.get("style") or {}).get(key), default)

def truncate(w):
    # This is overview only; use the SVG master and independent high-resolution
    # focus tiles for readable content. A fixed 4300 px overview is not a zoom.
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

def svg_text(text, x, y, width, height, style, fill, box_type, native_html=""):
    from PIL import ImageFont
    fs_initial = number(style.get("fontSize"), 27 if box_type == "sticky_note" else 24)
    is_sticky = box_type == "sticky_note"
    fs = min(96, max(10, fs_initial * (1.95 if is_sticky else 1.0)))
    padx = max(10, min(22, width * 0.045))
    inner_width = max(12, width - 2 * padx)

    def font_for(size):
        return ImageFont.truetype("DejaVuSans.ttf", max(8, int(round(size))))

    def measure(font, value):
        return font.getlength(value)

    def wrap(font):
        out = []
        for source_line in text.split(chr(10)):
            words = source_line.split()
            if not words:
                out.append("")
                continue
            current = ""
            for word in words:
                candidate = (current + " " + word) if current else word
                if current and measure(font, candidate) > inner_width:
                    out.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                out.append(current)
        return out

    # Iteratively choose the largest font which both contains native text and
    # fits the note height. Geometry is authoritative and never silently grown.
    while True:
        font = font_for(fs)
        lines = wrap(font)
        line_height = fs * 1.18
        too_wide = any(measure(font, line) > inner_width + 1 for line in lines if line)
        too_high = len(lines) * line_height > max(1, height - 12)
        if not (too_wide or too_high) or fs <= 13:
            break
        fs *= 0.965

    align = str(style.get("textAlign") or ("center" if is_sticky else "left")).lower()
    anchor_name, tx = ("middle", x + width / 2) if align == "center" else (
        ("end", x + width - padx) if align == "right" else ("start", x + padx))
    vertical = str(style.get("textAlignVertical") or ("middle" if is_sticky else "top")).lower()
    if vertical in ("middle", "center"):
        ty = y + (height - len(lines) * line_height) / 2 + 0.91 * fs
    else:
        ty = y + 10 + fs
    deco = str(style.get("textDecoration") or "").lower()
    underline = is_sticky or "underline" in deco or "<u>" in native_html.lower()
    weight = str(style.get("fontWeight") or "normal").lower()
    bold = "bold" if weight in ("bold", "700", "800", "900") else "normal"
    decoration = ' text-decoration="underline"' if underline else ""
    parts = []
    for i, line in enumerate(lines):
        if not line:
            continue
        yy = ty + line_height * i
        parts.append(
            '<text x="{:.2f}" y="{:.2f}" font-family="DejaVu Sans,Arial,sans-serif" '
            'font-size="{:.2f}" font-weight="{}" text-anchor="{}" fill="{}"{}>{}</text>'.format(
                tx, yy, fs, bold, anchor_name, fill, decoration, escape(line)))
        if underline:
            linew = min(inner_width, max(4, measure(font, line)))
            lx = tx - linew / 2 if anchor_name == "middle" else (
                 tx - linew if anchor_name == "end" else tx)
            parts.append('<path d="M {:.2f},{:.2f} h {:.2f}" stroke="{}" '
                         'stroke-width="{:.2f}" opacity="0.92"/>'.format(
                             lx, yy + fs * 0.10, linew, fill, max(0.85, fs * 0.048)))
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
    # Draw each semantic Miro connector as one SVG path.
    # Native endpoints, line color/dash and captions are preserved where exposed.
    for z in chosen:
        start, end = z["startItem"], z["endItem"]
        s_id, e_id = str(start["id"]), str(end["id"])
        bb1, bb2 = absolute[s_id], absolute[e_id]
        center2 = (bb2[0] + bb2[2] / 2, bb2[1] + bb2[3] / 2)
        p1 = anchor(bb1, start.get("snapTo"), center2)
        p2 = anchor(bb2, end.get("snapTo"), p1)
        p1 = anchor(bb1, start.get("snapTo"), p2)
        stroke = color(z, "strokeColor", "#D97706")
        sw = max(1.15, min(7, number((z.get("style") or {}).get("strokeWidth"), 2)))
        st = str((z.get("style") or {}).get("strokeStyle") or "").lower()
        dash = ' stroke-dasharray="13,8"' if "dash" in st else ""
        x1, y1 = p1
        x2, y2 = p2
        shape = str(z.get("shape") or "straight").lower()
        if "elbow" in shape:
            midx = (x1 + x2) / 2
            path_d = "M {:.2f},{:.2f} L {:.2f},{:.2f} L {:.2f},{:.2f} L {:.2f},{:.2f}".format(
                x1, y1, midx, y1, midx, y2, x2, y2)
        elif "curve" in shape:
            bend = min(500, max(65, abs(x2 - x1) * 0.26))
            sign = 1 if x2 >= x1 else -1
            path_d = "M {:.2f},{:.2f} C {:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}".format(
                x1, y1, x1 + sign * bend, y1, x2 - sign * bend, y2, x2, y2)
        else:
            path_d = "M {:.2f},{:.2f} L {:.2f},{:.2f}".format(x1, y1, x2, y2)
        marker = "arrowTeal" if stroke.lower() in ("#007680", "#00838f", "#0097a7") else "arrowOrange"
        marker_end = ' marker-end="url(#{})"'.format(marker) if str((z.get("style") or {}).get("endStrokeCap") or "arrow").lower() != "none" else ""
        elements.append('<path d="{}" stroke="{}" stroke-width="{:.2f}" fill="none"{}{} />'.format(
            path_d, stroke, sw, dash, marker_end))
        # REST caption data is optional; omit fabricated labels.
        for caption in z.get("captions") or []:
            label = str((caption or {}).get("content") or "").strip()
            if not label:
                continue
            label = html.unescape(re.sub(r"<[^>]+>", "", label))
            if not label:
                continue
            xcap, ycap = (x1 + x2) / 2, (y1 + y2) / 2 - 8
            elements.append('<text x="{:.2f}" y="{:.2f}" font-family="Arial,sans-serif" '
                            'font-size="17" text-anchor="middle" fill="#4A5053">{}</text>'.format(
                                xcap, ycap, escape(label)))
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
        is_sticky = t == "sticky_note"
        bg = color(z, "fillColor", "#FFBC83" if is_sticky else "#EAF4F5")
        ink = color(z, "color", "#6C3100" if is_sticky else "#223943")
        if t != "text":
            if is_sticky:
                # Native Miro notes have near-square corners, a warm orange
                # fill and a subtle offset shadow, not a generic yellow card.
                # CairoSVG does not reliably apply feDropShadow. Explicit
                # offset underlay remains visible at every output resolution.
                elements.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" '
                                'fill="#666666" opacity="0.14"/>'.format(
                                    x + 2.7, y + 4.1, w, h))
                elements.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" '
                                'fill="{}" stroke="none"/>'.format(x, y, w, h, bg))
            else:
                elements.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" '
                                'rx="4" fill="{}" stroke="#9AAEB8" stroke-width="1.2"/>'.format(
                                    x, y, w, h, bg))
        body = content(z)
        if body:
            raw_html = str((z.get("data") or {}).get("content") or "")
            txt, lc = svg_text(body, x, y, w, h, style, ink, t, raw_html)
            elements.append(txt)
            text_lines += lc
    defs = ('<defs><filter id="stickyShadow" x="-15%" y="-15%" width="140%" height="150%">'
            '<feDropShadow dx="1.6" dy="3.8" stdDeviation="3.5" flood-color="#666666" flood-opacity="0.24"/>'
            '</filter><marker id="arrowTeal" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" '
            'fill="#007680"/></marker><marker id="arrowOrange" viewBox="0 0 10 10" '
            'refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
            '<path d="M0 0 L10 5 L0 10Z" fill="#D97706"/></marker></defs>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" height="{:.0f}" '
           'viewBox="0 0 {:.2f} {:.2f}">{}{}</svg>').format(
               fw, fh, fw, fh, defs, "".join(elements))
    import cairosvg
    from PIL import Image
    import io
    pixw = truncate(fw)
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=pixw,
                           output_height=max(300, int(pixw * fh / fw)))
    im = Image.open(io.BytesIO(png))
    if im.width < 900 or im.height < 250:
        raise RuntimeError("RENDER_DIMENSIONS_FAIL")
    # Native-scale precision export for a focus zone. The full-frame SVG
    # stays vector sharp. A 4300px overview alone is NOT a legible zoom.
    if name == "1a_bp":
        vx, vy = fw * 0.34, fh * 0.18
        vw, vh = fw * 0.33, fh * 0.19
        original_vb = 'viewBox="0 0 {:.2f} {:.2f}"'.format(fw, fh)
        tile_vb = 'viewBox="{:.2f} {:.2f} {:.2f} {:.2f}"'.format(vx, vy, vw, vh)
        focus_svg = svg.replace(original_vb, tile_vb, 1)
        focus_width = 3400
        focus_png = cairosvg.svg2png(bytestring=focus_svg.encode("utf-8"),
                  output_width=focus_width,
                  output_height=int(focus_width * vh / vw))
        (root / (name + "_focus.svg")).write_text(focus_svg, encoding="utf-8")
        (root / (name + "_focus.png")).write_bytes(focus_png)
    (root / (name + ".svg")).write_text(svg, encoding="utf-8")
    (root / (name + ".png")).write_bytes(png)
    report = {"scope": name, "frame_id": frame_id,
              "frame_size": [fw, fh], "png_size": list(im.size),
              "direct_items": len(item_list), "all_items": len(queue),
              "item_types": types, "connectors": len(chosen),
              "text_lines": text_lines, "unsupported_items": unsupported,
              "kind": "MIRO_REST_SVG_APPROXIMATION_V2_CALIBRATED", "native_g4": "OPEN"}
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
