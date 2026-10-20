#!/usr/bin/env python3
"""One-catalog CES DEMO hotspot marker projection. Business definitions remain in Google Sheets.
Modes: audit (default), apply (explicit one-time workflow promotion).
No existing model items or connectors are edited/deleted.
"""
import os,sys,json,html,re,time,urllib.request,urllib.parse,urllib.error,collections
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
MODE=os.getenv("HOTSPOT_MODE","audit")
assert MODE in ("audit","apply")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")
FRAME="3458764687757375873"
TITLE="CES-1A · L1 DOMAIN LANDSCAPE · v3 (BP ES v14 / 147 událostí)"
SHEET="https://docs.google.com/spreadsheets/d/1qA_lsfm5Vka9kaglLrX9B7D-WjBSDAapA76pKGVi0ew/edit#gid=1505008023"
# Only stable technical references and worksheet row keys belong in the automation.
# Full problem definitions, event mappings, decision questions and source status live in CES_DEMO_DATA.
ANCHORS=[
("HS-S0-01",2,"3458764687757748076"),
("HS-S0-02",3,"3458764687757748470"),
("HS-S0-03",4,"3458764687757748470"),
("HS-S0-04",5,"3458764687757748364"),
("HS-S0-05",6,"3458764687757748296"),
("HS-S0-06",7,"3458764687757748379"),
("HS-S0-07",8,"3458764687757748415"),
("HS-S0-08",9,"3458764687757748051"),
("HS-S0-09",10,"3458764687757748459"),
("HS-S0-10",11,"3458764687757748392"),
("HS-S0-11",12,"3458764687757748470"),
("HS-S0-12",13,"3458764687757748296")
]
def get(path,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    for i in range(5):
        try:
            q=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
            with urllib.request.urlopen(q,timeout=40) as h:return json.load(h)
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and i<4:time.sleep(min(16,2**i+1));continue
            raise RuntimeError("REST_GET_HTTP_"+str(e.code)) from None
def post(path,body):
    q=urllib.request.Request(BASE+"/"+path,data=json.dumps(body,ensure_ascii=False).encode("utf-8"),
        headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json","Content-Type":"application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError("REST_POST_HTTP_"+str(e.code)) from None
    except Exception:
        # Outcome can be uncertain: no automatic retry on POST.
        raise RuntimeError("REST_POST_UNCERTAIN_REQUIRES_FRESH_READ") from None
def listing(path,params=None):
    out=[];cursor=None
    for i in range(120):
        p=dict(params or {},limit=50)
        if cursor:p["cursor"]=cursor
        res=get(path,p);out+=res.get("data",[])
        cursor=res.get("cursor")
        if not cursor:return out
    raise RuntimeError("PAGINATION_INCOMPLETE")
def oid(o):return str(o.get("id",""))
def parent(o):return str((o.get("parent") or {}).get("id") or "")
def content(o):
    raw=str((o.get("data") or {}).get("content",""))
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",raw))).strip()
def geom(o):return (float((o.get("position") or {}).get("x") or 0),
    float((o.get("position") or {}).get("y") or 0),
    float((o.get("geometry") or {}).get("width") or 0),
    float((o.get("geometry") or {}).get("height") or 0))
def fresh():
    frames=listing("items",{"type":"frame"})
    f=[o for o in frames if oid(o)==FRAME and (o.get("data") or {}).get("title")==TITLE]
    if len(f)!=1:raise RuntimeError("L1_V3_FRAME_CHANGED")
    ls=listing("items",{"parent_item_id":FRAME})
    cs=listing("connectors")
    ids={oid(o) for o in ls}
    rel=[o for o in cs if str((o.get("startItem") or {}).get("id") or "") in ids and str((o.get("endItem") or {}).get("id") or "") in ids]
    orange=[o for o in ls if o.get("type")=="sticky_note" and (o.get("style") or {}).get("fillColor")=="orange"]
    native=[o for o in ls if o.get("type")=="sticky_note" and content(o).startswith("HOTSPOT HS-S0-")]
    allnative=[o for o in ls if o.get("type")=="sticky_note"]
    if len(orange)!=147 or len(rel)!=51 or len(allnative)!=147+len(native):
        raise RuntimeError("PROTECTED_PRIMARY_ITEM_OR_EDGE_DRIFT")
    for key,row,anchor in ANCHORS:
        a=next((o for o in orange if oid(o)==anchor),None)
        if a is None:raise RuntimeError("ANCHOR_MISSING_"+key)
        print("ANCHOR_GEOMETRY",key,*[round(t,1) for t in geom(a)],flush=True)
    for key,row,anchor in ANCHORS:
        matches=[o for o in native if content(o).startswith("HOTSPOT "+key+" ")]
        if len(matches)>1:raise RuntimeError("DUPLICATE_HOTSPOT_"+key)
    if len(native)>12:raise RuntimeError("UNEXPECTED_HOTSPOT_NOTES")
    shape=[o for o in ls if o.get("type")=="shape"
        and content(o).startswith("S0 · Správa a evidence subjektů")]
    if len(shape)!=1:raise RuntimeError("S0_DOMAIN_PANEL_NOT_UNIQUE")
    x,y,w,h=geom(shape[0])
    print("S0_PANEL_GEOMETRY",*[round(z,1) for z in (x,y,w,h)],flush=True)
    if not 500<h<10000:raise RuntimeError("S0_ROW_GEOMETRY_CHANGED")
    rowtop=y-h/2-15
    return ls,rel,native,(rowtop,x+w/2)
def note(key,row):
    url=SHEET+"&range=A"+str(row)+":L"+str(row)
    return ('<p><strong>HOTSPOT '+key+'</strong></p><p>DEMO · OPEN</p>'
            '<p><a href="'+html.escape(url,quote=True)+'">Otázka, důkazy a události → CES_DEMO_DATA</a></p>')
def slots(geometry):
    top,right_edge=geometry
    return {key:(right_edge+488+(i%4)*500,top+134+(i//4)*395) for i,(key,_,_) in enumerate(ANCHORS)}
def collision(pos,items):
    x,y=pos
    for o in items:
        if o.get("type") not in ("sticky_note","shape","text"):continue
        ox,oy,w,h=geom(o)
        if w>=1800 and h>=700:continue # frame/domain background
        if w<=0 or h<=0:continue
        if abs(ox-x)<(w+350)/2+12 and abs(oy-y)<(h+230)/2+12:
            return o.get("type")
    return None
def run():
    ls,rel,native,live_s0=fresh()
    positions=slots(live_s0)
    existing={}
    for z in native:
        txt=content(z)
        key=next((k for k,_,_ in ANCHORS if txt.startswith("HOTSPOT "+k+" ")),None)
        if key is None:raise RuntimeError("UNKNOWN_HOTSPOT_PREFIX")
        if key in existing:raise RuntimeError("DUPLICATE_"+key)
        existing[key]=z
    pending=[x for x in ANCHORS if x[0] not in existing]
    for key,row,anchor in pending:
        if collision(positions[key],ls):
            raise RuntimeError("HOTSPOT_LAYOUT_COLLISION_"+key)
    print("NEAR_S0_RAIL_CANDIDATES",[(xx,yy,collision((xx,yy),ls)) for yy in (1930,2325,2720) for xx in (5500,6000,6500,7000)],flush=True)
    print("FRESH_READ_PASS frame=yes orange_events=147 business_relations=51 existing_hotspots="+str(len(native))+" pending="+str(len(pending)),flush=True)
    print("S0_RAIL_PLACEMENT_PASS 4_columns_x_3_rows; mode="+MODE,flush=True)
    if MODE=="audit":return
    # Created notes carry only a stable key and link into canonical Google Sheet,
    # not a second editable copy of business definitions.
    for key,row,anchor in pending:
        x,y=positions[key]
        b={"data":{"content":note(key,row),"shape":"rectangle"},
            "position":{"x":x,"y":y,"origin":"center"},
            "geometry":{"width":350},
            "parent":{"id":FRAME},
            "style":{"fillColor":"violet","textAlign":"center","textAlignVertical":"middle"}}
        q=post("sticky_notes",b)
        if not oid(q):raise RuntimeError("NO_NATIVE_ID_"+key)
        print("CREATED "+key+" NOTE_ID "+oid(q),flush=True)
    a,b,ns,_=fresh()
    if len(ns)!=12:raise RuntimeError("POST_WRITE_MISSING_NOTES")
    for key,row,anchor in ANCHORS:
        matches=[o for o in ns if content(o).startswith("HOTSPOT "+key+" ")]
        if len(matches)!=1 or (matches[0].get("style") or {}).get("fillColor")!="violet":
            raise RuntimeError("READBACK_FAIL_"+key)
        if "CES_DEMO_DATA" not in content(matches[0]):raise RuntimeError("LINK_TEXT_MISSING_"+key)
    print("STRUCTURAL_READBACK_PASS primary_events=147 original_relations=51 hotspots=12",flush=True)
    print("VISUAL_REVIEW_OPEN native rendered-frame screenshot not available in GitHub REST",flush=True)
if __name__=="__main__":
    try:run()
    except Exception as e:
        print("FAIL "+str(e),file=sys.stderr);sys.exit(2)
