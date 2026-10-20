#!/usr/bin/env python3
"""CES 1A routing reconciliation: direct event-to-event native connectors.
Native Miro REST v2. Read-only audit default. Never print private event content.
After migration BP & DL have 147 events, 51 equal-semantic curved links, 1 doc each.
"""
import os,sys,json,re,html,math,time,collections,urllib.request,urllib.parse,urllib.error
MODE=os.environ.get("MIRO_ROUTE_MODE","audit")
if MODE not in ("audit","apply"):raise SystemExit("INVALID_MODE")
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
BP="3458764687741774534";DL="3458764687757375873"
BPDOC="3458764687806287544";DLDOC="3458764687803477373"
def call(method,path,obj=None):
    body=json.dumps(obj,ensure_ascii=False).encode() if obj is not None else None
    headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None:headers["Content-Type"]="application/json"
    for k in range(6):
        try:
            r=urllib.request.urlopen(urllib.request.Request(ROOT+path,data=body,headers=headers,method=method),timeout=55)
            b=r.read()
            return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and k<5 and (method=="GET" or e.code==429):
                time.sleep(min(2**k,24));continue
            raise RuntimeError("HTTP_"+str(e.code)+"_"+method+"_"+path.split("?")[0]) from None
        except (urllib.error.URLError,TimeoutError):
            raise RuntimeError("TRANSPORT_UNKNOWN_"+method+"_"+path.split("?")[0]) from None
def listing(path,params=None):
    data=[];cursor=None
    while True:
        ps=dict(params or {});ps["limit"]=50
        if cursor:ps["cursor"]=cursor
        r=call("GET",path+"?"+urllib.parse.urlencode(ps))
        data.extend(r.get("data") or [])
        cursor=r.get("cursor") or r.get("nextCursor")
        if not cursor:return data
def ident(z):return str(z.get("id") or "")
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def endpoint(c,k):return str((c.get(k) or {}).get("id") or "")
def label(z):
    return " ".join(html.unescape(re.sub(r"<[^>]*>"," ",str((z.get("data") or {}).get("content") or ""))).split())
SIDES={"left","right","top","bottom"}
def side(e):
    k=str((e or {}).get("snapTo") or "").lower()
    if k in SIDES:return k
    p=(e or {}).get("position") or {}
    try:
        x=float(str(p.get("x","")).replace("%",""))
        y=float(str(p.get("y","")).replace("%",""))
    except(ValueError,TypeError):return "unknown"
    if 0<=x<=1 and 0<=y<=1:x*=100;y*=100
    if abs(x-0)<0.01 and abs(y-50)<0.01:return "left"
    if abs(x-100)<0.01 and abs(y-50)<0.01:return "right"
    if abs(x-50)<0.01 and abs(y-0)<0.01:return "top"
    if abs(x-50)<0.01 and abs(y-100)<0.01:return "bottom"
    return "noncanonical"
def bbox(z):
    p=z.get("position") or {};g=z.get("geometry") or {}
    return tuple(float(v) for v in (p.get("x") or 0,p.get("y") or 0,g.get("width") or 0,g.get("height") or 0))
def point(r,s):
    x,y,w,h=r
    return {"left":(x-w/2,y),"right":(x+w/2,y),
            "top":(x,y-h/2),"bottom":(x,y+h/2)}[s]
def crosses(a,b,c,d):
    def ori(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    o1=ori(a,b,c);o2=ori(a,b,d);o3=ori(c,d,a);o4=ori(c,d,b)
    return o1*o2<-1e-5 and o3*o4<-1e-5
def hits(a,b,r,pad=8):
    x,y,w,h=r;left=x-w/2-pad;right=x+w/2+pad;top=y-h/2-pad;bottom=y+h/2+pad
    for k in range(1,32):
        t=k/32;u=a[0]*(1-t)+b[0]*t;v=a[1]*(1-t)+b[1]*t
        if left<u<right and top<v<bottom:return True
    return False
def metrics(links,rects,sides):
    paths=[]
    for c,s in zip(links,sides):
        if s[0] not in SIDES or s[1] not in SIDES:raise RuntimeError("UNREADABLE_ANCHOR")
        aa=endpoint(c,"startItem");bb=endpoint(c,"endItem")
        a=point(rects[aa],s[0]);b=point(rects[bb],s[1])
        paths.append((aa,bb,a,b))
    crossings=0;collisions=0;parallel=0;length=0
    for i,(aID,bID,a,b) in enumerate(paths):
        length+=math.dist(a,b)
        collisions+=sum(hits(a,b,r,12) for id,r in rects.items() if id not in (aID,bID))
        for j in range(i):
            cID,dID,c,d=paths[j]
            if not ({aID,bID}&{cID,dID}) and crosses(a,b,c,d):crossings+=1
            v=(b[0]-a[0],b[1]-a[1]);w=(d[0]-c[0],d[1]-c[1])
            den=math.hypot(*v)*math.hypot(*w)
            if den>0 and abs(v[0]*w[1]-v[1]*w[0])/den<.035:
                mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
                deviation=abs(w[0]*(mid[1]-c[1])-w[1]*(mid[0]-c[0]))/math.hypot(*w)
                if deviation<45:parallel+=1
    return dict(crossings=crossings,collisions=collisions,parallel_corridors=parallel,stroke_length=round(length),
                proxy_cost=round(collisions*650+crossings*70+parallel*30+length*.015,2))
def main():
    # Parent-scoped native item inventories (no full board item enumeration).
    bp_items=listing("items",{"parent_item_id":BP})
    dl_items=listing("items",{"parent_item_id":DL})
    bp_cards={ident(z):z for z in bp_items if z.get("type")=="sticky_note"}
    dl_cards={ident(z):z for z in dl_items if z.get("type")=="sticky_note"}
    if len(bp_cards)!=147 or len(dl_cards)!=147:raise RuntimeError("EVENT_COUNT_DRIFT")
    bevents={label(z):ident(z) for z in bp_cards.values()}
    devents={label(z):ident(z) for z in dl_cards.values()}
    if len(bevents)!=147 or set(bevents)!=set(devents):raise RuntimeError("EVENT_SEMANTICS_DRIFT")
    for did,fid in ((BPDOC,BP),(DLDOC,DL)):
        d=call("GET","docs/"+did+"?textContentType=markdown")
        c=str((d.get("data") or {}).get("content") or "")
        if parent(d)!=fid or len(c)<16000 or not all(k in c for k in bevents):
            raise RuntimeError("CATALOG_DOC_DRIFT")
    redundant=[z for z in dl_items if z.get("type")=="text" and
        "movetowidget=" in html.unescape(str((z.get("data") or {}).get("content") or "")).lower()]
    if redundant:raise RuntimeError("REDUNDANT_EVENT_DESCRIPTIONS_REMAIN")
    links=listing("connectors")
    ble=[z for z in links if endpoint(z,"startItem") in bp_cards and endpoint(z,"endItem") in bp_cards]
    dle=[z for z in links if endpoint(z,"startItem") in dl_cards and endpoint(z,"endItem") in dl_cards]
    if len(ble)!=51 or len(dle)!=51:raise RuntimeError("EDGE_COUNT_DRIFT")
    def signature(z,cards):return (label(cards[endpoint(z,"startItem")]),label(cards[endpoint(z,"endItem")]))
    bpS={signature(z,bp_cards):z for z in ble};dlS={signature(z,dl_cards):z for z in dle}
    if len(bpS)!=51 or len(dlS)!=51 or set(bpS)!=set(dlS):
        raise RuntimeError("EDGE_SEMANTICS_DRIFT")
    for pair,z in dlS.items():
        b=bpS[pair]
        if z.get("shape")!=b.get("shape") or z.get("captions")!=b.get("captions"):
            raise RuntimeError("CONNECTOR_CAPTIONS_OR_SHAPE_CHANGED")
        for field in ("strokeColor","strokeStyle","strokeWidth"):
            if (z.get("style") or {}).get(field)!=(b.get("style") or {}).get(field):
                raise RuntimeError("CONNECTOR_STYLE_DRIFT")
    rects={i:bbox(z) for i,z in dl_cards.items()}
    options=[]
    for c in dle:
        a=rects[endpoint(c,"startItem")];b=rects[endpoint(c,"endItem")]
        dx=b[0]-a[0];dy=b[1]-a[1]
        h=("right","left") if dx>=0 else ("left","right")
        v=("bottom","top") if dy>=0 else ("top","bottom")
        cur=[h,v] if abs(dx)>.6*min(a[2],b[2]) and abs(dy)>.6*min(a[3],b[3]) else (
          [h] if abs(dx)>.6*min(a[2],b[2]) else [v] if abs(dy)>.6*min(a[3],b[3])
          else [h if abs(dx)>abs(dy) else v])
        options.append(cur)
    before=[(side(z.get("startItem")),side(z.get("endItem"))) for z in dle]
    actual_unknown=sum(s[0] not in SIDES or s[1] not in SIDES for s in before)
    actual_misaligned=sum(s not in o for s,o in zip(before,options))
    print("ROUTING_FRESH_READ",json.dumps({
      "events":147,"links":51,"bp_doc":True,"dl_doc":True,
      "description_boxes":len(redundant),"anchor_unreadable":actual_unknown,
      "anchor_nonfacing":actual_misaligned,"side_pairs":dict(collections.Counter(str(x) for x in before))}),flush=True)
    if actual_unknown:raise RuntimeError("UNKNOWN_NATIVE_CONNECTOR_SIDE")
    before_metrics=metrics(dle,rects,before)
    # Candidate search, requiring strict proxy improvement, never drift semantics.
    chosen=list(before)
    for i,o in enumerate(options):
        if chosen[i] not in o:chosen[i]=o[0]
    def candidate_cost(i,x):
        trial=list(chosen);trial[i]=x;return metrics(dle,rects,trial)["proxy_cost"]
    for iteration in range(4):
        changed=False
        for i,o in enumerate(options):
            scores=[(candidate_cost(i,xx),xx) for xx in o]
            best=min(scores,key=lambda z:z[0])[1]
            if best!=chosen[i] and candidate_cost(i,best)+.001<candidate_cost(i,chosen[i]):
                chosen[i]=best;changed=True
        if not changed:break
    after_metrics=metrics(dle,rects,chosen)
    planned=[(c,s) for c,s,b in zip(dle,chosen,before) if s!=b]
    print("ROUTE_COST_AUDIT",json.dumps({"before":before_metrics,"optimized":after_metrics,
                                     "changes":len(planned),"mode":MODE}),flush=True)
    if MODE=="audit":
        print("ROUTING_AUDIT_PASS_NO_WRITES",flush=True);return
    old={ident(c):{"pair":signature(c,dl_cards),"style":c.get("style"),
        "captions":c.get("captions"),"shape":c.get("shape")} for c in dle}
    if after_metrics["proxy_cost"]>before_metrics["proxy_cost"]+1e-5:
        raise RuntimeError("ROUTE_OBJECTIVE_WORSE")
    for c,(a,b) in planned:
        call("PATCH","connectors/"+ident(c),{"startItem":{"id":endpoint(c,"startItem"),"snapTo":a},
                                       "endItem":{"id":endpoint(c,"endItem"),"snapTo":b}})
        time.sleep(.24)
    fresh=listing("connectors")
    found={ident(c):c for c in fresh if ident(c) in old}
    if len(found)!=51:raise RuntimeError("ROUTE_READBACK_COUNT_DRIFT")
    for old_c,new_side in zip(dle,chosen):
        q=found[ident(old_c)];o=old[ident(old_c)]
        if signature(q,dl_cards)!=o["pair"] or q.get("style")!=o["style"] or q.get("captions")!=o["captions"] or q.get("shape")!=o["shape"]:
            raise RuntimeError("ROUTE_SEMANTIC_OR_STYLE_POST_DRIFT")
        sides=(side(q.get("startItem")),side(q.get("endItem")))
        if sides!=new_side:raise RuntimeError("ROUTE_SIDE_POST_DRIFT_"+ident(q)+"_"+str(sides))
    print("ROUTING_STRUCTURAL_SEMANTIC_ACCEPTANCE_PASS",json.dumps({
       "events":147,"bp_catalog":True,"dl_catalog":True,"links":51,"patches":len(planned),
       "before":before_metrics,"after":metrics(dle,rects,chosen),
       "rendered_visual_acceptance":"OPEN"}),flush=True)
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("STOP",str(e),flush=True);sys.exit(1)
