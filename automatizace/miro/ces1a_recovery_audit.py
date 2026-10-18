#!/usr/bin/env python3
"""Read-only recovery inventory after an interrupted CES-1A update."""
from ces1a_branch_approved import page,call,id,xx,yy,ww,hh,txt,close,tag,edge,EXTRA,ZOOM_EXTRA
fs=page("items",{"type":"frame"})
target=[x for x in fs if close(ww(x),6075,25) and (close(hh(x),7746,25) or close(hh(x),7746+EXTRA+ZOOM_EXTRA,25))]
if len(target)!=1:raise RuntimeError("1A unique frame absent")
f=target[0]
children=page("items",{"parent_item_id":id(f)})
dom=[v for v in children if v.get("type")=="shape" and tag(v) and "Aktéři" in txt(v) and ww(v)>2900]
ref=[v for v in page("items",{"type":"text"}) if
    "HEURISTIKY HRANIC DOMÉN" in txt(v) or "ZDROJE DEMO 1A" in txt(v)]
cs=page("connectors")
member={id(x) for x in children}
inside=[c for c in cs if edge(c,"startItem") in member and edge(c,"endItem") in member]
from collections import Counter
print("RECOVERY STATE:")
print("frame dimensions",round(ww(f)),round(hh(f)))
print("frame children types",dict(Counter(x.get("type") for x in children)))
print("domains",len(dom),"expanded",sum(hh(x)>300 for x in dom))
print("connectors",len(inside),"total on board",len(cs))
print("reference blocks",len(ref),"positions",[(round(xx(x)),round(yy(x))) for x in ref])
print("event count",sum(x.get("type")=="sticky_note" for x in children))
print("metadata category counts",dict(Counter(tag(x) for x in dom)))

old_centers=[468,735,1004,1273,1542,1811,2080,2349,2618,2887,3156,3425,3694,3963,4232,4501,4770,5039,5308,5577]
print("CURRENT DOMAIN Y/HEIGHT:",[(tag(x),round(yy(x)),round(hh(x))) for x in sorted(dom,key=yy)])
notes=[x for x in children if x.get("type")=="sticky_note"]
print("STICKIES ON ORIGINAL ROW CENTERS:",[sum(abs(yy(n)-cy)<=40 for n in notes) for cy in old_centers])
reasons=[x for x in children if x.get("type")=="shape" and "BOUNDARY RATIONALE" in txt(x).upper()]
print("RATIONALE SHAPES EXPANDED:",sum(hh(x)>300 for x in reasons),"TOTAL:",len(reasons))
print("TEXT OUTSIDE TOP:",sum(yy(x)>7200 for x in children if x.get("type")=="text"))

from collections import Counter
alltexts=[x for x in children if x.get("type")=="text"]
allnotes=[x for x in children if x.get("type")=="sticky_note"]
testcodes=["S0","B1","B2","B3","B6","B8","B9"]
expected_h=["H01","H03","H04","H07","H09","H10","H11","H12","H13","H14","H15"]
reason_map={}
for c in testcodes:
    d=next(z for z in dom if tag(z)==c)
    rats=[x for x in children if x.get("type")=="shape" and
          "BOUNDARY RATIONALE" in txt(x).upper() and abs(yy(x)-yy(d))<40]
    if len(rats)!=1:raise RuntimeError("Boundary rationale count changed")
    t=txt(rats[0])
    if not all(word in t for word in ("Pravidla","Životní cyklus","Využití","Odpovědnost","H15")):
        raise RuntimeError("Four-test boundary rationale incomplete")
    reason_map[c]=len(t)
titlecount=sum("CES INTERACTION ZOOM" in txt(z).upper() for z in alltexts)
xref=[c for c in ["D01","D04","D06","D08","D09"]
      if any(c+" ·" in txt(z) for z in alltexts)]
branch=sum(any(word in txt(z) for word in
    ("Standardní ztotožnění","Kontraktace poskytovatele",
     "Ukončení vztahu","Přerozdělování","Refundace a vyúčtování"))
    for z in alltexts)
if len(allnotes)!=131 or len(inside)!=51 or titlecount!=1 or len(xref)!=5 or branch<4:
    raise RuntimeError("Final 1A acceptance inventory mismatch")
if any((z.get("style") or {}).get("strokeColor")!="#000000" for z in inside):
    raise RuntimeError("Non-black connector in approved 1A")
if len({(edge(z,"startItem"),edge(z,"endItem")) for z in inside})!=len(inside):
    raise RuntimeError("Duplicate connector endpoint pair")
older=0
for d in dom:
    old=[n for n in allnotes if abs(yy(n)-yy(d))<380 and
         str(n.get("createdAt",""))<str(d.get("createdAt",""))]
    if tag(d) in testcodes:older+=len(old)
print("APPROVED READBACK PASS: 131 native event cards; 51 distinct black connectors")
print("FOUR-TEST BOUNDARY RATIONALE PASS:",len(reason_map),"regions with Hxx IDs")
print("INTERACTION ZOOM PASS: 5 event references; branch-label sample",branch)
print("LAYER VISIBILITY RISK, heuristic count (not a render):",older)

# Visual-layout metrics. No business text or object IDs printed.
codes=["S0","B1","B2","B3","B6","B8","B9"]
for code in codes:
    d=next(z for z in dom if tag(z)==code)
    rat=next(z for z in reasons if abs(yy(z)-yy(d))<40)
    block=txt(d)
    rtext=txt(rat)
    font=(d.get("style") or {}).get("fontSize")
    near=[z for z in children if z.get("type")=="text" and abs(yy(z)-yy(d)) < (hh(d)/2+85)
          and not any(word in txt(z) for word in ("ZOOM", "D01", "D04", "D06", "D08", "D09"))]
    labels=sorted([(round(xx(z)),round(yy(z)-yy(d)),round(ww(z)),len(txt(z)),(z.get("style") or {}).get("fontSize")) for z in near],key=lambda x:x[1])
    print("LAYOUT",code,"domain",round(xx(d)),round(yy(d)),round(ww(d)),round(hh(d)),
          "font",font,"chars",len(block),"lines",block.count("\n")+block.count("<br/>"),
          "has4tests",all(t in block for t in ("Pravidla","Životní cyklus","Využití","Odpovědnost")),
          "rationale",round(xx(rat)),round(yy(rat)),round(ww(rat)),round(hh(rat)),"chars",len(rtext),
          "near_text",labels)
print("SCENE TEXT COUNT",sum(z.get("type")=="text" for z in children))
