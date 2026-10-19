#!/usr/bin/env python3
"""Read-only live L1-v2 domain coverage audit. Aggregate counts only in public logs."""
import hashlib,os,json,html,re,urllib.request,urllib.parse,urllib.error,time,collections,sys
from pathlib import Path
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
TARGET_SHA="395d1b419c137f269732ea2d979a2a5ae69edf88122d5ce70ebd349ac6f12ffb"
RULES=json.loads((Path(__file__).parent/"landscape_rules.json").read_text())
def request(path,p=None):
 url=ROOT+"/"+path
 if p:url+="?"+urllib.parse.urlencode(p)
 for n in range(5):
  try:
   req=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
   with urllib.request.urlopen(req,timeout=40) as res:return json.load(res)
  except urllib.error.HTTPError as err:
   if err.code in (429,500,502,503,504) and n<4:time.sleep(min(15,2**n+1));continue
   raise RuntimeError("API error "+str(err.code)) from None
def listing(path,p=None):
 items=[];cursor=None
 for _ in range(120):
  q=dict(p or {},limit=50)
  if cursor:q["cursor"]=cursor
  r=request(path,q);items+=r.get("data",[]);cursor=r.get("cursor")
  if not cursor:return items
 raise RuntimeError("pagination overflow")
def tx(z):
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",str((z.get("data") or {}).get("content",""))))).strip()
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 frames=listing("items",{"type":"frame"})
 matched=[x for x in frames if h(str(x.get("id")))==TARGET_SHA]
 if len(matched)!=1:raise RuntimeError("TARGET_FRAME_NOT_UNIQUE")
 frame=matched[0];fid=str(frame["id"])
 children=listing("items",{"parent_item_id":fid})
 counts=collections.Counter(z["type"] for z in children)
 notes=[z for z in children if z["type"]=="sticky_note"]
 lookup={h(tx(z)):[] for z in notes}
 for z in notes:lookup[h(tx(z))].append(z)
 expected={k:c for c,hs in RULES["groups"].items() for k in hs}
 seen=set();dups=0
 print("LIVE_FRAME_PRESENT yes; EVENT_NOTES",len(notes),"CHILDREN",len(children),"TYPE_COUNTS",dict(counts),flush=True)
 for code in RULES["codes"]:
  group=RULES["groups"][code]
  found=sum(len(lookup.get(x,[])) for x in group)
  duplicates=sum(max(0,len(lookup.get(x,[]))-1) for x in group)
  matchedhashes=sum(bool(lookup.get(x)) for x in group)
  print("L1_CODE",code,"EXPECTED_V12",len(group),"LIVE_PRIMARY",found,"HASH_MATCHED",matchedhashes,"DUPLICATES",duplicates,flush=True)
  for x in group:
   if lookup.get(x):seen.add(x)
 unmatched=sum(len(v) for k,v in lookup.items() if k not in expected)
 missing=sum(not lookup.get(x) for x in expected)
 print("READ_ONLY_VALIDATION unmatched",unmatched,"missing",missing,"source_v12_hashes",len(expected),flush=True)
 print("AUDIT_ONLY_NO_WRITES",flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:print("AUDIT_FAILURE",type(e).__name__,str(e));sys.exit(1)
