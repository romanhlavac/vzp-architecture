#!/usr/bin/env python3
"""Create complete native L1 Domain Landscape v3 from live ES Big Picture v14.

Protected: original BP v14, existing L1 v2, original template.
Source: 147 BP event titles and 51 native business relationships.
Output: 20 scenario domains, 147 native event cards, 147 editable descriptions,
        51 native P/D connectors on two-column relationship zoom.
No assertion of historical event occurrence; demonstration scenario assumes
business acceptance per project brief. Mode audit / pilot / apply; audit default.
"""
import os,json,re,html,hashlib,urllib.request,urllib.parse,urllib.error,time,sys,math,collections
from landscape_build import RULES
from ces1a_v14_integrate import SHORT
from l1_v3_descriptions import describe
MODE=os.environ.get("L1V3_MODE","audit")
if MODE not in ("audit","pilot","apply"):sys.exit("BAD_MODE")
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")
BP_TITLE="CES-1A · BP ES v14 · Enterprise business events · pracovní návrh"
L1_V2_TITLE="CES-1A · L1 DOMAIN LANDSCAPE · v2 (BP ES v12 mapping)"
TITLE="CES-1A · L1 DOMAIN LANDSCAPE · v3 (BP ES v14 / 147 událostí)"
ADD={
 "N01":"B2","N02":"B4","N03":"B5","N04":"B8","N05":"B5","N06":"B5",
 "EV02":"A1","EV03":"A1","EV05":"A2","EV06":"B6","EV07":"A3","EV08":"A3",
 "EV09":"B7","EV10":"B7","EV11":"B3","EV12":"B3","EV13":"B5","EV14":"B5",
 "EV15":"B8","EV16":"B9","EV17":"C1","EV18":"C1","EV19":"D1",
 "EV20":"D1","EV21":"D1","EV22":"D2","EV23":"D2","EV24":"D3","EV25":"D3",
 "EV26":"D4","EV27":"D4","EV28":"D4","EV29":"D5","EV30":"D5",
 "EV31":"D6","EV32":"D6","EV33":"D6"
}
assert set(ADD)==set(SHORT) and len(ADD)==37
# Purposeful demonstration scope; all 20 areas are populated, no open/candidate labels.
RATIONALE_PATCH={
 "B7":("Klient se rozhodl změnit pojišťovnu a jeho přihláška byla přijata, případně byl napraven neoprávněný přestup.",
       "Akviziční milník a retenční náprava předcházejí nebo napravují právně účinnou pojistnou příslušnost.",
       "CES drží identitu, B7 milník získání klienta; právní účast a platnost pojištění se eviduje odděleně.",
       "Účinnost pojištění a plátcovství se řeší ve správě kmene a pojistného."),
 "D2":("Byla ztracena nebo obnovena odborná kapacita nezbytná pro poskytování klíčové služby VZP.",
       "Kapacitní milníky významně mění schopnost splnit veřejnoprávní agendu.",
       "Identita zaměstnance může být referencována, ale dostupnost odborné kapacity není životní cyklus subjektů.",
       "Rutinní pracovněprávní administrativa se zde v Big Picture nemodeluje."),
 "D3":("Klientská digitální služba se stala nedostupnou nebo byla obnovena.",
       "Události vyjadřují uživatelsky významnou dostupnost, nikoli interní technické deployment kroky.",
       "Technická identita není business identita pojištěnce; klientské služby čerpají CES referenční údaje.",
       "Správa konkrétních chybových ticketů a integrací zůstává podrobnější úrovní."),
 "D5":("Klienti ztratili nebo znovu získali možnost podat právně významné podání.",
       "Změny dostupnosti podací služby mají právní a obslužný dopad.",
       "Identita podatele se ověřuje proti referenčním údajům, ale dostupnost podání je samostatný výsledek služby.",
       "Evidenční zpracování jednotlivého dokumentu se nemodeluje jako enterprise událost."),
 "D6":("Byl potvrzen závažný incident, oznámen dotčeným osobám nebo byla narušena důvěryhodnost evidence.",
       "Rozhodné jsou doložené bezpečnostní a zákonné milníky; oznámení má podmínky vysokého rizika.",
       "CES podléhá bezpečnostním pravidlům, bezpečnostní incident však není změnou identity evidovaného subjektu.",
       "Operativní reakce CSIRT a technické logování jsou podrobnější procesní detaily.")
}
DOMAIN_LABELS={
 "S0":"Správa a evidence subjektů","A1":"Strategické řízení","A2":"Zdravotní a úhradová politika",
 "A3":"Kvalita a hodnota péče","B1":"Správa pojistného kmene","B2":"Výběr pojistného a pohledávky",
 "B3":"Smluvní síť poskytovatelů","B4":"Úhrady zdravotních služeb","B5":"Revize a individuální souhlasy",
 "B6":"Klientské služby a komunikace","B7":"Akvizice a retence","B8":"Mezistátní agendy",
 "B9":"Agendy v zastoupení státu","C1":"Analytika a výkaznictví","D1":"Finance a účetnictví",
 "D2":"Lidské zdroje","D3":"Informační technologie","D4":"Právo a veřejné zakázky",
 "D5":"Provoz a spisová služba","D6":"Bezpečnost informací"
}
COLS=5
CW=900
ROW_GAP=550
W=16200
LANE_X=5400
NOTE_X0=3600
REF_XA=10300
REF_XB=14300
LEFT_X=1480
def request(method,path,payload=None,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    body=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
    headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None:headers["Content-Type"]="application/json"
    attempts=5 if method=="GET" else 1
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,data=body,headers=headers,method=method)
            with urllib.request.urlopen(req,timeout=45) as res:
                b=res.read()
                return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            if method=="GET" and e.code in (429,500,502,503,504) and i<attempts-1:
                time.sleep(min(20,2**i+1));continue
            raise RuntimeError("MIRO_"+method+"_HTTP_"+str(e.code)) from None
        except Exception:
            if method=="GET" and i<attempts-1:time.sleep(2);continue
            raise RuntimeError("MIRO_"+method+"_UNCERTAIN_OUTCOME") from None
def listing(path,params=None):
    out=[];cursor=None
    for _ in range(150):
        q=dict(params or {},limit=50)
        if cursor:q["cursor"]=cursor
        d=request("GET",path,params=q)
        out+=d.get("data",[]);cursor=d.get("cursor")
        if not cursor:return out
    raise RuntimeError("PAGINATION_OVERFLOW")
def oid(z):return str(z.get("id",""))
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def edge(z,k):return str((z.get(k) or {}).get("id") or "")
def x(z):return float((z.get("position") or {}).get("x") or 0)
def y(z):return float((z.get("position") or {}).get("y") or 0)
def wd(z):return float((z.get("geometry") or {}).get("width") or 0)
def ht(z):return float((z.get("geometry") or {}).get("height") or 0)
def txt(z):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str((z.get("data") or {}).get("content") or "")))).strip()
def sha(z):return hashlib.sha256(z.encode()).hexdigest()
def ident(z):
    return (oid(z),z.get("type"),parent(z),txt(z),round(x(z),2),round(y(z),2))
def esig(z):
    return (oid(z),edge(z,"startItem"),edge(z,"endItem"),z.get("shape"),json.dumps(z.get("captions") or [],sort_keys=True,ensure_ascii=False))
def clean(a):return html.escape(str(a),quote=False)
def source():
    objs=listing("items");cons=listing("connectors")
    frames=[z for z in objs if z.get("type")=="frame"]
    bp=[z for z in frames if (z.get("data") or {}).get("title")==BP_TITLE]
    v2=[z for z in frames if (z.get("data") or {}).get("title")==L1_V2_TITLE]
    tm=[z for z in frames if sha(oid(z))==RULES["template_frame_id_hash"]]
    out=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
    if any(len(z)!=1 for z in (bp,v2,tm)) or len(out)>1:raise RuntimeError("SOURCE_TEMPLATE_IDENTITY_DRIFT")
    bp=bp[0];v2=v2[0];tm=tm[0];target=out[0] if out else None
    bpitems=[z for z in objs if parent(z)==oid(bp)]
    v2items=[z for z in objs if parent(z)==oid(v2)]
    tmitems=[z for z in objs if parent(z)==oid(tm)]
    notes=[z for z in bpitems if z.get("type")=="sticky_note"]
    ids={oid(z) for z in notes}
    edges=[z for z in cons if edge(z,"startItem") in ids and edge(z,"endItem") in ids]
    if len(notes)!=147 or len(edges)!=51 or any(z.get("shape")!="curved" for z in edges):
        raise RuntimeError("BP_V14_BASELINE_DRIFT")
    texts=[txt(z) for z in notes]
    if len(set(texts))!=147:raise RuntimeError("BP_TEXT_DUPLICATE")
    historical={h:c for c,vals in RULES["groups"].items() for h in vals}
    shortmap={v:k for k,v in SHORT.items()}
    bycode=collections.defaultdict(list)
    old_count=0;new_count=0
    for z in notes:
        st=txt(z);h=sha(st)
        if h in historical:code=historical[h];old_count+=1
        elif st in shortmap:code=ADD[shortmap[st]];new_count+=1
        else:raise RuntimeError("UNROUTED_BP_EVENT")
        bycode[code].append(z)
    if old_count!=110 or new_count!=37 or sorted(bycode)!=sorted(RULES["codes"]):
        raise RuntimeError("L1_COMPLETENESS_OR_COVERAGE_DRIFT")
    domains={}
    for z in v2items:
        s=txt(z)
        m=re.match(r"(A[123]|S0|B[1-9]|C1|D[1-6])\s*·",s)
        if z.get("type")=="shape" and m and "Aktéři" in s:
            if m[1] in domains:raise RuntimeError("L1_V2_DOMAIN_DUPLICATE")
            domains[m[1]]=z
    if set(domains)!=set(RULES["codes"]):raise RuntimeError("L1_TEMPLATE_DOMAIN_MISMATCH")
    ordered={}
    for code in RULES["codes"]:
        # Keep original v2 order for the 110 historical events.
        oldsort={h:i for i,h in enumerate(RULES["groups"][code])}
        ordered[code]=sorted(bycode[code],key=lambda z:(
            0 if sha(txt(z)) in oldsort else 1,
            oldsort.get(sha(txt(z)),0),
            y(z),x(z)))
    if sum(map(len,ordered.values()))!=147:raise RuntimeError("EVENT_COUNT_MISMATCH")
    protected={ident(z) for z in bpitems+v2items+tmitems}
    protect_ed={esig(z) for z in edges}
    print("L1V3_FRESH_SOURCE_PASS","bp_events=147","relations=51","historical=110",
          "additions=37","domain_rows=20","source_template_protected",len(protected),flush=True)
    return {"obj":objs,"conn":cons,"frames":frames,"bp":bp,"v2":v2,"tm":tm,
            "target":target,"bp_items":bpitems,"v2_items":v2items,"tm_items":tmitems,
            "events":ordered,"links":edges,"domains":domains,"protected":protected,"edprotected":protect_ed,
            "notes":notes,"v2_headings":{oid(z) for z in v2items}}
def geometry(s):
    top=570;rows={}
    for code in RULES["codes"]:
        n=len(s["events"][code])
        height=max(890,math.ceil(n/COLS)*ROW_GAP+275)
        rows[code]={"top":top,"height":height}
        top+=height+55
    right_height=780+51*375
    H=round(max(top+500,right_height+500))
    return rows,H
def create(st,typ,pos,content,width=500,height=None,style=None):
    # Deterministic geometry slot is the idempotency key. Never replace manually edited objects.
    a=[z for z in st["items"] if z.get("type")==typ and abs(x(z)-pos[0])<2 and abs(y(z)-pos[1])<2]
    plain=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(content)))).strip()
    if len(a)>1:raise RuntimeError("TARGET_SLOT_DUPLICATE")
    if a:
        if txt(a[0])!=plain:raise RuntimeError("TARGET_SLOT_CONTENT_DRIFT")
        return a[0]
    body={"data":{"content":content},
          "position":{"x":pos[0],"y":pos[1],"origin":"center"},
          "geometry":{"width":width},
          "parent":{"id":oid(st["frame"])}}
    if height is not None:body["geometry"]["height"]=height
    if typ=="shape":body["data"]["shape"]="rectangle"
    if typ=="sticky_note":body["data"]["shape"]="rectangle"
    if style:body["style"]=style
    path={"shape":"shapes","sticky_note":"sticky_notes","text":"texts"}[typ]
    z=request("POST",path,body)
    if not oid(z):raise RuntimeError("MISSING_NEW_OBJECT_ID")
    st["items"].append(z)
    st["created"]+=1
    return z
def text(st,pos,content,width=780,font=18,style=None):
    s={"fontFamily":"open_sans","fontSize":str(font),"color":"#26353a","textAlign":"left"}
    s.update(style or {})
    return create(st,"text",pos,content,width=width,style=s)
def dom(st,code):
    g=st["rows"][code];top=g["top"];h=g["height"]
    r=RATIONALE_PATCH.get(code,RULES["rationales"][code])
    if code=="S0":
        r=("Ztotožněný subjekt a správa jeho referenčního životního cyklu.",
           "Vlastní pravidla identity, atributů, provenience a oprávnění zastupování.",
           "CES poskytuje referenční identitu dalším agendám; neurčuje jejich pojištění, smlouvy ani finanční nároky.",
           "Vznik konkrétní pojistné účasti či platební povinnosti vzniká mimo CES.")
    # Strip stale hypothetical wording in demonstration story while preserving rationale substance.
    vals=[re.sub(r"\bOPEN\b|\bPROPOSED\b|\bk validaci\b|\bk ověření\b","",str(v),flags=re.I) for v in r]
    desc="<p><strong>"+clean(code+" · "+DOMAIN_LABELS[code])+"</strong></p>"
    for k,v in zip(("Business výsledek","Pravidla / autorita","CES hranice","Odlišení od sousedů"),vals):
        desc+="<p><strong>"+k+":</strong> "+clean(v)+"</p>"
    desc+="<p><strong>"+str(len(st["source"]["events"][code]))+" událostí</strong></p>"
    ref=st["source"]["domains"][code]
    style={k:v for k,v in (ref.get("style") or {}).items() if k in (
        "fillColor","fillOpacity","borderColor","borderWidth","borderOpacity","borderStyle","fontFamily",
        "fontSize","color","textAlign","textAlignVertical")}
    style.update({"fontSize":"18","textAlign":"left","textAlignVertical":"top"})
    create(st,"shape",(LEFT_X,top+h/2),desc,width=2820,height=h-30,style=style)
    create(st,"shape",(LANE_X,top+h/2),"",width=4900,height=h-30,
           style={"fillColor":"#f8f9fa","fillOpacity":"0.50","borderColor":"#dee2e6","borderWidth":"1","borderOpacity":"1","borderStyle":"normal"})
    for n,z in enumerate(st["source"]["events"][code]):
        col=n%COLS;row=n//COLS
        xx=NOTE_X0+col*CW
        yy=top+195+row*ROW_GAP
        title=z["data"]["content"]
        card=create(st,"sticky_note",(xx,yy),title,width=440,
              style={"fillColor":"orange","textAlign":"center","textAlignVertical":"middle"})
        st["map"][oid(z)]=card
        business=describe(txt(z),code)
        url="https://miro.com/app/board/"+BOARD+"/?moveToWidget="+oid(z)
        note="<p>"+clean(business)+"</p><p><a href=\""+url+"\">↗ Zdrojový BP</a></p>"
        text(st,(xx,yy+266),note,width=760,font=17,
             style={"color":"#485560","textAlign":"center"})
    print("L1V3_ROW_DONE",code,len(st["source"]["events"][code]),flush=True)
def head(st):
    text(st,(3890,100),"<strong>L1 DOMAIN LANDSCAPE · v3 / BP ES v14</strong>",width=7550,font=48)
    text(st,(3890,200),"DEMO METODY · všech 147 business událostí v 20 oblastech · v příběhu předpokládaná business akceptace",width=7600,font=23)
    text(st,(3890,305),"Oranžově = jedna primární událost. Pod ní = business význam a odkaz na BP. CES boundary je vysvětlen v levém sloupci. Řazení neznamená procesní tok.",width=7600,font=19)
    text(st,(12300,100),"<strong>51 VĚCNÝCH P/D VAZEB</strong>",width=6000,font=39)
    text(st,(12300,220),"Samostatný referenční zoom: každý konektor má svůj původní význam. P = předpoklad; D = podmíněný důsledek.",width=6100,font=20)
def refshape(st,z,xp,yp):
    url="https://miro.com/app/board/"+BOARD+"/?moveToWidget="+oid(st["map"][oid(z)])
    content="<p><a href=\""+url+"\">"+clean(txt(z))+"</a></p>"
    return create(st,"shape",(xp,yp),content,width=1700,height=230,
           style={"fillColor":"#f2f2f2","fillOpacity":"1","borderColor":"#aeb6ba","borderWidth":"1",
                  "borderOpacity":"1","borderStyle":"normal","fontFamily":"open_sans","fontSize":"19",
                  "color":"#26353a","textAlign":"center","textAlignVertical":"middle"})
def relation(st,i,e):
    by={oid(z):z for z in st["source"]["notes"]}
    a=by[edge(e,"startItem")];b=by[edge(e,"endItem")]
    yy=650+i*375
    left=refshape(st,a,REF_XA,yy)
    right=refshape(st,b,REF_XB,yy)
    # show domains as analytical attribution, without imposing dependencies.
    ac=st["domain"][oid(a)];bc=st["domain"][oid(b)]
    text(st,((REF_XA+REF_XB)/2,yy-143),
        "<strong>"+f"R{i+1:02d} · "+clean(ac+" → "+bc)+"</strong>",width=3500,font=18,
        style={"textAlign":"center","color":"#596671"})
    matches=[q for q in st["links"] if edge(q,"startItem")==oid(left) and edge(q,"endItem")==oid(right)]
    if len(matches)>1:raise RuntimeError("RELATION_DUPLICATED")
    if matches:
        if matches[0].get("captions",[])!=e.get("captions",[]) or matches[0].get("shape")!="curved":
            raise RuntimeError("EXISTING_RELATION_SEMANTIC_DRIFT")
        return
    style={k:v for k,v in (e.get("style") or {}).items() if k in (
        "strokeColor","strokeWidth","strokeStyle","strokeCap","fontSize","color","textOrientation",
        "startStrokeCap","endStrokeCap")}
    p={"startItem":{"id":oid(left),"snapTo":"right"},
       "endItem":{"id":oid(right),"snapTo":"left"},
       "shape":"curved","captions":e.get("captions",[])}
    if style:p["style"]=style
    z=request("POST","connectors",p)
    if not oid(z):raise RuntimeError("LINK_RETURNED_NO_ID")
    st["links"].append(z)
    st["created_links"]+=1
    if i%10==0:print("L1V3_EDGE_PROGRESS",i+1,flush=True)
def revalidate(s,st,mode):
    allitems=listing("items")
    con=listing("connectors")
    expected_ids={oid(z) for z in st["source"]["notes"]}
    protected=[z for z in allitems if parent(z) in (
        oid(s["bp"]),oid(s["v2"]),oid(s["tm"]))]
    if {ident(z) for z in protected}!=s["protected"]:raise RuntimeError("SOURCE_TEMPLATE_MUTATED")
    eprot=[z for z in con if edge(z,"startItem") in expected_ids and edge(z,"endItem") in expected_ids]
    if {esig(z) for z in eprot}!=s["edprotected"]:raise RuntimeError("PROTECTED_BP_CONNECTORS_MUTATED")
    target=[z for z in allitems if parent(z)==oid(st["frame"])]
    cards=[z for z in target if z.get("type")=="sticky_note"]
    ids={oid(z) for z in target}
    links=[z for z in con if edge(z,"startItem") in ids and edge(z,"endItem") in ids]
    ex=(len(s["events"]["A1"]),1) if mode=="pilot" else (147,51)
    if len(cards)!=ex[0] or len(links)!=ex[1]:raise RuntimeError("L1V3_TARGET_COUNTS_"+str((len(cards),len(links))))
    if mode=="apply":
        original=collections.Counter(txt(z) for z in s["notes"])
        new=collections.Counter(txt(z) for z in cards)
        if new!=original or sum(len(s["events"][c]) for c in RULES["codes"])!=147:raise RuntimeError("EVENT_147_TEXT_MISMATCH")
        domain_count={c:0 for c in RULES["codes"]}
        for z in s["notes"]:domain_count[st["domain"][oid(z)]]+=1
        if any(not domain_count[c] for c in RULES["codes"]):raise RuntimeError("EMPTY_DOMAIN_AFTER_MAPPING")
        if any(z.get("shape")!="curved" for z in links):raise RuntimeError("NATIVE_CONNECTOR_MISMATCH")
        textitems=[z for z in target if z.get("type")=="text"]
        if len(textitems)!=147+5+51:raise RuntimeError("DESCRIPTION_OR_REFERENCE_TEXT_MISSING")
        if len([z for z in target if z.get("type")=="shape"])!=40+102:raise RuntimeError("DOMAIN_OR_REFERENCE_SHAPES_MISSING")
        print("L1V3_VALIDATION_PASS","primary",len(cards),"descriptions",len(textitems)-55,
              "domain_rows",len(domain_count),"links",len(links),"source_protected",True,
              "items_total",len(target),flush=True)
    else:
        print("L1V3_PILOT_READBACK_PASS","primary",len(cards),"native_links",len(links),"source_protected",True,flush=True)
    print("L1V3_FRAME_URL https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget="+oid(st["frame"]),flush=True)
    print("VISUAL_ACCEPTANCE_OPEN",flush=True)
def main():
    s=source()
    rows,H=geometry(s)
    out=s["target"]
    print("L1V3_PLAN","mode",MODE,"target_present",bool(out),"events",147,"domains",20,
          "relations",51,"width",W,"height",H,flush=True)
    if MODE=="audit":print("AUDIT_ONLY_NO_WRITES");return
    if not out:
        right=max(x(z)+wd(z)/2 for z in s["frames"])
        out=request("POST","frames",{"data":{"title":TITLE},"style":{"fillColor":"#ffffff"},
            "geometry":{"width":W,"height":H},
            "position":{"x":right+2100+W/2,"y":H/2+600,"origin":"center"}})
        if not oid(out):raise RuntimeError("NEW_FRAME_ID_MISSING")
        print("L1V3_FRAME_CREATED",flush=True)
    st={"frame":out,"rows":rows,"source":s,"items":[z for z in s["obj"] if parent(z)==oid(out)],
        "links":[z for z in s["conn"] if
                 edge(z,"startItem") in {oid(k) for k in s["obj"] if parent(k)==oid(out)} and
                 edge(z,"endItem") in {oid(k) for k in s["obj"] if parent(k)==oid(out)}],
        "created":0,"created_links":0,"map":{},
        "domain":{oid(z):c for c,v in s["events"].items() for z in v}}
    head(st)
    doms=["A1"] if MODE=="pilot" else RULES["codes"]
    for c in doms:dom(st,c)
    if MODE=="pilot":
        # References can link to the first pilot event on each side.
        ev=s["events"]["A1"][0]
        fake= {"startItem":{"id":oid(ev)},"endItem":{"id":oid(ev)},
               "style":{"strokeColor":"#111111","strokeWidth":"2"},
               "shape":"curved","captions":[]}
        relation(st,0,fake)
    else:
        for i,z in enumerate(s["links"]):relation(st,i,z)
    revalidate(s,st,MODE)
if __name__=="__main__":
    try:main()
    except Exception as e:print("L1V3_STOP",type(e).__name__,str(e));sys.exit(1)

