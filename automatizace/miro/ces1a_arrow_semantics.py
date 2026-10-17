#!/usr/bin/env python3
"""VZP 1A Event Storming: arrow semantics, chronology and local scenario links.

Uses existing GitHub Environment OAuth token and Miro REST v2 ONLY.
No client event text, board ID, token, person names or API bodies in logs.
The initial Event Storming cards stay business events without domain prefixes.
Rows are a later DEMO interpretation, not a causal/domain identity.
"""
import hashlib, html, json, math, os, re, sys, time
import urllib.parse, urllib.request, urllib.error

TOKEN=os.getenv("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.getenv("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
MODE=os.getenv("MIRO_ARROW_MODE","audit")
if not TOKEN or not BOARD or MODE not in ("audit","apply"):
    sys.exit("FAIL: missing OAuth or invalid mode")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")
INK="#000000"
ROW_COUNT=20
EXPECTED_COUNTS=[4,6,6,8,8,8,8,8,8,8,6,6,8,6,6,4,6,6,4,6]
RELATED=(3,4,5,6,9,11,12)
# All pairs are 1-based column positions in a DEMO row, NOT domain identifiers.
# Their intended business meaning is recorded in 1A analysis, outside the public repository.
LINKS={
 3:[(1,2),(2,3),(4,5),(5,6),(7,8)],
 4:[(3,4),(6,7)],
 5:[(4,5),(5,6),(6,7),(7,8)],
 6:[(3,4),(4,5)],
 9:[(4,5),(5,6)],
 11:[(2,3),(4,5),(5,6)],
 12:[(2,3),(7,8)],
}
# In S0, resolved identity ambiguity should precede correction of reference data.
# The two existing sticky notes are exchanged ONLY if their contents are exactly
# the expected unchanged DEMO events; no business names are stored in this repository.
SIG_AFTER=hashlib.sha256("Nejednoznačnost identity byla vyřešena".encode()).hexdigest()
SIG_BEFORE=hashlib.sha256("Referenční údaj byl opraven".encode()).hexdigest()
REMOVE_AMBIGUOUS=[((3,3),(4,4)),((4,3),(5,3)),((4,4),(5,5)),((6,6),(7,6))]
# Prior direct links above were read back from the demo and represent ambiguous
# leaps / unrelated outcomes. An independent analysis is in 1A_analysis.md.
CAPTIONS_REMOVE=True

def api(method,path,data=None,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    body=None if data is None else json.dumps(data,ensure_ascii=False).encode()
    hdr={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if body is not None:hdr["Content-Type"]="application/json"
    for t in range(4):
        try:
            req=urllib.request.Request(url,method=method,data=body,headers=hdr)
            with urllib.request.urlopen(req,timeout=35) as resp:
                raw=resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and t<3:
                time.sleep(2**t+1);continue
            raise RuntimeError(method+" "+path.split("/")[0]+" HTTP "+str(e.code)) from None
        except Exception:
            raise RuntimeError(method+" "+path.split("/")[0]+" unavailable") from None

def page(path,params=None,limit=70):
    found=[];cursor=None
    for _ in range(limit):
        p=dict(params or {},limit=50)
        if cursor:p["cursor"]=cursor
        obj=api("GET",path,params=p)
        found.extend(obj.get("data",[]))
        cursor=obj.get("cursor")
        if not cursor:return found
    raise RuntimeError("pagination incomplete")

def width(v):return float((v.get("geometry") or {}).get("width") or 0)
def height(v):return float((v.get("geometry") or {}).get("height") or 0)
def xy(v):
    p=v.get("position") or {}
    return float(p.get("x") or 0),float(p.get("y") or 0)
def close(a,b,eps=5):return abs(a-b)<=eps
def plain(v):
    t=str((v.get("data") or {}).get("content") or "")
    return html.unescape(re.sub(r"<[^>]+>","",t)).strip()
def sha(v):return hashlib.sha256(plain(v).encode()).hexdigest()
def endpoint(c,key):return str((c.get(key) or {}).get("id") or "")
def ident(v):return str(v["id"])
def conn_full(c):return api("GET","connectors/"+ident(c))

def discover():
    fr=[v for v in page("items",{"type":"frame"})
        if close(width(v),6075,20) and close(height(v),7746,20)]
    if len(fr)!=1:raise RuntimeError("1A frame not unique")
    frame=api("GET","frames/"+ident(fr[0]))
    ch=page("items",{"parent_item_id":ident(frame)})
    domains=sorted([v for v in ch if v.get("type")=="shape"
                    and close(height(v),224,5) and 2900<width(v)<4600],key=lambda z:xy(z)[1])
    if len(domains)!=ROW_COUNT:raise RuntimeError("domain band count drift")
    rows=[]
    for idx,d in enumerate(domains):
        y=xy(d)[1];x=xy(d)[0]
        events=sorted([v for v in ch if v.get("type")=="sticky_note"
                       and close(width(v),258,10) and close(height(v),168,12)
                       and close(xy(v)[1],y,40) and xy(v)[0]>(x-width(d)/2)+450],
                       key=lambda z:xy(z)[0])
        if len(events)!=EXPECTED_COUNTS[idx]:
            raise RuntimeError("event row inventory drift at row "+str(idx))
        rows.append([api("GET","sticky_notes/"+ident(v)) for v in events])
    evs={ident(v) for row in rows for v in row}
    if len(evs)!=130:raise RuntimeError("expected 130 distinct event cards")
    return frame,ch,rows,evs

def live_connectors(ev_ids):
    allc=page("connectors")
    matches=[]
    for c in allc:
        x=endpoint(c,"startItem");y=endpoint(c,"endItem")
        if x in ev_ids and y in ev_ids:matches.append(conn_full(c))
    return matches

def row_addr(rows):
    return {ident(v):(idx,j+1) for idx,row in enumerate(rows) for j,v in enumerate(row)}

def adjust_s0(rows):
    row=rows[3]
    a,b=row[5],row[6]
    if sha(a)==SIG_AFTER and sha(b)==SIG_BEFORE:return False
    if sha(a)!=SIG_BEFORE or sha(b)!=SIG_AFTER:
        raise RuntimeError("S0 temporal correction guard mismatch")
    xa,ya=xy(a);xb,yb=xy(b)
    api("PATCH","sticky_notes/"+ident(a),data={"position":{"x":xb,"y":yb,"origin":"center"}})
    api("PATCH","sticky_notes/"+ident(b),data={"position":{"x":xa,"y":ya,"origin":"center"}})
    aa=api("GET","sticky_notes/"+ident(a))
    bb=api("GET","sticky_notes/"+ident(b))
    if not(close(xy(aa)[0],xb,3) and close(xy(bb)[0],xa,3)):
        raise RuntimeError("S0 temporal swap readback mismatch")
    return True

def blacken(cs):
    updated=0
    for c in cs:
        old=c.get("style") or {}
        present=str(old.get("strokeColor") or "").lower()
        cap=c.get("captions") or []
        if present.lower()==INK.lower() and not cap and c.get("shape")=="curved":
            continue
        patch={"style":{"strokeColor":INK,"strokeWidth":2,"strokeStyle":"normal"},"shape":"curved"}
        if CAPTIONS_REMOVE:patch["captions"]=[]
        api("PATCH","connectors/"+ident(c),data=patch)
        newer=conn_full(c)
        if str((newer.get("style") or {}).get("strokeColor") or "").lower()!=INK.lower():
            raise RuntimeError("black stroke write failed")
        if CAPTIONS_REMOVE and newer.get("captions"):
            raise RuntimeError("caption removal failed")
        updated+=1
    return updated

def apply_links(rows,cs):
    idx=row_addr(rows)
    current={(endpoint(c,"startItem"),endpoint(c,"endItem")):c for c in cs}
    rem={(ident(rows[ra][ca-1]),ident(rows[rb][cb-1])) for (ra,ca),(rb,cb) in REMOVE_AMBIGUOUS}
    removed=0
    for pair in rem:
        c=current.get(pair)
        if not c:continue
        api("DELETE","connectors/"+ident(c)); removed+=1
    # A prior parallel edge between two identical cards is treated as unsafe.
    current={(endpoint(c,"startItem"),endpoint(c,"endItem")):c for c in live_connectors(set(idx))}
    created=0
    for ri,links in LINKS.items():
        if ri not in RELATED:raise RuntimeError("link plan escapes related rows")
        for ai,bi in links:
            if bi!=ai+1:raise RuntimeError("nonadjacent link would cross an event")
            src=rows[ri][ai-1];dst=rows[ri][bi-1]
            pair=(ident(src),ident(dst))
            if pair in current:continue
            out=api("POST","connectors",data={
                "startItem":{"id":pair[0],"snapTo":"auto"},
                "endItem":{"id":pair[1],"snapTo":"auto"},
                "shape":"curved",
                "style":{"strokeColor":INK,"strokeWidth":2,"strokeStyle":"normal",
                         "startStrokeCap":"none","endStrokeCap":"rounded_stealth"},
                "captions":[]
            })
            if not out.get("id"):raise RuntimeError("connector create did not return id")
            ck=conn_full(out)
            if (endpoint(ck,"startItem"),endpoint(ck,"endItem"))!=pair:
                raise RuntimeError("new connector endpoint mismatch")
            current[pair]=ck;created+=1
    return removed,created

def legend(frame,ch):
    # Identify existing legend items by generic terminology; no item IDs in code.
    txts=[]
    for v in ch:
        if v.get("type")!="text":continue
        data=str((v.get("data") or {}).get("content") or "")
        if any(term in data.upper() for term in
               ("HNĚDÁ ŠIPKA","MODRÁ ŠIPKA","ČERNÁ ŠIPKA","ZLEVA DOPRAVA")):
            txts.append(api("GET","texts/"+ident(v)))
    candidates={ident(v):v for v in txts}
    if len(candidates)<2:raise RuntimeError("arrow legend entries unavailable")
    changed=0;blackLegend=0;timeLegend=0
    for v in candidates.values():
        t=str((v.get("data") or {}).get("content") or "")
        up=plain(v).upper()
        revised=None
        if "HNĚDÁ ŠIPKA" in up or "ČERNÁ ŠIPKA" in up:
            revised="ČERNÁ ŠIPKA = VĚCNÁ NÁVAZNOST (NE INVOKACE)"
            blackLegend+=1
        elif "MODRÁ ŠIPKA" in up or "ZLEVA DOPRAVA" in up:
            revised="ZLEVA DOPRAVA = ORIENTAČNÍ ČAS SCÉNÁŘE"
            timeLegend+=1
        if revised is not None and plain(v)!=revised:
            api("PATCH","texts/"+ident(v),data={"data":{"content":revised}})
            chk=api("GET","texts/"+ident(v))
            if plain(chk)!=revised:raise RuntimeError("legend readback mismatch")
            changed+=1
    if blackLegend!=1 or timeLegend!=1:
        raise RuntimeError("arrow legend is not uniquely identified")
    return changed

def run():
    frame,ch,rows,evs=discover()
    cs=live_connectors(evs)
    print("PREFLIGHT PASS: %d event cards and %d existing frame-to-frame links"%(len(evs),len(cs)))
    if MODE=="audit":
        print("AUDIT ONLY: 7 relevant event groups; %d planned adjacent links"%sum(len(x) for x in LINKS.values()))
        print("RELEVANT EVENT COUNTS:",[len(rows[i]) for i in RELATED])
        return
    moved=adjust_s0(rows)
    frame,ch,rows,evs=discover()
    orig=live_connectors(evs)
    changed_ink=blacken(orig)
    removed,created=apply_links(rows,orig)
    changes=legend(frame,ch)
    frame,ch,rows,evs=discover()
    final=live_connectors(evs)
    expected=len(orig)-removed+created
    if len(final)!=expected:raise RuntimeError("final connector count mismatch")
    if any(str((c.get("style") or {}).get("strokeColor") or "").lower()!=INK.lower() for c in final):
        raise RuntimeError("non-black connector remains")
    pairs={(endpoint(c,"startItem"),endpoint(c,"endItem")) for c in final}
    if len(pairs)!=len(final):raise RuntimeError("duplicate connector pairs")
    for ri,lnks in LINKS.items():
        for ai,bi in lnks:
            if (ident(rows[ri][ai-1]),ident(rows[ri][bi-1])) not in pairs:
                raise RuntimeError("planned scenario link missing")
    print("SEMANTIC ROUTING PASS: %d all-black connectors; %d new; %d excluded; %d style fixes"%(
        len(final),created,removed,changed_ink))
    print("CHRONOLOGY CHECK PASS: CES shared-identity exception branch reordered:",moved)
    print("LEGEND PASS: %d entries updated; black=business relevance; time=spatial order"%changes)

try:run()
except Exception as e:
    print("FAIL:",str(e));sys.exit(1)
