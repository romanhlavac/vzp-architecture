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
