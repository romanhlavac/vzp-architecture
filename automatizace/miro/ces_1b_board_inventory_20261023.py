#!/usr/bin/env python3
"""READ ONLY Miro 1B/CES demo frame inventory. No demo business card text, no writes.
Audit intended to distinguish methodological story vs. legacy/overlapping frames.
"""
import os,json,re,urllib.request,urllib.parse,urllib.error,time,collections,datetime
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];T=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
assert B=="uXjVHiylz-0=", "WRONG_BOARD"
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
def get(path,params=None):
 u=BASE+path+("?"+urllib.parse.urlencode(params) if params else "")
 for n in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={"Authorization":"Bearer "+T,"Accept":"application/json"}),timeout=55) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code in (429,500,502,503,504) and n<3:time.sleep(2**n);continue
   raise RuntimeError("READ_ERROR_"+str(e.code)+"_"+path)
def page(path,filters=None):
 out=[];q=dict(filters or {},limit=50);cursor=None
 for _ in range(120):
  if cursor:q["cursor"]=cursor
  r=get(path,q);out.extend(r.get("data") or [])
  cursor=r.get("cursor") or r.get("nextCursor")
  if not cursor:return out
 raise RuntimeError("PAGINATION_GUARD")
def tit(o):return str((o.get("data") or {}).get("title") or "")
def ident(o):return str(o.get("id") or "")
def position(o):return o.get("position") or {}
def types(items):
 c=collections.Counter(x.get("type") or "" for x in items)
 return {k:c[k] for k in sorted(c)}
def signal(items):
 c=collections.Counter()
 for it in items:
  t=it.get("type")
  if t=="sticky_note":
   color=str((it.get("style") or {}).get("fillColor") or "").lower()
   if color in ("orange","#ff9d48","#ffab91","#ffbc72"):c["event"]+=1
   elif color in ("red","#f45b69","#ff4b52"):c["hotspot"]+=1
   else:c["sticky_other"]+=1
  elif t=="shape":
   col=str((it.get("style") or {}).get("fillColor") or "").lower()
   if col=="#72d5ed":c["command"]+=1
   elif col=="#e5a6cd":c["system_pink"]+=1
   elif col=="#bb8dcc":c["policy"]+=1
   elif col=="#fff35a":c["actor"]+=1
   elif col=="#c8e99b":c["query"]+=1
 return dict(c)
def main():
 frames=page("items",{"type":"frame"})
 print("AUDIT_HEADER",json.dumps({"board":"CES demo","frames_total":len(frames),"run_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}),flush=True)
 # Geographically include 1B and adjacent synthesis. Whole 1B hierarchy and historical related titles.
 include=lambda s: bool(re.search(r"1B|1C|CES|DEMO|SUBDOMAIN|L2|PROCESS|METOD|OVERVIEW|E2E|DOMA[IÍ]N",s,re.I))
 selected=[f for f in frames if include(tit(f))]
 selected.sort(key=lambda f:(float((position(f).get("y") or 0)),float((position(f).get("x") or 0))))
 all_links=page("connectors")
 for f in selected:
  fid=ident(f);p=position(f);g=f.get("geometry") or {}
  title=tit(f);relevant=bool(re.search(r"1B|1C|SC-0[1-9]|Subdomain|Process|Metodický vzor|L2",title,re.I))
  kids=page("items",{"parent_item_id":fid}) if relevant else []
  kidids={ident(i) for i in kids}
  links=[e for e in all_links if ident(e.get("startItem") or {}) in kidids or ident(e.get("endItem") or {}) in kidids] if relevant else []
  within=sum(ident(e.get("startItem") or {}) in kidids and ident(e.get("endItem") or {}) in kidids for e in links)
  rec={"id":fid,"title":title,"x":round(float(p.get("x") or 0)),"y":round(float(p.get("y") or 0)),
       "w":round(float(g.get("width") or 0)),"h":round(float(g.get("height") or 0)),
       "created":f.get("createdAt"),"modified":f.get("modifiedAt"),
       "n":len(kids) if relevant else None,"types":types(kids) if relevant else None,
       "signals":signal(kids) if relevant else None,"connectors":within if relevant else None,
       "external_edges":len(links)-within if relevant else None}
  print("FRAME_AUDIT",json.dumps(rec,ensure_ascii=False,separators=(",",":")),flush=True)
 print("AUDIT_END",json.dumps({"selected":len(selected),"mode":"READ_ONLY","writes":0}),flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:print("AUDIT_STOP",type(e).__name__,str(e),flush=True);raise SystemExit(1)
