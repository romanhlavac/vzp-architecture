#!/usr/bin/env python3
"""One-time DEMO 1B process-first refactor. Canonical business definitions: CES_DEMO_DATA.
The embedded title/row map is a transient transport snapshot; not a new business source.
No writes to BPv14 / L1DLv3. Modes audit, pilot, apply. No private content in CI logs.
"""
import os,sys,json,html,re,urllib.request,urllib.parse,urllib.error,time,math,collections
MODE=os.getenv("CES_1B_FIX_MODE","audit")
assert MODE in ("audit","pilot","apply")
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
GS="https://docs.google.com/spreadsheets/d/1qA_lsfm5Vka9kaglLrX9B7D-WjBSDAapA76pKGVi0ew/edit#gid="
BF={"map":"3458764687938964779","sc1":"3458764687939229431",
    "sc2":"3458764687939229785","sc3":"3458764687939406397","e2e":"3458764687942876552"}
SC0="CES-1B · 00 · Identifikace procesních scénářů S0.1 a S0.2"
SC4="CES-1B · S0.2 · SC-04 Doložené zastupování a opravy · v2"
PAIRMAP={"3458764687939229435":"S0-E001","3458764687939229436":"S0-E016","3458764687939229438":"S0-E009","3458764687939229439":"S0-E018","3458764687939229440":"S0-E019","3458764687939229441":"S0-E017","3458764687939229442":"S0-E022","3458764687939229444":"HS-S0-03","3458764687939229789":"S0-E003","3458764687939229790":"S0-E027","3458764687939229791":"S0-E029","3458764687939229792":"S0-E031","3458764687939229793":"S0-E032","3458764687939229794":"S0-E033","3458764687939229795":"S0-E056","3458764687939229797":"HS-S0-01","3458764687939229798":"HS-S0-09","3458764687939406407":"S0-E037","3458764687939406410":"S0-E038","3458764687939406413":"S0-E039","3458764687939406416":"S0-E041","3458764687939406418":"HS-S0-02","3458764687939406419":"HS-S0-05"}
TITLES={"S0-E001":"Podnět ke ztotožnění subjektu byl převzat k posouzení.","S0-E016":"Kandidátní shoda s existujícím subjektem byla nalezena.","S0-E009":"Existující referenční subjekt byl jednoznačně určen.","S0-E018":"Více možných identitních shod bylo zjištěno.","S0-E019":"Kandidátní shoda byla předána k odbornému posouzení.","S0-E017":"Jednoznačná shoda subjektů byla potvrzena.","S0-E022":"Duplicitní referenční identity byly sloučeny.","S0-E003":"Změnové oznámení z registru bylo přijato k ověření.","S0-E027":"Rozpor mezi zdroji referenčního údaje byl zjištěn.","S0-E029":"O původu a důvěryhodnosti referenčního údaje bylo rozhodnuto.","S0-E031":"Referenční atribut subjektu byl opraven.","S0-E032":"Zpětná platnost referenční změny byla stanovena.","S0-E033":"Historie referenčního údaje byla zpětně opravena.","S0-E056":"Ověřená referenční změna byla oznámena dotčeným agendám.","S0-E037":"Vznik agendově potvrzené role subjektu byl referenčně zaznamenán.","S0-E038":"Změna agendově potvrzené role byla referenčně zaznamenána.","S0-E039":"Ukončení agendově potvrzené role bylo referenčně zaznamenáno.","S0-E041":"Vztah zastupování byl v referenční evidenci zaznamenán.","S0-E042":"Změna doloženého zastupování byla referenčně zaznamenána.","S0-E043":"Ukončení doloženého zastupování bylo referenčně zaznamenáno.","S0-E044":"Vztah mezi subjekty byl opraven po zjištění rozporu.","EVT-0017":"Vzniklo oprávnění jednat za subjekt","EVT-0018":"Oprávnění jednat za subjekt se změnilo","EVT-0019":"Oprávnění jednat za subjekt zaniklo","EVT-0034":"Pojištěnci vznikla příslušnost k VZP","HS-S0-01":"Kdo ručí za správnost údajů?","HS-S0-02":"Kdo rozhoduje o roli subjektu?","HS-S0-03":"Jak zabránit chybnému sloučení?","HS-S0-05":"Kdo smí jednat za subjekt?","HS-S0-09":"Co vyvolá zpětná oprava údajů?"}
EROWS={"S0-E001":2,"S0-E016":4,"S0-E009":5,"S0-E018":6,"S0-E019":7,"S0-E017":8,"S0-E022":11,"S0-E003":14,"S0-E027":15,"S0-E029":16,"S0-E031":17,"S0-E032":18,"S0-E033":19,"S0-E056":21,"S0-E037":22,"S0-E038":23,"S0-E039":24,"S0-E041":25,"S0-E042":26,"S0-E043":27,"S0-E044":28}
HROWS={"HS-S0-01":2,"HS-S0-02":3,"HS-S0-03":4,"HS-S0-05":6,"HS-S0-09":10}
def call(method,path,body=None):
    data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
    head={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if data is not None:head["Content-Type"]="application/json"
    attempts=4 if method=="GET" else 1
    for i in range(attempts):
        try:
            q=urllib.request.Request(ROOT+path,data=data,headers=head,method=method)
            with urllib.request.urlopen(q,timeout=45) as x:
                b=x.read();return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            if method=="GET" and e.code in (429,500,502,503,504) and i<attempts-1:
                time.sleep(2**i+1);continue
            raise RuntimeError("HTTP_"+str(e.code)+"_"+method+"_"+path.split("?")[0]) from None
        except (TimeoutError,urllib.error.URLError):
            raise RuntimeError("TRANSPORT_UNCERTAIN_"+method+"_"+path.split("?")[0]) from None
    raise RuntimeError("GET_RETRY_EXHAUSTED")
def listing(path,filter=None):
    out=[];cursor=None
    for _ in range(110):
        q=dict(filter or {},limit=50)
        if cursor:q["cursor"]=cursor
        res=call("GET",path+"?"+urllib.parse.urlencode(q))
        out.extend(res.get("data") or [])
        cursor=res.get("cursor") or res.get("nextCursor")
        if not cursor:return out
    raise RuntimeError("PAGINATION_GUARD")
def text(z):
    raw=str((z.get("data") or {}).get("content") or "")
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",html.unescape(raw)))).strip()
def id(z):return str(z.get("id") or "")
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def shape(g):return float((g or {}).get("width") or 0),float((g or {}).get("height") or 0)
def xy(z):
    p=z.get("position") or {};return float(p.get("x") or 0),float(p.get("y") or 0)
def event_url(k):
    if k.startswith("HS-"):return GS+"1505008023&range=B"+str(HROWS[k])
    if k.startswith("EVT-"):return GS+"504368542&range=B"+str(int(k[4:])+1)
    return GS+"1510001002&range=B"+str(EROWS[k])
def anchor(k):
    # The visible native Miro sticky displays only the canonical business/event title.
    return '<p><a href="'+html.escape(event_url(k),quote=True)+'">'+html.escape(TITLES[k])+'</a></p>'
def baseline():
    fs=listing("items",{"type":"frame"});fm={id(x):x for x in fs}
    for k,fid in BF.items():
        if fid not in fm:raise RuntimeError("MISSING_"+k.upper()+"_FRAME")
    tasks={}
    for k in ("sc1","sc2","sc3","e2e"):
        tasks[k]=listing("items",{"parent_item_id":BF[k]})
    m={id(z):z for v in tasks.values() for z in v if z.get("type")=="sticky_note"}
    for widget,semantic in PAIRMAP.items():
        z=m.get(widget)
        if not z:raise RuntimeError("MISSING_STICKY_"+widget)
        old=text(z)
        if not (old.startswith(semantic+" ") or old==TITLES[semantic] or
                event_url(semantic) in html.unescape(str((z.get("data") or {}).get("content") or ""))):
            raise RuntimeError("STICKY_ID_DRIFT_"+widget)
    e2e=[z for z in tasks["e2e"] if z.get("type")=="sticky_note"]
    if len(e2e)!=4:raise RuntimeError("E2E_EVENT_COUNT_DRIFT")
    e2emap={}
    for z in e2e:
        name=text(z)
        k=next((a for a in ("S0-E001","S0-E009","S0-E037","EVT-0034") if name.startswith(a+" ") or name==TITLES[a]),None)
        if k is None or k in e2emap:raise RuntimeError("E2E_STICKY_DRIFT")
        e2emap[k]=z
    if len(e2emap)!=4:raise RuntimeError("E2E_MISSING_EVENT")
    for k,z in e2emap.items():PAIRMAP[id(z)]=k
    allitems={id(z):z for v in tasks.values() for z in v}
    return fm,tasks,allitems,m
def frame_create(title,cx,cy,w,h):
    exist=[z for z in listing("items",{"type":"frame"}) if (z.get("data") or {}).get("title")==title]
    if len(exist)>1:raise RuntimeError("DUPLICATE_1B_FRAME")
    if exist:return exist[0]
    obj=call("POST","frames",{"data":{"title":title},"position":{"x":cx,"y":cy,"origin":"center"},
          "geometry":{"width":w,"height":h},"style":{"fillColor":"#ffffff"}})
    if not id(obj):raise RuntimeError("FRAME_CREATE_FAILED")
    return obj
def add(typ,frame,content,cx,cy,w,fill,fs=24):
    kids=listing("items",{"parent_item_id":id(frame)})
    normalized=re.sub(r"\s+"," ",content).strip()
    matches=[z for z in kids if text(z)==normalized]
    if len(matches)>1:raise RuntimeError("DUPLICATE_WIDGET_CONTENT")
    if matches:return matches[0]
    body={"data":{"content":content},"position":{"x":cx,"y":cy,"origin":"center"},
          "geometry":{"width":w},"parent":{"id":id(frame)}}
    if typ=="sticky_notes":
        body["data"]["shape"]="rectangle"
        body["style"]={"fillColor":fill,"textAlign":"center","textAlignVertical":"middle"}
    elif typ=="shapes":
        body["data"]["shape"]="rectangle"
        body["style"]={"fillColor":fill,"fontFamily":"open_sans",
                       "fontSize":str(fs),"textAlign":"center","textAlignVertical":"middle","color":"#26353a"}
        body["geometry"]["height"]=150
    elif typ=="texts":
        body["style"]={"fontFamily":"open_sans","fontSize":str(fs),"color":"#26353a"}
    return call("POST",typ,body)
def make_edge(start,end):
    edges=listing("connectors")
    got=[z for z in edges if str((z.get("startItem") or {}).get("id"))==id(start) and str((z.get("endItem") or {}).get("id"))==id(end)]
    if len(got)>1:raise RuntimeError("DUPLICATE_SC04_EDGE")
    if got:return got[0]
    return call("POST","connectors",{"startItem":{"id":id(start),"snapTo":"right"},
      "endItem":{"id":id(end),"snapTo":"left"},"shape":"curved",
      "style":{"strokeColor":"#26353a","strokeWidth":"2"}})
def create_scenarios(fm):
    ref=fm[BF["map"]];px,py=xy(ref);mw,mh=shape(ref.get("geometry"))
    width,height=5600,1560
    top=py-mh/2-340-height
    cx=px;cy=top+height/2
    nw=frame_create(SC0,cx,cy,width,height)
    x,y=xy(nw)
    add("texts",nw,"1B · Nejprve identifikujeme procesní scénáře",x,y-height/2+135,5100,"#26353a",48)
    add("texts",nw,"S0.1 a S0.2 · čtyři business příběhy, pak detail Event Stormingu a vysvětlení hranic",x,y-height/2+235,5100,"#26353a",25)
    for i,(name,sub,descr,fil,scid) in enumerate([
       ("Ztotožnění subjektu","S0.1","Podnět → matching → reference; výjimka: nejednoznačná shoda","#d9e9ff",BF["sc1"]),
       ("Změna referenčního údaje","S0.1","Registr → posouzení autority → oprava → oznámení","#d9e9ff",BF["sc2"]),
       ("Promítnutí role z agendy","S0.2","Agendové rozhodnutí → převzetí → referenční projekce","#fff0dc",BF["sc3"]),
       ("Zastupování a jeho změny","S0.2","Právní/agendová skutečnost → přijetí → platnost → oprava","#fff0dc",None)
    ]):
        col=i%2;row=i//2
        xx=x-1330+col*2660
        yy=y-265+row*475
        label=("S0.1" if i<2 else "S0.2")+" | "+name
        add("shapes",nw,label,xx,yy,2440,fil,33)
        add("texts",nw,descr,xx,yy+140,2400,"#26353a",23)
    return nw
def create_sc4(fm):
    s=fm[BF["sc3"]];sx,sy=xy(s);sw,sh=shape(s.get("geometry"))
    width,height=5200,2500
    x=sx+(sw+width)/2+540
    y=sy
    # One new sibling next to SC-03, above the existing combined E2E recap.
    f=frame_create(SC4,x,y,width,height)
    x,y=xy(f)
    add("texts",f,"SC-04 · Procesní scénář: doložené zastupování a opravy",x,y-height/2+130,4980,"#26353a",45)
    add("texts",f,"Vzor Process Modelling: vnější událost → command → referenční událost; výjimka se nezamlčuje.",x,y-height/2+235,4960,"#26353a",25)
    pairs=[
      ("EVT-0017","Zaznamenat doložené zastupování","S0-E041","Vznik"),
      ("EVT-0018","Promítnout doloženou změnu zastupování","S0-E042","Změna"),
      ("EVT-0019","Ukončit referenční platnost zastupování","S0-E043","Zánik")
    ]
    for i,(source,cmd,target,stage) in enumerate(pairs):
        yy=y-height/2+550+i*485
        add("texts",f,stage,x-width/2+225,yy,380,"#26353a",28)
        ev1=add("sticky_notes",f,anchor(source),x-width/2+1000,yy,350,"orange")
        command=add("shapes",f,cmd,x-width/2+2650,yy,1090,"#c6dcff",25)
        ev2=add("sticky_notes",f,anchor(target),x-width/2+4350,yy,350,"orange")
        make_edge(ev1,command);make_edge(command,ev2)
    ey=y-height/2+2080
    add("shapes",f,"Po doložené opravě: opravit referenční vztah",x-width/2+1390,ey,2180,"#c6dcff",24)
    add("sticky_notes",f,anchor("S0-E044"),x-width/2+3240,ey,350,"orange")
    add("sticky_notes",f,anchor("HS-S0-05"),x-width/2+4610,ey,350,"violet")
    add("texts",f,"Policy: S0.2 pouze eviduje rozhodnutí; nenabývá pravomoc jednat ani nerozhoduje o právu.",x,ey+190,5000,"#26353a",23)
    return f
def update_notes(allitems):
    targets=dict(PAIRMAP)
    nchanged=0
    for widget,k in targets.items():
        z=allitems.get(widget)
        if z is None:
            z=call("GET","items/"+widget)
        data=(z.get("data") or {}).get("content") or ""
        want=anchor(k)
        if text(z)==TITLES[k] and event_url(k) in html.unescape(str(data)):
            continue
        new=call("PATCH","sticky_notes/"+widget,{"data":{"content":want}})
        a=call("GET","sticky_notes/"+widget)
        if text(a)!=TITLES[k] or event_url(k) not in html.unescape(str((a.get("data") or {}).get("content") or "")):
            raise RuntimeError("LINK_READBACK_FAIL_"+widget)
        nchanged+=1
        if nchanged%6==0:print("STICKY_PATCH_PROGRESS",nchanged,flush=True)
    return nchanged
def audit_linksets(allitems):
    out={"existing":0,"required":len(PAIRMAP),"linked":0,"wrong_visible_id":0}
    for widget,k in PAIRMAP.items():
        z=allitems.get(widget)
        if z is None:continue
        out["existing"]+=1
        source=html.unescape(str((z.get("data") or {}).get("content") or ""))
        if event_url(k) in source:out["linked"]+=1
        if re.search(r"\b(?:S0-E\d{3}|HS-S0-\d{2}|EVT-\d{4})\b",text(z)):out["wrong_visible_id"]+=1
    return out
def main():
    fm,tasks,allitems,_=baseline()
    summary=audit_linksets(allitems)
    fs=listing("items",{"type":"frame"})
    print("FRESH_1B_PREFLIGHT_PASS","frameIds="+str(len(BF)),
       "curatedExistingSticky="+str(summary["existing"]),
       "pendingLinks="+str(summary["required"]-summary["linked"]),
       "visibleIds="+str(summary["wrong_visible_id"]),
       "processOverview="+str(sum((z.get("data") or {}).get("title")==SC0 for z in fs)),
       "SC04="+str(sum((z.get("data") or {}).get("title")==SC4 for z in fs)),flush=True)
    print("MODE",MODE,flush=True)
    if MODE=="audit":return
    if MODE=="pilot":
       k=next(iter(PAIRMAP));z=call("GET","sticky_notes/"+k)
       if text(z).startswith(PAIRMAP[k]+" "):
           a=call("PATCH","sticky_notes/"+k,{"data":{"content":anchor(PAIRMAP[k])}})
       z=call("GET","sticky_notes/"+k)
       if text(z)!=TITLES[PAIRMAP[k]] or event_url(PAIRMAP[k]) not in html.unescape((z.get("data") or {}).get("content") or ""):
           raise RuntimeError("PILOT_FAILED")
       print("1B_PILOT_NATIVE_LINK_PASS",flush=True);return
    n=update_notes(allitems)
    a=create_scenarios(fm)
    b=create_sc4(fm)
    fm2,tasks2,all2,_=baseline()
    summary2=audit_linksets(all2)
    if summary2["linked"]!=summary2["required"] or summary2["wrong_visible_id"]:
       raise RuntimeError("EXISTING_1B_LINK_INCOMPLETE")
    for fid,min_stickies in [(id(a),0),(id(b),7)]:
        ch=listing("items",{"parent_item_id":fid})
        if sum(z.get("type")=="sticky_note" for z in ch)<min_stickies:
            raise RuntimeError("SCENARIO_CREATE_INCOMPLETE")
        for z in ch:
            if z.get("type")=="sticky_note":
                s=html.unescape((z.get("data") or {}).get("content") or "")
                if 'href=' not in s or re.search(r"\b(?:HS-S0-\d+|S0-E\d+|EVT-\d+)\b",text(z)):
                    raise RuntimeError("NEW_STICKY_LINK_OR_ID_ERROR")
    print("1B_PROCESS_FIRST_READBACK_PASS","existingLinked="+str(summary2["linked"]),
      "overview="+id(a),"newSC04="+id(b),"patched="+str(n),
      "existingFrames="+str(len(BF)),flush=True)
    print("G4_NATIVE_VISUAL_REVIEW_OPEN",flush=True)
try:main()
except Exception as e:
 print("1B_FIX_STOP",type(e).__name__,str(e),flush=True);sys.exit(2)
