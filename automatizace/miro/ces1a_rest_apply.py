#!/usr/bin/env python3
"""Miro REST v2 one-shot: normalize 1A event types, publish generic references.
No client content or board identifiers in GitHub code/logs. OAuth through Environment.
"""
import html,json,math,os,re,sys,time,urllib.request,urllib.error,urllib.parse
from ces1a_references import HEURISTICS,SOURCES

TOKEN=os.getenv("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.getenv("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
MODE=os.getenv("MIRO_CHANGE_MODE","inspect")
if not TOKEN or not BOARD or MODE not in ("inspect","apply"):
    sys.exit("FAIL: missing environment credentials or invalid mode")
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")

def api(method,path,data=None,params=None):
    url=BASE+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    body=None if data is None else json.dumps(data,ensure_ascii=False).encode("utf8")
    h={"Accept":"application/json","Authorization":"Bearer "+TOKEN}
    if body is not None:h["Content-Type"]="application/json"
    for n in range(4):
        try:
            req=urllib.request.Request(url,headers=h,method=method,data=body)
            with urllib.request.urlopen(req,timeout=35) as resp:
                raw=resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and n<3:
                time.sleep(2**n+1);continue
            raise RuntimeError("Miro API "+method+" "+path.split("/")[0]+" returned HTTP "+str(e.code)) from None
        except Exception:
            raise RuntimeError("Miro API request failed") from None

def lst(**args):
    out=[]; cursor=None
    for _ in range(40):
        p=dict(args,limit=50)
        if cursor:p["cursor"]=cursor
        d=api("GET","items",params=p)
        out+=d.get("data",[])
        cursor=d.get("cursor")
        if not cursor:return out
    raise RuntimeError("Pagination safety gate failed")

def w(o):return float(o.get("geometry",{}).get("width") or 0)
def h(o):return float(o.get("geometry",{}).get("height") or 0)
def pos(o):return o.get("position") or {}
def xy(o):return float(pos(o).get("x") or 0),float(pos(o).get("y") or 0)
def par(o):return str((o.get("parent") or {}).get("id") or "")
def close(a,b,t=5):return abs(float(a)-float(b))<=t
def label(o):
    s=str(o.get("data",{}).get("content") or "")
    return html.unescape(re.sub(r"<[^>]+>","",s)).strip()
def detail(o):
    return api("GET",("sticky_notes/" if o["type"]=="sticky_note" else "shapes/")+str(o["id"]))

def discover():
    frames=lst(type="frame")
    matches=[f for f in frames if close(w(f),6920,20) and close(h(f),7160,20)]
    if len(matches)!=1:raise RuntimeError("1A frame geometry or identity changed")
    frame=api("GET","frames/"+str(matches[0]["id"]))
    children=lst(parent_item_id=str(frame["id"]))
    domains=[z for z in children if z.get("type")=="shape" and close(w(z),1250,10) and "S0" in label(z)[:12]]
    if len(domains)!=1:raise RuntimeError("S0 domain not unique")
    dx,dy=xy(detail(domains[0]))
    ev=[z for z in children if z.get("type") in ("sticky_note","shape") and
        close(w(z),258,10) and close(h(z),168,10) and
        abs(xy(z)[1]-dy)<45 and xy(z)[0]>dx+450]
    ev=[detail(z) for z in ev]
    if len(set(map(label,ev)))!=8 or not 8<=len(ev)<=16:raise RuntimeError("S0 event inventory drift")
    if sum(z.get("type")=="sticky_note" for z in children)<120:
        raise RuntimeError("Baseline sticky population drift")
    return frame,ev

def connectors():
    out=[];cursor=None
    for _ in range(20):
        params={"limit":50}
        if cursor:params["cursor"]=cursor
        obj=api("GET","connectors",params=params)
        out.extend(obj.get("data",[]))
        cursor=obj.get("cursor")
        if not cursor:return out
    raise RuntimeError("Connector pagination safety gate failed")

def replace(events):
    mapping={};changed=0;changed_links=0
    for z in events:mapping.setdefault(label(z),[]).append(z)
    all_lines=connectors()
    for group in mapping.values():
        shapes=[z for z in group if z["type"]=="shape"]
        notes=[z for z in group if z["type"]=="sticky_note"]
        if len(shapes)>1 or len(notes)>1:raise RuntimeError("Ambiguous event conversion")
        if not shapes:continue
        source=shapes[0];old=str(source["id"])
        if notes:
            target=notes[0]
        else:
            new=api("POST","sticky_notes",data={
                "data":{"content":source["data"]["content"],"shape":"rectangle"},
                "style":{"fillColor":"orange","textAlign":"center","textAlignVertical":"middle"},
                "geometry":{"width":w(source)},
                "position":{"x":xy(source)[0],"y":xy(source)[1],"origin":"center"},
                "parent":{"id":par(source)}
            })
            target=api("GET","sticky_notes/"+str(new["id"]))
        if target.get("type")!="sticky_note" or label(target)!=label(source) or par(target)!=par(source):
            raise RuntimeError("Converted item semantics differ")
        if abs(xy(target)[0]-xy(source)[0])>3 or abs(xy(target)[1]-xy(source)[1])>3 or abs(w(target)-w(source))>4:
            raise RuntimeError("Converted item geometry differs")
        dest=str(target["id"])
        for c in all_lines:
            ends={}
            for name in ("startItem","endItem"):
                if str((c.get(name) or {}).get("id"))==old:ends[name]={"id":dest,"snapTo":"auto"}
            if not ends:continue
            updated=api("PATCH","connectors/"+str(c["id"]),data=ends)
            chk=api("GET","connectors/"+str(c["id"]))
            if any(str((chk.get(name) or {}).get("id"))==old for name in ("startItem","endItem")):
                raise RuntimeError("Connector readback mismatch; old shape retained")
            changed_links+=1
        api("DELETE","shapes/"+old)
        if api("GET","sticky_notes/"+dest).get("type")!="sticky_note":
            raise RuntimeError("Replacement lost after deletion")
        changed+=1
    return changed,changed_links

def references(frame):
    title="1A · Referenční tabulky heuristik a zdrojů"
    matches=[z for z in lst(type="frame") if (z.get("data") or {}).get("title")==title]
    if len(matches)>1:raise RuntimeError("Multiple reference frames")
    if matches:f=api("GET","frames/"+str(matches[0]["id"]))
    else:
        cx,cy=xy(frame)
        f=api("POST","frames",data={
            "data":{"title":title},"geometry":{"width":6920,"height":2700},
            "position":{"x":cx,"y":cy+h(frame)/2+180+1350,"origin":"center"}
        })
        f=api("GET","frames/"+str(f["id"]))
    existing=lst(parent_item_id=str(f["id"]))
    if existing:
        if len(existing)<23:raise RuntimeError("Partial reference layout requires reconciliation")
        return False,len(existing)
    cx,cy=xy(f);x0=cx-w(f)/2;y0=cy-h(f)/2
    rows=[]
    for i,(code,name,note) in enumerate(HEURISTICS):
        rows.append((i//8,i%8,code+" | "+name,note,False))
    for i,(code,name,note) in enumerate(SOURCES):
        rows.append((i//4,i%4,code+" | "+name,note,True))
    for col,row,name,note,is_source in rows:
        x=x0+70+col*3380+1620
        y=y0+(1530 if is_source else 160)+row*151+72
        payload={
            "data":{"content":"<b>"+html.escape(name)+"</b><br/>"+html.escape(note),"shape":"round_rectangle"},
            "style":{"fillColor":"#E6F4F6" if is_source else "#F2F5F5",
                     "fontFamily":"open_sans","fontSize":"18","textAlign":"left"},
            "geometry":{"width":3240,"height":144},
            "position":{"x":x,"y":y,"origin":"center"},
            "parent":{"id":str(f["id"])}
        }
        out=api("POST","shapes",data=payload)
        if not out.get("id"):raise RuntimeError("Reference item creation failed")
    count=len(lst(parent_item_id=str(f["id"])))
    if count<23:raise RuntimeError("Reference table readback incomplete")
    return True,count

def run():
    frame,ev=discover()
    sh=sum(z["type"]=="shape" for z in ev)
    print("PREFLIGHT PASS: eight distinct events; %d shape replacements pending"%sh)
    if MODE=="inspect":
        print("READ ONLY PASS");return
    changed,edges=replace(ev)
    _,final=discover()
    if len(final)!=8 or any(z["type"]!="sticky_note" for z in final):
        raise RuntimeError("Eight native sticky acceptance failed")
    created,count=references(frame)
    print("REST WRITE PASS: %d events converted; %d connector endpoints updated"%(changed,edges))
    print("REFERENCE PASS: %d methodology rows; newly created=%s"%(count,str(created).lower()))

try:run()
except Exception as e:
    print("FAIL:",str(e))
    sys.exit(1)
