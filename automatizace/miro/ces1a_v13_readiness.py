#!/usr/bin/env python3
"""Guarded read-only V13 clone readiness; does not print client data or any IDs."""
import os,json,hashlib,collections,html,re,urllib.request,urllib.parse,urllib.error,time,sys
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];T=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")
SOURCE_HASH="2ea7655a20b9f137232eabbf3e620d70a5c28e58ad9480a0af990dd58699b003"
TARGET_TITLE="CES-1A · BP ES v13 · 116 událostí · pracovní verze"
def req(path,p=None):
    url=BASE+"/"+path
    if p:url+="?"+urllib.parse.urlencode(p)
    for n in range(5):
        try:
            q=urllib.request.Request(url,headers={"Authorization":"Bearer "+T,"Accept":"application/json"})
            with urllib.request.urlopen(q,timeout=35) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and n<4:time.sleep(2**n+1);continue
            raise RuntimeError("REST read failed HTTP "+str(e.code))
def listing(path,p=None):
    out=[];cursor=None
    for n in range(100):
        q=dict(p or {},limit=50)
        if cursor:q["cursor"]=cursor
        v=req(path,q);out.extend(v.get("data",[]));cursor=v.get("cursor")
        if not cursor:return out
    raise RuntimeError("Pagination incomplete")
def text(x):return re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",str((x.get("data") or {}).get("content",""))))).strip()
def main():
    frames=listing("items",{"type":"frame"})
    source=[f for f in frames if hashlib.sha256(str(f["id"]).encode()).hexdigest()==SOURCE_HASH]
    assert len(source)==1,"Source frame not unique"
    source=source[0]
    children=listing("items",{"parent_item_id":str(source["id"])})
    notes=[x for x in children if x["type"]=="sticky_note"]
    ids={str(x["id"]) for x in notes}
    edges=[e for e in listing("connectors") if str((e.get("startItem") or {}).get("id")) in ids and str((e.get("endItem") or {}).get("id")) in ids]
    assert len(notes)==110 and len(edges)==46,"V12 inventory drift"
    tgt=[f for f in frames if (f.get("data") or {}).get("title")==TARGET_TITLE]
    if len(tgt)>1:raise RuntimeError("Ambiguous V13 target")
    counts=collections.Counter(x["type"] for x in children)
    bounds={x["type"]:(round(min(float((z.get("position") or {}).get("x") or 0) for z in children if z["type"]==x["type"])),round(max(float((z.get("position") or {}).get("x") or 0) for z in children if z["type"]==x["type"]))) for x in children}
    print("SOURCE_OK","notes",len(notes),"edges",len(edges),"types",dict(counts),"candidateV13",len(tgt),"geometry",source.get("geometry"),"position",source.get("position"))
    print("SOURCE_COORDINATES",bounds)
    print("NATIVE_EDGES",dict(collections.Counter(e.get("shape") for e in edges)))
    known={"vykazan":0,"zahranic":0,"souhlas":0,"leciv":0,"pojistn":0}
    for x in notes:
        s=text(x).lower()
        for k in known:
            if k in s:known[k]+=1
    print("ANCHOR_SIGNALS",known)
    print("AUDIT_ONLY_NO_WRITES")
if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL:",type(e).__name__,str(e));sys.exit(1)
