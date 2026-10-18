#!/usr/bin/env python3
"""Normalize 1A boundary rationale composition and scenario captions via REST.

Never modifies orange event cards, domain semantics, connectors or domain bounds.
Live Miro business text is read at runtime; no board content or IDs go to logs.
Modes: audit, pilot (B1), apply (all remaining).
"""
import os,sys,re,html,textwrap
from ces1a_branch_approved import call,page,id,xx,yy,ww,hh,close,txt,tag,edge
from ces1a_branch_resume import oldY
from ces1a_branch_approved import CODES,HEIGHTS,LANES,BRANCH_LABELS,scenecenter

MODE=os.environ.get("CES_LAYOUT_MODE","audit")
if MODE not in ("audit","pilot","apply"):raise SystemExit("invalid mode")
TARGET_CODES=[c for c in CODES if c!="S0"]
SCENARIO={
"B1":["Vznik pojištění","Změny pojištění","Ukončení"],
"B2":["Povinnost","Platby a saldo","Vymáhání"],
"B3":["Nová smlouva","Změna / dodatek","Ukončení"],
"B6":["Vyřízení podání","Změna údajů","Reklamace"],
"B8":["Nárok EU","Refundace"],
"B9":["CRP","Kapitační agenda","Přerozdělení"]
}
BLUE=("S0","B1","B2","B3","B6","B8","B9")
WIDTH_LIMIT={"blue":79,"grey":98}
def norm(s):
    s=html.unescape(re.sub(r"<[^>]+>"," ",str(s or "")))
    return re.sub(r"\s+"," ",s).strip()
def plain(o):return norm((o.get("data") or {}).get("content") or "")
def par(o):return str((o.get("parent") or {}).get("id") or "")
def detail(o):
    path={"shape":"shapes/","text":"texts/","sticky_note":"sticky_notes/"}[o["type"]]
    return call("GET",path+id(o))
def find():
    fs=page("items",{"type":"frame"})
    frames=[z for z in fs if close(ww(z),6075,25) and close(hh(z),12238,25)]
    if len(frames)!=1:raise RuntimeError("CES-1A frame geometry changed")
    f=call("GET","frames/"+id(frames[0]))
    ch=page("items",{"parent_item_id":id(f)})
    domain={}
    for z in ch:
        if z.get("type")!="shape" or not(ww(z)>2900) or "Aktéři" not in plain(z):continue
        code=tag(z)
        if code not in CODES:continue
        if code in domain:raise RuntimeError("ambiguous domain band "+code)
        domain[code]=z
    if len(domain)!=20:raise RuntimeError("expected twenty domain bands")
    notes=[z for z in ch if z.get("type")=="sticky_note"]
    if len(notes)!=131:raise RuntimeError("ES event inventory not 131")
    cons=page("connectors")
    ids={id(z) for z in ch}
    intra=[z for z in cons if str((z.get("startItem") or {}).get("id")) in ids and
           str((z.get("endItem") or {}).get("id")) in ids]
    if len(intra)!=51:raise RuntimeError("existing connector count drift")
    if any(str((z.get("style") or {}).get("strokeColor") or "").lower()!="#000000" for z in intra):
        raise RuntimeError("non-black ES arrows")
    rationale={}
    for c,d in domain.items():
        candidates=[z for z in ch if z.get("type")=="shape" and
                   "BOUNDARY RATIONALE" in plain(z).upper() and close(yy(z),yy(d),45)]
        if len(candidates)!=1:raise RuntimeError("rationale ambiguous "+c)
        rationale[c]=candidates[0]
    if id(rationale["S0"])!=id(domain["S0"]):raise RuntimeError("S0 unified reference absent")
    return f,ch,domain,rationale
def make_content(dom,rat,code):
    # Full fidelity: preserve exactly all words from both existing boxes,
    # only reflow whitespace and soft visual line breaks.
    before=plain(dom);why=plain(rat)
    merged=before+" "+why
    cols=WIDTH_LIMIT["blue" if code in BLUE else "grey"]
    parts=[]
    for index,part in enumerate((before,why)):
        pieces=textwrap.wrap(part,width=cols,break_long_words=False,
                break_on_hyphens=False,replace_whitespace=True,drop_whitespace=True)
        if not pieces:raise RuntimeError("missing domain or rationale text")
        parts.extend(pieces)
        if index==0:parts.append("")
    lines=len(parts)
    htmltext="<br/>".join(html.escape(t) for t in parts)
    if norm(htmltext)!=norm(merged):
        raise RuntimeError("unified content textual fidelity failed")
    # Native element has original font 18. Compact columns: avoid event rail.
    return htmltext,lines
def safe_reconcile_reason(dom,rat,code):
    if id(dom)==id(rat):
        return False
    old=detail(dom);why=detail(rat)
    content,lines=make_content(old,why,code)
    if code in BLUE and lines>31:raise RuntimeError("blue content cannot fit "+code)
    if code not in BLUE and lines>12:raise RuntimeError("grey content cannot fit "+code)
    patch={"data":{"content":content}}
    call("PATCH","shapes/"+id(old),patch)
    now=call("GET","shapes/"+id(old))
    if norm((now.get("data") or {}).get("content")) != norm(plain(old)+" "+plain(why)):
        raise RuntimeError("merged text verification failed")
    if not close(ww(now),ww(old),2) or not close(hh(now),hh(old),2):
        raise RuntimeError("domain geometry modified")
    fresh=call("GET","shapes/"+id(why))
    if plain(fresh)!=plain(why):raise RuntimeError("source rationale changed while merging")
    call("DELETE","shapes/"+id(why))
    return True
def rowlabels(ch,c):
    y0=oldY[c]
    labels=[]
    for i in range(len(BRANCH_LABELS[c])):
        y=scenecenter(c,i,y0)
        candidates=[z for z in ch if z.get("type")=="text" and close(yy(z),y,26) and
                    600<xx(z)<1500 and ww(z)<=920]
        if len(candidates)!=1:
            raise RuntimeError("scenario caption at row "+c+" branch "+str(i)+" ambiguous: "+str(len(candidates)))
        labels.append(candidates[0])
    return labels
def clone_short_label(frame,old,newtext):
    # Use S0's compact width and x-alignment. Creation precedes deletion.
    x,y=1334,yy(old)
    data={"data":{"content":"<b>"+html.escape(newtext)+"</b>"},
          "geometry":{"width":305},
          "position":{"x":x,"y":y,"origin":"center"},
          "style":{"color":"#26353A","fontFamily":"open_sans",
                   "fontSize":"18","textAlign":"center"},
          "parent":{"id":id(frame)}}
    created=call("POST","texts",data)
    if not created.get("id"):raise RuntimeError("short caption creation failed")
    fresh=call("GET","texts/"+id(created))
    if plain(fresh)!=newtext or not close(xx(fresh),x,3) or not close(yy(fresh),y,3) or
       not close(ww(fresh),305,5) or par(fresh)!=id(frame):
        raise RuntimeError("short caption readback failed")
    call("DELETE","texts/"+id(old))
    return True
def preflight():
    frame,ch,dom,why=find()
    code_size={}
    for code in CODES:
        if code=="S0":continue
        if id(dom[code])==id(why[code]):continue
        content,lines=make_content(detail(dom[code]),detail(why[code]),code)
        code_size[code]=lines
    cap={}
    for code in SCENARIO:
        cap[code]=len(rowlabels(ch,code))
    print("PREFLIGHT PASS: 20 domain shapes, 131 events, 51 black connectors")
    print("SEPARATE_BOUNDARY_BOXES:",len(code_size),"MERGE_ESTIMATED_LINES:",code_size)
    print("CES_SCENARIO_CAPTIONS:",cap)
    return frame,ch,dom,why
def execute(pilot):
    frame,ch,domain,rationale=preflight()
    codes=["B1"] if pilot else TARGET_CODES
    changed=0
    for code in codes:
        if id(domain[code])!=id(rationale[code]):
            if safe_reconcile_reason(domain[code],rationale[code],code):changed+=1
    labels=0
    for c in (["B1"] if pilot else list(SCENARIO)):
        # After the merge, the original captions are unchanged in this same
        # run; re-read each caption to prevent races.
        current=page("items",{"parent_item_id":id(frame)})
        for obj,text in zip(rowlabels(current,c),SCENARIO[c]):
            old=detail(obj)
            if close(xx(old),1334,6) and close(ww(old),305,6) and plain(old)==text:
                continue
            clone_short_label(frame,old,text)
            labels+=1
    # Structural audit: no source rationale duplicates after migration, all
    # domains preserve codes and full text, no event/connector modifications.
    fr,ch,dom,rat=find()
    for code in codes:
        if id(dom[code])!=id(rat[code]):
            raise RuntimeError("remaining standalone rationale "+code)
    for c in (["B1"] if pilot else list(SCENARIO)):
        for item,text in zip(rowlabels(ch,c),SCENARIO[c]):
            if plain(item)!=text or not close(xx(item),1334,6) or
               not close(ww(item),305,6):
                raise RuntimeError("caption acceptance failed "+c)
    print("LIVE LAYOUT REST PASS: domain rationale merged",changed,"compact captions",labels)
    print("UNMODIFIED MODEL PASS: 131 event cards and 51 black connectors")
try:
    if MODE=="audit":preflight();print("READ ONLY: no changes")
    else:execute(MODE=="pilot")
except Exception as e:
    print("FAIL:",str(e));sys.exit(1)
