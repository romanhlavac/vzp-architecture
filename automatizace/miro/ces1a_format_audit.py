#!/usr/bin/env python3
"""Read-only CES-1A format fingerprint: compare domain band markup/styles to S0.

No board data, object IDs, or texts are logged.
"""
import collections,re,html
from ces1a_branch_approved import call,page,id,xx,yy,ww,hh,close,txt,tag,edge,CODES
fs=page("items",{"type":"frame"})
frames=[z for z in fs if close(ww(z),6075,25) and close(hh(z),12238,25)]
if len(frames)!=1:raise RuntimeError("CES1A frame drift")
f=frames[0]
items=page("items",{"parent_item_id":id(f)})
D={}
for z in items:
    if z.get("type")=="shape" and ww(z)>2900 and "Aktéři" in txt(z):
        c=tag(z)
        if c in CODES:
            if c in D:raise RuntimeError("duplicate domain")
            D[c]=call("GET","shapes/"+id(z))
if len(D)!=20:
    print("DOMAIN_DISCOVERY",len(D),"codes",sorted(D),"shape_count",sum(x.get("type")=="shape" for x in items))
    print("CANDIDATES",[(tag(x),int(ww(x)),int(hh(x)),"Aktéři" in txt(x)) for x in items if x.get("type")=="shape" and ww(x)>2900])
    raise RuntimeError("wrong domain count")
def fingerprint(d):
    content=str((d.get("data") or {}).get("content") or "")
    style=d.get("style") or {}
    dat=d.get("data") or {}
    tags=collections.Counter(x.lower() for x in re.findall(r"</?([a-zA-Z0-9_-]+)",content))
    chunks=re.split(r"<br\s*/?>|</p>|</div>",content,flags=re.I)
    boldpieces=re.findall(r"<b>(.*?)</b>|<strong>(.*?)</strong>",content,flags=re.I|re.S)
    starts=[html.unescape(re.sub("<[^>]+>"," ",a or b)).strip() for a,b in boldpieces]
    return {
       "type":d.get("type"),"shape":dat.get("shape"),
       "fontFamily":style.get("fontFamily"),"fontSize":style.get("fontSize"),
       "fontColor":style.get("color"),"fontAlign":style.get("textAlign"),
       "fontAlignVertical":style.get("textAlignVertical"),
       "styleKeys":sorted(style),"tagCounts":dict(tags),
       "htmlChars":len(content),"plaintextChars":len(txt(d)),
       "chunks":len(chunks),"maxChunkChars":max(map(len,chunks)),
       "boldTokens":len(starts),
       "boldHeadLengths":[len(x) for x in starts[:16]],
       "newlineCount":content.count("\n"),"brCount":len(re.findall(r"<br",content,re.I)),
       "width":int(ww(d)),"height":int(hh(d))
    }
for c in CODES:
    print("FMT",c,fingerprint(D[c]))
labs=[z for z in items if z.get("type")=="text" and 1100<xx(z)<1485]
by=collections.Counter((round(ww(z)),str((z.get("style") or {}).get("fontFamily")),
                         str((z.get("style") or {}).get("fontSize")),
                         str((z.get("style") or {}).get("textAlign"))) for z in labs)
print("SCENARIO_LABEL_STYLE_COUNTS",dict(by))
print("EVENT_COUNT",sum(z.get("type")=="sticky_note" for z in items))
members={id(x) for x in items}
cons=[z for z in page("connectors") if str((z.get("startItem") or {}).get("id")) in members and
      str((z.get("endItem") or {}).get("id")) in members]
print("CONNECTOR_COUNT",len(cons))
