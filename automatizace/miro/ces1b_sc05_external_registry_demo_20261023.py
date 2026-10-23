#!/usr/bin/env python3
"""One-shot CES 1B SC-05 illustrative business scenario: external ROB/ROS source.
Miro REST API v2 through pre-authorized GitHub environment.
EXISTING external registries (AS-IS), not future target VZP system.
Strictly additive; no changes to SC01-04/BP/DL or existing registered catalogue.
Source authority: current VZP working inputs S50/S51; attribute authority/notification contract OPEN.
"""
import os,json,urllib.request,urllib.parse,urllib.error,time,html,re,sys
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]; TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
if B!="uXjVHiylz-0=":raise RuntimeError("WRONG_BOARD")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
FRAME_TITLE="CES-1B · S0.1 · SC-05 ROB/ROS → reakce VZP · v1 WORKING"
F_W,F_H=7400,5200
FX,FY=275100,37950
COLORS={"ext":"#e5a6cd","event":"orange","policy":"#bb8dcc","command":"#72d5ed",
"actor":"#fff35a","query":"#c8e99b","hotspot":"red"}
# Each row: stable key, class, user-readable business content, local centre x/y, object width, optional font
NODES=[
 ("rob","ext","EXTERNÍ / AS-IS\nROB – Registr obyvatel",720,1070,1050,41),
 ("fochange","event","Změna referenčního údaje FO byla v ROB evidována.",2170,1070,1000,37),
 ("foarrive","event","Informace o změně FO byla VZP zpřístupněna k ověření. [HYPOTHESIS]",3770,1070,1120,37),
 ("ros","ext","EXTERNÍ / AS-IS\nROS – Registr osob",720,1900,1050,41),
 ("pochange","event","Změna referenčního údaje PO byla v ROS evidována.",2170,1900,1000,37),
 ("poarrive","event","Informace o změně PO byla VZP zpřístupněna k ověření. [HYPOTHESIS]",3770,1900,1120,37),
 ("policy","policy","POLICY / BUSINESS RULE\nOvěřit autoritu atributu, původ, platnost a dopad změny.",5550,1500,1420,38),
 ("actor","actor","ACTOR / ROLE\nPověřená referenční agenda VZP",3820,2820,1050,38),
 ("query","query","READ MODEL\nStávající reference, provenience a historie změn",2220,2820,1090,38),
 ("command","command","COMMAND / ACTION\nPosoudit dopad změny do referenčních údajů VZP",5570,2820,1380,38),
 ("accepted","event","Ověřená změna byla promítnuta do referenční evidence. [HYPOTHESIS]",5700,3780,1390,39),
 ("exception","event","Rozpor mezi referenčními údaji byl zjištěn.",5700,4450,1390,39),
 ("hotspot","hotspot","HOTSPOT / OPEN\nZpůsob získání změn (notifikace/dotaz)? Kdo má autoritu k atributu? Jak řešit rozpory a zpětnou platnost?",2420,4120,1400,39),
]
# native connectors: key, source, target, labelled causal relationship, source side, target side
LINKS=[
 ("r1","rob","fochange","externí autoritativní zdroj","right","left"),
 ("r2","ros","pochange","externí autoritativní zdroj","right","left"),
 ("r3","fochange","foarrive","zpřístupnění VZP (OPEN)","right","left"),
 ("r4","pochange","poarrive","zpřístupnění VZP (OPEN)","right","left"),
 ("r5","foarrive","policy","aktivuje pravidlo","right","top"),
 ("r6","poarrive","policy","aktivuje pravidlo","right","bottom"),
 ("r7","policy","command","vyvolá posouzení","bottom","top"),
 ("r8","actor","query","nahlíží do informací","left","right"),
 ("r9","actor","command","rozhoduje / prověřuje","right","left"),
 ("r10","command","accepted","změna ověřena","bottom","top"),
 ("r11","command","exception","rozpor / nejasnost","right","top"),
]
def request(method,path,payload=None):
 data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode("utf-8")
 headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
 if data is not None:headers["Content-Type"]="application/json"
 for a in range(4 if method=="GET" else 1):
  try:
   q=urllib.request.Request(BASE+path,headers=headers,data=data,method=method)
   with urllib.request.urlopen(q,timeout=55) as r:
    body=r.read();return json.loads(body) if body else {}
  except urllib.error.HTTPError as e:
   if method=="GET" and a<3 and e.code in (429,500,502,503,504):
    time.sleep(2**a);continue
   raise RuntimeError("REST_"+method+"_"+path.split("?")[0]+"_HTTP_"+str(e.code)) from None
def listing(path,filters=None):
 result=[];cursor=None
 for _ in range(90):
  q=dict(filters or {},limit=50)
  if cursor:q["cursor"]=cursor
  r=request("GET",path+"?"+urllib.parse.urlencode(q))
  result.extend(r.get("data") or [])
  cursor=r.get("cursor") or r.get("nextCursor")
  if not cursor:return result
 raise RuntimeError("PAGINATION_UNBOUNDED")
def name(x):return html.unescape(re.sub(r"<[^>]*>","",str((x.get("data") or {}).get("content") or ""))).replace("\n"," ").strip()
def iid(x):return str(x.get("id") or "")
def main():
 fs=listing("items",{"type":"frame"})
 existing=[f for f in fs if (f.get("data") or {}).get("title")==FRAME_TITLE]
 if len(existing)>1:raise RuntimeError("FRAME_DUPLICATE")
 if existing:
  frame=existing[0]
  print("FRAME_REUSED",iid(frame),flush=True)
 else:
  frame=request("POST","frames",{"data":{"title":FRAME_TITLE},"geometry":{"width":F_W,"height":F_H},"position":{"x":FX,"y":FY,"origin":"center"},"style":{"fillColor":"#ffffff"}})
  if not iid(frame):raise RuntimeError("FRAME_NO_ID")
  print("FRAME_CREATED",iid(frame),flush=True)
 f_id=iid(frame)
 def add(endpoint,key,content,x,y,w,color,font=38):
  current=listing("items",{"parent_item_id":f_id})
  prior=[z for z in current if name(z)==re.sub(r"\\s+"," ",content).strip()]
  if len(prior)>1:raise RuntimeError("DUPLICATE_NODE_CONTENT_"+key)
  if prior:return prior[0]
  body={"data":{"content":content},"position":{"x":x,"y":y,"origin":"center"},"geometry":{"width":w},"parent":{"id":f_id}}
  if endpoint=="sticky_notes":
   body["data"]["shape"]="rectangle"
   body["style"]={"fillColor":color,"textAlign":"center","textAlignVertical":"middle"}
  else:
   body["data"]["shape"]="rectangle"
   body["geometry"]["height"]=220
   body["style"]={"fillColor":color,"fontSize":str(font),"fontFamily":"open_sans","textAlign":"center","textAlignVertical":"middle","color":"#26353a"}
  return request("POST",endpoint,body)
 def add_title(content,x,y,w,font):
  return add("shapes","header-"+str(y),content,x,y,w,"#ffffff",font)
 add_title("1B · SC-05 · Externí autoritativní změna FO / PO → business reakce VZP",3700,155,7020,57)
 add_title("WORKING HYPOTHESIS · ROB/ROS = EXISTUJÍCÍ EXTERNÍ REGISTRY · target aplikace VZP zde nejsou modelovány",3700,315,6960,31)
 objects={}
 for key,typ,content,x,y,w,font in NODES:
  route="sticky_notes" if typ in ("event","hotspot") else "shapes"
  item=add(route,key,content,x,y,w,COLORS[typ],font)
  objects[key]=item
 add_title("OPEN: notifikace versus dotazování, atributová autorita, okamžik platnosti a vazba na SC-02. Business draft S50/S51 ≠ schválený integrační kontrakt.",3700,5020,7000,30)
 edges=listing("connectors")
 for key,src,dst,label,start_side,end_side in LINKS:
  a,b=iid(objects[src]),iid(objects[dst])
  match=[e for e in edges if iid(e.get("startItem") or {})==a and iid(e.get("endItem") or {})==b]
  if len(match)>1:raise RuntimeError("DUPLICATE_CONNECTOR_"+key)
  if match:continue
  conn=request("POST","connectors",{"startItem":{"id":a,"snapTo":start_side},"endItem":{"id":b,"snapTo":end_side},
   "captions":[{"content":label,"position":"50%"}],"shape":"curved",
   "style":{"strokeColor":"#26353a","strokeWidth":"5","fontSize":"46","endStrokeCap":"filled_triangle","color":"#26353a"}})
  if not iid(conn):raise RuntimeError("CONNECTOR_CREATE_"+key)
  edges.append(conn)
 children=listing("items",{"parent_item_id":f_id})
 edgecheck=listing("connectors")
 nodeids={iid(z) for z in children}
 active=[e for e in edgecheck if iid(e.get("startItem") or {}) in nodeids and iid(e.get("endItem") or {}) in nodeids]
 assert len([z for z in children if z.get("type")=="sticky_note"])==7, "STICKY_COUNT_DRIFT"
 assert len(active)==11,"EDGE_COUNT_DRIFT_"+str(len(active))
 assert all(iid(objects[k]) in nodeids for k,_,*__ in NODES),"NODE_DRIFT"
 assert all((e.get("startItem") or {}).get("id") and (e.get("endItem") or {}).get("id") for e in active),"DANGLING_EDGE"
 print("SC05_ACCEPTANCE_PASS",json.dumps({"frame":f_id,"nodes":len(NODES),"events":6,"external_systems":2,"policy":1,"actor":1,"read_model":1,"command":1,"hotspot":1,"connectors":len(active),"working_only":True,"visual_gate":"OPEN"}),flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("SC05_STOP",type(e).__name__,str(e),flush=True)
  sys.exit(1)
