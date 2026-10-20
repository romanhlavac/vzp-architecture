#!/usr/bin/env python3
"""Native Miro catalog / connector routing migration (no board content in repository).
Run via GitHub Actions with existing Miro environment secrets. Default: audit.
Never replay legacy L1 builder. Do not emit private item text or full snapshots.
"""
import os, re, sys, json, html, math, time, urllib.request, urllib.parse, urllib.error, collections, hashlib

MODE=os.environ.get("MIRO_CATALOG_MODE","audit")
if MODE not in {"audit","apply"}: raise SystemExit("INVALID_MODE")
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
BP="3458764687741774534"
DL="3458764687757375873"
DL_DOC="3458764687803477373"
REPO="https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget="
EXPECTED={"bp_stickies":147,"dl_stickies":147,"bp_edges":51,"dl_edges":51,"dl_descriptions":147}
def req(method,path,payload=None):
    body=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
    headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    url=ROOT+path
    for i in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,body,headers,method=method),timeout=55)
            b=r.read()
            return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            if i<3 and (e.code==429 or (e.code in (500,502,503,504) and method=="GET")):
                time.sleep(2**i);continue
            # Redact provider error bodies: they may contain private board data.
            raise RuntimeError("MIRO_HTTP_"+str(e.code)+"_"+method+"_"+path.split("?")[0]) from None
        except (TimeoutError,urllib.error.URLError) as e:
            raise RuntimeError("MIRO_TRANSPORT_UNCERTAIN_"+method+"_"+path.split("?")[0]) from None
    raise RuntimeError("MIRO_RETRIES_EXHAUSTED")
def listing(path,params=None):
    data=[];cursor=None
    while True:
        qs=dict(params or {});qs["limit"]=50
        if cursor:qs["cursor"]=cursor
        r=req("GET",path+"?"+urllib.parse.urlencode(qs))
        data.extend(r.get("data") or [])
        cursor=r.get("cursor") or r.get("nextCursor")
        if not cursor: return data
def iid(z):return str(z.get("id") or "")
def par(z):return str((z.get("parent") or {}).get("id") or "")
def tex(z):
    return " ".join(html.unescape(re.sub(r"<[^>]*>"," ",str((z.get("data") or {}).get("content") or ""))).split())
def bb(z):
    p=z.get("position") or {};g=z.get("geometry") or {}
    return (float(p.get("x") or 0),float(p.get("y") or 0),float(g.get("width") or 0),float(g.get("height") or 0))
def ends(c,k):return str((c.get(k) or {}).get("id") or "")
def side(c,k):return str((c.get(k) or {}).get("snapTo") or "").lower()
def main():
    items=listing("items")
    cn=listing("connectors")
    frames={iid(z):z for z in items if z.get("type")=="frame"}
    if BP not in frames or DL not in frames:raise RuntimeError("FRAME_IDENTITY_DRIFT")
    bp_items=[z for z in items if par(z)==BP]
    dl_items=[z for z in items if par(z)==DL]
    bp_cards={iid(z):z for z in bp_items if z.get("type")=="sticky_note"}
    dl_cards={iid(z):z for z in dl_items if z.get("type")=="sticky_note"}
    src={tex(z):iid(z) for z in bp_cards.values()}
    tgt={tex(z):iid(z) for z in dl_cards.values()}
    if len(bp_cards)!=147 or len(dl_cards)!=147 or len(src)!=147 or set(src)!=set(tgt):
        raise RuntimeError("BUSINESS_EVENT_MAPPING_DRIFT")
    bpe=[z for z in cn if ends(z,"startItem") in bp_cards and ends(z,"endItem") in bp_cards]
    dle=[z for z in cn if ends(z,"startItem") in dl_cards and ends(z,"endItem") in dl_cards]
    if len(bpe)!=51 or len(dle)!=51:raise RuntimeError("CONNECTOR_COUNT_DRIFT")
    def rel(c,cards):
        a=tex(cards[ends(c,"startItem")]);b=tex(cards[ends(c,"endItem")])
        return (a,b)
    bpmap={rel(c,bp_cards):c for c in bpe}
    if len(bpmap)!=51 or set(bpmap)!=set(rel(c,dl_cards) for c in dle):
        raise RuntimeError("CONNECTOR_SEMANTIC_DRIFT")
    for c in dle:
        bc=bpmap[rel(c,dl_cards)]
        for field in ("shape","captions"):
            if c.get(field)!=bc.get(field):raise RuntimeError("CONNECTOR_"+field+"_DRIFT")
        bs=bc.get("style") or {};ds=c.get("style") or {}
        for field in ("strokeColor","strokeStyle"):
            if ds.get(field)!=bs.get(field):raise RuntimeError("CONNECTOR_STYLE_DRIFT")
    # Existing descriptions are authoritative business meaning / traceability.
    ds=[z for z in dl_items if z.get("type")=="text" and "movetowidget=" in html.unescape(str((z.get("data") or {}).get("content") or "")).lower()]
    # Read-only representation diagnostic: do not expose private event text.
    texts=[z for z in dl_items if z.get("type")=="text"]
    raw=[str((z.get("data") or {}).get("content") or "") for z in texts]
    print("TEXT_REPRESENTATION_AUDIT",json.dumps({
      "types":dict(collections.Counter(z.get("type") for z in dl_items)),
      "text_count":len(texts),"nonempty":sum(bool(v) for v in raw),
      "direct_bp_marker":sum("moveToWidget=" in v for v in raw),
      "marker_case_insensitive":sum("movetowidget" in v.lower() for v in raw),
      "source_bp_phrase":sum("Zdrojový BP" in v for v in raw),
      "hyperlink_tag":sum("<a " in v or "&lt;a " in v for v in raw),
      "html_p":sum("<p>" in v or "&lt;p&gt;" in v for v in raw),
      "max_content_len":max((len(v) for v in raw),default=0)
    }),flush=True)
    tails=[]
    for v in raw:
        p=v.lower().find("movetowidget")
        if p>=0:
            t=v[p+len("movetowidget"):p+len("movetowidget")+19]
            tails.append(re.sub(r"[0-9]","#",t))
    print("URL_MARKER_SHAPES",json.dumps(dict(collections.Counter(tails))),flush=True)
    original_desc=len(ds)
    meaning={}
    for z in ds:
        raw=html.unescape(str((z.get("data") or {}).get("content") or ""))
        m=re.search(r"movetowidget=(\d+)",raw,re.I)
        p=re.search(r"<p>(.*?)</p>",raw,re.S|re.I)
        if not m or not p or m.group(1) not in bp_cards: raise RuntimeError("DESCRIPTION_PROVENANCE_DRIFT")
        name=tex(bp_cards[m.group(1)])
        val=html.unescape(re.sub("<[^>]+>","",p.group(1))).strip()
        if not val or name in meaning:raise RuntimeError("DESCRIPTION_MAPPING_DRIFT")
        meaning[name]=val
    # Existing L1 native doc must be read back before any delete.
    doc=req("GET","docs/"+DL_DOC+"?textContentType=markdown")
    ddata=doc.get("data") or {}
    dcontent=str(ddata.get("content") or "")
    docparent=par(doc)
    existing_doc_valid=(docparent==DL and len(dcontent)>16000 and
        all(name in dcontent for name in src))
    if not existing_doc_valid:
        # No write before validating the 32k Miro Doc saved via Canvas Composer.
        raise RuntimeError("DL_DOC_READBACK_INCOMPLETE_OR_PARENT_DRIFT")
    if original_desc not in (0,147) or (original_desc==147 and len(meaning)!=147):
        raise RuntimeError("DL_DESCRIPTION_COUNT_DRIFT")
    print("FRESH_PREFLIGHT_PASS",json.dumps({"bp_events":len(bp_cards),
        "dl_events":len(dl_cards),"bp_edges":len(bpe),"dl_edges":len(dle),
        "dl_descriptions":original_desc,"native_l1_doc":True,"doc_characters":len(dcontent)}),flush=True)
    if MODE=="audit":
        print("AUDIT_ONLY_NO_WRITES",flush=True);return
    if original_desc==0:
        raise RuntimeError("MIGRATION_ALREADY_APPLIED_STOP_FOR_REVIEW")
    # Reconstruct exact existing Miro Doc content for source BP as a distinct
    # native Doc Format. No private source text is stored in this public repo.
    legend=[z for z in dl_items if z.get("type")=="text" and
            "Pod kartou" in tex(z) and "business význam" in tex(z)]
    if len(legend)!=1:raise RuntimeError("L1_LEGEND_IDENTITY_DRIFT")
    bpdocs=[z for z in bp_items if z.get("type") in ("doc","doc_format")]
    if bpdocs: raise RuntimeError("BP_DOC_ALREADY_PRESENT_RECONCILE")
    # Native docs may have board-dependent content, but markdown source is
    # provided directly with all 147 event names and their original meanings.
    md="# Katalog business událostí · BP ES v14\n\n"
    md+="147 business událostí a jejich význam z L1 DL v3; zdrojové BP odkazy. Pracovní demo, ne schválené rozhodnutí VZP.\n\n"
    # L1 Doc itself already records domain grouping and every original meaning:
    # use full content directly, keeping its same 147 references and domain groupings.
    md=dcontent.replace("# Katalog business událostí · BP ES v14 / L1 DL v3",
        "# Katalog business událostí · BP ES v14",1)
    # Catalog position below active source work area; frame will be enlarged.
    frame=frames[BP];cx,cy,fw,fh=bb(frame)
    top=cy-fh/2;left=cx-fw/2
    patch={"geometry":{"width":fw,"height":47000}}
    req("PATCH","frames/"+BP,patch)
    created=req("POST","docs",{
        "data":{"content":md,"contentType":"markdown"},
        "parent":{"id":BP},
        "position":{"x":left+650,"y":top+14150,"origin":"center"}})
    new_id=iid(created)
    if not new_id:raise RuntimeError("BP_DOC_CREATE_UNCERTAIN")
    chk=req("GET","docs/"+new_id+"?textContentType=markdown")
    check_content=str((chk.get("data") or {}).get("content") or "")
    if par(chk)!=BP or len(check_content)<16000 or not all(n in check_content for n in src):
        raise RuntimeError("BP_DOC_READBACK_FAIL_STOP_BEF_DELETE")
    print("BP_CATALOG_PASS","native_doc_id",new_id,"characters",len(check_content),flush=True)
    # Delete only superseded per-event description widgets, after both native
    # documents have been read back and source references checked.
    for i,z in enumerate(ds):
        req("DELETE","texts/"+iid(z))
        if (i+1)%20==0:print("DESCRIPTION_MIGRATED",i+1,flush=True)
        time.sleep(0.3)
    print("DL_DESCRIPTION_REMOVAL_PASS",len(ds),flush=True)
    req("PATCH","texts/"+iid(legend[0]),{"data":{"content":
        "Oranžově = jedna primární business událost. Popis a odkaz na zdrojový BP jsou v úplném editovatelném Katalogu událostí pod doménami. Šipky P/D vedou přímo mezi událostmi."}})
    print("L1_LEGEND_UPDATED",flush=True)
    # Routing optimizer: 2 facing anchor pairs for diagonal relations; score
    # geometrical clearance, crossings, near-parallel co-routing. Native shape
    # stays curved; connector endpoint ids/captions/colors/style immutable.
    rects={iid(z):bb(z) for z in dl_cards.values()}
    def anchor(r,sd):
        x,y,w,h=r
        return {"left":(x-w/2,y),"right":(x+w/2,y),
                "top":(x,y-h/2),"bottom":(x,y+h/2)}[sd]
    def options(c):
        a=rects[ends(c,"startItem")];b=rects[ends(c,"endItem")]
        dx=b[0]-a[0];dy=b[1]-a[1]
        horizontal=("right","left") if dx>=0 else ("left","right")
        vertical=("bottom","top") if dy>=0 else ("top","bottom")
        opts=[]
        if abs(dx)>min(a[2],b[2])*.6:opts.append(horizontal)
        if abs(dy)>min(a[3],b[3])*.6:opts.append(vertical)
        if not opts:opts=[horizontal if abs(dx)>abs(dy) else vertical]
        return opts
    def loc(c,sd):
        a=rects[ends(c,"startItem")];b=rects[ends(c,"endItem")]
        return anchor(a,sd[0]),anchor(b,sd[1])
    def cross(a,b,c,d):
        def orient(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
        o=[orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)]
        return o[0]*o[1]<-1e-5 and o[2]*o[3]<-1e-5
    def rect_hit(a,b,r,margin=4):
        x,y,w,h=r;l=x-w/2-margin;rr=x+w/2+margin;t=y-h/2-margin;bot=y+h/2+margin
        for k in range(1,20):
            f=k/20;px=a[0]+(b[0]-a[0])*f;py=a[1]+(b[1]-a[1])*f
            if l<px<rr and t<py<bot:return True
        return False
    def score(i,sd,chosen,individual=False):
        c=dle[i];a,b=loc(c,sd)
        length=math.dist(a,b)
        s=length*.015
        blocked=sum(rect_hit(a,b,r,15) for rid,r in rects.items()
            if rid not in (ends(c,"startItem"),ends(c,"endItem")))
        s+=blocked*650
        for j,other in enumerate(dle):
            if j==i:continue
            d=chosen[j]
            p,q=loc(other,d)
            if cross(a,b,p,q) and not ({ends(c,"startItem"),ends(c,"endItem")} &
                {ends(other,"startItem"),ends(other,"endItem")}):
                s+=70
            v=(b[0]-a[0],b[1]-a[1]);w=(q[0]-p[0],q[1]-p[1])
            den=math.hypot(*v)*math.hypot(*w)
            if den and abs(v[0]*w[1]-v[1]*w[0])/den<.035:
                # Co-linear near-duplicate corridors get penalized.
                md=((a[0]+b[0])/2,(a[1]+b[1])/2)
                dist=abs((w[0])*(md[1]-p[1])-(w[1])*(md[0]-p[0]))/math.hypot(*w)
                if dist<45:s+=30
        return s
    opts=[options(c) for c in dle]
    chosen=[]
    for i,c in enumerate(dle):
        cur=(side(c,"startItem"),side(c,"endItem"))
        chosen.append(cur if cur in opts[i] else opts[i][0])
    originals=[(side(c,"startItem"),side(c,"endItem")) for c in dle]
    before=chosen[:]
    beforeScore=sum(score(i,sd,before) for i,sd in enumerate(before))
    for _ in range(5):
        count=0
        for i,c in enumerate(dle):
            o=min(opts[i],key=lambda x:score(i,x,chosen))
            if score(i,o,chosen)+1e-6<score(i,chosen[i],chosen):
                chosen[i]=o;count+=1
        if not count:break
    changes=[(c,sd) for c,sd,old in zip(dle,chosen,originals) if sd!=old]
    print("ROUTING_PLAN",json.dumps({"changes":len(changes),
        "proxy_cost_before":round(beforeScore,2),
        "proxy_cost_after":round(sum(score(i,v,chosen) for i,v in enumerate(chosen)),2)}),flush=True)
    original={iid(c):{"a":ends(c,"startItem"),"b":ends(c,"endItem"),
        "shape":c.get("shape"),"captions":c.get("captions"),
        "style":c.get("style")} for c in dle}
    for c,(a,b) in changes:
        req("PATCH","connectors/"+iid(c),
            {"startItem":{"id":ends(c,"startItem"),"snapTo":a},
             "endItem":{"id":ends(c,"endItem"),"snapTo":b}})
        time.sleep(0.07)
    fresh=listing("connectors")
    current={iid(c):c for c in fresh if iid(c) in original}
    if len(current)!=51:raise RuntimeError("CONNECTOR_READBACK_COUNT_FAIL")
    for c in dle:
        orig=original[iid(c)];v=current[iid(c)]
        for field in ("shape","captions","style"):
            if v.get(field)!=orig.get(field):raise RuntimeError("CONNECTOR_"+field+"_CHANGED")
        if ends(v,"startItem")!=orig["a"] or ends(v,"endItem")!=orig["b"]:
            raise RuntimeError("CONNECTOR_ENDPOINT_CHANGED")
        expected=chosen[dle.index(c)]
        if (side(v,"startItem"),side(v,"endItem"))!=expected:
            raise RuntimeError("CONNECTOR_ANCHOR_READBACK_FAIL")
    finalitems=listing("items")
    countD=sum(par(z)==DL and z.get("type")=="text" and "movetowidget=" in html.unescape(str((z.get("data") or {}).get("content") or "")).lower() for z in finalitems)
    if countD:raise RuntimeError("DESCRIPTION_DELETION_INCOMPLETE")
    print("MIRO_SEMANTIC_AND_NATIVE_READBACK_PASS",
        json.dumps({"bp_doc_id":new_id,"dl_doc_id":DL_DOC,
        "catalog_events":147,"dl_events":147,
        "relations":51,"description_boxes_deleted":147,
        "routing_changes":len(changes),"visual_acceptance":"OPEN"}),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        # Never emit raw private responses.
        print("STOP",str(exc),flush=True);sys.exit(1)
