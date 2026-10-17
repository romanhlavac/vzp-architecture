#!/usr/bin/env python3
"""Úprava živého rámce Miro. Nezveřejňovat obsah, identifikátory ani odpovědi API."""
import collections
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN=os.environ.get("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.environ.get("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
MODE=os.environ.get("REZIM","kontrola").strip()
ALLOWED={"kontrola","sipky","pilot","pasma","separator","final"}
if not TOKEN or not BOARD or MODE not in ALLOWED:
    raise SystemExit("CHYBA: přístup k boardu nebo režim není připraven.")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"

def api(method,path,data=None,params=None):
    url=BASE+path+(("?" + urllib.parse.urlencode(params)) if params else "")
    body=json.dumps(data,ensure_ascii=False).encode("utf-8") if data is not None else None
    hdr={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None:hdr["Content-Type"]="application/json"
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,data=body,headers=hdr,method=method)
            with urllib.request.urlopen(req,timeout=30) as ans:
                raw=ans.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as err:
            if err.code in (429,500,502,503,504) and attempt<3:
                time.sleep(attempt*2+2);continue
            raise RuntimeError("Miro API selhalo (HTTP "+str(err.code)+").") from None
        except Exception:
            raise RuntimeError("Nedostupná odpověď Miro API.") from None

def listing(params):
    all_items=[];cursor=None
    for _ in range(40):
        q=dict(params,limit=50)
        if cursor:q["cursor"]=cursor
        data=api("GET","items",params=q)
        all_items+=data.get("data",[])
        cursor=data.get("cursor")
        if not cursor:return all_items
    raise RuntimeError("Překročen limit stránkování.")

def number(obj,path,default=0):
    x=obj
    for k in path:x=(x or {}).get(k)
    try:return float(x)
    except (TypeError,ValueError):return default

def xy(obj):return number(obj,("position","x")),number(obj,("position","y"))
def wh(obj):return number(obj,("geometry","width")),number(obj,("geometry","height"))
def label(obj):
    data=str((obj.get("data") or {}).get("content") or "")
    return html.unescape(re.sub("<[^>]*>"," ",data))
def code(obj):
    m=re.search(r"(?:^|\s)([A-D][1-9]|S0)\s*[·.]",label(obj))
    return m.group(1) if m and "Aktéři" in label(obj) else None

def get_frame():
    fs=listing({"type":"frame"})
    matches=[f for f in fs if abs(wh(f)[0]-6075)<20 and abs(wh(f)[1]-7746)<20]
    if len(matches)!=1:raise RuntimeError("Rámec 1A není jednoznačně určen.")
    frame=matches[0]
    children=listing({"parent_item_id":str(frame["id"])})
    dom={code(x):x for x in children if x.get("type")=="shape" and code(x)}
    if len(dom)!=20:raise RuntimeError("Nalezen neočekávaný počet doménových pásů.")
    notes=[x for x in children if x.get("type")=="sticky_note"]
    divs=[x for x in children if x.get("type")=="divider"]
    if len(notes)!=130 or len(divs) not in (0,19):
        raise RuntimeError("Počet událostí nebo oddělovačů neodpovídá modelu.")
    return frame,children,dom,notes,divs

def plan(dom,notes):
    prepared={}
    for k,d in dom.items():
        x,y=xy(d)
        matched=[n for n in notes if abs(xy(n)[1]-y)<=35]
        if not 4<=len(matched)<=8:
            raise RuntimeError("Počet událostí u řádku "+k+" je neočekávaný.")
        right=max(xy(n)[0]+wh(n)[0]/2 for n in matched)+72.0
        left=56.0
        width=right-left
        cx=(right+left)/2
        prepared[k]={"x":cx,"y":y,"width":width,"height":224.0,"notes":len(matched)}
    return prepared

def all_connectors():
    all_items=[];cursor=None
    for _ in range(20):
        q={"limit":50}
        if cursor:q["cursor"]=cursor
        resp=api("GET","connectors",params=q)
        all_items+=resp.get("data",[])
        cursor=resp.get("cursor")
        if not cursor:return all_items
    raise RuntimeError("Překročen limit konektorů.")

def inside_connections(children):
    known={str(c["id"]) for c in children}
    connected=[x for x in all_connectors() if
        str((x.get("startItem") or {}).get("id")) in known and
        str((x.get("endItem") or {}).get("id")) in known]
    if len(connected)!=34:raise RuntimeError("Počet konektorů 1A se změnil.")
    return connected

def fix_arrows(children):
    cons=inside_connections(children)
    target=[x for x in cons if (x.get("style") or {}).get("strokeColor")=="#217b91"]
    if len(target) not in (0,7):
        raise RuntimeError("Neočekávaný počet modrých vazeb.")
    for c in target:
        cid=str(c["id"])
        fresh=api("GET","connectors/"+cid)
        if (fresh.get("style") or {}).get("strokeColor")!="#217b91":
            raise RuntimeError("Spojnice se mezitím změnila.")
        before=((fresh.get("startItem") or {}).get("id"),(fresh.get("endItem") or {}).get("id"),fresh.get("shape"))
        api("PATCH","connectors/"+cid,{"style":{"strokeColor":"#000000","strokeStyle":"normal"}})
        after=api("GET","connectors/"+cid)
        rest=((after.get("startItem") or {}).get("id"),(after.get("endItem") or {}).get("id"),after.get("shape"))
        style=after.get("style") or {}
        if before!=rest or style.get("strokeColor")!="#000000" or style.get("strokeStyle")!="normal":
            raise RuntimeError("Ověření aktualizované spojnice selhalo.")
    print("ŠIPKY: původně modrých spojnic sjednoceno:",len(target))

def resize(d,goal):
    sid=str(d["id"]);fresh=api("GET","shapes/"+sid)
    if code(fresh)!=code(d) or (fresh.get("data") or {}).get("shape")!="round_rectangle":
        raise RuntimeError("Doménový tvar změněn před aktualizací.")
    baseline={k:fresh.get(k) for k in ("data","style","parent")}
    g={"width":round(goal["width"],1),"height":goal["height"]}
    p={"x":round(goal["x"],1),"y":round(goal["y"],1),"origin":"center"}
    api("PATCH","shapes/"+sid,{"geometry":g,"position":p})
    out=api("GET","shapes/"+sid)
    if any(out.get(k)!=v for k,v in baseline.items()):
        raise RuntimeError("Při změně rozměrů došlo ke změně obsahu nebo stylu.")
    if abs(wh(out)[0]-g["width"])>2 or abs(wh(out)[1]-g["height"])>2 or abs(xy(out)[0]-p["x"])>2 or abs(xy(out)[1]-p["y"])>2:
        raise RuntimeError("Nový rozměr nebo umístění neprošlo kontrolou.")

def resize_rows(dom,notes,only_pilot=False):
    planned=plan(dom,notes)
    selected=["A2"] if only_pilot else [c for c in sorted(dom) if c!="A1"]
    for k in selected:
        d=dom[k];new=planned[k]
        if abs(wh(d)[0]-new["width"])<2 and abs(wh(d)[1]-new["height"])<2 and abs(xy(d)[0]-new["x"])<2:
            continue
        resize(d,new)
    print("PÁSY: kontrola dokončena; zpracovaných řádků:",len(selected))

def remove_dividers(divs,children):
    if not divs:
        print("ODDĚLOVAČE: žádné nezbývají.")
        return
    if len(divs)!=19:raise RuntimeError("Nesouhlasí počet oddělovačů.")
    for x in divs:
        if abs(wh(x)[1]-2)>0.5 or not wh(x)[0]>5700:
            raise RuntimeError("Oddělovač nesplňuje bezpečnostní filtr.")
        api("DELETE","items/"+str(x["id"]))
    print("ODDĚLOVAČE: odstraněno",len(divs))

def accept(dom,notes,divs,children):
    p=plan(dom,notes)
    mismatched=[k for k,d in dom.items() if abs(wh(d)[0]-p[k]["width"])>2 or abs(wh(d)[1]-224)>2 or abs(xy(d)[0]-p[k]["x"])>2]
    cs=inside_connections(children)
    black=[c for c in cs if (c.get("style") or {}).get("strokeColor")=="#000000"
           and (c.get("style") or {}).get("strokeStyle")=="normal"]
    orange=[c for c in cs if (c.get("style") or {}).get("strokeColor")=="#9b642f"]
    print("VÝSLEDEK: domén",len(dom),"nesouladů",len(mismatched),"plných černých vazeb",len(black),"hnědých vazeb",len(orange),"oddělovačů",len(divs))
    if mismatched or len(black)!=7 or len(orange)!=27 or divs:
        raise RuntimeError("Finální akceptace neprošla.")

def run():
    f,children,dom,notes,divs=get_frame()
    print("PREFLIGHT: 20 domén, 130 událostí, %d oddělovačů."%len(divs))
    if MODE=="kontrola":
        print("KONTROLA BEZ ZÁPISU");return
    if MODE=="sipky":
        fix_arrows(children)
    elif MODE=="pilot":
        resize_rows(dom,notes,only_pilot=True)
    elif MODE=="pasma":
        resize_rows(dom,notes)
    elif MODE=="separator":
        remove_dividers(divs,children)
    elif MODE=="final":
        accept(dom,notes,divs,children)

try:run()
except Exception as err:
    print("CHYBA:",str(err) if isinstance(err,RuntimeError) else "Neočekávaná interní chyba.")
    sys.exit(1)
