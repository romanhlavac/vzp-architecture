#!/usr/bin/env python3
"""CES DEMO 1A/1B semantic layout audit (read-only default). No private business content in logs."""
import os,urllib.request,urllib.parse,urllib.error,json,collections,hashlib,time
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];assert B=="uXjVHiylz-0="
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
T=os.environ["MIRO_DIAGNOSTIC_TOKEN"]; MODE=os.getenv("LAYOUT_MODE","audit")
assert MODE=="audit"
def api(method,path,body=None):
  q=urllib.request.Request(BASE+path,method=method,data=json.dumps(body).encode() if body else None,headers={"Authorization":"Bearer "+T,"Content-Type":"application/json","Accept":"application/json"})
  for n in range(4):
    try:
      with urllib.request.urlopen(q,timeout=35) as f:return json.load(f)
    except urllib.error.HTTPError as e:
      if e.code in (429,500,502,503,504) and n<3:time.sleep(2**n);continue
      raise RuntimeError("HTTP_"+str(e.code)+"_"+path.split("?")[0]) from None
def page(path,opts=None):
  o=[];p=dict(opts or {},limit=50)
  for _ in range(200):
    z=api("GET",path+"?"+urllib.parse.urlencode(p));o+=z.get("data",[])
    c=z.get("cursor") or z.get("nextCursor")
    if not c:return o
    p["cursor"]=c
  raise RuntimeError("PAGINATION_EXCEEDED")
def box(f):
  p=f["position"];g=f["geometry"]
  return [round(p["x"]-g["width"]/2),round(p["y"]-g["height"]/2),round(g["width"]),round(g["height"])]
def entry(f):
  t=f.get("data",{}).get("title","")
  return t
FRAME_IDS={
"BP":"3458764687741774534","DL":"3458764687757375873","nav":"3458764688218487258",
"inventory":"3458764687949068244","method":"3458764688162404596",
"sc01":"3458764687939229431","sc02":"3458764687939229785","sc05":"3458764688202201527",
"sc03":"3458764687939406397","sc04":"3458764687949762980",
"summary":"3458764687942876552","clusters":"3458764688217500338","L2":"3458764687938964779",
"boundary":"3458764688217622063"}
def main():
  fs=page("items",{"type":"frame"});fm={str(f["id"]):f for f in fs}
  print("TOTAL_FRAMES",len(fs),flush=True)
  for label,fid in FRAME_IDS.items():
    f=fm[fid];print("FRAME",label,fid,*box(f),len(entry(f)),flush=True)
    kids=page("items",{"parent_item_id":fid})
    counts=collections.Counter(x["type"] for x in kids)
    print("CHILDREN",label,len(kids),dict(counts),flush=True)
    if label in ("sc01","sc02","sc05","sc03","sc04"):
      for k in kids[:24]:
        z=k.get("style") or {};g=k.get("geometry") or {}
        print("STYLE",label,k["id"],k["type"],str(z.get("fillColor"))[:18],str(z.get("fontSize"))[:12],str(z.get("fontFamily"))[:12],round(g.get("width",0)),round(g.get("height",0)),flush=True)
  for key in ("nav","sc01","sc05"):
    fid=FRAME_IDS[key];kids=page("items",{"parent_item_id":fid})
    if key=="sc05":
      for k in kids:
        z=k.get("style") or {};p=k.get("position") or {};g=k.get("geometry") or {}
        print("DETAIL",key,k["id"],k["type"],round(p.get("x",0)),round(p.get("y",0)),round(g.get("width",0)),round(g.get("height",0)),z.get("fillColor"),z.get("fontSize"),len(str((k.get("data") or {}).get("content",""))),flush=True)
  for f in fs:
    t=entry(f)
    if "CES DEMO" in t and ("MAIN" in t or "KROK 1" in t or "1A" in t or "1B" in t):
      print("LABEL",f["id"],"MAIN" if "MAIN" in t else "OTHER", "1A" if "1A" in t else "1B" if "1B" in t else "GENERAL",*box(f),flush=True)
  print("AUDIT_READONLY_PASS",flush=True)
if __name__=="__main__":main()
