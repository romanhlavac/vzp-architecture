#!/usr/bin/env python3
"""Čtecí inventura jednoho vybraného rámce Miro. Do logu nejdou názvy ani ID položek."""
import collections
import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error

TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"].strip()
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"].strip()
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
assert TOKEN and BOARD

def get(path, params=None):
    url=BASE+path+(("?" + urllib.parse.urlencode(params)) if params else "")
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as ex:
        raise RuntimeError("Miro API HTTP "+str(ex.code)) from None

def listing(params):
    result=[]
    cursor=None
    for _ in range(30):
        q=dict(params)
        q["limit"]="50"
        if cursor: q["cursor"]=cursor
        resp=get("items",q)
        result.extend(resp.get("data",[]))
        cursor=resp.get("cursor")
        if not cursor: return result
    raise RuntimeError("Neočekávané stránkování")

def geo(x):
    g=x.get("geometry") or {}
    p=x.get("position") or {}
    return {k:round(float(v),1) for k,v in (("x",p.get("x")),("y",p.get("y")),("w",g.get("width")),("h",g.get("height"))) if v is not None}

frames=listing({"type":"frame"})
candidates=[f for f in frames if abs(float(f.get("geometry",{}).get("width",0))-6920)<20 and abs(float(f.get("geometry",{}).get("height",0))-7160)<20]
if len(candidates)!=1: raise RuntimeError("Cílový rámec nelze jednoznačně identifikovat")
fid=str(candidates[0]["id"])
items=listing({"parent_item_id":fid})
counts=collections.Counter(str(x.get("type")) for x in items)
print("POČTY_TYPŮ:",json.dumps(dict(counts),sort_keys=True,ensure_ascii=False))
domains=[]
for item in items:
    if item.get("type")!="shape": continue
    d=item.get("data") or {}
    html=d.get("content") or ""
    plain=re.sub("<[^>]+>"," ",html)
    key=re.search(r"(?:^|\s)([A-D][1-9]|S0)\s*[·.]",plain)
    if key and "Aktéři" in plain:
        domains.append((key.group(1),item))
print("POČET_DOMÉN:",len(domains))
print("GEOMETRIE_RÁMCE:",geo(candidates[0]))
for code,item in sorted(domains,key=lambda x:(x[1].get("position",{}).get("y",0),x[0])):
    d=item.get("data") or {}
    st=item.get("style") or {}
    print("DOMÉNA",code,"pozice_rozměry",geo(item),"typ",d.get("shape"),"barva",st.get("fillColor"),"vrstva",item.get("parent",{}).get("id") is not None)
for t in sorted(counts):
    if t not in {"connector","shape"}:
        sel=[i for i in items if i.get("type")==t]
        print("DALŠÍ_PRVKY",t,len(sel),"ukázka_geometrie",[geo(x) for x in sel[:25]])
connections=[x for x in items if x.get("type")=="connector"]
stylecount=collections.Counter()
for c in connections:
    st=c.get("style") or {}
    stylecount[(str(st.get("strokeColor")),str(st.get("strokeStyle")),str(st.get("strokeWidth")),str(c.get("shape")))]+=1
print("KONEKTORY_STYLY:",json.dumps([{"barva":k[0],"čára":k[1],"síla":k[2],"trasa":k[3],"počet":n} for k,n in stylecount.items()],ensure_ascii=False))
if connections:
    print("KONEKTORY_KLÍČE:",sorted(connections[0]))
    print("KONEKTORY_STYL_KLÍČE:",sorted((connections[0].get("style") or {}).keys()))
# Přímé podrobnosti o oddělovačích bez jejich identifikátorů a obsahu.
non_shapes=[x for x in items if x.get("type") not in {"shape","connector","sticky_note","text","frame"}]
for x in non_shapes[:30]:
    print("OSTATNÍ",x.get("type"),"geometrie",geo(x),"styl_keys",sorted((x.get("style") or {}).keys()))
