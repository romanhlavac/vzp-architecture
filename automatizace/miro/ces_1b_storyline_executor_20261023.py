#!/usr/bin/env python3
"""Read-only preflight; identifiers and geometry only in logs, never board card text."""
import os,json,urllib.request,urllib.parse,urllib.error,time,hashlib
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
assert B=="uXjVHiylz-0="
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
def api(verb,path,body=None):
    req=urllib.request.Request(BASE+path,method=verb,data=json.dumps(body).encode() if body is not None else None,headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
    for n in range(4 if verb=="GET" else 1):
        try:
            with urllib.request.urlopen(req,timeout=55) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if verb=="GET" and e.code in (429,500,502,503,504) and n<3: time.sleep(2**n);continue
            raise RuntimeError("REST_"+str(e.code)) from None
def page(path,filters=None):
    out=[];q=dict(filters or {},limit=50)
    for _ in range(200):
        z=api("GET",path+"?"+urllib.parse.urlencode(q));out+=z.get("data",[])
        c=z.get("cursor") or z.get("nextCursor")
        if not c:return out
        q["cursor"]=c
    raise RuntimeError("PAGINATION")
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def main():
    fs=page("items",{"type":"frame"});links=page("connectors")
    print("READ_ONLY_PREFLIGHT",len(fs),len(links),flush=True)
    for f in fs:
        print("FRAME",json.dumps({k:f.get(k) for k in ("id","position","geometry")}),flush=True)
    for fid in ["3458764687949068244","3458764687741774534","3458764687757375873"]:
        kids=page("items",{"parent_item_id":fid})
        ids={o["id"] for o in kids}
        edges=[o for o in links if (o.get("startItem") or {}).get("id") in ids or (o.get("endItem") or {}).get("id") in ids]
        print("BASELINE",fid,len(kids),len(edges),digest(kids),digest(edges),flush=True)
    print("PREFLIGHT_PASS_WRITES_0",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e: print("STOP",type(e).__name__,str(e),flush=True);raise SystemExit(1)
