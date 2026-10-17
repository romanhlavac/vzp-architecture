#!/usr/bin/env python3
"""Bezpečné obnovení vrstev událostí CES-1A; bez výpisu klientských údajů."""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

token=os.environ.get("MIRO_DIAGNOSTIC_TOKEN","").strip()
board=os.environ.get("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
mode=os.environ.get("REZIM","pilot").strip()
if not token or not board or mode not in {"pilot","udalosti","spojnice","kontrola"}:
    raise SystemExit("CHYBA: neplatná konfigurace.")
base="https://api.miro.com/v2/boards/"+urllib.parse.quote(board,safe="")+"/"
codes={"B7","B8","B9","C1","D1","D2","D3","D4","D5","D6"}

def request(method,path,payload=None,params=None):
    url=base+path+(("?" + urllib.parse.urlencode(params)) if params else "")
    data=json.dumps(payload,ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers={"Accept":"application/json","Authorization":"Bearer "+token}
    if data is not None:headers["Content-Type"]="application/json"
    for retry in range(6):
        try:
            req=urllib.request.Request(url,headers=headers,data=data,method=method)
            with urllib.request.urlopen(req,timeout=30) as res:
                raw=res.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and retry<5:
                time.sleep(min(30,2**retry+1));continue
            raise RuntimeError("Miro API: HTTP "+str(e.code)+" při operaci "+method+".") from None
        except Exception:
            raise RuntimeError("Volání Miro API se nezdařilo.") from None

def listing(path,params=None):
    result=[]; cursor=None
    for _ in range(30):
        q=dict(params or {});q["limit"]=50
        if cursor:q["cursor"]=cursor
        res=request("GET",path,params=q);result+=res.get("data",[])
        cursor=res.get("cursor")
        if not cursor:return result
    raise RuntimeError("Neočekávané stránkování.")

def wh(o):
    d=o.get("geometry") or {}
    return float(d.get("width") or 0),float(d.get("height") or 0)

def pos(o):
    p=o.get("position") or {}
    return float(p.get("x") or 0),float(p.get("y") or 0)

def domain_code(o):
    z=html.unescape(re.sub("<[^>]+>"," ",str((o.get("data") or {}).get("content") or "")))
    match=re.search(r"(?:^|\\s)([A-D][1-9]|S0)\\s*[·.]",z)
    return match.group(1) if match and "Aktéři" in z else None

def discover():
    fs=listing("items",{"type":"frame"})
    frame=[x for x in fs if abs(wh(x)[0]-6075)<20 and abs(wh(x)[1]-7746)<20]
    if len(frame)!=1:raise RuntimeError("Cílový rámec není jednoznačný.")
    fid=str(frame[0]["id"])
    children=listing("items",{"parent_item_id":fid})
    dom={domain_code(d):d for d in children if d.get("type")=="shape" and domain_code(d)}
    notes=[x for x in children if x.get("type")=="sticky_note"]
    if len(dom)!=20 or len(notes)!=130 or any(k not in dom for k in codes):
        raise RuntimeError("Inventura domén/událostí nesouhlasí; žádný zápis.")
    if any(x.get("type")=="divider" for x in children):
        raise RuntimeError("Nalezeny neočekávané separátory.")
    return fid,children,dom,notes

def per_row(dom,notes):
    result={}
    for code in codes:
        d=dom[code];y=pos(d)[1]
        matches=[x for x in notes if abs(pos(x)[1]-y)<=35]
        if len(matches) not in (4,6,8):raise RuntimeError("Neznámý počet událostí v řádku.")
        result[code]=sorted(matches,key=lambda n:(pos(n)[0],str(n["id"])))
    if sum(len(v) for v in result.values())!=58:raise RuntimeError("Čekáno právě 58 událostí.")
    return result

def outdated(dom,notes):
    rows=per_row(dom,notes)
    return [(c,n) for c in sorted(codes) for n in rows[c]
            if str(n.get("createdAt",""))<str(dom[c].get("createdAt",""))]

def all_connectors():
    return listing("connectors")

def core_note(o):
    return (o.get("data"),o.get("style"),str((o.get("parent") or {}).get("id")),pos(o),wh(o))

def same_note(a,b):
    data_a,style_a,parent_a,pa,ga=core_note(a)
    data_b,style_b,parent_b,pb,gb=core_note(b)
    return (data_a==data_b and style_a==style_b and parent_a==parent_b
            and max(abs(pa[0]-pb[0]),abs(pa[1]-pb[1]))<2
            and max(abs(ga[0]-gb[0]),abs(ga[1]-gb[1]))<3)

def clone_one(n,fid,notes,cons):
    old=request("GET","sticky_notes/"+str(n["id"]))
    if old.get("type")!="sticky_note" or str((old.get("parent") or {}).get("id"))!=fid:
        raise RuntimeError("Zdrojová událost se změnila.")
    if old.get("tagIds") or old.get("groupId") or old.get("locked"):
        raise RuntimeError("Událost má nepodporované asociace.")
    if set((old.get("links") or {}).keys())-{"self"}:
        raise RuntimeError("Událost má další externí odkazy.")
    originals=[x for x in notes if x["id"]!=old["id"] and
               abs(pos(x)[0]-pos(old)[0])<2 and abs(pos(x)[1]-pos(old)[1])<2]
    if len(originals)>1:raise RuntimeError("Nejednoznačná náhradní událost.")
    if originals:
        dest=request("GET","sticky_notes/"+str(originals[0]["id"]))
        if not same_note(old,dest):raise RuntimeError("Náhradní událost není shodná.")
    else:
        made=request("POST","sticky_notes",{
            "data":old["data"],
            "style":old["style"],
            "geometry":{"width":wh(old)[0]},
            "position":{"x":pos(old)[0],"y":pos(old)[1],"origin":"center"},
            "parent":{"id":fid}
        })
        dest=request("GET","sticky_notes/"+str(made["id"]))
        if not same_note(old,dest):
            raise RuntimeError("Nová událost neodpovídá originálu; originál zachován.")
    oldid=str(old["id"]);newid=str(dest["id"])
    touched=0
    for index,c in enumerate(cons):
        names=[name for name in ("startItem","endItem")
               if str((c.get(name) or {}).get("id"))==oldid]
        if not names:continue
        fresh=request("GET","connectors/"+str(c["id"]))
        update={name:{"id":newid,"snapTo":"auto"} for name in names}
        before_style=fresh.get("style");before_shape=fresh.get("shape")
        request("PATCH","connectors/"+str(c["id"]),update)
        changed=request("GET","connectors/"+str(c["id"]))
        if any(str((changed.get(name) or {}).get("id"))!=newid for name in names):
            raise RuntimeError("Připojení konektoru se nepodařilo obnovit.")
        if changed.get("style")!=before_style or changed.get("shape")!=before_shape:
            raise RuntimeError("Při obnově konektoru došlo ke změně typu nebo stylu.")
        cons[index]=changed
        touched+=1
    request("DELETE","sticky_notes/"+oldid)
    if request("GET","sticky_notes/"+newid).get("type")!="sticky_note":
        raise RuntimeError("Náhradní událost po odstranění originálu chybí.")
    return touched

def replace_notes(pilot):
    fid,items,dom,notes=discover()
    bad=outdated(dom,notes)
    expected=58 if pilot else None
    if pilot and len(bad)!=expected and len(bad)!=57:
        raise RuntimeError("Nečekaný počet zakrytých událostí.")
    if pilot and len(bad)==57:
        print("PILOT: jedna událost již byla přesunuta do přední vrstvy.")
        return
    if not pilot and not bad:
        print("UDÁLOSTI: všechny již jsou nad doménovými pásy.")
        return
    conns=all_connectors()
    processed=0;relinked=0
    work=sorted(bad,key=lambda t:(t[0],pos(t[1])[0]))
    if pilot:work=work[:1]
    for code,n in work:
        touched=clone_one(n,fid,notes,conns)
        processed+=1;relinked+=touched
    _,_,new_dom,new_notes=discover()
    remaining=len(outdated(new_dom,new_notes))
    if remaining!=len(bad)-processed:
        raise RuntimeError("Počet zbývajících překrytých událostí neodpovídá.")
    print("OBNOVA UDÁLOSTÍ: provedeno",processed,"aktualizovaných spojení",relinked,"zbývá",remaining)

def replace_lines():
    fid,items,dom,notes=discover()
    if outdated(dom,notes):raise RuntimeError("Nejdříve obnovit všechny události.")
    target_ids={str(n["id"]) for n in notes if any(
        abs(pos(n)[1]-pos(dom[c])[1])<35 and str(n.get("createdAt",""))>str(dom[c].get("createdAt",""))
        for c in codes)}
    if len(target_ids)!=58:raise RuntimeError("Přesunuto méně než 58 událostí.")
    cons=all_connectors()
    affected=[c for c in cons if (
        str((c.get("startItem") or {}).get("id")) in target_ids or
        str((c.get("endItem") or {}).get("id")) in target_ids)
        and str(c.get("createdAt",""))<max(str(dom[cod].get("createdAt","")) for cod in codes)]
    if len(affected)>11:raise RuntimeError("Neočekávaný počet propojení.")
    changed=0
    for c in affected:
        old=request("GET","connectors/"+str(c["id"]))
        payload={
            "startItem":{"id":str((old.get("startItem") or {})["id"]),"snapTo":"auto"},
            "endItem":{"id":str((old.get("endItem") or {})["id"]),"snapTo":"auto"},
            "shape":old.get("shape") or "straight",
            "style":old.get("style") or {}
        }
        if old.get("captions"):payload["captions"]=old["captions"]
        added=request("POST","connectors",payload)
        new=request("GET","connectors/"+str(added["id"]))
        if any(str((new.get(k) or {}).get("id"))!=str((old.get(k) or {}).get("id")) for k in ("startItem","endItem")) or
            new.get("shape")!=old.get("shape") or new.get("style")!=old.get("style"):
            raise RuntimeError("Nový konektor nesouhlasí; originál zachován.")
        request("DELETE","connectors/"+str(old["id"]))
        changed+=1
    print("OBNOVA SPOJNIC: obnoveno",changed)

def final():
    fid,items,dom,notes=discover()
    if outdated(dom,notes):raise RuntimeError("Stále existují zakryté události.")
    member={str(x["id"]) for x in items}
    cons=[c for c in all_connectors() if str((c.get("startItem") or {}).get("id")) in member
          and str((c.get("endItem") or {}).get("id")) in member]
    if len(cons)!=34:raise RuntimeError("Počet interních spojnic se změnil.")
    black=sum(1 for c in cons if (c.get("style") or {}).get("strokeColor")=="#000000"
              and (c.get("style") or {}).get("strokeStyle")=="normal")
    brown=sum(1 for c in cons if (c.get("style") or {}).get("strokeColor")=="#9b642f")
    if (black,brown)!=(7,27):raise RuntimeError("Styly spojnic neodpovídají.")
    print("FINÁLNÍ PASS: 130 událostí nad pásy, 20 domén, 34 spojnic (7 černých, 27 hnědých).")

try:
    if mode=="pilot":replace_notes(True)
    elif mode=="udalosti":replace_notes(False)
    elif mode=="spojnice":replace_lines()
    elif mode=="kontrola":final()
except Exception as exc:
    print("CHYBA:",str(exc) if isinstance(exc,RuntimeError) else "Neočekávaná chyba, operace zastavena.")
    sys.exit(1)
