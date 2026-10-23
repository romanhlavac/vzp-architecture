#!/usr/bin/env python3
"""CES DEMO 1A/1B semantic layout audit (read-only default). No private business content in logs."""
import os,urllib.request,urllib.parse,urllib.error,json,collections,hashlib,time
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];assert B=="uXjVHiylz-0="
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
T=os.environ["MIRO_DIAGNOSTIC_TOKEN"]; MODE=os.getenv("LAYOUT_MODE","audit")
assert MODE in ("audit","apply","verify")
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

# ---- Scope-limited demo layout refinement (no change to protected business content) ----
import html
URLROOT="https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget="
MAIN="3458764688218487286"
NAMED={
 "3458764688218487286":"CES DEMO · KROK 1B · S0 – Správa a evidence subjektů · PRŮVODCE",
 "3458764688218487258":"CES DEMO · 1B · S0 · ČTECÍ NAVIGACE",
 "3458764687949068244":"CES DEMO · 1B.B · S0 · VÝBĚR SCÉNÁŘŮ",
 "3458764688162404596":"CES DEMO · 1B.A–E · S0 · METODIKA",
 "3458764687939229431":"CES DEMO · 1B.C · S0/S0.1 · SC-01 · Ztotožnění · WORKING",
 "3458764687939229785":"CES DEMO · 1B.C · S0/S0.1 · SC-02 · Referenční změna · WORKING",
 "3458764688202201527":"CES DEMO · 1B.C · S0/S0.1 · SC-05 · ROB/ROS → reakce VZP · WORKING",
 "3458764687939406397":"CES DEMO · 1B.C · S0/S0.2 · SC-03 · Agendová role · WORKING",
 "3458764687949762980":"CES DEMO · 1B.C · S0/S0.2 · SC-04 · Zastupování · WORKING",
 "3458764687942876552":"CES DEMO · 1B.D · S0 · E2E SYNTÉZA",
 "3458764688217500338":"CES DEMO · 1B.D · S0 · EVIDENCE CLUSTERING",
 "3458764687938964779":"CES DEMO · 1B.D · S0 · KANDIDÁTNÍ L2 MAPA",
 "3458764688217622063":"CES DEMO · 1B.E · S0 · BOUNDARY EVIDENCE PRO 1C"
}
FRESH={"1a_bp":"3458764687741774534","1a_dl":"3458764687757375873"}
OTHER_GROUPS=[
 ("CES DEMO · KROK 1 · 1A · BP ES → L1 DOMAIN LANDSCAPE",237767,-300,24400,1800,"1A"),
 ("CES DEMO · 1A → 1B · S0 · VSTUPNÍ KONTEXT",237767,20000,24400,3400,"BRIDGE"),
 ("CES DEMO · 1B.C · S0 · PROCESNÍ SCÉNÁŘE",258870,26900,39600,2200,"C"),
 ("CES DEMO · 1B.D · S0 · SYNTÉZA A L2",289970,26900,20600,2200,"D"),
 ("CES DEMO · 1B.E · S0 · EVIDENCE A 1C",305170,26900,7400,2200,"E")
]
def safe_tag(v):return html.escape(str(v),quote=False)
def html_link(fid,label):return '<a href="'+URLROOT+fid+'">'+safe_tag(label)+'</a>'
def bboxes_overlap(a,b,margin=0):
 x1,y1,w1,h1=a;x2,y2,w2,h2=b
 return abs(x1-x2)<(w1+w2)/2+margin and abs(y1-y2)<(h1+h2)/2+margin
def escname(o):return (o.get("data") or {}).get("title","")
def get_target(f):return api("GET","frames/"+f)
def shapes(parent):
 return page("items",{"parent_item_id":parent})
def childkey(z):
 return {k:z.get(k) for k in ("id","type","data","style","geometry","position","parent")}
def check_protected(fid):
 kids=shapes(fid)
 return hashlib.sha256(json.dumps([childkey(x) for x in sorted(kids,key=lambda x:x["id"])],sort_keys=True).encode()).hexdigest()
def patch_with_validation(kind,item_id,payload):
 pre=api("GET",kind+"/"+item_id)
 upd=api("PATCH",kind+"/"+item_id,payload)
 post=api("GET",kind+"/"+item_id)
 if post.get("id")!=pre["id"]:raise RuntimeError("ID_CHANGED_"+item_id)
 for k in ("parent","type"):
  if pre.get(k)!=post.get(k):raise RuntimeError("PARENT_OR_TYPE_CHANGED_"+item_id)
 return pre,post
def create_frame(title,x,y,w,h):
 fs=page("items",{"type":"frame"});hit=[f for f in fs if escname(f)==title]
 if len(hit)>1:raise RuntimeError("FRAME_DUPLICATE")
 if hit:
  f=hit[0]
  if abs(f["position"]["x"]-x)>2 or abs(f["position"]["y"]-y)>2:raise RuntimeError("FRAME_GEOMETRY_DRIFT")
  return f
 f=api("POST","frames",{"data":{"title":title},"position":{"x":x,"y":y,"origin":"center"},"geometry":{"width":w,"height":h},"style":{"fillColor":"#ffffff"}})
 print("CREATED_FRAME",f["id"],flush=True)
 return f
def upsert_shape(fid,key,text,x,y,w,h,bg="#e8f4f1",font=90,color="#172b4d"):
 kids=shapes(fid)
 m=[o for o in kids if o.get("type")=="shape" and str((o.get("data") or {}).get("content","")).startswith("<p><strong>"+key+"</strong>")]
 if len(m)>1:raise RuntimeError("SHAPE_DUP_"+key)
 content="<p><strong>"+key+"</strong></p><p>"+text+"</p>"
 body={"data":{"content":content,"shape":"round_rectangle"},"position":{"x":x,"y":y,"origin":"center"},"geometry":{"width":w,"height":h},"style":{"fillColor":bg,"color":color,"fontSize":str(font),"fontFamily":"open_sans","textAlign":"left","textAlignVertical":"middle","borderColor":"#a6b9c1","borderWidth":"2"}}
 if m:
  obj=api("PATCH","shapes/"+m[0]["id"],body)
 else:
  body["parent"]={"id":fid}
  obj=api("POST","shapes",body)
 final=api("GET","shapes/"+obj["id"])
 if final["parent"]["id"]!=fid or key not in final["data"]["content"]:raise RuntimeError("SHAPE_READBACK_"+key)
 print("SHAPE_PASS",obj["id"],flush=True)
 return obj
def revise_title(fid,title):
 old=get_target(fid)
 if escname(old)==title:return
 patch_with_validation("frames",fid,{"data":{"title":title}})
 if escname(get_target(fid))!=title:raise RuntimeError("RENAME_FAILED_"+fid)
 print("FRAME_RENAMED",fid,flush=True)
def edit_main():
 v=shapes(MAIN)
 f=[o for o in v if o["type"]=="shape"]
 if len(f)!=1:raise RuntimeError("INTRO_CHILD_SCOPE_CHANGED")
 cid=f[0]["id"]
 links=(
  "1A: "+html_link(FRESH["1a_bp"],"Big Picture ES")+" → "+html_link(FRESH["1a_dl"],"L1 Domain Landscape")+" (vybrána S0).<br/>"
  "1B.B: "+html_link(FRAME_IDS["inventory"],"výběr scénářů")+" → "
  "1B.A–E: "+html_link(FRAME_IDS["method"],"metoda")+" → "
  "1B.C: "+html_link(FRAME_IDS["sc01"],"SC-01/02/05/03/04")+" → "
  "1B.D: "+html_link(FRAME_IDS["summary"],"syntéza")+" / "+html_link(FRAME_IDS["L2"],"L2 mapa")+" → "
  "1B.E: "+html_link(FRAME_IDS["boundary"],"evidence pro 1C")+"."
 )
 val="<p><strong>KROK 1B · S0 – Správa a evidence subjektů · DEMO / WORKING</strong></p><p>Rozpracování L1 domény S0 z 1A do kandidátních S0.1/S0.2. Jde o business discovery, nikoliv target IS.</p><p>"+links+"</p>"
 old,post=patch_with_validation("shapes",cid,{"data":{"content":val},"style":{"fontSize":"112","fontFamily":"open_sans","fillColor":"#dbeff0","color":"#153b45","textAlign":"left","textAlignVertical":"middle"}})
 if "S0" not in post["data"]["content"] or "1B.C" not in post["data"]["content"]:raise RuntimeError("INTRO_READBACK")
 print("MAIN_EXPLAINED",cid,flush=True)
def refine_sc05():
 fid=FRAME_IDS["sc05"]
 orig=shapes(fid);base={o["id"]:o for o in orig}
 if len(orig)!=16:raise RuntimeError("SC05_CHILD_COUNT_CHANGED")
 # All geometry positions stay unchanged; only typographic scale and native card sizes change.
 typ={
 "3458764688202201691":("shape",40,6450),
 "3458764688202201720":("shape",25,6450),
 "3458764688202201730":("shape",32,760),
 "3458764688202201764":("shape",32,760),
 "3458764688202201794":("shape",32,1050),
 "3458764688202201803":("shape",32,680),
 "3458764688202201809":("shape",32,760),
 "3458764688202201827":("shape",32,900),
 "3458764688202201884":("shape",25,6450),
 }
 notes={
 "3458764688202201748":500,"3458764688202201756":500,
 "3458764688202201777":500,"3458764688202201786":500,
 "3458764688202201855":500,"3458764688202201865":500,
 "3458764688202201871":720
 }
 for id,(typname,font,width) in typ.items():
  pre=base[id];style=pre.get("style") or {}
  if pre["type"]!="shape":raise RuntimeError("SC05_TYPE_CHANGED")
  # Existing semantics, colors, coordinates, endpoint ids unchanged.
  newstyle=dict(style,fontSize=str(font),fontFamily="open_sans")
  if id=="3458764688202201691":
   payload={"data":{"content":"<p><strong>1B.C · S0 / S0.1 · SC-05 ROB/ROS → reakce VZP · WORKING</strong></p>"},"style":newstyle,"geometry":{"width":width,"height":pre["geometry"]["height"]}}
  else:payload={"style":newstyle,"geometry":{"width":width,"height":pre["geometry"]["height"]}}
  a,b=patch_with_validation("shapes",id,payload)
  if b.get("style",{}).get("fillColor")!=style.get("fillColor"):raise RuntimeError("SC05_COLOR_DRIFT_"+id)
  if id!="3458764688202201691" and b["data"]!=a["data"]:raise RuntimeError("SC05_CONTENT_DRIFT_"+id)
  print("SC05_SHAPE_STYLED",id,flush=True)
 for id,width in notes.items():
  pre=base[id];assert pre["type"]=="sticky_note"
  a,b=patch_with_validation("sticky_notes",id,{"geometry":{"width":width}})
  if b["data"]!=a["data"] or b.get("style",{}).get("fillColor")!=a.get("style",{}).get("fillColor"):raise RuntimeError("STICKY_CONTENT_COLOR_CHANGED_"+id)
  print("SC05_STICKY_SIZED",id,round(b.get("geometry",{}).get("width",0)),flush=True)
 upsert_shape(fid,"S0.1 / SC-05", "Procesní scénář v L1 S0 · externí ROB/ROS (pink) → dopad na referenční evidenci · DEMO/WORKING",3700,565,6450,130,"#e8f4f1",31)
 if len(shapes(fid))!=17:raise RuntimeError("SC05_CHILD_AFTER_SCOPE")
def check_mode(mode):
 fs=page("items",{"type":"frame"});fm={f["id"]:f for f in fs}
 bp=shapes(FRESH["1a_bp"]);dl=shapes(FRESH["1a_dl"])
 print("LAYOUT_READBACK",len(fs),len(bp),len(dl),flush=True)
 assert len(bp)==169 and len(dl)==184,"PROTECTED_1A_ITEMS"
 links=page("connectors");print("CONNECTORS",len(links),flush=True)
 if mode=="audit":return
 assert len(links)==703,"CONNECTOR_COUNT_DRIFT"
 for k,v in NAMED.items():
  if escname(fm[k])!=v:raise RuntimeError("FRAME_RENAME_MISSING_"+k)
 for name,*_ in OTHER_GROUPS:
  if sum(escname(f)==name for f in fs)!=1:raise RuntimeError("HEADER_FRAME_MISSING")
 notes=shapes(FRAME_IDS["sc05"])
 assert len(notes)==17,"SC05_NOTES_DRIFT"
 assert "1B.C" in str(next(o for o in notes if o["id"]=="3458764688202201691")["data"]["content"]),"SC05_TITLE"
 print("VERIFICATION_PASS",len(fs),len(links),len(notes),flush=True)
def apply_refinement():
 fs=page("items",{"type":"frame"});ids={f["id"] for f in fs}
 assert len(fs)==65 and all(fid in ids for fid in list(NAMED)+list(FRESH.values())),"BASELINE_FRAME_DRIFT"
 before_bp=check_protected(FRESH["1a_bp"]);before_dl=check_protected(FRESH["1a_dl"])
 before_edges={x["id"]:(x["startItem"]["id"],x["endItem"]["id"]) for x in page("connectors")}
 assert len(before_edges)==703,"BASELINE_EDGES_DRIFT"
 old_sc05=shapes(FRAME_IDS["sc05"])
 assert len(old_sc05)==16,"SC05_BASELINE_DRIFT"
 for title,x,y,w,h,label in OTHER_GROUPS:
  f=create_frame(title,x,y,w,h)
  fid=f["id"]
  if label=="1A":
   upsert_shape(fid,"1A · BUSINESS BIG PICTURE", html_link(FRESH["1a_bp"],"BP ES v14 · zdrojová E2E business story a události"),5150,950,9600,950,"#e8f4f1",103)
   upsert_shape(fid,"1A · L1 DOMAIN LANDSCAPE",html_link(FRESH["1a_dl"],"DL v3 · 20 domén / výběr S0 pro krok 1B"),18150,950,9600,950,"#e8f4f1",103)
  elif label=="BRIDGE":
   upsert_shape(fid,"KROK 1 · 1A → 1B","Business-first DEMO: z 1A "+html_link(FRESH["1a_dl"],"L1 Domain Landscape")+" vybíráme "+safe_tag("S0 – Správa a evidence subjektů")+".",12200,570,22900,1000,"#dbeff0",150)
   upsert_shape(fid,"1A.B · INPUT",html_link(FRESH["1a_bp"],"BP ES v14")+" → "+html_link(FRESH["1a_dl"],"Domain Landscape v3")+". L1 eventy, role, hotspots a sousední odpovědnosti.",6150,2190,11000,1520,"#f1f5f9",110)
   upsert_shape(fid,"1B · DISCOVERY",html_link(FRAME_IDS["inventory"],"1B.B Inventory")+" → "+html_link(FRAME_IDS["method"],"metoda 1B.A–E")+" → "+html_link(FRAME_IDS["sc01"],"1B.C Process-Level ES")+" → L2 candidates.",18020,2190,11000,1520,"#f1f5f9",110)
  elif label=="C":
   upsert_shape(fid,"1B.C · S0 · PROCESS-LEVEL ES","Pět vybraných scénářů nad L1 doménou S0 / kandidáty S0.1 a S0.2 (DEMO / WORKING).",19800,480,38100,730,"#dbeff0",125)
   for i,(key,ff) in enumerate([("SC-01",FRAME_IDS["sc01"]),("SC-02",FRAME_IDS["sc02"]),("SC-05",FRAME_IDS["sc05"]),("SC-03",FRAME_IDS["sc03"]),("SC-04",FRAME_IDS["sc04"])]):
    upsert_shape(fid,key,html_link(ff,"Otevřít detail"),4100+7900*i,1520,7200,1030,"#f1f5f9",108)
  elif label=="D":
   upsert_shape(fid,"1B.D · S0 · SYNTÉZA","Z pěti scénářů → evidence clusters → pracovní Subdomain Map S0.1/S0.2.",10300,540,19300,760,"#dbeff0",125)
   for i,(key,ff) in enumerate([("E2E",FRAME_IDS["summary"]),("Evidence",FRAME_IDS["clusters"]),("L2 mapa",FRAME_IDS["L2"])]):
    upsert_shape(fid,key,html_link(ff,"Otevřít detail"),3620+6720*i,1600,6200,960,"#f1f5f9",102)
  elif label=="E":
   upsert_shape(fid,"1B.E · S0 · EVIDENCE", "Boundary Decision Records a OPEN → "+html_link(FRAME_IDS["boundary"],"předání pro 1C"),3700,1100,6900,1650,"#dbeff0",105)
 for fid,title in NAMED.items():revise_title(fid,title)
 edit_main()
 refine_sc05()
 after_bp=check_protected(FRESH["1a_bp"]);after_dl=check_protected(FRESH["1a_dl"])
 if before_bp!=after_bp or before_dl!=after_dl:raise RuntimeError("PROTECTED_BP_DL_CHANGED")
 after_edges={x["id"]:(x["startItem"]["id"],x["endItem"]["id"]) for x in page("connectors")}
 if before_edges!=after_edges:raise RuntimeError("SEMANTIC_EDGES_DRIFT")
 check_mode("verify")
 print("APPLY_PRESERVED_1A_AND_BUSINESS_EDGES",flush=True)

if __name__=="__main__":
 mode=os.getenv("LAYOUT_MODE","audit")
 if mode=="audit":main()
 elif mode=="apply":apply_refinement()
 elif mode=="verify":check_mode("verify")
 else:raise RuntimeError("INVALID_MODE")

