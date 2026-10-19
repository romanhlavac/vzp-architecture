#!/usr/bin/env python3
"""Reintegrate 31 new EV events with original BP stories; compact all 37 new events.

READ ONLY by default. Pilot modifies one existing new event. Apply modifies only
37 v14 additions, removes 18 generated off-canvas annotations, and creates 4
compact thematic headers. Source v13, 110 original v12 sticky contents/positions
and 51 native relationships protected. No client Miro texts/IDs in public logs.
"""
import os,sys,collections,json,re,html,hashlib,urllib.parse,urllib.request,urllib.error,time,math
from ces1a_v14_screen import DATA
from ces1a_v14_build import STORIES, TITLE, CAUSAL, SOURCE_SHA
from landscape_build import RULES
MODE=os.getenv("V14_REGROUP_MODE","audit")
if MODE not in ("audit","pilot","apply"):sys.exit("INVALID_MODE")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
SHORT={
"EV02":"Hospodaření VZP přešlo do zákonného provizoria.",
"EV03":"VZP byla uložena závažná nápravná povinnost.",
"EV05":"Změnil se rozsah hrazené péče pro skupinu pojištěnců.",
"EV06":"Byl zaveden nový příspěvek z fondu prevence.",
"EV07":"Hrazená péče se stala dostupnou v nedostatkovém území.",
"EV08":"Nový způsob hrazené péče se stal dostupným.",
"EV09":"VZP přijala platnou přihlášku ke změně pojišťovny.",
"EV10":"Neoprávněná přeregistrace pojištěnce byla zrušena.",
"EV11":"Smlouva o zajištění nedostatkové péče nabyla účinnosti.",
"EV12":"Poskytovatel ztratil oprávnění k významné části péče.",
"EV13":"Bylo potvrzeno neoprávněné vykázání hrazené péče.",
"EV14":"Pravomocný přezkum změnil rozhodnutí VZP.",
"EV15":"Pojištěnci se změnil přeshraniční nárok na péči v ČR.",
"EV16":"Byla stanovena nová výše přerozdělení pojistného.",
"EV17":"VZP vznikla nová povinnost předávat data státu.",
"EV18":"VZP zpřístupnila novou významnou datovou službu.",
"EV19":"Účetní závěrka VZP byla schválena.",
"EV20":"VZP přestala včas hradit péči poskytovatelům.",
"EV21":"VZP obnovila včasné úhrady péče poskytovatelům.",
"EV22":"VZP ztratila kritickou odbornou kapacitu.",
"EV23":"VZP obnovila kritickou odbornou kapacitu.",
"EV24":"Klientská digitální služba VZP byla nedostupná.",
"EV25":"Klientská digitální služba VZP byla obnovena.",
"EV26":"Strategická dodavatelská smlouva nabyla účinnosti.",
"EV27":"Strategické dodavatelské zajištění VZP skončilo.",
"EV28":"Pravomocné rozhodnutí změnilo závazky VZP.",
"EV29":"VZP přestala přijímat právně významná podání v části území.",
"EV30":"VZP obnovila příjem právně významných podání.",
"EV31":"Bylo potvrzeno závažné porušení zabezpečení osobních údajů.",
"EV32":"Dotčené osoby byly vyrozuměny o porušení zabezpečení údajů.",
"EV33":"Klíčová evidence VZP přestala být důvěryhodně dostupná.",
"N01":"Zpětně se změnila povinnost plátce k úhradě pojistného.",
"N02":"VZP neuznala část vykázané péče k úhradě.",
"N03":"Pojištěnci byla předem schválena úhrada péče.",
"N04":"Pojištěnci byla schválena plánovaná péče v zahraničí.",
"N05":"Pojištěnec dosáhl ochranného limitu doplatků za léky.",
"N06":"Pojištěnci nebyla předem schválena úhrada péče."
}
assert len(SHORT)==37 and len({v for v in SHORT.values()})==37
EVS=set(k for k in SHORT if k.startswith("EV"))
NS=set(k for k in SHORT if k.startswith("N"))
assert len(EVS)==31 and len(NS)==6
# Working grouping is for visual placement only; not a domain ownership decision.
ANCHORS={"EV05":"A2","EV06":"B6","EV07":"A3","EV08":"A3",
         "EV09":"B1","EV10":"B1","EV11":"B3","EV12":"B3",
         "EV13":"B5","EV14":"B5","EV15":"B8","EV16":"B9",
         "EV17":"C1","EV18":"C1"}
assert len(ANCHORS)==14
PANELS=[
 ("Řízení, finance a závazky",
  [("EV02",625,11040),("EV19",1515,11040),("EV03",2405,11040),
   ("EV20",625,11470),("EV21",1515,11470),
   ("EV26",625,11900),("EV27",1515,11900),("EV28",2405,11900)],
  2750,10600,5300),
 ("Dostupnost služeb a kapacit",
  [("EV22",6625,11040),("EV23",7515,11040),
   ("EV24",6625,11470),("EV25",7515,11470),
   ("EV29",6625,11900),("EV30",7515,11900)],
  8850,10600,5300),
 ("Bezpečnost informací",
  [("EV31",12625,11040),("EV32",13515,11040),("EV33",14405,11040)],
  14850,10600,5300)
]
INTEGRATED=[k for k in SHORT if k.startswith("EV") and k not in {key for _,items,*_ in PANELS for key,_,_ in items}]
assert set(INTEGRATED)==set(ANCHORS)
SOURCE_HEADING_COUNT=18
SRC_CARD_COUNT=116
# exact 18 generated meta annotations from historical v14 builder; none are original source text.
EXPECTED_META_HEADS=["ES BIG PICTURE · v14 · enterprise business events",
 "31 nových kandidátních typů událostí",
 "DEMO / SCÉNÁŘE",
 "EV31 → EV32"]
def call(method,path,payload=None,params=None):
 url=BASE+"/"+path
 if params:url+="?"+urllib.parse.urlencode(params)
 data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
 heads={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
 if data is not None:heads["Content-Type"]="application/json"
 for n in range(5 if method=="GET" else 1):
  try:
   req=urllib.request.Request(url,data=data,headers=heads,method=method)
   with urllib.request.urlopen(req,timeout=45) as r:
    body=r.read();return json.loads(body) if body else {}
  except urllib.error.HTTPError as e:
   if method=="GET" and e.code in (429,500,502,503,504) and n<4:
    time.sleep(2**n+1);continue
   raise RuntimeError("MIRO_"+method+"_HTTP_"+str(e.code)) from None
  except Exception:
   if method=="GET" and n<3:time.sleep(2);continue
   raise RuntimeError("MIRO_"+method+"_OUTCOME_UNCERTAIN_STOP") from None
def pages(path,params=None):
 a=[];cur=None
 for _ in range(120):
  q=dict(params or {},limit=50)
  if cur:q["cursor"]=cur
  p=call("GET",path,params=q);a+=p.get("data",[]);cur=p.get("cursor")
  if not cur:return a
 raise RuntimeError("PAGINATION_INCOMPLETE")
def oid(z):return str(z.get("id",""))
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def txt(z):return re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",str((z.get("data") or {}).get("content",""))))).strip()
def x(z):return float((z.get("position") or {}).get("x") or 0)
def y(z):return float((z.get("position") or {}).get("y") or 0)
def width(z):return float((z.get("geometry") or {}).get("width") or 0)
def height(z):return float((z.get("geometry") or {}).get("height") or 0)
def eid(z,k):return str((z.get(k) or {}).get("id") or "")
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def item_sig(z):return (oid(z),z.get("type"),parent(z),txt(z),round(x(z),1),round(y(z),1),round(width(z),1))
def edge_sig(z):return (oid(z),eid(z,"startItem"),eid(z,"endItem"),z.get("shape"))
def parse_key(z):
 t=txt(z)
 m=re.match(r"^(EV\d{2}|N\d{2})\s+·\s+",t)
 if m:return m.group(1)
 return next((k for k,v in SHORT.items() if t==v),None)
def is_new_meta(t,sourcecontents):
 if t in sourcecontents:return False
 # The original source has exactly 18 text objects; all remaining are generated.
 return True
def plan_positions(srcnotes,allnotes):
 original={h(txt(z)):z for z in srcnotes}
 occupied=[z for z in allnotes if parse_key(z) is None or parse_key(z) in NS]
 positions={}
 # Group in the pre-existing three-column thematic blocks where business relevant.
 cells={
 "A2":([625,1515,2405,3295,4185,5075],[8026,8456,8886]),
 "A3":([625,1515,2405,3295,4185,5075],[8456,8886,9316]),
 "B6":([12625,13515,14405,15295,16185],[1106,1536,1966,2396]),
 "B1":([625,1515,2405,3295,4185,5075],[3126,3556,3986,4416]),
 "B3":([6625,7515,8405,9295,10185,11075],[676,1106,1536,1966,2396]),
 "B5":([6625,7515,8405,9295,10185,11075],[5576,6006,6436,6866]),
 "B8":([12625,13515,14405,15295,16185],[5576,6006,6436,6866]),
 "B9":([12625,13515,14405,15295,16185],[5576,6006,6436,6866]),
 "C1":([12625,13515,14405,15295,16185],[6436,6866,7296])
 }
 chosen=[]
 for key,gr in ANCHORS.items():
  refs=[original[z] for z in RULES["groups"][gr] if z in original]
  if not refs:raise RuntimeError("MISSING_ORIGINAL_ANCHOR_"+gr)
  medx=sorted(x(z) for z in refs)[len(refs)//2]
  medy=sorted(y(z) for z in refs)[len(refs)//2]
  xs,ys=cells[gr]
  cands=[]
  for iy,yp in enumerate(ys):
   for ix,xp in enumerate(xs):
    # Exclude all original note bounding boxes, including unrelated nearby groups.
    if any(abs(xp-x(z))<425 and abs(yp-y(z))<300 for z in occupied):continue
    if any(abs(xp-cx)<425 and abs(yp-cy)<300 for cx,cy in chosen):continue
    score=abs(yp-medy)*4+abs(xp-medx)+ix*0.1+iy*0.1
    cands.append((score,xp,yp))
  if not cands:raise RuntimeError("NO_FREE_GROUP_SLOT_"+key)
  _,xp,yp=min(cands)
  positions[key]=(xp,yp)
  chosen.append((xp,yp))
 for _,entries,*_ in PANELS:
  for key,xp,yp in entries:positions[key]=(xp,yp)
 if len(positions)!=31:raise RuntimeError("PLAN_MISSING_EVENT")
 if len({(int(p[0]),int(p[1])) for p in positions.values()})!=31:raise RuntimeError("TARGET_DUPLICATE_SLOT")
 # Grid compatibility with original 387x252 orange notes.
 for a,(ax,ay) in positions.items():
  for b,(bx,by) in positions.items():
   if a>=b:continue
   if abs(ax-bx)<430 and abs(ay-by)<300:raise RuntimeError("TARGET_NEW_NOTE_OVERLAP_"+a+"_"+b)
 return positions
def metadata():
 return {k:val for k,val in DATA if k not in ("EV01","EV04")}
def main():
 items=pages("items");frames=[z for z in items if z.get("type")=="frame"]
 v13=[z for z in frames if h(oid(z))==SOURCE_SHA]
 v14=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
 if len(v13)!=1 or len(v14)!=1:raise RuntimeError("FRAME_IDENTITY_DRIFT")
 v13=v13[0];v14=v14[0]
 source=[z for z in items if parent(z)==oid(v13)]
 target=[z for z in items if parent(z)==oid(v14)]
 source_notes=[z for z in source if z.get("type")=="sticky_note"]
 if len(source_notes)!=SRC_CARD_COUNT:raise RuntimeError("SOURCE_V13_DRIFT")
 source_snap={item_sig(z) for z in source}
 orig_longs={txt(z) for z in source_notes}
 tnotes=[z for z in target if z.get("type")=="sticky_note"]
 ttexts=[z for z in target if z.get("type")=="text"]
 if len(tnotes)!=147:raise RuntimeError("TARGET_CARD_COUNT_DRIFT")
 if not (18<=len(ttexts)<=36):raise RuntimeError("TARGET_HEADER_COUNT_DRIFT")
 bykey=collections.defaultdict(list)
 for z in tnotes:
  k=parse_key(z)
  if k:bykey[k].append(z)
 if set(bykey)!=set(SHORT) or any(len(v)!=1 for v in bykey.values()):
  raise RuntimeError("NEW_EVENT_IDENTITIES_MISMATCH")
 for k,v in bykey.items():
  observed=txt(v[0])
  original=(k+" · "+metadata()[k]) if k.startswith("EV") else None
  if original and observed not in (original,SHORT[k]):raise RuntimeError("UNEXPECTED_EVENT_TEXT_"+k)
  if k.startswith("N") and observed not in (SHORT[k],) and not observed.startswith(k+" · "):
   raise RuntimeError("UNEXPECTED_N_TEXT_"+k)
 positions=plan_positions(source_notes,tnotes)
 oldtexts={txt(z) for z in source if z.get("type")=="text"}
 extras=[z for z in ttexts if txt(z) not in oldtexts]
 if len(extras) not in (18,4):raise RuntimeError("GENERATED_HEADER_SET_DRIFT")
 if len(extras)==18:
  # Ensure historical extras are generated by the known builder, not user additions.
  texts=[txt(z) for z in extras]
  if not all(any(t.startswith(prefix) for t in texts) for prefix in EXPECTED_META_HEADS):
   raise RuntimeError("GENERATED_HEADERS_NOT_CANONICAL")
  if sum(bool(re.match(r"^\d\d\s+·",t)) for t in texts)!=14:
   raise RuntimeError("GENERATED_STORY_HEADER_DRIFT")
 old_edges=pages("connectors")
 src_ids={oid(z) for z in source_notes};target_ids={oid(z) for z in tnotes}
 src_links=[z for z in old_edges if eid(z,"startItem") in src_ids and eid(z,"endItem") in src_ids]
 dst_links=[z for z in old_edges if eid(z,"startItem") in target_ids and eid(z,"endItem") in target_ids]
 if len(src_links)!=46 or len(dst_links)!=51:raise RuntimeError("EDGE_COUNT_DRIFT")
 src_edge_snap={edge_sig(z) for z in src_links}
 print("REGROUP_PREFLIGHT_OK","mode",MODE,"events",len(bykey),"original",len(source_notes),"to_move",len(positions),"generated_headers",len(extras),"native_links",len(dst_links),flush=True)
 if MODE=="audit":
  print("REGROUP_PLAN","near_original_groups",len(ANCHORS),"new_blocks",len(PANELS),"concise_texts",len(SHORT),"EV_labels_removed",len(EVS),"N_labels_removed",len(NS))
  print("AUDIT_ONLY_NO_WRITES");return
 patchkeys=["EV06"] if MODE=="pilot" else list(SHORT)
 for seq,key in enumerate(patchkeys):
  z=bykey[key][0]
  pos=positions.get(key,(x(z),y(z)))
  if txt(z)==SHORT[key] and abs(x(z)-pos[0])<2 and abs(y(z)-pos[1])<2 and abs(width(z)-387)<2:
   continue
  payload={"data":{"content":SHORT[key]},"geometry":{"width":387},
           "style":{"fillColor":"orange","textAlign":"center"},
           "position":{"x":pos[0],"y":pos[1],"origin":"center"}}
  call("PATCH","sticky_notes/"+oid(z),payload)
  if seq%7==0:print("REGROUP_PATCH_PROGRESS",seq+1,flush=True)
 if MODE=="apply":
  # Eliminate the now-obsolete 14 isolated rows + obsolete big right-side header.
  # Retain all 18 inherited source headers and the five native causal arrows.
  if len(extras)==18:
   for z in extras:call("DELETE","texts/"+oid(z))
  head_specs=[(title,xp,yp,ww) for title,entries,xp,yp,ww in PANELS]
  head_specs.append(("EV31 → EV32 pouze při vysokém riziku pro dotčené osoby.",14850,12450,5300))
  cur=pages("items",{"parent_item_id":oid(v14)})
  for title,xp,yp,ww in head_specs:
   m=[z for z in cur if z.get("type")=="text" and txt(z)==title]
   if len(m)>1:raise RuntimeError("DUPLICATE_NEW_HEADER")
   if m:continue
   body={"data":{"content":title},"position":{"x":xp,"y":yp,"origin":"center"},
         "parent":{"id":oid(v14)},"geometry":{"width":ww},
         "style":{"fontFamily":"open_sans","fontSize":"24","color":"#26353a","textAlign":"left"}}
   z=call("POST","texts",body)
   if not oid(z):raise RuntimeError("HEADER_CREATE_ID_MISSING")
  print("REGROUP_HEADINGS_DONE","three_thematic_headers_and_one_legal_note",flush=True)
 # fresh readback
 live=pages("items");ln=[z for z in live if parent(z)==oid(v14) and z.get("type")=="sticky_note"]
 lt=[z for z in live if parent(z)==oid(v14) and z.get("type")=="text"]
 if len(ln)!=147:raise RuntimeError("READBACK_NOTES_DRIFT")
 live_keys=collections.defaultdict(list)
 for z in ln:
  k=parse_key(z)
  if k:live_keys[k].append(z)
 for key in patchkeys:
  if len(live_keys[key])!=1 or txt(live_keys[key][0])!=SHORT[key]:
   raise RuntimeError("READBACK_LABEL_FAILURE_"+key)
 if MODE=="apply":
  if len(lt)!=22:raise RuntimeError("READBACK_HEADER_COUNTS")
  if any(re.match(r"^(EV\d\d|N\d\d)\s+·",txt(z)) for z in ln):
   raise RuntimeError("VISIBLE_IDS_REMAIN")
  # Source 110 note texts preserve identity, and all 6 N notes have revised copy in v14 only.
  original110={txt(z) for z in source_notes if not re.match(r"^N\d\d\s+·",txt(z))}
  if not original110.issubset({txt(z) for z in ln}):raise RuntimeError("ORIGINAL_BUSINESS_EVENTS_CHANGED")
  after=pages("connectors"); dst_ids={oid(z) for z in ln}
  links=[z for z in after if eid(z,"startItem") in dst_ids and eid(z,"endItem") in dst_ids]
  if len(links)!=51 or any(z.get("shape")!="curved" for z in links):
   raise RuntimeError("NATIVE_LINKS_LOST")
  if any(abs(x(live_keys[k][0])-positions[k][0])>2 or abs(y(live_keys[k][0])-positions[k][1])>2 or abs(width(live_keys[k][0])-387)>2 for k in positions):
   raise RuntimeError("GROUP_PLACEMENT_DRIFT")
 check_source=pages("items",{"parent_item_id":oid(v13)})
 if {item_sig(z) for z in check_source}!=source_snap:
  raise RuntimeError("V13_SOURCE_CHANGED")
 c2=pages("connectors")
 if {edge_sig(z) for z in c2 if eid(z,"startItem") in src_ids and eid(z,"endItem") in src_ids}!=src_edge_snap:
  raise RuntimeError("V13_NATIVE_LINKS_CHANGED")
 print("REGROUP_READBACK_PASS","mode",MODE,"events",len(ln),"text_objects",len(lt),"source_v13_unchanged",True,flush=True)
 print("VISUAL_ACCEPTANCE_OPEN",flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:print("REGROUP_STOP",type(e).__name__,str(e));sys.exit(1)
