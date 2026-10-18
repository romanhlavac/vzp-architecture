#!/usr/bin/env python3
"""CES-1A visual-only consistency with native S0 shape typography (Miro REST v2).

Operating modes: audit, pilot (B1 only), apply (other 19 domains + 17 labels).
No business facts, orange events, connectors, shapes, references or IDs logged.
No deletions. S0 is never modified.
"""
import os,sys,re,html,collections
from ces1a_branch_approved import call,page,id,xx,yy,ww,hh,close,txt,tag,CODES

MODE=os.getenv("CES_TYPO_MODE","audit")
if MODE not in ("audit","pilot","apply"):raise SystemExit("Invalid mode")
BLUE={"S0","B1","B2","B3","B6","B8","B9"}
CAPTIONS={c:3 for c in BLUE}
CAPTIONS["B8"]=2
SCENARIO_X=1334
FONT_KEYS=("fontFamily","fontSize","color","textAlign","textAlignVertical")
TOKENS=re.compile(
    r"Rozsah:|Aktéři\s*/\s*odpovědnost:|BOUNDARY RATIONALE(?:\s*·\s*DEMO\s*/\s*K BUSINESS VALIDACI)?"
    r"|Pravidla\s*·\s*H\d{2}(?:/H?\d{2})*"
    r"|Životní cyklus\s*·\s*H\d{2}(?:/H?\d{2})*"
    r"|Využití\s*·\s*H\d{2}(?:/H?\d{2})*"
    r"|Odpovědnost\s*·\s*H\d{2}(?:/H?\d{2})*"
    r"|Zdroje?:",re.I)
def norm(s):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",str(s or "")))).strip()
def content(o):return str((o.get("data") or {}).get("content") or "")
def fetch(o):
    return call("GET",{"shape":"shapes/","text":"texts/"}[o["type"]]+id(o))
def snapshot():
    frames=page("items",{"type":"frame"})
    f=[z for z in frames if close(ww(z),6075,25) and close(hh(z),12238,25)]
    if len(f)!=1:raise RuntimeError("1A frame changed")
    frame=f[0]
    items=page("items",{"parent_item_id":id(frame)})
    shapes={}
    for z in items:
        if z.get("type")!="shape" or "Aktéři" not in txt(z) or tag(z) not in CODES:continue
        if not any(close(hh(z),h,7) for h in (224,480,680)):continue
        code=tag(z)
        if code in shapes:raise RuntimeError("Duplicate domain")
        shapes[code]=z
    if set(shapes)!=set(CODES):raise RuntimeError("Domain inventory mismatch")
    n=sum(z.get("type")=="sticky_note" for z in items)
    if n!=131:raise RuntimeError("131 events baseline changed")
    ids={id(z) for z in items}
    con=[z for z in page("connectors") if
         str((z.get("startItem") or {}).get("id")) in ids and
         str((z.get("endItem") or {}).get("id")) in ids]
    if len(con)!=51:raise RuntimeError("51 connector baseline changed")
    if any((z.get("style") or {}).get("strokeColor")!="#000000" for z in con):
        raise RuntimeError("ES arrows no longer uniformly black")
    labels={}
    for c,n in CAPTIONS.items():
        dom=shapes[c]
        subset=sorted([z for z in items
            if z.get("type")=="text" and close(xx(z),SCENARIO_X,8)
            and close(ww(z),305,8) and abs(yy(z)-yy(dom))<hh(dom)/2+15],key=yy)
        if len(subset)!=n:raise RuntimeError("Scenario count mismatch "+c)
        labels[c]=subset
    return frame,items,shapes,labels
def html_sections(d):
    src=norm(content(d))
    found=list(TOKENS.finditer(src))
    if len(found)<3 or found[0].group().lower()!="rozsah:":
        raise RuntimeError("Unknown domain content structure")
    before=src[:found[0].start()].strip()
    if not before:raise RuntimeError("Missing domain heading")
    parts=["<p><strong>"+html.escape(before)+"</strong></p>"]
    for i,m in enumerate(found):
        end=found[i+1].start() if i+1<len(found) else len(src)
        t=src[m.end():end].strip()
        key=m.group()
        if t:
            parts.append("<p><strong>"+html.escape(key)+"</strong> "+html.escape(t)+"</p>")
        else:
            parts.append("<p><strong>"+html.escape(key)+"</strong></p>")
    out="".join(parts)
    if norm(out)!=src:
        raise RuntimeError("Content preservation violated")
    # Demand the same rich-text paragraph/strong structure already used by S0.
    return out,len(parts)
def targetstyle(reference):
    x=reference.get("style") or {}
    if any(not x.get(k) for k in FONT_KEYS):
        raise RuntimeError("S0 formatting is incomplete")
    return {k:x[k] for k in FONT_KEYS}
def consistent(d,reference):
    st=d.get("style") or {}
    expected=targetstyle(reference)
    return all(str(st.get(k)).lower()==str(v).lower() for k,v in expected.items())
def isrich(d):
    t=content(d).lower()
    return "<p" in t and ("<strong" in t or "<b>" in t)
def audit():
    frame,items,domains,captions=snapshot()
    ref=fetch(domains["S0"])
    expected=targetstyle(ref)
    print("S0_REFERENCE_STYLE",expected)
    plan={}
    for code in CODES:
        d=fetch(domains[code])
        if code!="S0":
            markup,sections=html_sections(d)
            plan[code]=(len(markup),sections,isrich(d),consistent(d,ref))
    print("DOMAINS_TOBE_FIXED",sum(not (p[2] and p[3]) for p in plan.values()))
    print("FORMAT_PARSE",[(k,v[1],v[2],v[3]) for k,v in plan.items()])
    diff=[]
    for code in CAPTIONS:
        for t in captions[code]:
            if code=="S0":continue
            style=t.get("style") or {}
            match=all(str(style.get(k)).lower()==str(ref.get("style",{}).get(k)).lower()
                      for k in ("fontFamily","fontSize","color","textAlign"))
            if not match:diff.append(code)
    print("SCENARIO_LABELS_NEED_STYLE",len(diff))
    return frame,domains,captions,ref
def update_domain(d,ref):
    current=fetch(d)
    htmltext,_=html_sections(current)
    old_plain=norm(content(current))
    old_style=current.get("style") or {}
    font=targetstyle(ref)
    if isrich(current) and consistent(current,ref):return False
    baseline={k:old_style.get(k) for k in
              ("fillColor","borderColor","borderWidth","borderStyle","fillOpacity","borderOpacity")}
    call("PATCH","shapes/"+id(current),{
        "data":{"content":htmltext},
        "style":font
    })
    updated=fetch(current)
    if norm(content(updated))!=old_plain:raise RuntimeError("Domain content readback drift")
    if not consistent(updated,ref):raise RuntimeError("Domain S0 style mismatch")
    if any((updated.get("style") or {}).get(k)!=v for k,v in baseline.items()):
        raise RuntimeError("Domain fill/border style changed")
    if not close(ww(updated),ww(current),2) or not close(hh(updated),hh(current),2):
        raise RuntimeError("Domain dimensions changed")
    return True
def update_caption(text,ref):
    old=fetch(text)
    orig=norm(content(old))
    st=old.get("style") or {}
    target={k:(ref.get("style") or {})[k] for k in
            ("fontFamily","fontSize","color","textAlign")}
    if all(str(st.get(k)).lower()==str(v).lower() for k,v in target.items()):
        return False
    call("PATCH","texts/"+id(old),{"style":target})
    after=fetch(old)
    if norm(content(after))!=orig:raise RuntimeError("Caption text changed")
    if any(str((after.get("style") or {}).get(k)).lower()!=str(v).lower() for k,v in target.items()):
        raise RuntimeError("Caption font style readback mismatch")
    if not close(xx(after),xx(old),2) or not close(yy(after),yy(old),2) or not close(ww(after),ww(old),2):
        raise RuntimeError("Caption geometry changed")
    return True
def apply(pilot):
    f,domains,captions,ref=audit()
    target_codes=["B1"] if pilot else [c for c in CODES if c!="S0"]
    changed=0
    for c in target_codes:
        changed+=int(update_domain(domains[c],ref))
    clabels=["B1"] if pilot else [c for c in CAPTIONS if c!="S0"]
    updated_labels=0
    for c in clabels:
        for z in captions[c]:updated_labels+=int(update_caption(z,ref))
    f2,dom2,cap2,r=audit()
    for c in target_codes:
        d=fetch(dom2[c])
        if not isrich(d) or not consistent(d,r):
            raise RuntimeError("Domain typography acceptance "+c)
    for c in clabels:
        for item in cap2[c]:
            style=fetch(item).get("style") or {}
            if any(str(style.get(k)).lower()!=str((r.get("style") or {}).get(k)).lower()
                   for k in ("fontFamily","fontSize","color","textAlign")):
                raise RuntimeError("Scenario label style acceptance "+c)
    print("TYPOGRAPHY REST PASS: corrected domains",changed,"scenario labels",updated_labels)
    print("MODEL PRESERVED: 131 native events, 51 black connectors")
try:
    if MODE=="audit":
        audit()
        print("AUDIT ONLY")
    else:apply(MODE=="pilot")
except Exception as e:
    print("FAIL:",str(e))
    sys.exit(1)
