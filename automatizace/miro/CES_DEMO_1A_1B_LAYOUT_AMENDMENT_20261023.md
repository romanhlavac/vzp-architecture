# CES DEMO — 1A/1B navigation and SC-05 style correction (2026-10-23)

Scope: **DEMO / WORKING**, no approved VZP target architecture, no business-domain boundary approval.

## Live change summary

- Live baseline: 65 native Miro frames / 703 connectors, BP v14 169 children and L1 DL v3 184 children.
- Native 1A header and an explicit 1A → 1B / S0 bridge created. Existing BP/DL frame IDs and all their business widgets remain in place.
- Added native 1B.C / 1B.D / 1B.E headings and deep links to the actual scenario, synthesis and 1C-evidence frames.
- Replaced unclear first 1B MAIN introduction by a named step/domain guide: `KROK 1B · S0 – Správa a evidence subjektů`, with exact links.
- Renamed 13 frames: removed `MAIN`, aligned named activities, inserted parent L1 `S0` and `S0.1/S0.2` where applicable. No semantic status promotion.
- SC-05 header and subheader, actor/participant/command/policy/read model shapes, and footer font sizes aligned with the other Process-Level ES scenarios. Native colors remain true to their semantics. Added S0.1 demo scene caption.
- *Open defect:* the 7 large native SC-05 stickies were NOT resized. REST PATCH `geometry.width` returned HTTP 200 with unchanged geometry for all 7; independent pilot with `geometry.height` plus `position` again returned unchanged geometry. Never interpret successful PATCH as verified geometry. Do not delete/recreate notes just for aesthetics without deliberate rewire/ID-impact approval.
- Preserved all BP/DL children and all 703 native relationship endpoint pairs (explicit before/after comparison). 70 frames and 17 SC-05 children after change.
- Updated historical read-only verification to expect current frame names; normal workflow remains `verify`. New scoped workflow returned to `audit`.

## New navigation frames (live)

- [1A header](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688236063826)
- [1A → 1B / S0 bridge](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688236063901)
- [1B.C scenario section](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688236189023)
- [1B.D synthesis section](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688236189804)
- [1B.E evidence section](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688236315081)
- [1B/S0 entry guide](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487286)
- [SC-05](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688202201527)

## Acceptance

| Gate | Result | Basis |
|---|---|---|
| G1 | PASS (DEMO scope) | No business event/subdomain decision modified. |
| G2 | PASS | REST read-back: 70 frames, 703 original connectors, unchanged BP/DL child snapshots. |
| G3 | PASS / proxy for new section rectangles; SC-05 size gap OPEN | New sections occupy free horizontal/vertical lanes; extra native sticky dimensions remain non-harmonized. |
| G4 | **OPEN** | Miro MCP org call quota exhausted; no fresh independently reviewed native screenshot of this change. Prior historical G4 PASS does not extend to this revision. |

[One-off guarded apply and structural read-back](https://github.com/romanhlavac/vzp-architecture/actions/runs/39975546202).
[Independent resize pilot (not effective)](https://github.com/romanhlavac/vzp-architecture/actions/runs/39976370288).

No Miro AI or production architecture change.
