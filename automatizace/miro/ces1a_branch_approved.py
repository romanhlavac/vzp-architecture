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
            if e.code in (429,502,503,504) and n<4:time.sleep(min(25,2**n+1));continue
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
    f=[x for x in frames if close(ww(x),6075,25) and close(hh(x),7746,25)]
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
if __name__=="__main__" and MODE=="audit":
    try:audit();print("AUDIT ONLY. No Miro write.")
    except Exception as e:print("FAIL:",e);sys.exit(1)
