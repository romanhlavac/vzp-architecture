#!/usr/bin/env python3
"""Řízená kontrola a oprava zaoblení doménových kontejnerů Miro.

Bez identifikátorů boardu a bez klientských textů ve zdrojovém kódu a logu.
"""

import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ZAKLAD_API = "https://api.miro.com/v2"
SIRKA_RAMCE = 4470
VYSKA_RAMCE = 5650
SIRKA_KONTEJNERU = 635
VYSKA_KONTEJNERU = 182
POCET_KONTEJNERU = 19
HLAVICKY = {"Accept": "application/json"}

token = os.environ.get("MIRO_DIAGNOSTIC_TOKEN", "").strip()
board = os.environ.get("MIRO_DIAGNOSTIC_BOARD_ID", "").strip()
rezim = os.environ.get("REZIM", "kontrola").strip()
if not token or not board or rezim not in {"kontrola", "pilot", "oprava"}:
    print("CHYBA: chybí tajné hodnoty nebo je neplatný režim.")
    sys.exit(2)


def pozadavek(cesta, metoda="GET", telo=None, parametry=None):
    cesta = cesta.lstrip("/")
    url = ZAKLAD_API + "/boards/" + urllib.parse.quote(board, safe="") + "/" + cesta
    if parametry:
        url += "?" + urllib.parse.urlencode(parametry)
    payload = json.dumps(telo, ensure_ascii=False).encode("utf-8") if telo is not None else None
    headers = dict(HLAVICKY)
    headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers, method=metoda)
    try:
        with urllib.request.urlopen(req, timeout=25) as odpoved:
            return json.load(odpoved)
    except urllib.error.HTTPError as exc:
        # Nikdy nevypisovat požadavek, identifikátory, token ani tělo odpovědi.
        raise RuntimeError("Miro API vrátilo HTTP " + str(exc.code)) from None
    except Exception:
        raise RuntimeError("Miro API nelze bezpečně načíst.") from None


def seznam(parametry):
    nalezene = []
    kurzor = None
    for _ in range(30):
        q = dict(parametry)
        q["limit"] = "50"
        if kurzor:
            q["cursor"] = kurzor
        data = pozadavek("items", parametry=q)
        nalezene.extend(data.get("data", []))
        kurzor = data.get("cursor")
        if not kurzor:
            return nalezene
    raise RuntimeError("Překročen limit stránkování. Bez zápisu.")


def rozmer(polozka, slozka, cil):
    try:
        return math.isclose(float(polozka.get("geometry", {}).get(slozka)), cil, abs_tol=1.0)
    except (ValueError, TypeError):
        return False


def nacti_tvary():
    ramce = seznam({"type": "frame"})
    kandidati = [
        ram for ram in ramce
        if rozmer(ram, "width", SIRKA_RAMCE) and rozmer(ram, "height", VYSKA_RAMCE)
    ]
    if len(kandidati) != 1:
        raise RuntimeError("Kontrolní rámec není jednoznačný. Bez zápisu.")

    prvky = seznam({"parent_item_id": str(kandidati[0]["id"]), "type": "shape"})
    odpovidajici = [
        item for item in prvky
        if rozmer(item, "width", SIRKA_KONTEJNERU)
        and rozmer(item, "height", VYSKA_KONTEJNERU)
    ]
    if len(odpovidajici) != POCET_KONTEJNERU:
        raise RuntimeError("Počet kontejnerů se od očekávání liší. Bez zápisu.")

    # Detailní čtení slouží k porovnání před změnou a po ní.
    tvary = [pozadavek("shapes/" + str(item["id"])) for item in odpovidajici]
    if any(t.get("data", {}).get("shape") not in ("rectangle", "round_rectangle") for t in tvary):
        raise RuntimeError("Nalezen nepodporovaný typ tvaru. Bez zápisu.")
    return tvary


def podpis(t):
    # Ověřujeme zachování textu, stylu, geometrie, polohy i rodiče.
    return {k: t.get(k) for k in ("style", "position", "geometry", "parent")}, t.get("data", {}).get("content")


def zmenit(t):
    identifikator = str(t["id"])
    data = {"shape": "round_rectangle"}
    if "content" in t.get("data", {}):
        data["content"] = t["data"]["content"]
    pozadavek("shapes/" + identifikator, metoda="PATCH", telo={"data": data})
    nova = pozadavek("shapes/" + identifikator)
    if nova.get("data", {}).get("shape") != "round_rectangle" or podpis(nova) != podpis(t):
        raise RuntimeError("Změna nebyla beze zbytku ověřena; zastavuji další úpravy.")


try:
    tvary = nacti_tvary()
    zaculene = [t for t in tvary if t["data"]["shape"] == "round_rectangle"]
    nevyhovujici = [t for t in tvary if t["data"]["shape"] == "rectangle"]
    print("Kontrola: nalezeno 19 kontejnerů. Zaoblené: %d. K opravě: %d." % (
        len(zaculene), len(nevyhovujici)
    ))
    if rezim == "kontrola":
        print("Pouze čtení: na boardu nebyla provedena žádná změna.")
    elif rezim == "pilot":
        if not nevyhovujici:
            print("Pilot není potřeba: všechny kontejnery jsou již zaoblené.")
        else:
            zmenit(sorted(nevyhovujici, key=lambda x: str(x["id"]))[0])
            print("Pilot: změněn právě jeden původní objekt. Požadována vizuální revize.")
    else:
        if len(zaculene) < 10 or not nevyhovujici:
            raise RuntimeError("Chybí ověřený pilot nebo již není co měnit. Bez zápisu.")
        for t in sorted(nevyhovujici, key=lambda x: str(x["id"])):
            zmenit(t)
        tvary_po = nacti_tvary()
        if sum(t.get("data", {}).get("shape") == "round_rectangle" for t in tvary_po) != 19:
            raise RuntimeError("Kontrola celkového výsledku neprošla.")
        print("Hotovo: všech 19 kontejnerů má typ round_rectangle.")
except RuntimeError as err:
    print("CHYBA: " + str(err))
    sys.exit(1)
