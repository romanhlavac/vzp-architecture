#!/usr/bin/env python3
"""Approved VZP CES-1A DEMO branching + boundary rationale via Miro REST v2.

Guarded non-destructive audit by default. Public repo contains only generic
method-demo text, no access tokens, private board IDs or Miro event inventories.
"""
import os,sys,time,json,re,html,urllib.request,urllib.parse,urllib.error
TOKEN=os.getenv("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.getenv("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
MODE=os.getenv("CES_BRANCH_MODE","audit")
if not TOKEN or not BOARD or MODE not in ("audit","apply"):sys.exit("FAIL: config")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
CODES=["A1","A2","A3","S0","B1","B2","B3","B4","B5","B6","B7","B8","B9","C1","D1","D2","D3","D4","D5","D6"]
EXPECTED=[4,6,6,8,8,8,8,8,8,8,6,6,8,6,6,4,6,6,4,6]
LANES={
  "S0":[[0,1,2],["NEW",5],[3,4,6,7]],
  "B1":[[0,1,2,3],[4,5,6],[7]],
  "B2":[[0,1,2],[3,4,5,6],[7]],
  "B3":[[0,1,2,3,4],[5,6],[7]],
  "B6":[[0,1,3,4,5,7],[2],[6]],
  "B8":[[0,1,2],[3,4,5]],
  "B9":[[0,1,2,3,4],[5],[6,7]],
}
HEIGHTS={c:(480 if c=="B8" else 680) for c in LANES}
EXTRA=sum(h-224 for h in HEIGHTS.values())
# Four complementary boundary tests. These are own analytical DEMO rationale,
# not client-approved domain boundaries, data authority or organizational chart.
RATIONALE={
"S0":[
("Pravidla · H04/H09","Ztotožnění, matching, provenience a řešení rozporů se významově liší od pravidel pojištění, předpisu pojistného a kontraktace."),
("Životní cyklus · H13/H14","Referenční identita může existovat před agendovým vztahem i po jeho ukončení; její oprava vztah automaticky nemění."),
("Využití · H03/H08/H11","Ověření potřebují B1/B2/B3; podněty ke společným údajům přicházejí také z B6. Věcný dopad vyhodnocuje příslušná agenda."),
("Odpovědnost · H01/H15","Business owner referenční identity a data steward jsou k určení; agendoví ownery rozhodují o vlastních vztazích; externí autorita registrů OPEN.")],
"B1":[
("Pravidla · H04/H09","Rozhodnutí o účasti, kategorii a pojistné příslušnosti není pouhé určení identity osoby."),
("Životní cyklus · H13/H14","Pojistný vztah vzniká, mění se a končí podle zákonných předpokladů nezávisle na trvání referenční identity."),
("Využití · H03/H11","Ztotožnění je vstupem do prověření registrace; výsledek pojistné evidence je samostatná agendová skutečnost."),
("Odpovědnost · H01/H15","Gestor pojištění vlastní právní výsledek a klasifikace, vlastník S0 společnou identitu; konkrétní owner/steward TBD.")],
"B2":[
("Pravidla · H07/H09","Stanovení povinnosti, předpis, saldo a vymáhání řídí finanční pravidla, nikoli pravidla ztotožnění plátce."),
("Životní cyklus · H13/H14","Povinnost a pohledávka se mění podle rozhodných skutečností a vypořádání, nikoli při každé referenční opravě."),
("Využití · H03/H11","S0 poskytuje identitu plátce; agendové posouzení následně tvoří své finanční výsledky a výjimky."),
("Odpovědnost · H01/H15","Business owner pojistného a steward finančních údajů jsou oddělení od vlastníka referenční identity; obsazení TBD.")],
"B3":[
("Pravidla · H04/H09","Oprávnění PZS, pracoviště a smluvní podmínky mají odlišnou autoritu a pravidla od identity FO/PO."),
("Životní cyklus · H13/H14","Uzavření, změna a ukončení smlouvy mají vlastní účinnost; nevyplývají automaticky ze změny referenčních údajů."),
("Využití · H03/H11","Ověřená identita a referenční změny jsou podkladem pro samostatné vyhodnocení PZS a smluvního dopadu."),
("Odpovědnost · H01/H15","Gestor smluvní sítě rozhoduje o kontraktaci; data steward PZS a externí autority oprávnění zůstávají k vyjasnění.")],
"B6":[
("Pravidla · H09/H10","Přijetí a vyřízení klientského podání není samo ověřením referenčního údaje ani rozhodnutím agendy."),
("Životní cyklus · H12/H13","Podání prochází od přijetí po odpověď různými věcnými scénáři; oprava údajů a reklamace jsou samostatné větve."),
("Využití · H03/H11","Klientský kanál předává podnět S0 nebo gestorovi věci; zpět přebírá výsledek pro komunikaci."),
("Odpovědnost · H01/H15","Vlastník klientské obsluhy/case managementu neprohlašuje vlastnictví identity ani rozhodnutí o pojištění; role TBD.")],
"B8":[
("Pravidla · H04/H09","Zahraniční příslušnost, nárok a refundace mají zvláštní mezinárodní režim oproti tuzemskému ztotožnění."),
("Životní cyklus · H13/H14","Nárokový doklad a refundace tvoří dva odlišné průběhy s jinými podmínkami a lhůtami."),
("Využití · H03/H12","Ověřenou identitu lze použít pro určení osoby; rozhodnutí o nároku je však výsledkem EU agendy."),
("Odpovědnost · H01/H15","Gestor EU nároků/refundací a příslušné zahraniční instituce; autorita údajů zahraniční příslušnosti OPEN.")],
"B9":[
("Pravidla · H04/H09","CRP, kapitační agenda a přerozdělování mají zvláštní zákonný mandát, odlišný od interního matching S0."),
("Životní cyklus · H13/H14","Zápis CRP, registrace u PL a přerozdělení sledují rozdílné právní a rozhodovací cykly."),
("Využití · H03/H11","Vybrané údaje mohou být důkazem identity, ne všechny údaje CRP jsou automaticky autoritativní pro S0."),
("Odpovědnost · H01/H15","Vlastníci zákonných agend, správce CRP a další ZP; system-of-record a atributové pravomoci OPEN.")],
}
SOURCES={"S0":"S35/S36/S51","B1":"S17/S36/S51","B2":"S17/S36/S51",
         "B3":"S17/S36/S51","B6":"S17/S36/S51","B8":"S17/S51","B9":"S17/S35/S36/S51"}
# Five first-priority cross-scenario links are references to EXISTING business events.
# Index locations are (row number, original left-to-right event index).
FIVE=[("D01",("B6",2),("S0",0),"Podnět z obsluhy → společné ověření"),
      ("D04",("S0",2),("B1",1),"Ztotožnění → posouzení identity pro pojištění"),
      ("D06",("S0",2),("B2",1),"Ztotožnění → posouzení identity plátce"),
      ("D08",("S0",2),("B3",1),"Ztotožnění → prověrka PZS (oprávnění samostatně)"),
      ("D09",("S0",7),("B3",5),"Referenční změna → vyhodnocení dopadu PZS")]
# Source indices are row indices; existing events themselves remain unchanged.
def call(method,path,payload=None,params=None):
    url=BASE+path+(("?"+urllib.parse.urlencode(params)) if params else "")
    raw=None if payload is None else json.dumps(payload,ensure_ascii=False).encode("utf-8")
    hdr={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if raw is not None:hdr["Content-Type"]="application/json"
    for n in range(5):
        try:
            q=urllib.request.Request(url,data=raw,headers=hdr,method=method)
            with urllib.request.urlopen(q,timeout=40) as ans:
                data=ans.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and n<4:time.sleep(min(25,2**n+1));continue
            raise RuntimeError(method+" "+path.split("/")[0]+" HTTP "+str(e.code)) from None
        except Exception:
            raise RuntimeError(method+" "+path.split("/")[0]+" unavailable") from None
def page(path,params=None):
    out=[];cursor=None
    for _ in range(80):
        p=dict(params or {},limit=50)
        if cursor:p["cursor"]=cursor
        d=call("GET",path,params=p);out+=d.get("data",[])
        cursor=d.get("cursor")
        if not cursor:return out
    raise RuntimeError("Pagination failed")
def xx(z):return float((z.get("position") or {}).get("x") or 0)
def yy(z):return float((z.get("position") or {}).get("y") or 0)
def ww(z):return float((z.get("geometry") or {}).get("width") or 0)
def hh(z):return float((z.get("geometry") or {}).get("height") or 0)
def id(z):return str(z["id"])
def close(a,b,t=6):return abs(float(a)-float(b))<=t
def txt(z):return html.unescape(re.sub(r"<[^>]*>"," ",str((z.get("data") or {}).get("content") or ""))).strip()
def tag(z):
    m=re.search(r"(^|\s)(A[123]|S0|B[1-9]|C1|D[1-6])\s*[·.]",txt(z))
    return m.group(2) if m else None
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def detail(z):
    t=z["type"];return call("GET",("sticky_notes/" if t=="sticky_note" else "shapes/" if t=="shape" else "texts/")+id(z))
def moved(z,dy,geom=None,content=None):
    typ=z["type"]
    path=("sticky_notes/" if typ=="sticky_note" else "shapes/" if typ=="shape" else "texts/")+id(z)
    data={"position":{"x":xx(z),"y":yy(z)+dy,"origin":"center"}}
    if geom is not None:data["geometry"]={"width":ww(z),"height":geom}
    if content is not None:data["data"]={"content":content}
    call("PATCH",path,data)
    v=call("GET",path)
    if abs(yy(v)-(yy(z)+dy))>3:raise RuntimeError("Position readback failed")
    return v
def read():
    frames=page("items",{"type":"frame"})
    f=[x for x in frames if close(ww(x),6075,25) and (close(hh(x),7746,25) or close(hh(x),7746+EXTRA+ZOOM_EXTRA,25))]
    if len(f)!=1:raise RuntimeError("Exact CES-1A frame geometry changed")
    frame=call("GET","frames/"+id(f[0]))
    items=page("items",{"parent_item_id":id(frame)})
    domains={tag(z):z for z in items if z.get("type")=="shape" and
             close(hh(z),224,7) and 2900<ww(z)<4600 and tag(z) in CODES and "Aktéři" in txt(z)}
    if len(domains)!=20:raise RuntimeError("20 bands not uniquely identified")
    order=sorted(domains,key=lambda c:yy(domains[c]))
    if order!=CODES:raise RuntimeError("Band sequence drift")
    rows={}
    for i,c in enumerate(CODES):
        y=yy(domains[c])
        members=sorted([z for z in items if z.get("type")=="sticky_note" and
                        close(ww(z),258,10) and close(hh(z),168,14) and close(yy(z),y,40)],
                       key=xx)
        if len(members)!=EXPECTED[i]:raise RuntimeError("Event count drift in row "+str(i))
        rows[c]=members
    if sum(map(len,rows.values()))!=130:raise RuntimeError("Event total drift")
    reasons={}
    for c in LANES:
        items0=[z for z in items if z.get("type")=="shape" and
                "BOUNDARY RATIONALE" in txt(z).upper() and close(yy(z),yy(domains[c]),45)]
        if len(items0)!=1:raise RuntimeError("Rationale not unique for "+c)
        reasons[c]=items0[0]
    return frame,items,domains,rows,reasons
def audit():
    fr,items,dom,rows,why=read()
    print("PREFLIGHT PASS: 20 bands, 130 native events, 7 boundary rationales")
    print("ROWS:",[(c,len(rows[c]),len(LANES.get(c,[]))) for c in CODES if c in LANES])
    print("HEIGHT DELTA:",EXTRA)
    # Ensure reference blocks can be identified outside 1A, and no second relevant nearby frame.
    possible=[z for z in page("items",{"type":"text"}) if ("HEURISTIKY HRANIC DOMÉN" in txt(z) or "ZDROJE DEMO 1A" in txt(z))]
    print("REFERENCE TEXT BLOCKS:",len(possible))
    if len(possible)!=2:raise RuntimeError("Reference blocks are not unique")
    return fr,items,dom,rows,why,possible

ZOOM_EXTRA=1500
CHRONOLOGY={
 "S0":[(0,1),(1,2),(3,4),(4,6),(6,7)],
 "B1":[(0,1),(1,2),(2,3),(5,6)],
 "B2":[(0,1),(1,2),(3,4),(4,5),(5,6)],
 "B3":[(0,1),(1,2),(2,3),(3,4)],
 "B6":[(0,1),(1,3),(3,4),(4,5),(5,7)],
 "B8":[(0,1),(1,2),(3,4),(4,5)],
 "B9":[(0,1),(1,2),(2,3),(3,4),(6,7)],
}
BRANCH_LABELS={
 "S0":["Standardní ztotožnění","Výjimka: nejednoznačná identita","Oprava referenčního údaje"],
 "B1":["Registrace a vznik vztahu","Změny během pojištění","Ukončení vztahu"],
 "B2":["Stanovení povinnosti","Předpis, platby a saldo","Podmíněné vymáhání"],
 "B3":["Kontraktace poskytovatele","Změna údajů a dodatky","Ukončení smlouvy"],
 "B6":["Podání a věcné vyřízení","Změna referenčních údajů","Samostatná reklamace"],
 "B8":["Zahraniční nárok a výpomoc","Refundace a vyúčtování"],
 "B9":["Agenda CRP","Kapitační agenda","Přerozdělování"],
}
def gapbefore(index):
    return sum(HEIGHTS.get(CODES[i],224)-224 for i in range(index))
def scenecenter(rowcode,lane,y):
    top=y-112+gapbefore(CODES.index(rowcode))
    return top+120+lane*(228 if rowcode=="B8" else 218)
def replace_event_text(o):
    return (o.get("data") or {}).get("content") or ""
def connector_list():
    out=page("connectors")
    return [call("GET","connectors/"+id(z)) for z in out]
def edge(c,k):return str((c.get(k) or {}).get("id") or "")
def link_plan_for_rows(rows):
    result={}
    for code,branch in LANES.items():
        for lane,indices in enumerate(branch):
            for j,index in enumerate(indices):
                if index=="NEW":continue
                x=1610+j*430
                if code=="S0" and lane==0:
                    x={0:1610,1:2040,2:3350}[index]
                if code=="S0" and lane==1:
                    x=2920
                result[(code,index)]=(x,lane)
    return result
def rationale_content(code):
    lines=["<p><b>BOUNDARY RATIONALE · DEMO / K BUSINESS VALIDACI</b></p>"]
    for h,v in RATIONALE[code]:
        lines.append("<p><b>"+html.escape(h)+"</b><br/>"+html.escape(v)+"</p>")
    lines.append("<p><i>Zdroje: "+SOURCES[code]+"; owner/atributová autorita OPEN. Heuristiky ≠ schválení hranice.</i></p>")
    return "".join(lines)
def update_header_legend_text(items):
    count=0
    for obj in items:
        if obj.get("type")!="text":continue
        name=txt(obj).upper()
        update=None
        if "KANDIDÁTNÍ L1 DOMÉNY" in name and "METODICKÉ" not in name:
            update=None
        elif "HODNOCENÍ HRANIC" in name or "DOMÉNOVÉ HRANICE" in name:
            update="VERTIKÁLNÍ VĚTVE = ALTERNATIVNÍ / SOUBĚŽNÉ BUSINESS SCÉNÁŘE"
        elif "ČERNÁ ŠIPKA" in name:
            update="ČERNÁ ŠIPKA = VÝZNAMNÁ BUSINESS NÁVAZNOST; NE INVOKACE"
        elif "ZLEVA DOPRAVA" in name:
            update="ZLEVA DOPRAVA = ORIENTAČNÍ ČAS V DANÉM SCÉNÁŘI"
        if update and txt(obj)!=update:
            call("PATCH","texts/"+id(obj),{"data":{"content":update}})
            count+=1
    return count
def relocate_reference_blocks(refs,dy):
    for z in refs:
        moved(detail(z),dy)
def safe_frame_expand(frame):
    d={"geometry":{"width":ww(frame),"height":hh(frame)+EXTRA+ZOOM_EXTRA},
       "position":{"x":xx(frame),"y":yy(frame)+(EXTRA+ZOOM_EXTRA)/2,"origin":"center"}}
    call("PATCH","frames/"+id(frame),d)
    readback=call("GET","frames/"+id(frame))
    if not close(hh(readback),hh(frame)+EXTRA+ZOOM_EXTRA,4):
        raise RuntimeError("Frame resize verification failed")
    return readback
def scenario_event_ids(rows):
    return {id(z) for c in LANES for z in rows[c]}
def prune_relevant_connectors(existing,related_event_ids):
    # Only connectors incident to approved CES-related events are rebuilt;
    # untouched other-area links remain unchanged.
    dropped=0
    for con in existing:
        if edge(con,"startItem") in related_event_ids or edge(con,"endItem") in related_event_ids:
            call("DELETE","connectors/"+id(con));dropped+=1
    return dropped
def add_new_subject_event(frame,x,y):
    content="Více možných shod bylo zjištěno"
    payload={"data":{"content":content,"shape":"rectangle"},
             "style":{"fillColor":"orange","textAlign":"center","textAlignVertical":"middle"},
             "geometry":{"width":258},"position":{"x":x,"y":y,"origin":"center"},
             "parent":{"id":id(frame)}}
    created=call("POST","sticky_notes",payload)
    if not created.get("id"):raise RuntimeError("Approved new S0 event creation failed")
    obj=call("GET","sticky_notes/"+id(created))
    if txt(obj)!=content or parent(obj)!=id(frame):
        raise RuntimeError("New subject-event readback mismatch")
    return obj
def create_link(a,b):
    out=call("POST","connectors",{
        "startItem":{"id":id(a),"snapTo":"auto"},
        "endItem":{"id":id(b),"snapTo":"auto"},
        "shape":"curved","style":{"strokeColor":"#000000","strokeWidth":2,
                   "strokeStyle":"normal","startStrokeCap":"none",
                   "endStrokeCap":"rounded_stealth"},"captions":[]})
    if not out.get("id"):raise RuntimeError("No ID after connector creation")
    ck=call("GET","connectors/"+id(out))
    if edge(ck,"startItem")!=id(a) or edge(ck,"endItem")!=id(b):raise RuntimeError("New local connector mismatch")
    return ck
def clone_front(o,frame):
    obj=call("GET","sticky_notes/"+id(o))
    if not obj.get("data") or not obj.get("style") or parent(obj)!=id(frame):
        raise RuntimeError("Cannot safely restore event stacking")
    new=call("POST","sticky_notes",{
       "data":obj["data"],"style":obj["style"],
       "geometry":{"width":ww(obj)},
       "position":{"x":xx(obj),"y":yy(obj),"origin":"center"},
       "parent":{"id":id(frame)}})
    restored=call("GET","sticky_notes/"+id(new))
    if txt(restored)!=txt(obj) or not close(xx(restored),xx(obj),3) or not close(yy(restored),yy(obj),3):
        raise RuntimeError("Z-layer replacement comparison failed")
    call("DELETE","sticky_notes/"+id(obj))
    return restored
def text_create(frame,x,y,w,content,font=20):
    obj=call("POST","texts",{
        "data":{"content":content},
        "style":{"color":"#26353A","fontFamily":"open_sans","fontSize":str(font),"textAlign":"left"},
        "geometry":{"width":w},"position":{"x":x,"y":y,"origin":"center"},
        "parent":{"id":id(frame)}})
    if not obj.get("id"):raise RuntimeError("Text element creation failed")
    return obj
def zoom(frame,model):
    title="<b>CES INTERACTION ZOOM – REFERENCE NA STEJNÉ BUSINESS UDÁLOSTI</b>"
    sub="Následující řádky odkazují na původní Event Storming události. Nejsou to další event cards. Černá šipka = významná business návaznost; ne automatické spuštění."
    text_create(frame,3000,10820,5100,title,28)
    text_create(frame,3000,10885,5100,sub,18)
    for j,(name,(a,ai),(b,bi),rationale) in enumerate(FIVE):
        source=model[a][ai];target=model[b][bi]
        # Render as neutral text references, not as orange events.
        title="<b>"+name+" · "+html.escape(rationale)+"</b>"
        pair=("<b>Zdroj:</b> "+html.escape(txt(source))+
              "　<b>→</b>　<b>Cíl:</b> "+html.escape(txt(target)))
        text_create(frame,3000,11005+145*j,5300,title+"<br/>"+pair,19)
    text_create(frame,3000,11740,5300,
        "Hranice S0 je vysvětlena kombinací H04/H09 (pravidla), H13/H14 (životní cyklus), H03/H11 (sdílené výsledky) a H01/H15 (odpovědnost). B8/B9: autorita a konkrétní scénář OPEN.",18)
def apply():
    fr,items,domains,rows,reasons,refs=audit()
    original_rows={k:list(v) for k,v in rows.items()}
    affected=scenario_event_ids(rows)
    before_connections=connector_list()
    inframe={id(z) for z in items}
    inside=[c for c in before_connections if edge(c,"startItem") in inframe and edge(c,"endItem") in inframe]
    partial=close(hh(fr),7746+EXTRA+ZOOM_EXTRA,25)
    if (not partial and len(inside)!=50) or (partial and len(inside)!=17):
        raise RuntimeError("Baseline/recovery connector count changed; no write")
    # All 20 original row centers and their relative shifts are frozen before writes.
    oldY={c:yy(domains[c]) for c in CODES}
    shifts={c:gapbefore(i) for i,c in enumerate(CODES)}
    reference_moves=EXTRA+ZOOM_EXTRA
    if not partial:
        safe_frame_expand(fr)
        relocate_reference_blocks(refs,reference_moves)
        # Remove incident links BEFORE recreating any old S0/B8/B9 endpoints.
        dropped=prune_relevant_connectors(inside,affected)
    else:
        if any(edge(z,"startItem") in affected or edge(z,"endItem") in affected for z in inside):
            raise RuntimeError("Recovery connector baseline contains unreviewed links")
        dropped=33
        print("RECOVERY RESUME: frame and references already shifted; 33 impacted connectors already removed")
    placement=link_plan_for_rows(rows)
    done=0
    # Update non-event children. Domain shapes are underlay, rationale boxes follow.
    domain_ids={id(d) for d in domains.values()}
    why_ids={id(d) for d in reasons.values()}
    event_ids={id(n) for row in rows.values() for n in row}
    for c in CODES:
        idx=CODES.index(c);shift=shifts[c]
        d=detail(domains[c]);oldheight=hh(d);newheight=HEIGHTS.get(c,224)
        moved(d,shift+(newheight-oldheight)/2,geom=newheight)
        if c in reasons:
            rat=detail(reasons[c])
            moved(rat,shift+(newheight-224)/2,geom=newheight-16,content=rationale_content(c))
            done+=1
    # Other per-row shapes and texts are moved down to remain on their matching rows.
    for item in items:
        if id(item) in domain_ids|why_ids|event_ids:continue
        typ=item.get("type")
        if typ not in ("shape","text"):continue
        y=yy(item)
        if y<oldY["S0"]-130:continue
        i=min(range(20),key=lambda j:abs(y-oldY[CODES[j]]))
        code=CODES[i]
        dy=gapbefore(i)
        if y>oldY["D6"]+250:dy=EXTRA
        # Move one small row-local auxiliary widget with each band.
        if dy:moved(detail(item),dy)
    # Reposition notes according to the exact approved branches.
    rebuilt={}
    for c in CODES:
        if c not in LANES:
            dy=shifts[c]
            for z in original_rows[c]:
                if dy:moved(detail(z),dy)
            rebuilt[c]=original_rows[c]
            continue
        rebuilt[c]=list(original_rows[c])
        for lane,indices in enumerate(LANES[c]):
            for laneidx,index in enumerate(indices):
                if index=="NEW":continue
                obj=detail(original_rows[c][index])
                x,l=placement[(c,index)]
                y=scenecenter(c,l,oldY[c])
                call("PATCH","sticky_notes/"+id(obj),{"position":{"x":x,"y":y,"origin":"center"}})
                fresh=call("GET","sticky_notes/"+id(obj))
                if not(close(xx(fresh),x,3) and close(yy(fresh),y,3)):
                    raise RuntimeError("Scenario card position mismatch")
                rebuilt[c][index]=fresh
        # Refresh the two rows where backgrounds are known newer than the cards:
        # create identical native Stickies ON TOP of the background, then retire old.
        if c in ("B8","B9"):
            for i,z in enumerate(rebuilt[c]):
                rebuilt[c][i]=clone_front(z,fr)
    # One user-approved new event in the identity ambiguity branch.
    subj=add_new_subject_event(fr,2490,scenecenter("S0",1,oldY["S0"]))
    created=0
    for c,pairs in CHRONOLOGY.items():
        for a,b in pairs:
            create_link(rebuilt[c][a],rebuilt[c][b]);created+=1
    create_link(rebuilt["S0"][1],subj);created+=1
    create_link(subj,rebuilt["S0"][5]);created+=1
    # The five selected cross-area business links are visible together in
    # an explicit Zoom of REFERENCES, not drawn diagonally through other event cards.
    zoom(fr,rebuilt)
    leg=update_header_legend_text(items)
    # Exact REST read-back
    allitems=page("items",{"parent_item_id":id(fr)})
    stickies=[z for z in allitems if z.get("type")=="sticky_note"]
    if len(stickies)!=131:raise RuntimeError("Expected 131 native ES event cards")
    if any(re.match(r"^(A\d|B\d|S0)\.\d{2}",txt(z)) for z in stickies):
        raise RuntimeError("Domain identifier leaked into event text")
    cons=connector_list()
    valid_ids={id(z) for z in allitems}
    linked=[z for z in cons if edge(z,"startItem") in valid_ids and edge(z,"endItem") in valid_ids]
    expected_links=(17 if partial else len(inside)-dropped)+created
    if len(linked)!=expected_links:
        raise RuntimeError("Connector count not conserved")
    if any(str((z.get("style") or {}).get("strokeColor") or "").lower()!="#000000" for z in linked):
        raise RuntimeError("Non-black in-frame connector")
    for c in LANES:
        why=page("items",{"parent_item_id":id(fr)})
        match=[x for x in why if x.get("type")=="shape" and "BOUNDARY RATIONALE" in txt(x).upper()
               and c in CODES and close(yy(x),oldY[c]+shifts[c]+(HEIGHTS[c]-224)/2,35)]
        if len(match)!=1 or "H15" not in txt(match[0]):raise RuntimeError("Boundary rationale readback failed")
    print("LIVE WRITE PASS: 7 branched business areas; one approved new S0 event")
    print("BUSINESS BOUNDARY PASS: 7 four-test rationales with H-IDs")
    print("CONNECTORS: old relevant removed=%d, new scenario links=%d, final=%d"%(dropped,created,len(linked)))
    print("CES INTERACTION ZOOM PASS: 5 cross-scenario textual references")
    print("STRUCTURAL PASS: %d sticky events; frame enlarged by %d; legend changes=%d"%(len(stickies),EXTRA+ZOOM_EXTRA,leg))
    print("VISUAL RENDER REVIEW: remains OPEN until human screenshot acceptance")
if __name__=="__main__":
    try:
        if MODE=="audit":audit();print("AUDIT ONLY: no board mutations")
        else:apply()
    except Exception as e:
        print("FAIL:",str(e));sys.exit(1)
