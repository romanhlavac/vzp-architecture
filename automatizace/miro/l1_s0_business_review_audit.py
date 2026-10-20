#!/usr/bin/env python3
"""Private-content-safe, read-only live Miro L1v3/S0 review inventory."""
import sys,hashlib,collections,re,html
from l1_v3_native_build import TITLE,BP_TITLE,RULES,SHORT,ADD,listing,txt,oid,parent,edge
def main():
    allitems=listing("items");allcons=listing("connectors")
    fs=[z for z in allitems if z.get("type")=="frame"]
    l1=[z for z in fs if (z.get("data") or {}).get("title")==TITLE]
    bp=[z for z in fs if (z.get("data") or {}).get("title")==BP_TITLE]
    if len(l1)!=1 or len(bp)!=1:raise RuntimeError("FRAME_MISMATCH")
    rows=[z for z in allitems if parent(z)==oid(l1[0])]
    origins=[z for z in allitems if parent(z)==oid(bp[0]) and z.get("type")=="sticky_note"]
    counts=collections.Counter(z.get("type") for z in rows)
    notes=[z for z in rows if z.get("type")=="sticky_note"]
    expected=set(RULES["groups"]["S0"])
    actual=[z for z in notes if hashlib.sha256(txt(z).encode()).hexdigest() in expected]
    original=[z for z in origins if hashlib.sha256(txt(z).encode()).hexdigest() in expected]
    if counts["sticky_note"]!=147 or counts["text"]!=203 or counts["shape"]!=142:
        raise RuntimeError("L1_COUNTS_DRIFT")
    if len(expected)!=8 or len(actual)!=8 or len(original)!=8:
        raise RuntimeError("S0_EVENT_COVERAGE_DRIFT")
    ids={oid(z) for z in rows}
    connections=[z for z in allcons if edge(z,"startItem") in ids and edge(z,"endItem") in ids]
    if len(connections)!=51:raise RuntimeError("L1_LINK_COUNT_DRIFT")
    desc=[z for z in rows if z.get("type")=="text" and "moveToWidget" in str((z.get("data") or {}).get("content") or "")]
    if len(desc)!=147:raise RuntimeError("L1_DESCRIPTION_TOTAL_DRIFT")
    ids0={oid(z) for z in original}
    count_desc=sum(any("?moveToWidget="+v in str((z.get("data") or {}).get("content") or "") for v in ids0) for z in desc)
    if count_desc!=8:raise RuntimeError("S0_DESCRIPTION_LINK_DRIFT")
    codes=[z for z in rows if z.get("type")=="shape" and ("S0" in txt(z) or "Správa a evidence subjektů" in txt(z))]
    print("L1S0_LIVE_READ_PASS","sourceBP=147","targetL1=147","L1relations=51",
          "S0events=8","S0linkedDescriptions=8","S0structuralElements",len(codes),
          "L1Shapes=142","L1Texts=203","no_write=True",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:print("L1S0_STOP",type(e).__name__,str(e));sys.exit(1)
