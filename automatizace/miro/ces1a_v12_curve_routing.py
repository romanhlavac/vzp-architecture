#!/usr/bin/env python3
"""CES-1A v12 routing-only repair, using live Miro REST v2.
Audited modes: audit, pilot (one connector), apply (four node positions + 46 connectors).
No client board title/content/IDs or bearer credentials are committed or logged.
No create/delete operation, no business-content change, no historical 1A replay.
"""
import hashlib, json, math, os, sys, time, urllib.parse, urllib.request, urllib.error

MODE=os.environ.get("V12_ROUTE_MODE","audit").strip()
TOKEN=os.environ.get("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.environ.get("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
if MODE not in ("audit","pilot","apply") or not TOKEN or not BOARD:
    sys.exit("FAIL: invalid mode or missing configured environment")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")
EXPECTED_EVENTS=110
EXPECTED_LINKS=46
WIDTH=16746.0
HEIGHT=10480.0
# Only the expected geometric location of this specific frame, not a board ID.
FRAME_CX=179373.0
FRAME_CY=6540.0
# Existing current-note coordinates are relative to the target frame's top-left.
# Explicit pixel baseline guards avoid moving any manually edited/stale content.
MOVES=(
    ((418,1861),(5720,2070)),     # first active overall relationship
    ((3161,1662),(5720,2470)),    # last active overall relationship
    ((3102,550),(1322,2310)),     # cross-lane source 1
    ((3992,550),(2212,2310)),     # cross-lane source 2
)
SIDES=("top","right","bottom","left")
DIR={"top":(0,-1),"right":(1,0),"bottom":(0,1),"left":(-1,0)}

def request(method, path, payload=None, params=None):
    url=BASE+"/"+path
    if params: url+="?"+urllib.parse.urlencode(params)
    body=None if payload is None else json.dumps(payload, separators=(",",":")).encode("utf-8")
    headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    for trial in range(5):
        try:
            req=urllib.request.Request(url,data=body,headers=headers,method=method)
            with urllib.request.urlopen(req,timeout=35) as response:
                raw=response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429,502,503,504) and trial<4:
                time.sleep(min(20,2**trial+2)); continue
            raise RuntimeError("REST operation failed HTTP "+str(exc.code)+" on "+path.split("/")[0]) from None
        except Exception:
            if trial<2:
                time.sleep(trial+1); continue
            raise RuntimeError("REST transport failure in "+path.split("/")[0]) from None

def listing(path,query=None):
    out=[];cursor=None
    for _ in range(100):
        params=dict(query or {})
        params["limit"]=50
        if cursor: params["cursor"]=cursor
        obj=request("GET",path,params=params)
        out.extend(obj.get("data",[]))
        cursor=obj.get("cursor")
        if not cursor: return out
    raise RuntimeError("REST pagination not exhausted")

def ident(x): return str(x.get("id",""))
def geom(x): return x.get("geometry") or {}
def pos(x): return x.get("position") or {}
def xy(x): return float(pos(x).get("x") or 0),float(pos(x).get("y") or 0)
def wh(x): return float(geom(x).get("width") or 0),float(geom(x).get("height") or 0)
def near(a,b,tol=5):return abs(a-b)<=tol
def src(c):return str((c.get("startItem") or {}).get("id") or "")
def dst(c):return str((c.get("endItem") or {}).get("id") or "")
def digest_text(x):
    return hashlib.sha256(str((x.get("data") or {}).get("content") or "").encode()).hexdigest()
def style_fingerprint(x):
    return json.dumps(x.get("style") or {},sort_keys=True)
def caption_fingerprint(x):
    return json.dumps(x.get("captions") or [],sort_keys=True)

def load():
    frames=listing("items",{"type":"frame"})
    choices=[f for f in frames if near(wh(f)[0],WIDTH,5) and near(wh(f)[1],HEIGHT,5)
             and near(xy(f)[0],FRAME_CX,8) and near(xy(f)[1],FRAME_CY,8)]
    if len(choices)!=1:
        print("FRAME_GEOMETRY_DIAGNOSTIC:",[(round(wh(z)[0]),round(wh(z)[1]),round(xy(z)[0]),round(xy(z)[1])) for z in frames if 15000<wh(z)[0]<22000][:30])
        raise RuntimeError("V12 frame geometry / identity not unique: "+str(len(choices)))
    f=choices[0];fid=ident(f)
    children=listing("items",{"parent_item_id":fid})
    notes={ident(x):x for x in children if x.get("type")=="sticky_note"}
    if len(notes)!=EXPECTED_EVENTS:
        raise RuntimeError("V12 event-card inventory drift: "+str(len(notes)))
    con_all=listing("connectors")
    linked=[c for c in con_all if src(c) in notes and dst(c) in notes]
    if len(linked)!=EXPECTED_LINKS:
        raise RuntimeError("V12 connector inventory drift: "+str(len(linked)))
    if len({ident(c) for c in linked})!=EXPECTED_LINKS:
        raise RuntimeError("V12 duplicate connector identities")
    if len({(src(c),dst(c)) for c in linked})!=EXPECTED_LINKS:
        raise RuntimeError("V12 duplicate endpoint pairs")
    return f,notes,linked

def map_moves(frame,notes):
    selected={}
    used=set()
    for old,new in MOVES:
        ox=old[0]+193.5
        oy=old[1]+126
        nx=new[0]+193.5
        ny=new[1]+126
        original=[v for v in notes.values() if near(xy(v)[0],ox,8) and near(xy(v)[1],oy,8)]
        moved=[v for v in notes.values() if near(xy(v)[0],nx,8) and near(xy(v)[1],ny,8)]
        if len(original)==1 and len(moved)==0: selected[ident(original[0])]=(nx,ny,True)
        elif len(original)==0 and len(moved)==1: selected[ident(moved[0])]=(nx,ny,False)
        else:
            nearest=sorted(notes.values(),key=lambda v:abs(xy(v)[0]-ox)+abs(xy(v)[1]-oy))[:3]
            print("MOVE_COORDINATE_DIAGNOSTIC:",old,"old",(round(ox),round(oy)),"nearest",[(round(xy(v)[0]),round(xy(v)[1])) for v in nearest])
            raise RuntimeError("V12 moved-note anchor ambiguous or manual drift")
    if len(selected)!=4: raise RuntimeError("V12 move map incomplete")
    return selected

def point(node,side):
    x,y=node["x"],node["y"];w,h=node["w"],node["h"]
    return (x+((-w/2) if side=="left" else (w/2 if side=="right" else 0)),
            y+((-h/2) if side=="top" else (h/2 if side=="bottom" else 0)))
def curve(a,b,start,end):
    p=point(a,start);q=point(b,end)
    # Approximation for collision-safe anchor choice. Miro owns actual rendering.
    dist=math.dist(p,q);t=min(1700,max(110,dist*.34))
    c1=(p[0]+DIR[start][0]*t,p[1]+DIR[start][1]*t)
    c2=(q[0]+DIR[end][0]*t,q[1]+DIR[end][1]*t)
    out=[]
    for j in range(43):
        z=j/42;h=1-z
        out.append((h**3*p[0]+3*h*h*z*c1[0]+3*h*z*z*c2[0]+z**3*q[0],
                    h**3*p[1]+3*h*h*z*c1[1]+3*h*z*z*c2[1]+z**3*q[1]))
    return out

def route_cost(e,side1,side2,nodes,prior):
    a,b=nodes[src(e)],nodes[dst(e)]
    curve_points=curve(a,b,side1,side2)
    hits=0;nearby=0
    for px,py in curve_points[2:-2]:
        for n in nodes.values():
            if n is a or n is b: continue
            dx=max(abs(px-n["x"])-n["w"]/2,0)
            dy=max(abs(py-n["y"])-n["h"]/2,0)
            d2=dx*dx+dy*dy
            if d2==0:hits+=1
            elif d2<55*55:nearby+=1
    dx=b["x"]-a["x"];dy=b["y"]-a["y"]
    fwd=(side1=="right" and dx>0) or (side1=="left" and dx<0) or (side1=="bottom" and dy>0) or (side1=="top" and dy<0)
    inbound=(side2=="left" and dx>0) or (side2=="right" and dx<0) or (side2=="top" and dy>0) or (side2=="bottom" and dy<0)
    length=sum(math.dist(p,q) for p,q in zip(curve_points,curve_points[1:]))
    baseline=math.dist(curve_points[0],curve_points[-1])
    overlap=0
    # Discourage near-identical arcs and intersections with other already planned paths.
    for other in prior:
        if src(other[0]) in (src(e),dst(e)) or dst(other[0]) in (src(e),dst(e)):
            continue
        path=other[1]
        for px,py in curve_points[3::3]:
            d2=min((px-qx)**2+(py-qy)**2 for qx,qy in path[3::3])
            if d2<65*65:overlap+=1
    return (hits*500 + nearby*4 + overlap*3.0 + (length-baseline)*.1 +
            (0 if fwd else 55)+(0 if inbound else 55),hits,nearby,curve_points)

def plan(frame,notes,links,moves):
    nodes={}
    for id_,v in notes.items():
        x,y=xy(v);w,h=wh(v)
        if not(100<w<2000 and 70<h<1000):raise RuntimeError("V12 event size drift")
        if id_ in moves: x,y=moves[id_][:2]
        nodes[id_]={"x":x,"y":y,"w":w,"h":h}
    links=sorted(links,key=lambda c:math.dist(
        (nodes[src(c)]["x"],nodes[src(c)]["y"]),
        (nodes[dst(c)]["x"],nodes[dst(c)]["y"])))
    chosen={};prior=[];hit_count=0;near_count=0
    for c in links:
        options=[]
        for s in SIDES:
            for t in SIDES:
                co,hits,nearby,pts=route_cost(c,s,t,nodes,prior)
                options.append((co,s,t,hits,nearby,pts))
        best=min(options,key=lambda x:x[0])
        chosen[ident(c)]=(best[1],best[2])
        prior.append((c,best[5]))
        hit_count+=best[3];near_count+=best[4]
    print("ROUTE_PREVIEW: links=%d estimated_sticky_contacts=%d near_sticky_samples=%d"%(len(chosen),hit_count,near_count))
    # Structural model is guaranteed; estimated geometry is NOT a render acceptance.
    return chosen

def reported_side(endpoint):
    snap=endpoint.get("snapTo")
    if snap in SIDES:return snap
    p=endpoint.get("position") or {}
    x=str(p.get("x","")).strip().replace("%","")
    y=str(p.get("y","")).strip().replace("%","")
    try:x=float(x);y=float(y)
    except ValueError:return "unknown"
    if (x,y)==(50,0):return "top"
    if (x,y)==(50,100):return "bottom"
    if (x,y)==(0,50):return "left"
    if (x,y)==(100,50):return "right"
    if (x,y)==(.5,0):return "top"
    if (x,y)==(.5,1):return "bottom"
    if (x,y)==(0,.5):return "left"
    if (x,y)==(1,.5):return "right"
    return "unknown"

def readback(baseline_nodes,baseline_links,moves,chosen,limit=None):
    frame,notes,links=load()
    if {x:digest_text(n) for x,n in notes.items()}!=baseline_nodes:
        raise RuntimeError("post-write event text changed")
    current={ident(c):c for c in links}
    if set(current)!=set(baseline_links):raise RuntimeError("post-write connector IDs changed")
    for id_,c in current.items():
        before=baseline_links[id_]
        if (src(c),dst(c))!=(before["src"],before["dst"]):raise RuntimeError("post-write endpoints changed")
        if style_fingerprint(c)!=before["style"]:raise RuntimeError("post-write style drift")
        if caption_fingerprint(c)!=before["captions"]:raise RuntimeError("post-write caption drift")
    if limit is None: targets=set(chosen)
    else:targets=set(limit)
    for id_ in targets:
        if current[id_].get("shape")!="curved":raise RuntimeError("curved connector readback mismatch")
        for key,side in (("startItem",chosen[id_][0]),("endItem",chosen[id_][1])):
            if reported_side(current[id_].get(key) or {})!=side:
                raise RuntimeError("anchor side readback mismatch")
    if limit is None:
        for id_,(x,y,_) in moves.items():
            p=xy(notes[id_])
            if not(near(p[0],x,4) and near(p[1],y,4)):
                raise RuntimeError("moved-note geometry readback mismatch")
    print("READBACK PASS: events=%d connectors=%d curved_verified=%d"%(len(notes),len(links),len(targets)))

def execute():
    frame,notes,links=load()
    moves=map_moves(frame,notes)
    before_nodes={id_:digest_text(n) for id_,n in notes.items()}
    before_links={ident(c):{"src":src(c),"dst":dst(c),
        "style":style_fingerprint(c),"captions":caption_fingerprint(c)}
        for c in links}
    chosen=plan(frame,notes,links,moves)
    already=sum(c.get("shape")=="curved" for c in links)
    print("PREFLIGHT PASS: v12 110 events 46 links; curved=%d; moved_notes=%d"%(already,sum(x[2] for x in moves.values())))
    if MODE=="audit":
        shapes=[(v.get("startItem") or {},v.get("endItem") or {}) for v in links if v.get("shape")=="curved"]
        print("CURVED_ENDPOINT_READBACK:",[{"s":{"snapTo":x.get("snapTo"),"position":x.get("position")},"e":{"snapTo":y.get("snapTo"),"position":y.get("position")}} for x,y in shapes[:2]])
        # Read-only coverage signals for business-event candidates, no event text/IDs in logs.
        import re, html, unicodedata
        def plain(s):
            s=html.unescape(re.sub(r"<[^>]+>"," ",str(s or ""))).lower()
            return "".join(z for z in unicodedata.normalize("NFKD",s) if not unicodedata.combining(z))
        labels=[plain((n.get("data") or {}).get("content")) for n in notes.values()]
        tests={
          "G01":["pohledav|dluh|nedoplat|preplat","zmen|oprav|zpetn"],
          "G02":["dodatec|domer|kontrol|stanov","pojistn|povinnost"],
          "G03":["regres|nahrad.*naklad|cizi zavin"],
          "G04":["vymah|exekuc"],
          "G05":["smlouv|rozsah|kapacit","zmen|dodat|rozsir"],
          "G06":["vyuct|vykazan|uhrad|pece","odmit|neuzna|neproplac|kracen"],
          "G07":["doplatk|limit","vracen|preplat|vyporad"],
          "G08":["schval|souhlas|povol","uhrad|lec|sluzb|pece"],
          "G09":["zam it|neschval|zam itn|nepovol|odmit","uhrad|lec|sluzb|pece"],
          "G10":["neopravn|reviz|kontrol|podvod","vykazan|uhrad|pec"],
          "G11":["prispev|bonus|benefit","prevenc|schval|priznan"],
          "G12":["namit|odvolan|reklamac","zmen|vyhov|rozhod"],
          "G13":["zahranic|jineho statu|cizi pojist","prislusn|narok"],
          "G14":["zahranic|planovan","schval|povol|souhlas"],
          "G15":["zahranic|mezistat|instituc","vyuct|vyporad|zavaz|pohledav"],
          "G16":["registrac|registrovan","kapitac|praktick|poskytovat"],
          "G17":["prerozdel|zvlastni ucet"],
          "G18":["pausaln","osvc|rezim"],
          "G19":["neposkytnut|nevykonan|zpochybn","pec|vykazan"],
          "G20":["prestoup|preregistr|pojisteni vznik|vznikl.*pojist"],
          "G21":["zastup|opravnen","subjekt|osob"],
          "G22":["kategor|platce","zmen|vznik|ztratil"]
        }
        for name,groups in tests.items():
            count=sum(all(re.search(p,t) for p in groups) for t in labels)
            print("COVERAGE_SIGNAL",name,count)
        print("AUDIT ONLY: no Miro writes");return
    if MODE=="pilot":
        candidates=sorted([c for c in links if c.get("shape")!="curved"],
             key=lambda c:math.dist(xy(notes[src(c)]),xy(notes[dst(c)])))
        if not candidates:
            print("PILOT NOOP: all connectors already curved");return
        c=candidates[0];id_=ident(c)
        s,t=chosen[id_]
        request("PATCH","connectors/"+id_,{
            "startItem":{"id":src(c),"snapTo":s},
            "endItem":{"id":dst(c),"snapTo":t},"shape":"curved"})
        readback(before_nodes,before_links,moves,chosen,limit=(id_,))
        print("PILOT PASS: one existing connector patched")
        return
    for id_,(x,y,needs_change) in moves.items():
        if needs_change:
            request("PATCH","sticky_notes/"+id_,{"position":{"x":x,"y":y,"origin":"center"}})
    for c in links:
        id_=ident(c);s,t=chosen[id_]
        if c.get("shape")=="curved" and (c.get("startItem") or {}).get("snapTo")==s and (c.get("endItem") or {}).get("snapTo")==t:
            continue
        request("PATCH","connectors/"+id_,{"startItem":{"id":src(c),"snapTo":s},
            "endItem":{"id":dst(c),"snapTo":t},"shape":"curved"})
    readback(before_nodes,before_links,moves,chosen)
    print("APPLY STRUCTURAL PASS: all original objects preserved; visual acceptance separate")

try:execute()
except Exception as e:
    print("FAIL:",str(e))
    sys.exit(1)
