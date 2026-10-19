#!/usr/bin/env python3
"""V14 read-only layout planning; prints aggregate geometry and safe semantic categories only."""
import collections,hashlib,json,math,re,os,urllib.parse,urllib.request,urllib.error,html,time,sys
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
V13H="26f142048d8aeda0cb2ce6d4fa31d1aa45b236cfc41d08a1ef1badb139421486"
V14TITLE="CES-1A · BP ES v14 · Enterprise business events · pracovní návrh"
TAGS={"OSOBA":r"osob|subjekt|identit|ztoto[zž]","POJISTENI":r"poji[šs]t[eě]n|p[řr]eregistr","POJISTNE":r"pojistn[eé]|pl[aá]tc|pohled[aá]vk|nedoplat|regres|p[řr]erozd[eě]l","PZS":r"poskytovat|smlouv|registruj|kapitac","PECE":r"p[eé][čc]|[úu]hrad|reviz|v[yý]kaz|zdravotn","PREVENCE":r"preven|screen|bonifik|program","ZAHRANICI":r"zahrani[čc]|p[řr]eshrani[čc]","STRATEGIE":r"strateg|pl[aá]n|vl[aá]dn|parlament|vyhl[aá]š|legislativ","OPERACE":r"dat|služb|provoz|pr[aá]vn|bezpe[čc]|incident"}
def req(path,p=None):
 url=BASE+"/"+path
 if p:url+="?"+urllib.parse.urlencode(p)
 for n in range(5):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN}),timeout=40) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code in (429,500,502,503,504) and n<4:time.sleep(min(15,2**n+1));continue
   raise RuntimeError("MIRO_HTTP_"+str(e.code))
def pages(path,p=None):
 out=[];cur=None
 for _ in range(90):
  q=dict(p or {},limit=50)
  if cur:q["cursor"]=cur
  d=req(path,q);out+=d.get("data",[]);cur=d.get("cursor")
  if not cur:return out
 raise RuntimeError("pagination")
def x(a):return float((a.get("position") or {}).get("x") or 0)
def y(a):return float((a.get("position") or {}).get("y") or 0)
def w(a):return float((a.get("geometry") or {}).get("width") or 0)
def tx(a):return re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",str((a.get("data") or {}).get("content",""))))).strip()
def tag(s):
 s=s.lower();return ",".join(k for k,r in TAGS.items() if re.search(r,s)) or "-"
def main():
 frames=pages("items",{"type":"frame"})
 src=[f for f in frames if hashlib.sha256(str(f["id"]).encode()).hexdigest()==V13H]
 dest=[f for f in frames if (f.get("data") or {}).get("title")==V14TITLE]
 if len(src)!=1 or len(dest)!=1:raise RuntimeError("FRAMES_UNIQUE_REQUIRED")
 srcid=src[0]["id"];destid=dest[0]["id"]
 items=pages("items")
 old=[i for i in items if (i.get("parent") or {}).get("id")==srcid]
 oldnotes=[i for i in old if i["type"]=="sticky_note"];headings=[i for i in old if i["type"]=="text"]
 new=[i for i in items if (i.get("parent") or {}).get("id")==destid]
 added=[i for i in new if i.get("type")=="sticky_note" and re.match(r"EV\d\d\s+·",tx(i))]
 print("V13_GEOM","notes",len(oldnotes),"headings",len(headings),"frame_width",w(src[0]),"frame_h",(src[0].get("geometry") or {}).get("height"),"V14ADDED",len(added))
 for b in range(0,10500,700):
  bin_notes=[i for i in oldnotes if b<=y(i)<b+700]
  if not bin_notes:continue
  topics=collections.Counter(k for z in bin_notes for k in tag(tx(z)).split(",") if k!="-")
  print("BAND",b,b+700,"notes",len(bin_notes),"rangeX",round(min(x(i) for i in bin_notes)),round(max(x(i) for i in bin_notes)),"topics",dict(topics.most_common(5)))
 for i,z in enumerate(sorted(headings,key=lambda z:(y(z),x(z)))):
  print("HEADING",i+1,"x",round(x(z)),"y",round(y(z)),"w",round(w(z)),"tag",tag(tx(z)))
 for z in sorted(added,key=lambda z:tx(z)[:4]):
  print("EV_POSITION",tx(z)[:4],"x",round(x(z)),"y",round(y(z)),"width",round(w(z)))
 import pathlib, statistics
 rules=json.loads((pathlib.Path(__file__).parent/"landscape_rules.json").read_text())
 notehash={hashlib.sha256(tx(z).encode()).hexdigest():z for z in oldnotes}
 for c in rules["codes"]:
  cards=[notehash[k] for k in rules["groups"][c] if k in notehash]
  if not cards:continue
  print("COVERAGE_ANCHOR",c,"n",len(cards),"x",round(statistics.median(x(z) for z in cards)),"y",round(statistics.median(y(z) for z in cards)),
        "bounds",tuple(round(v) for v in (min(x(z) for z in cards),max(x(z) for z in cards),min(y(z) for z in cards),max(y(z) for z in cards))),
        "sizes",dict(collections.Counter(round(w(z)) for z in cards)))
 print("READ_ONLY_NO_WRITES")
if __name__=="__main__":
 try:main()
 except Exception as e:print("AUDIT_FAIL",type(e).__name__,str(e));sys.exit(1)
