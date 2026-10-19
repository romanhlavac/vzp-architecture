#!/usr/bin/env python3
"""Safe Miro BP ES v14 versioned builder.

SOURCE: independently read v13 (116 native sticky notes, 18 native text, 46 native edges).
TARGET: untouched original content + 31 approved business event candidates, scenario-oriented
timeline, 5 conditional causal relations. EV01 and EV04 reuse existing original events.
Idempotent STOP/RECONCILE; no source text, frame/board IDs, token in stdout or source.
Run modes: audit(default), pilot(representative), apply(all). Source immutability checked.
"""
import os,json,re,html,hashlib,time,urllib.parse,urllib.request,urllib.error,collections,sys
from ces1a_v14_screen import DATA
MODE=os.getenv("V14_MODE","audit")
if MODE not in ("audit","pilot","apply"):sys.exit("INVALID_MODE")
B=os.getenv("MIRO_DIAGNOSTIC_BOARD_ID","");T=os.getenv("MIRO_DIAGNOSTIC_TOKEN","")
if not B or not T:sys.exit("MISSING_MIRO_RUNTIME_CREDENTIALS")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")
SOURCE_SHA="26f142048d8aeda0cb2ce6d4fa31d1aa45b236cfc41d08a1ef1badb139421486"
TITLE="CES-1A · BP ES v14 · Enterprise business events · pracovní návrh"
REUSE={"EV01","EV04"}
NEW={key:s for key,s in DATA if key not in REUSE}
# Temporal story bands, NOT candidate domain boundaries or process swimlanes.
STORIES=[
 ("Institucionální rámec",["EV02","EV03","EV19"]),
 ("Zákonné nároky a podpora péče",["EV05","EV06","EV08"]),
 ("Dostupnost hrazené péče",["EV11","EV07","EV12"]),
 ("Svobodná volba pojišťovny",["EV09","EV10"]),
 ("Revize a přezkum",["EV13","EV14"]),
 ("Přeshraniční nároky",["EV15"]),
 ("Přerozdělení",["EV16"]),
 ("Regulatorní a veřejná data",["EV17","EV18"]),
 ("Finanční kontinuita",["EV20","EV21"]),
 ("Odborná kontinuita",["EV22","EV23"]),
 ("Dostupnost digitální služby",["EV24","EV25"]),
 ("Strategické smluvní zajištění",["EV26","EV27","EV28"]),
 ("Právně účinná podání",["EV29","EV30"]),
 ("Ochrana osobních údajů a evidence",["EV31","EV32","EV33"])
]
assert len(DATA)==33 and len(NEW)==31
assert [k for _,keys in STORIES for k in keys] and set(k for _,keys in STORIES for k in keys)==set(NEW)
# Only genuine business prerequisites and their resolutions, not arbitrary adjacency.
CAUSAL=[("EV20","EV21"),("EV22","EV23"),("EV24","EV25"),("EV29","EV30"),("EV31","EV32")]
HEIGHT=19200;WIDTH=30400
def request(method,path,payload=None,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    h={"Authorization":"Bearer "+T,"Accept":"application/json"}
    if data is not None:h["Content-Type"]="application/json"
    for attempt in range(5 if method=="GET" else 1):
        try:
            req=urllib.request.Request(url,headers=h,data=data,method=method)
            with urllib.request.urlopen(req,timeout=50) as res:
                buf=res.read();return json.loads(buf) if buf else {}
        except urllib.error.HTTPError as e:
            if method=="GET" and e.code in (429,500,502,503,504) and attempt<4:
                time.sleep(min(15,1+2**attempt));continue
            raise RuntimeError("MIRO_"+method+"_"+path.split("/")[0]+"_HTTP_"+str(e.code)) from None
        except Exception:
            if method=="GET" and attempt<3:time.sleep(2);continue
            raise RuntimeError("MIRO_"+method+"_UNCERTAIN_OUTCOME_RECONCILE") from None
def pages(path,params=None):
    out=[];cur=None
    for _ in range(120):
        q=dict(params or {},limit=50)
        if cur:q["cursor"]=cur
        r=request("GET",path,params=q);out+=r.get("data",[]);cur=r.get("cursor")
        if not cur:return out
    raise RuntimeError("PAGINATION_INCOMPLETE")
def oid(z):return str(z.get("id",""))
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def txt(z):return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str((z.get("data") or {}).get("content",""))))).strip()
def x(z):return float((z.get("position") or {}).get("x") or 0)
def y(z):return float((z.get("position") or {}).get("y") or 0)
def w(z):return float((z.get("geometry") or {}).get("width") or 0)
def h(z):return float((z.get("geometry") or {}).get("height") or 0)
def end(z,k):return str((z.get(k) or {}).get("id") or "")
def edge_sig(z):return (oid(z),end(z,"startItem"),end(z,"endItem"),json.dumps(z.get("captions") or [],sort_keys=True,ensure_ascii=False),z.get("shape"))
def item_sig(z):return (oid(z),z.get("type"),parent(z),txt(z),round(x(z),2),round(y(z),2),round(w(z),2),round(h(z),2),json.dumps(z.get("style") or {},sort_keys=True,ensure_ascii=False))
def edge_side(z,k,default):
    s=(z.get(k) or {}).get("snapTo")
    return s if s in ("top","bottom","left","right") else default
def header(name,xp,yp,width,font):
    return create("text",xp,yp,width,name,{"fontFamily":"open_sans","fontSize":str(font),"color":"#26353a","textAlign":"left"})
def setup():
    global targetItems,targetEdges,target,source_notes,source_texts,sourceEdges,source,frames,notes
    allitems=pages("items")
    frames=[z for z in allitems if z.get("type")=="frame"]
    sources=[z for z in frames if hashlib.sha256(oid(z).encode()).hexdigest()==SOURCE_SHA]
    if len(sources)!=1:raise RuntimeError("V13_SOURCE_FRAME_IDENTITY_DRIFT")
    source=sources[0]
    sons=[z for z in allitems if parent(z)==oid(source)]
    source_notes=sorted([z for z in sons if z["type"]=="sticky_note"],key=lambda z:(y(z),x(z)))
    source_texts=sorted([z for z in sons if z["type"]=="text"],key=lambda z:(y(z),x(z)))
    if len(source_notes)!=116 or len(source_texts)!=18 or len(sons)!=134:raise RuntimeError("V13_SOURCE_COUNT_DRIFT")
    if len(set(txt(z) for z in source_notes))!=116:raise RuntimeError("V13_NONUNIQUE_EVENTS")
    ids={oid(z) for z in source_notes}
    allEdges=pages("connectors")
    sourceEdges=[z for z in allEdges if end(z,"startItem") in ids and end(z,"endItem") in ids]
    if len(sourceEdges)!=46 or any(z.get("shape")!="curved" for z in sourceEdges):raise RuntimeError("V13_EDGE_DRIFT")
    targets=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
    if len(targets)>1:raise RuntimeError("DUPLICATE_V14_FRAME")
    target=targets[0] if targets else None
    targetItems=[z for z in allitems if target and parent(z)==oid(target)]
    ids2={oid(z) for z in targetItems}
    targetEdges=[e for e in allEdges if end(e,"startItem") in ids2 and end(e,"endItem") in ids2]
    print("V14_PREFLIGHT_OK", "source_events=116","source_texts=18","source_edges=46",
          "target_present="+str(bool(target)),"target_items="+str(len(targetItems)),
          "target_edges="+str(len(targetEdges)),flush=True)
    return { "source_items":{item_sig(z) for z in sons},"source_edges":{edge_sig(z) for z in sourceEdges}}
def create(typ,xp,yp,width,content,style=None,data=None):
    global targetItems
    canonical=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(content)))).strip()
    matches=[z for z in targetItems if z["type"]==typ and txt(z)==canonical]
    if len(matches)>1:raise RuntimeError("TARGET_DUPLICATE_OBJECT_TEXT")
    if matches:
        z=matches[0]
        if abs(x(z)-xp)>3 or abs(y(z)-yp)>3 or abs(w(z)-width)>3:raise RuntimeError("TARGET_MANUAL_GEOMETRY_DRIFT")
        return z
    occupancy=[z for z in targetItems if z["type"]==typ and abs(x(z)-xp)<3 and abs(y(z)-yp)<3]
    if occupancy:raise RuntimeError("TARGET_POSITION_COLLISION")
    payload={"data":dict(data or {},content=content),"position":{"x":xp,"y":yp,"origin":"center"},"geometry":{"width":width},"parent":{"id":oid(target)}}
    if style:payload["style"]=style
    if typ=="sticky_note":payload["data"].setdefault("shape","rectangle")
    result=request("POST",{"sticky_note":"sticky_notes","text":"texts"}[typ],payload)
    if not oid(result):raise RuntimeError("CREATE_ID_MISSING")
    targetItems.append(result)
    return result
def ensure_edge(left,right,sourceEdge=None):
    # Copy native connector semantic styles/captions without inventing new types.
    lid,rid=oid(left),oid(right)
    existing=[z for z in targetEdges if end(z,"startItem")==lid and end(z,"endItem")==rid]
    if existing:
        if len(existing)>1:raise RuntimeError("DUPLICATE_TARGET_NATIVE_EDGE")
        return existing[0]
    payload={"startItem":{"id":lid,"snapTo":edge_side(sourceEdge,"startItem","right") if sourceEdge else "right"},
            "endItem":{"id":rid,"snapTo":edge_side(sourceEdge,"endItem","left") if sourceEdge else "left"},
            "shape":"curved"}
    if sourceEdge:
        if sourceEdge.get("captions"):payload["captions"]=sourceEdge["captions"]
        sty={k:v for k,v in (sourceEdge.get("style") or {}).items() if k in ("strokeColor","strokeWidth","strokeStyle","strokeCap","fontSize","color")}
        if sty:payload["style"]=sty
    else:payload["style"]={"strokeColor":"#111111","strokeWidth":"2"}
    z=request("POST","connectors",payload)
    if not oid(z):raise RuntimeError("EDGE_CREATE_ID_MISSING")
    targetEdges.append(z);return z
def verify(pre,expectednotes,expectedtexts,expectedlinks):
    allitems=pages("items")
    allconn=pages("connectors")
    source_now=[z for z in allitems if parent(z)==oid(source)]
    eids={oid(z) for z in source_notes}
    srclinks=[z for z in allconn if end(z,"startItem") in eids and end(z,"endItem") in eids]
    if {item_sig(z) for z in source_now}!=pre["source_items"] or {edge_sig(z) for z in srclinks}!=pre["source_edges"]:
        raise RuntimeError("SOURCE_V13_CHANGED_STOP")
    ch=[z for z in allitems if parent(z)==oid(target)]
    ns=[z for z in ch if z.get("type")=="sticky_note"]
    tt=[z for z in ch if z.get("type")=="text"]
    chids={oid(z) for z in ns}
    ce=[z for z in allconn if end(z,"startItem") in chids and end(z,"endItem") in chids]
    if (len(ns),len(tt),len(ce))!=(expectednotes,expectedtexts,expectedlinks):
        raise RuntimeError("V14_READBACK_COUNT_MISMATCH_"+str((len(ns),len(tt),len(ce))))
    if expectednotes==147:
        content=collections.Counter(txt(z) for z in ns)
        if any(content[txt(z)]!=1 for z in source_notes):raise RuntimeError("V13_TEXT_NOT_PRESERVED")
        if any(content[k+" · "+v]!=1 for k,v in NEW.items()):raise RuntimeError("APPROVED_EVENT_MISSING")
        if any(content["EV01 · "+dict(DATA)["EV01"]]>0 or content["EV04 · "+dict(DATA)["EV04"]]>0 for _ in (1,)):
            raise RuntimeError("REUSE_EVENT_DUPLICATED")
        if any(z.get("shape")!="curved" for z in ce):raise RuntimeError("NATIVE_EDGE_SHAPE_MISMATCH")
    print("V14_READBACK_PASS","native_event_cards",len(ns),"text_objects",len(tt),
          "native_curved_links",len(ce),"protected_v13_unchanged",True,flush=True)
def main():
    global target, targetItems
    before=setup()
    if MODE=="audit":
        print("DEDUPE_DECISIONS","REUSE_EV01_EV04","CREATE_NEW",len(NEW),"expected_v14=147","new_causal_relations",len(CAUSAL))
        if target:
            ns=[z for z in targetItems if z.get("type")=="sticky_note"]
            tt=[z for z in targetItems if z.get("type")=="text"]
            if (len(ns),len(tt),len(targetEdges))!=(147,36,51):
                raise RuntimeError("INDEPENDENT_AUDIT_COUNTS_FAIL")
            tx=collections.Counter(txt(z) for z in ns)
            if any(tx[txt(z)]!=1 for z in source_notes):
                raise RuntimeError("INDEPENDENT_AUDIT_SOURCE_CARD_MISMATCH")
            if any(tx[k+" · "+v]!=1 for k,v in NEW.items()):
                raise RuntimeError("INDEPENDENT_AUDIT_APPROVED_EVENT_MISMATCH")
            if any(tx[k+" · "+v]!=0 for k,v in DATA if k in REUSE):
                raise RuntimeError("INDEPENDENT_AUDIT_REUSE_DUPLICATE")
            if any(z.get("shape")!="curved" for z in targetEdges):
                raise RuntimeError("INDEPENDENT_AUDIT_NOT_NATIVE_CURVED")
            cond=[z for z in tt if "EV31" in txt(z) and "EV32" in txt(z) and "vysok" in txt(z)]
            if len(cond)!=1:raise RuntimeError("GDPR_CONDITION_ANNOTATION_MISSING")
            by={key:next(z for z in ns if txt(z)==key+" · "+value) for key,value in NEW.items()}
            for a,b in CAUSAL:
                if not any(end(e,"startItem")==oid(by[a]) and end(e,"endItem")==oid(by[b]) for e in targetEdges):
                    raise RuntimeError("BUSINESS_LINK_MISSING")
            # Independent geometric sanity: no two new cards share a slot or visually overlap.
            coords=[(key,x(z),y(z),w(z)) for key,z in by.items()]
            for i,(ki,xi,yi,wi) in enumerate(coords):
                for kj,xj,yj,wj in coords[i+1:]:
                    if abs(xi-xj)<(wi+wj)/2+80 and abs(yi-yj)<max(wi,wj)+80:
                        raise RuntimeError("NEW_CARDS_SPATIAL_OVERLAP")
            for _,keys in STORIES:
                sequence=[x(by[k]) for k in keys]
                if sequence!=sorted(sequence):
                    raise RuntimeError("LOCAL_TIMELINE_NOT_LEFT_TO_RIGHT")
            print("V14_INDEPENDENT_AUDIT_PASS","events",len(ns),"texts",len(tt),
                  "curved",len(targetEdges),"reused",len(REUSE),"new",len(NEW),
                  "business_links",len(CAUSAL),"story_bands",len(STORIES),flush=True)
        print("AUDIT_ONLY_NO_WRITES");return
    if not target:
        right=max(x(f)+w(f)/2 for f in frames)
        target=request("POST","frames",{"data":{"title":TITLE},"style":{"fillColor":"#ffffff"},
                    "geometry":{"width":WIDTH,"height":HEIGHT},
                    "position":{"x":right+2600+WIDTH/2,"y":10500,"origin":"center"}})
        if not oid(target):raise RuntimeError("FRAME_CREATE_ID_MISSING")
        print("V14_TARGET_FRAME_CREATED",flush=True)
    # Clone exact V13 objects without changing original content or layout.
    oldToNew={}
    for i,z in enumerate(source_notes[:1] if MODE=="pilot" else source_notes):
        style={k:v for k,v in (z.get("style") or {}).items() if k in ("fillColor","textAlign","textAlignVertical")}
        new=create("sticky_note",x(z),y(z),w(z),z["data"]["content"],style,{"shape":"rectangle"})
        oldToNew[oid(z)]=new
        if i%25==0:print("V14_CLONE_PROGRESS",i+1,flush=True)
    for z in source_texts[:1] if MODE=="pilot" else source_texts:
        style={k:v for k,v in (z.get("style") or {}).items() if k in ("fontFamily","fontSize","color","textAlign","textAlignVertical","fillOpacity")}
        create("text",x(z),y(z),w(z),z["data"]["content"],style)
    header("<strong>ES BIG PICTURE · v14 · enterprise business events</strong>",22400,160,13100,44)
    header("31 nových kandidátních typů událostí · EV01 a EV04 se používají z původní části bez duplicity",22400,310,13100,25)
    header("DEMO / SCÉNÁŘE: minulé tvary popisují typ významné business skutečnosti, nikoli doložený historický výskyt. Zleva doprava pouze v jednom příběhu.",22400,460,13200,22)
    if MODE=="apply":
        header("EV31 → EV32: oznámení dotčeným osobám jen při zákonných podmínkách vysokého rizika; nikoli automaticky po každém incidentu.",23200,18600,13600,19)
    newObjs={}
    stories=STORIES[:1] if MODE=="pilot" else STORIES
    for row,(title,keys) in enumerate(stories):
        yy=850+row*1280
        header("<strong>"+str(row+1).zfill(2)+" · "+html.escape(title)+"</strong>",18000,yy,2600,23)
        for idx,key in enumerate(keys[:1] if MODE=="pilot" else keys):
            xpos=20200+idx*2000
            z=create("sticky_note",xpos,yy+160,530,key+" · "+NEW[key],
                     {"fillColor":"orange","textAlign":"center"},{"shape":"rectangle"})
            newObjs[key]=z
        print("V14_STORY_WRITTEN",row+1,"events",len(keys) if MODE=="apply" else 1,flush=True)
    if MODE=="apply":
        for i,source_edge in enumerate(sourceEdges):
            src=oldToNew[end(source_edge,"startItem")]
            dst=oldToNew[end(source_edge,"endItem")]
            ensure_edge(src,dst,source_edge)
            if i%12==0:print("V14_SOURCE_LINKS",i+1,flush=True)
        for frm,to in CAUSAL:
            ensure_edge(newObjs[frm],newObjs[to])
        verify(before,147,36,51)
    else:
        verify(before,2,5,0)
    print("V14_TARGET_FRAME_ID",oid(target),flush=True)
    print("VISUAL_ACCEPTANCE_OPEN",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:print("V14_STOP",type(e).__name__,str(e));sys.exit(1)
