#!/usr/bin/env python3
"""Native, editable reconstruction of the exact 1B Process Modelling reference image.
Model semantics: actor/command/system/event/policy/query/hotspot and timeline example.
Source image on the DDD reference board: item 3458764567900106962.
No bitmap written. Existing BP/L1DL/1B frames are read-only.
Modes: audit (default), pilot (one native sticky), apply, verify.
"""
import os,sys,time,json,html,re,urllib.request,urllib.parse,urllib.error,collections
MODE=os.getenv("CES1B_METHOD_MODE","audit")
if MODE not in ("audit","pilot","apply","verify"):raise SystemExit("INVALID_MODE")
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
if BOARD!="uXjVHiylz-0=":raise RuntimeError("WRONG_TARGET_BOARD")
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
FRAME_TITLE="CES-1B · 00A · Metodický vzor Process Modelling · nativní Miro"
OVERVIEW="CES-1B · 00 · Identifikace procesních scénářů S0.1 a S0.2"
MAP_ID="3458764687938964779"
W,H=8000,6500
REF_URL="https://miro.com/app/board/uXjVH27wYU4=/?moveToWidget=3458764567900106962"
# Unique native sticky business labels; no machine IDs are printed on orange event or red hotspot notes.
NODES=[
 ("actor","Aktér / Actor","yellow",740,1780,420),
 ("command","Příkaz / akce\nCommand / Action","light_blue",2450,1780,540),
 ("system","Systém / System","pink",4320,1780,620),
 ("event","Doménová událost\nDomain Event","orange",6480,1780,540),
 ("policy","Politika / Policy","violet",4300,870,540),
 ("query","Čtecí model / informace\nQuery Model / Information","light_green",2450,2730,580),
 ("hotspot","Hotspot / nejasnost","red",4350,2880,480),
 ("ex_actor","Agendový pracovník","yellow",510,4200,370),
 ("ex_query","Dostupná referenční identita","light_green",1200,4200,450),
 ("ex_command","Prověřit shodu subjektu","light_blue",2220,4200,470),
 ("ex_system","Evidence identity","pink",3120,4200,520),
 ("ex_event","Subjekt byl ztotožněn","orange",4050,4200,470),
 ("ex_policy","Po potvrzení shody navázat agendou","violet",4920,3670,570),
 ("ex_command2","Převzít agendový výsledek","light_blue",5650,4200,470),
 ("ex_system2","Evidence rolí a vztahů","pink",6410,4200,470),
 ("ex_event2","Role byla referenčně zapsána","orange",7330,4200,470),
 ("branch_query","Sporná kandidátní shoda","light_green",3980,5230,430),
 ("branch_actor","Referent pro posouzení","yellow",4680,5230,370),
 ("branch_command","Odborně posoudit shodu","light_blue",5440,5230,430),
 ("branch_system","Posouzení identity","pink",6200,5230,460),
 ("branch_event","Shoda byla potvrzena","orange",7330,5230,460),
]
# Non-semantic explanatory headings and labels; these are editable Miro texts.
TEXTS=[
 ("title","1B · Process Modelling – prvky, vazby a jejich čtení",4000,180,7440,52),
 ("subtitle","Rekonstrukce metodického obrázku pomocí nativních Miro sticky notes a konektorů",4000,300,7400,29),
 ("upper_label","METODICKÁ GRAMATIKA EVENT STORMINGU",4000,470,7400,34),
 ("upper_hint","Příkaz spouští aktér nebo policy. Systém vytváří doménovou událost; výsledek může aktualizovat čtecí model. Hotspot označuje problém, nikoli událost.",4000,3220,7350,23),
 ("lower_label","PŘÍKLAD ČASOVÉHO PRŮBĚHU  →",4000,3490,7400,38),
 ("lower_hint","Příklad je adaptovaný na CES demo. U S0.2 vzniká referenční zápis role až po doloženém rozhodnutí příslušné agendy; S0.2 právo sama nezakládá.",4000,5850,7350,23),
 ("source","Metodický zdroj: Miro reference – Process modelling Picture that explains Almost Everything; nativně překresleno pro 1B.",4000,6230,7350,19)
]
# ID-less text, native connector endpoints pinned to genuinely facing edges.
EDGES=[
 ("actor","command","rozhoduje provést","right","left","curved"),
 ("command","system","vyvolá akci v","right","left","straight"),
 ("system","event","vytváří událost","right","left","straight"),
 ("event","policy","aktivuje","top","right","curved"),
 ("policy","command","vydává příkaz","left","top","curved"),
 ("event","query","vytváří informaci","bottom","right","curved"),
 ("actor","query","sleduje","bottom","left","curved"),
 ("ex_actor","ex_command","","right","left","curved"),
 ("ex_command","ex_system","","right","left","straight"),
 ("ex_system","ex_event","","right","left","straight"),
 ("ex_event","ex_policy","aktivuje podmínku","top","left","curved"),
 ("ex_policy","ex_command2","navazující akce","right","top","curved"),
 ("ex_command2","ex_system2","","right","left","straight"),
 ("ex_system2","ex_event2","","right","left","straight"),
 ("ex_event","branch_query","nejednoznačný případ","bottom","top","curved"),
 ("branch_actor","branch_command","","right","left","straight"),
 ("branch_query","branch_command","","right","left","curved"),
 ("branch_command","branch_system","","right","left","straight"),
 ("branch_system","branch_event","","right","left","straight")
]
def call(method,path,body=None):
  data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
  headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
  if data is not None:headers["Content-Type"]="application/json"
  retry=4 if method=="GET" else 1
  for t in range(retry):
    try:
      q=urllib.request.Request(ROOT+path,data=data,headers=headers,method=method)
      with urllib.request.urlopen(q,timeout=48) as r:
        raw=r.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
      if method=="GET" and e.code in (429,500,502,503,504) and t<retry-1:
        time.sleep(2**t+1);continue
      raise RuntimeError("REST_"+method+"_HTTP_"+str(e.code)+"_"+path.split("?")[0]) from None
    except (urllib.error.URLError,TimeoutError):
      raise RuntimeError("REST_"+method+"_UNCERTAIN_"+path.split("?")[0]) from None
def listing(path,params=None):
  out=[];cursor=None
  for _ in range(150):
    q=dict(params or {},limit=50)
    if cursor:q["cursor"]=cursor
    response=call("GET",path+"?"+urllib.parse.urlencode(q))
    out.extend(response.get("data",[]));cursor=response.get("cursor") or response.get("nextCursor")
    if not cursor:return out
  raise RuntimeError("PAGINATION_INCOMPLETE")
def iid(o):return str(o.get("id") or "")
def norm(o):
  s=str((o.get("data") or {}).get("content") or "")
  return " ".join(html.unescape(re.sub(r"<[^>]*>"," ",html.unescape(s))).split())
def xy(o):
  p=o.get("position") or {};return float(p.get("x") or 0),float(p.get("y") or 0)
def geom(o):
  g=o.get("geometry") or {};return float(g.get("width") or 0),float(g.get("height") or 0)
def baseline():
  frames=listing("items",{"type":"frame"});bytitle=collections.defaultdict(list)
  for f in frames:bytitle[(f.get("data") or {}).get("title")].append(f)
  if len(bytitle[FRAME_TITLE])>1 or len(bytitle[OVERVIEW])>1:
    raise RuntimeError("FRAME_TITLE_DUPLICATE")
  overview=bytitle[OVERVIEW][0] if bytitle[OVERVIEW] else None
  fallbacks=[f for f in frames if iid(f)==MAP_ID]
  if overview is None and len(fallbacks)!=1:raise RuntimeError("MISSING_1B_ANCHOR")
  anchor=overview or fallbacks[0]
  ax,ay=xy(anchor);aw,ah=geom(anchor)
  cx=ax+(aw+W)/2+610
  cy=ay+(H-ah)/2
  desired=(cx,cy)
  own=bytitle[FRAME_TITLE][0] if bytitle[FRAME_TITLE] else None
  if own is not None:
    fx,fy=xy(own);fw,fh=geom(own)
    if abs(fw-W)>3 or abs(fh-H)>3:raise RuntimeError("METHOD_FRAME_SIZE_DRIFT")
    if abs(fx-cx)>15 or abs(fy-cy)>15:
      print("METHOD_FRAME_MANUALLY_REPOSITIONED_PRESERVED",flush=True)
    desired=(fx,fy)
  print("METHOD_PREFLIGHT","existing="+str(bool(own)),"anchor="+iid(anchor),
        "targetX="+str(round(desired[0])),"targetY="+str(round(desired[1])),
        "expected_notes="+str(len(NODES)),"expected_edges="+str(len(EDGES)),flush=True)
  return own,desired
def create_frame(pos):
  obj=call("POST","frames",{"data":{"title":FRAME_TITLE},
    "position":{"x":pos[0],"y":pos[1],"origin":"center"},
    "geometry":{"width":W,"height":H},"style":{"fillColor":"#ffffff"}})
  if not iid(obj):raise RuntimeError("FRAME_CREATE_NO_ID")
  print("METHOD_FRAME_CREATED",iid(obj),flush=True)
  return obj
def item_children(frame):return listing("items",{"parent_item_id":iid(frame)})
def resolve(children,typ,expected):
  z=[v for v in children if v.get("type")==typ and norm(v)==norm({"data":{"content":expected}})]
  if len(z)>1:raise RuntimeError("DUPLICATE_METHOD_CHILD_LABEL")
  return z[0] if z else None
def add_note(frame,key,label,color,x,y,w,children):
  got=resolve(children,"sticky_note",label)
  if got:
    if (got.get("style") or {}).get("fillColor")!=color:raise RuntimeError("NOTE_COLOR_DRIFT_"+key)
    return got,False
  body={"data":{"content":"<p>"+html.escape(label).replace("\n","<br>")+"</p>","shape":"rectangle"},
        "position":{"x":x,"y":y,"origin":"center"},"geometry":{"width":w},
        "parent":{"id":iid(frame)},
        "style":{"fillColor":color,"textAlign":"center","textAlignVertical":"middle"}}
  created=call("POST","sticky_notes",body)
  if not iid(created):raise RuntimeError("NOTE_ID_MISSING_"+key)
  return created,True
def add_text(frame,key,label,x,y,w,size,children):
  got=resolve(children,"text",label)
  if got:return got,False
  b={"data":{"content":"<p>"+html.escape(label)+"</p>"},
     "position":{"x":x,"y":y,"origin":"center"},"geometry":{"width":min(w,1850)},
     "parent":{"id":iid(frame)},
     "style":{"fontFamily":"open_sans","fontSize":str(size),"color":"#26353a"}}
  z=call("POST","texts",b)
  if not iid(z):raise RuntimeError("TEXT_CREATE_MISSING_ID_"+key)
  return z,True
def add_edge(a,b,label,sa,sb,shape,existing):
  found=[z for z in existing if str((z.get("startItem") or {}).get("id"))==iid(a) and str((z.get("endItem") or {}).get("id"))==iid(b)]
  if len(found)>1:raise RuntimeError("DUPLICATE_METHOD_CONNECTOR")
  if found:return found[0],False
  body={"startItem":{"id":iid(a),"snapTo":sa},
        "endItem":{"id":iid(b),"snapTo":sb},"shape":shape,
        "style":{"strokeColor":"#26353a","strokeWidth":"3","endStrokeCap":"stealth"}}
  if label:body["captions"]=[{"content":label,"position":0.5,"textAlignVertical":"top"}]
  z=call("POST","connectors",body)
  if not iid(z):raise RuntimeError("CONNECTOR_CREATE_NO_ID")
  return z,True
def inspect(frame):
  kids=item_children(frame)
  notes=[z for z in kids if z.get("type")=="sticky_note"]
  labels={norm(z):z for z in notes}
  expected={v[1].replace("\n"," ") for v in NODES}
  if len(notes)!=len(NODES) or len(labels)!=len(notes) or set(labels)!=expected:
    raise RuntimeError("METHOD_STICKY_INVENTORY_DRIFT")
  actual_colors=collections.Counter((z.get("style") or {}).get("fillColor") for z in notes)
  for key,label,c,*other in NODES:
    matches=[z for z in notes if norm(z)==label.replace("\n"," ")]
    if len(matches)!=1 or (matches[0].get("style") or {}).get("fillColor")!=c:
      raise RuntimeError("METHOD_COLOR_OR_NAME_"+key)
    # No machine IDs on user-visible sticky notes.
    if re.search(r"\b(?:S0-E\d+|HS-S0-\d+|EVT-\d+)\b",norm(matches[0])):
      raise RuntimeError("VISIBLE_MACHINE_ID")
  textz=[z for z in kids if z.get("type")=="text"]
  if len(textz)!=len(TEXTS):raise RuntimeError("METHOD_TEXT_COUNT_DRIFT")
  ids={iid(z) for z in notes}
  conn=[z for z in listing("connectors") if str((z.get("startItem") or {}).get("id")) in ids
       and str((z.get("endItem") or {}).get("id")) in ids]
  if len(conn)!=len(EDGES):raise RuntimeError("METHOD_CONNECTOR_COUNT_DRIFT")
  keyids={k:iid(labels[label.replace("\n"," ")]) for k,label,*_ in NODES}
  expected_pair={(keyids[a],keyids[b]) for a,b,*_ in EDGES}
  actual_pair={(str((z.get("startItem") or {}).get("id")),str((z.get("endItem") or {}).get("id"))) for z in conn}
  if expected_pair!=actual_pair:raise RuntimeError("METHOD_CONNECTOR_SEMANTICS_DRIFT")
  print("METHOD_NATIVE_READBACK_PASS","notes="+str(len(notes)),"texts="+str(len(textz)),
        "connectors="+str(len(conn)),"colors="+str(dict(actual_colors)),
        "sourceImageItem=3458764567900106962",flush=True)
  print("VISUAL_ACCEPTANCE_OPEN_NO_SCREENSHOT",flush=True)
def main():
  frame,pos=baseline()
  if MODE=="audit":
    if frame:
      kids=item_children(frame)
      print("METHOD_AUDIT_EXISTING","items="+str(len(kids)),flush=True)
    print("METHOD_AUDIT_ONLY_NO_WRITES",flush=True)
    return
  if MODE=="verify":
    if not frame:raise RuntimeError("TARGET_FRAME_NOT_FOUND")
    inspect(frame);return
  if frame is None:frame=create_frame(pos)
  children=item_children(frame)
  if MODE=="pilot":
    key,label,color,x,y,w=NODES[0]
    item,created=add_note(frame,key,label,color,x,y,w,children)
    z=call("GET","items/"+iid(item))
    if norm(z)!=label.replace("\n"," ") or (z.get("style") or {}).get("fillColor")!=color:
      raise RuntimeError("PILOT_NOTE_READBACK_FAIL")
    print("METHOD_PILOT_PASS",iid(item),"created="+str(created),flush=True)
    return
  if len(children)>len(NODES)+len(TEXTS):
    print("METHOD_EXISTING_ITEMS",len(children),"reconcile_by_business_title",flush=True)
  d={}; newnotes=0; newtext=0; newedges=0
  for key,label,color,x,y,w in NODES:
    z,created=add_note(frame,key,label,color,x,y,w,children);d[key]=z;newnotes+=int(created)
    if created:children.append(z)
    time.sleep(0.10)
  for key,label,x,y,w,size in TEXTS:
    z,created=add_text(frame,key,label,x,y,w,size,children);newtext+=int(created)
    if created:children.append(z)
    time.sleep(0.10)
  all_edges=listing("connectors")
  for a,b,label,sa,sb,path in EDGES:
    z,created=add_edge(d[a],d[b],label,sa,sb,path,all_edges);newedges+=int(created)
    if created:all_edges.append(z)
    time.sleep(0.10)
  print("METHOD_APPLY_WRITES","notes="+str(newnotes),"text="+str(newtext),"connectors="+str(newedges),flush=True)
  inspect(frame)
  print("METHOD_FRAME_LINK","https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget="+iid(frame),flush=True)
try:main()
except Exception as e:print("METHOD_STOP",type(e).__name__,str(e),flush=True);sys.exit(2)
