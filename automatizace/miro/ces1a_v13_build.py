#!/usr/bin/env python3
"""Guarded additive V13 native clone. No source board text, IDs or token in public logs."""
import os,json,hashlib,collections,html,re,urllib.request,urllib.parse,urllib.error,time,sys,math
from pathlib import Path
T=os.environ["MIRO_DIAGNOSTIC_TOKEN"];B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
MODE=os.getenv("V13_MODE","audit")
if MODE not in ("audit","pilot","apply"):sys.exit("INVALID_MODE")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")
SOURCE_HASH="2ea7655a20b9f137232eabbf3e620d70a5c28e58ad9480a0af990dd58699b003"
TITLE="CES-1A · BP ES v13 · 116 událostí · pracovní verze"
# Publicly defensible, generic healthcare-payer event patterns approved for demo.
ADDITIONS=[
 ("N01","B2","V důsledku zpětně rozhodné skutečnosti se změnila povinnost plátce k úhradě pojistného."),
 ("N02","B4","VZP neuznala část vykázané zdravotní péče k úhradě."),
 ("N03","B5","Pojištěnci byla schválena úhrada konkrétní zdravotní služby v režimu předchozího souhlasu."),
 ("N04","B8","Pojištěnci byl udělen souhlas s úhradou plánované zdravotní péče v zahraničí."),
 ("N05","B5","Pojištěnec dosáhl ročního ochranného limitu započitatelných doplatků za léčivé přípravky."),
 ("N06","B5","Pojištěnci nebyla schválena úhrada konkrétní zdravotní služby v režimu předchozího souhlasu.")
]
def req(method,path,payload=None,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    raw=None if payload is None else json.dumps(payload,ensure_ascii=False).encode("utf-8")
    head={"Authorization":"Bearer "+T,"Accept":"application/json"}
    if raw is not None:head["Content-Type"]="application/json"
    for n in range(5):
        try:
            request=urllib.request.Request(url,data=raw,headers=head,method=method)
            with urllib.request.urlopen(request,timeout=50) as r:
                d=r.read();return json.loads(d) if d else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and n<4:
                time.sleep(min(20,2**n+1));continue
            raise RuntimeError(method+" "+path.split("/")[0]+" HTTP "+str(e.code)+"; inventory required") from None
        except Exception:
            if method=="GET" and n<2:time.sleep(2);continue
            raise RuntimeError(method+" transport uncertain; inventory before retry") from None
def listing(path,p=None):
    out=[];cursor=None
    for n in range(100):
        q=dict(p or {},limit=50)
        if cursor:q["cursor"]=cursor
        d=req("GET",path,params=q);out+=d.get("data",[]);cursor=d.get("cursor")
        if not cursor:return out
    raise RuntimeError("incomplete pagination")
def id(x):return str(x.get("id",""))
def par(x):return str((x.get("parent") or {}).get("id",""))
def txt(x):return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",str((x.get("data") or {}).get("content",""))))).strip()
def digest(x):return hashlib.sha256(txt(x).encode()).hexdigest()
def xx(x):return float((x.get("position") or {}).get("x") or 0)
def yy(x):return float((x.get("position") or {}).get("y") or 0)
def ww(x):return float((x.get("geometry") or {}).get("width") or 0)
def hh(x):return float((x.get("geometry") or {}).get("height") or 0)
def edge(e,k):return str((e.get(k) or {}).get("id") or "")
def side(e,k,default):
    a=e.get(k) or {};v=a.get("snapTo")
    if v in ("top","bottom","left","right"):return v
    q=a.get("position") or {}
    x=str(q.get("x",""));y=str(q.get("y",""))
    if x=="0%":return "left"
    if x=="100%":return "right"
    if y=="0%":return "top"
    if y=="100%":return "bottom"
    return default
def main():
    from landscape_build import RULES
    allitems=listing("items")
    frames=[x for x in allitems if x.get("type")=="frame"]
    f=[x for x in frames if hashlib.sha256(id(x).encode()).hexdigest()==SOURCE_HASH]
    if len(f)!=1:raise RuntimeError("V12 frame identity mismatch")
    f=f[0]; fid=id(f)
    raw=[x for x in allitems if par(x)==fid]
    notes=[x for x in raw if x.get("type")=="sticky_note"]
    texts=[x for x in raw if x.get("type")=="text"]
    if len(notes)!=110 or len(texts)!=18 or len(raw)!=128:raise RuntimeError("Source children drift")
    notes.sort(key=lambda z:(yy(z),xx(z)))
    srcmap={id(x):x for x in notes}
    beforeEdges=listing("connectors")
    edges=[e for e in beforeEdges if edge(e,"startItem") in srcmap and edge(e,"endItem") in srcmap]
    if len(edges)!=46:raise RuntimeError("Source edge drift")
    if len({digest(x) for x in notes})!=110:raise RuntimeError("Source text identity drift")
    refhash={digest(x):x for x in notes}
    if {z for v in RULES["groups"].values() for z in v}!=set(refhash):raise RuntimeError("V12 source does not match approved previous mapping")
    tgt=[x for x in frames if (x.get("data") or {}).get("title")==TITLE]
    if len(tgt)>1:raise RuntimeError("V13 duplicates")
    target=tgt[0] if tgt else None
    targetItems=[x for x in allitems if target and par(x)==id(target)]
    tid={id(x):x for x in targetItems}
    targetEdges=[e for e in beforeEdges if edge(e,"startItem") in tid and edge(e,"endItem") in tid]
    print("PREFLIGHT_OK","source_events=110","source_edges=46","target_exists="+str(bool(target)),"target_objects="+str(len(targetItems)),"target_edges="+str(len(targetEdges)),flush=True)
    if MODE=="audit":print("AUDIT_ONLY_NO_WRITES");return
    if target is None:
        right=max(xx(x)+ww(x)/2 for x in frames)
        target=req("POST","frames",{"data":{"title":TITLE},"style":{"fillColor":"#ffffff"},"geometry":{"width":ww(f),"height":hh(f)},"position":{"x":right+2200+ww(f)/2,"y":yy(f),"origin":"center"}})
        print("FRAME_CREATED",flush=True)
    targetId=id(target)
    if not targetId:raise RuntimeError("Frame create did not return ID")
    created=0
    def create(typ,sx,sy,width,content,style=None,data=None,height=None):
        nonlocal created
        matches=[z for z in targetItems if z.get("type")==typ and abs(xx(z)-sx)<3 and abs(yy(z)-sy)<3]
        if len(matches)>1:raise RuntimeError("Duplicate target slot")
        if matches:
            if txt(matches[0])!=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",str(content)))).strip():raise RuntimeError("Existing target slot drift")
            return matches[0]
        payload={"data":dict(data or {},content=content),"position":{"x":sx,"y":sy,"origin":"center"},"geometry":{"width":width},"parent":{"id":targetId}}
        if height is not None:payload["geometry"]["height"]=height
        if style:payload["style"]=style
        endpoint={"sticky_note":"sticky_notes","text":"texts"}[typ]
        obj=req("POST",endpoint,payload)
        targetItems.append(obj);created+=1
        return obj
    originalMap={}
    srcTodo=notes[:1] if MODE=="pilot" else notes
    txtTodo=texts[:1] if MODE=="pilot" else texts
    for n,z in enumerate(srcTodo):
        st={k:v for k,v in (z.get("style") or {}).items() if k in ("fillColor","textAlign","textAlignVertical")}
        new=create("sticky_note",xx(z),yy(z),ww(z),z["data"]["content"],st,{"shape":"rectangle"})
        originalMap[id(z)]=id(new)
        if n%20==0:print("CLONE_PROGRESS",n+1,flush=True)
    for z in txtTodo:
        st={k:v for k,v in (z.get("style") or {}).items() if k in ("fontFamily","fontSize","color","textAlign","textAlignVertical","fillOpacity")}
        create("text",xx(z),yy(z),ww(z),z["data"]["content"],st)
    # Keep exact source layout. New events occupy vacant positions in their related
    # scenarios, never displacing source notes or making false causal arrows.
    current=[z for z in targetItems if z["type"]=="sticky_note"]
    nextAdditions=[]
    for code,group,name in ADDITIONS[:1] if MODE=="pilot" else ADDITIONS:
        domain=[refhash[k] for k in RULES["groups"][group]]
        median_y=sorted(yy(z) for z in domain)[len(domain)//2]
        choices=[]
        for delta_y in (0,430,-430,860,-860,1290,-1290,1720):
            for x in range(9300,16300,890):
                y=median_y+delta_y
                if 400<y<hh(f)-260 and x<ww(f)-240:
                    if all(abs(xx(z)-x)>500 or abs(yy(z)-y)>315 for z in current):
                        score=abs(delta_y)*10+abs(x-(max(xx(z) for z in domain)+890))
                        choices.append((score,x,y))
        if not choices:raise RuntimeError("No collision-free slot for approved event")
        _,x,y=min(choices)
        obj=create("sticky_note",x,y,387,code+" · "+name,{"fillColor":"light_yellow","textAlign":"center"},{"shape":"rectangle"})
        current.append(obj);nextAdditions.append((code,obj))
    if MODE=="apply":
        targetIds={id(z) for z in targetItems if z.get("type")=="sticky_note"}
        for i,e in enumerate(edges):
            left=originalMap[edge(e,"startItem")];right=originalMap[edge(e,"endItem")]
            copies=[z for z in targetEdges if edge(z,"startItem")==left and edge(z,"endItem")==right and z.get("captions",[])==e.get("captions",[])]
            if len(copies)>1:raise RuntimeError("Duplicate connector")
            if not copies:
                st={k:v for k,v in (e.get("style") or {}).items() if k in ("strokeColor","strokeWidth","strokeStyle","strokeCap","fontSize","color")}
                payload={"startItem":{"id":left,"snapTo":side(e,"startItem","right")},"endItem":{"id":right,"snapTo":side(e,"endItem","left")},"shape":"curved","captions":e.get("captions",[])}
                if st:payload["style"]=st
                v=req("POST","connectors",payload);targetEdges.append(v);created+=1
            if i%10==0:print("EDGE_PROGRESS",i+1,flush=True)
    # Fresh independent REST readback and source-protection integrity.
    finalItems=listing("items");finalConn=listing("connectors")
    afterSource=[x for x in finalItems if par(x)==fid]
    if len(afterSource)!=128 or {(id(z),digest(z),xx(z),yy(z)) for z in afterSource}!={(id(z),digest(z),xx(z),yy(z)) for z in raw}:raise RuntimeError("SOURCE_OBJECTS_CHANGED")
    sourceLinksAfter=[e for e in finalConn if edge(e,"startItem") in srcmap and edge(e,"endItem") in srcmap]
    if len(sourceLinksAfter)!=46 or {(id(z),edge(z,"startItem"),edge(z,"endItem")) for z in sourceLinksAfter}!={(id(z),edge(z,"startItem"),edge(z,"endItem")) for z in edges}:raise RuntimeError("SOURCE_EDGES_CHANGED")
    after=[z for z in finalItems if par(z)==targetId]
    newnotes=[x for x in after if x.get("type")=="sticky_note"]
    newtext=[x for x in after if x.get("type")=="text"]
    afterIDs={id(x) for x in newnotes}
    conn=[e for e in finalConn if edge(e,"startItem") in afterIDs and edge(e,"endItem") in afterIDs]
    required=2 if MODE=="pilot" else 116
    if len(newnotes)!=required or len(newtext)!=(1 if MODE=="pilot" else 18) or len(conn)!=(0 if MODE=="pilot" else 46):raise RuntimeError("TARGET_COUNTS_CHANGED")
    if MODE=="apply":
        # All historical event texts preserved, six additions distinct.
        oldcnt=collections.Counter(txt(z) for z in notes)
        targetcnt=collections.Counter(txt(z) for z in newnotes)
        if any(targetcnt[k]!=v for k,v in oldcnt.items()):raise RuntimeError("Event text corruption or duplicate")
        if any(targetcnt[code+" · "+name]!=1 for code,grp,name in ADDITIONS):raise RuntimeError("Approved event text missing")
        if any(x.get("shape")!="curved" for x in conn):raise RuntimeError("Connector shape mismatch")
    print("READBACK_PASS","notes",len(newnotes),"texts",len(newtext),"native_curved",len(conn),"source_unchanged",True,"created_this_run",created,flush=True)
    print("TARGET_FRAME_URL: https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget="+targetId,flush=True)
    print("VISUAL_ACCEPTANCE_OPEN",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:print("BUILD_STOP:",type(e).__name__,str(e));sys.exit(1)
