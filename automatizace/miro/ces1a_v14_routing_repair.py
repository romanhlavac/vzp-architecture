#!/usr/bin/env python3
"""V14 connector anchor repair (Miro REST API v2 via Actions).

Ensures that connector endpoints attach to the facing, nearby sides of actual
native Sticky Notes. No event text, semantics, geometry, ids or source frame
are written. Modes: audit (default), pilot, apply. SAFE TO RE-RUN.
"""
import os,sys,math,collections,hashlib
from ces1a_v14_integrate import call,pages,oid,parent,txt,x,y,width,height,eid,TITLE,SOURCE_SHA

MODE=os.getenv("V14_ROUTING_MODE","audit")
if MODE not in ("audit","pilot","apply"):raise SystemExit("V14_ROUTING_INVALID_MODE")
SIDES=("left","right","top","bottom")
def as_side(z):
    s=str(z.get("snapTo") or "").lower()
    if s in SIDES:return s
    p=z.get("position") or {}
    try:
        a=float(str(p.get("x","")).replace("%",""));b=float(str(p.get("y","")).replace("%",""))
    except (TypeError,ValueError):return "unknown"
    if (a,b) in ((0,50),(0,.5)):return "left"
    if (a,b) in ((100,50),(1,.5)):return "right"
    if (a,b) in ((50,0),(.5,0)):return "top"
    if (a,b) in ((50,100),(.5,1)):return "bottom"
    return "unknown"
def point(n,side):
    cx,cy=x(n),y(n)
    if side=="left":return (cx-width(n)/2,cy)
    if side=="right":return (cx+width(n)/2,cy)
    if side=="top":return (cx,cy-height(n)/2)
    if side=="bottom":return (cx,cy+height(n)/2)
    raise RuntimeError("Unexpected side")
def inside_segment(a,b,n,margin=12):
    l=x(n)-width(n)/2-margin;r=x(n)+width(n)/2+margin
    t=y(n)-height(n)/2-margin;bottom=y(n)+height(n)/2+margin
    # sample interior section, omit immediate connector endpoint tangencies
    for i in range(2,31):
        frac=i/32
        px=a[0]+(b[0]-a[0])*frac
        py=a[1]+(b[1]-a[1])*frac
        if l<px<r and t<py<bottom:return True
    return False
def choose(a,b,others):
    dx=x(b)-x(a);dy=y(b)-y(a)
    # only genuinely facing opposed sides are allowed
    pairs=[]
    if dx>0:pairs.append(("right","left"))
    if dx<0:pairs.append(("left","right"))
    if dy>0:pairs.append(("bottom","top"))
    if dy<0:pairs.append(("top","bottom"))
    if not pairs:raise RuntimeError("Two endpoint events share the same center")
    combos=[]
    for first,last in pairs:
        p=point(a,first);q=point(b,last)
        collisions=sum(inside_segment(p,q,z) for z in others)
        # spatial preference comes first; choose the shorter facing boundary link
        dist=math.dist(p,q)
        penalty=10000*collisions
        combos.append((penalty+dist,collisions,dist,first,last))
    result=min(combos)
    return result[3],result[4],result[1],result[2]
def load():
    fs=pages("items",{"type":"frame"})
    target=[z for z in fs if (z.get("data") or {}).get("title")==TITLE]
    source=[z for z in fs if hashlib.sha256(oid(z).encode()).hexdigest()==SOURCE_SHA]
    if len(target)!=1 or len(source)!=1:raise RuntimeError("Frame identity drift")
    frame=target[0]
    children=pages("items",{"parent_item_id":oid(frame)})
    cards={oid(z):z for z in children if z.get("type")=="sticky_note"}
    texts=[z for z in children if z.get("type")=="text"]
    if len(cards)!=147 or len(texts)!=22:raise RuntimeError("V14 frame content inventory drift")
    connectors=pages("connectors")
    links=[z for z in connectors if eid(z,"startItem") in cards and eid(z,"endItem") in cards]
    if len(links)!=51 or len(set(oid(z) for z in links))!=51:
        raise RuntimeError("V14 connector count/identity drift")
    if any(z.get("shape")!="curved" for z in links):
        raise RuntimeError("Unexpected connector path shape")
    s_children=pages("items",{"parent_item_id":oid(source[0])})
    sn={oid(z) for z in s_children if z.get("type")=="sticky_note"}
    s_edges=[z for z in connectors if eid(z,"startItem") in sn and eid(z,"endItem") in sn]
    if len(sn)!=116 or len(s_edges)!=46:raise RuntimeError("Protected V13 baseline drift")
    return cards,links
def audit():
    cards,links=load()
    wanted={}
    before=collections.Counter()
    error=collections.Counter()
    collision_current=collision_target=0
    for link in links:
        a,b=cards[eid(link,"startItem")],cards[eid(link,"endItem")]
        other=[v for k,v in cards.items() if k not in (oid(a),oid(b))]
        sa,sb,hit,dist=choose(a,b,other)
        olda=as_side(link.get("startItem") or {})
        oldb=as_side(link.get("endItem") or {})
        before[(olda,oldb)]+=1
        if olda not in SIDES or oldb not in SIDES:
            error["unresolved_anchor"]+=1
        if (olda,oldb)!=(sa,sb):error["not_nearest_facing_sides"]+=1
        if olda in SIDES and oldb in SIDES:
            collision_current+=sum(inside_segment(point(a,olda),point(b,oldb),v) for v in other)
        collision_target+=hit
        wanted[oid(link)]=(sa,sb)
    print("V14_ROUTING_PREFLIGHT_PASS","events=147","connectors=51",flush=True)
    print("V14_ENDPOINT_CURRENT_SIDE_COUNTS",dict(before),flush=True)
    print("V14_ENDPOINT_MISMATCH_COUNTS",dict(error),flush=True)
    print("V14_LINE_OF_SIGHT_STICKY_CONTACTS","current",collision_current,"planned",collision_target,flush=True)
    return cards,links,wanted,error
def verify(wanted,baseline):
    _,links=load()
    now={oid(c):c for c in links}
    if set(now)!=set(baseline):raise RuntimeError("Connector IDs changed")
    for cid,(sa,sb) in wanted.items():
        link=now[cid]
        old=baseline[cid]
        if (eid(link,"startItem"),eid(link,"endItem"))!=(old["source"],old["target"]):
            raise RuntimeError("Connector event mapping changed")
        if link.get("style")!=old["style"] or link.get("captions")!=old["captions"]:
            raise RuntimeError("Connector style or captions changed")
        if link.get("shape")!="curved":raise RuntimeError("Connector type changed")
        if as_side(link.get("startItem") or {})!=sa or as_side(link.get("endItem") or {})!=sb:
            raise RuntimeError("Endpoint side read-back mismatch")
    print("V14_ROUTING_READBACK_PASS", "51 connector IDs, event IDs, caption/style and curved shape unchanged",flush=True)
def main():
    cards,links,wanted,error=audit()
    if MODE=="audit":
        print("V14_ROUTING_AUDIT_ONLY");return
    old={oid(z):{"source":eid(z,"startItem"),"target":eid(z,"endItem"),
                 "style":z.get("style"),"captions":z.get("captions")} for z in links}
    todo=[z for z in links if
          (as_side(z.get("startItem") or {}),as_side(z.get("endItem") or {}))!=wanted[oid(z)]]
    if MODE=="pilot":todo=todo[:1]
    print("V14_ROUTING_WRITE_PLAN","changes",len(todo),"mode",MODE,flush=True)
    if not todo:
        print("V14_ROUTING_NOOP_ALREADY_CORRECT");return
    for i,edge in enumerate(todo):
        cid=oid(edge);sa,sb=wanted[cid]
        a=eid(edge,"startItem");b=eid(edge,"endItem")
        # Preserve style, captions and semantic event endpoints. PATCH with only
        # both native attachment points so the Miro engine re-routes the curve.
        call("PATCH","connectors/"+cid,{"startItem":{"id":a,"snapTo":sa},
                                      "endItem":{"id":b,"snapTo":sb}})
        new=call("GET","connectors/"+cid)
        if (as_side(new.get("startItem") or {}),as_side(new.get("endItem") or {}))!=(sa,sb):
            raise RuntimeError("Single connector PATCH not reflected")
        if i%10==0:print("V14_ROUTING_UPDATE_PROGRESS",i+1,flush=True)
    # Audit all connections in apply, changed-only in pilot.
    if MODE=="apply":verify(wanted,old)
    else:
        chosen=set(oid(z) for z in todo)
        verify({cid:(wanted[cid] if cid in chosen else (
           as_side(next(z for z in links if oid(z)==cid).get("startItem") or {}),
           as_side(next(z for z in links if oid(z)==cid).get("endItem") or {})))
                 for cid in wanted},old)
    print("V14_ROUTING_STRUCTURAL_PASS",MODE,len(todo),"adjusted connections",flush=True)
    print("VISUAL_RENDER_ACCEPTANCE_OPEN",flush=True)
try:main()
except Exception as e:print("V14_ROUTING_STOP",type(e).__name__,str(e),flush=True);sys.exit(1)
