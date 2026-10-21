# CES DEMO: read-only Miro REST → SVG/PNG proxy

Status: technical renderer pilot/full CI PASS (2026-10-21); **native Miro G4 OPEN**.

- Python: `automatizace/miro/ces_demo_frame_render.py`
- Workflow: `.github/workflows/miro-ces-demo-frame-render.yml`
- Board: accessed only from existing `miro-external-probe` Actions secrets.
- Workflow `push` defaults to `pilot`; for all four frames manually dispatch with `scope=all`.
- Miro board contents are **never published** in repo or CI logs; only aggregate scalar metrics.
- The ZIP containing SVG, PNG and diagnostic JSON is envelope-encrypted using the public CMS certificate `ces_demo_render_recipient.crt`. The public certificate alone **cannot decrypt** the output.
- Keep the corresponding **private key outside GitHub and Project Sources**. The current certificate was intentionally generated as an ephemeral one-time delivery credential. For future runs, rotate to a new authorized recipient certificate held by the operator; do not assume any future session has the current private key.
- Action artifact retention: one day. Download and decrypt in an approved private workspace; never attach the unencrypted archive to a public issue or release.
- REST source frame IDs are fixed for CES DEMO and require fresh identity/read-back before interpreting metrics.
- Current limitations: this is an approximation of Miro-native typography/routing, not a browser/UI export. Some Miro types (e.g. `data_table_format`) are not rendered. Never mark `G4 Native Visual PASS` merely because CI succeeded.
- Runtime prerequisites: Python 3, Pillow, CairoSVG, OpenSSL, Miro REST token with board read permissions.

Observed full run: https://github.com/romanhlavac/vzp-architecture/actions/runs/39602903955

G1 semantic and G4 native visual review remain separate. Do not treat private business data or rendered diagrams as formally approved VZP decisions.
