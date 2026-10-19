#!/usr/bin/env python3
"""Refine existing editable L1v3 descriptions in-place, with immutable event/edge protection."""
import os,re,html,hashlib,collections,sys
from l1_v3_native_build import (
    TITLE,BP_TITLE,RULES,SHORT,ADD,request,listing,txt,oid,parent,x,y,edge,esig,ident
)
from l1_v3_descriptions import describe
MODE=os.environ.get("L1V3_DESC_MODE","audit")
if MODE not in ("audit","pilot","apply"):sys.exit("INVALID_MODE")
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
def plain(z):
 return " ".join(html.unescape(re.sub(r"<[^>]+>"," ",str((z.get("data") or {}).get("content") or ""))).split())
def doc(s):
 return '<p>'+html.escape(s)+'</p>'
def unpack_body(z):
 v=html.unescape(str((z.get("data") or {}).get("content") or ""))
 v=re.sub(r'<p>\s*<a\b[^>]*>.*?</a>\s*</p>','',v,flags=re.I|re.S)
 return " ".join(html.unescape(re.sub(r"<[^>]+>"," ",v)).split())
def source_ref(z):
 v=html.unescape(str((z.get("data") or {}).get("content") or ""))
 m=re.search(r"\?moveToWidget=(\d+)",v)
 return m.group(1) if m else None
def target_html(title,source_id,code):
 description=describe(title,code)
 return '<p>'+html.escape(description)+'</p><p><a href="https://miro.com/app/board/'+BOARD+'/?moveToWidget='+source_id+'">↗ Zdrojový BP</a></p>'
def main():
 allitems=listing("items");connections=listing("connectors")
 frames=[z for z in allitems if z.get("type")=="frame"]
 bs=[z for z in frames if (z.get("data") or {}).get("title")==BP_TITLE]
 ls=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
 if len(bs)!=1 or len(ls)!=1:raise RuntimeError("SOURCE_TARGET_FRAME_DRIFT")
 bp,land=bs[0],ls[0]
 bpi=[z for z in allitems if parent(z)==oid(bp)]
 li=[z for z in allitems if parent(z)==oid(land)]
 src=[z for z in bpi if z.get("type")=="sticky_note"]
 out=[z for z in li if z.get("type")=="sticky_note"]
 desc=[z for z in li if z.get("type")=="text"]
 if len(src)!=147 or len(out)!=147 or len(desc)!=203:raise RuntimeError("COUNTS_DRIFT")
 srcids={oid(z) for z in src}
 targetids={oid(z) for z in li}
 src_links=[z for z in connections if edge(z,"startItem") in srcids and edge(z,"endItem") in srcids]
 links=[z for z in connections if edge(z,"startItem") in targetids and edge(z,"endItem") in targetids]
 if len(src_links)!=51 or len(links)!=51:raise RuntimeError("CONNECTOR_COUNTS_DRIFT")
 old_cards={ident(z) for z in out}
 old_bp={ident(z) for z in bpi}
 oldlinks={esig(z) for z in links}
 oldbp_links={esig(z) for z in src_links}
 hist={h:c for c,values in RULES["groups"].items() for h in values}
 added={name:key for key,name in SHORT.items()}
 titlemap={txt(z):z for z in out}
 srcmap={oid(z):z for z in src}
 if len(titlemap)!=147:raise RuntimeError("SOURCE_DUPLICATE_TITLES")
 bysource=collections.defaultdict(list)
 for z in desc:
  rr=source_ref(z)
  if rr in srcmap:bysource[rr].append(z)
 if len(bysource)!=147 or any(len(v)!=1 for v in bysource.values()):
  raise RuntimeError("DESCRIPTION_SOURCE_LINK_DRIFT")
 changes=[]
 for sid,s in srcmap.items():
  title=txt(s)
  z=titlemap.get(title)
  if not z:raise RuntimeError("MISSING_EVENT")
  domain=hist.get(hashlib.sha256(title.encode()).hexdigest()) or ADD.get(added.get(title))
  if not domain:raise RuntimeError("UNKNOWN_DOMAIN")
  d=bysource[sid][0]
  if abs(x(d)-x(z))>2 or abs(y(d)-y(z)-266)>2:raise RuntimeError("DESCRIPTION_NOT_ALIGNED")
  new=describe(title,domain)
  if not new or len(new)<25:raise RuntimeError("UNHELPFUL_NEW_DESCRIPTION")
  if unpack_body(d)!=new:changes.append((sid,d,new,domain,title))
 print("DESCRIPTION_PREFLIGHT_PASS","source=147","descriptions=147","changes",len(changes),
       "unchanged",147-len(changes),"mode",MODE,flush=True)
 if MODE=="audit":
  print("AUDIT_ONLY_NO_WRITES");return
 change_set=changes[:1] if MODE=="pilot" else changes
 for index,(sid,z,meaning,code,title) in enumerate(change_set):
  data={"data":{"content":target_html(title,sid,code)}}
  request("PATCH","texts/"+oid(z),data)
  if index%15==0:print("DESCRIPTION_PATCH_PROGRESS",index+1,flush=True)
 fresh=listing("items");fresh_conn=listing("connectors")
 nextbp=[z for z in fresh if parent(z)==oid(bp)]
 nextout=[z for z in fresh if parent(z)==oid(land)]
 if {ident(z) for z in nextbp}!=old_bp:raise RuntimeError("BP_CONTENT_CHANGED")
 newcards=[z for z in nextout if z.get("type")=="sticky_note"]
 if {ident(z) for z in newcards}!=old_cards:raise RuntimeError("L1_CARDS_CHANGED")
 nexttexts=[z for z in nextout if z.get("type")=="text"]
 newlinks=[z for z in fresh_conn if edge(z,"startItem") in targetids and edge(z,"endItem") in targetids]
 bpcon=[z for z in fresh_conn if edge(z,"startItem") in srcids and edge(z,"endItem") in srcids]
 if {esig(z) for z in newlinks}!=oldlinks or {esig(z) for z in bpcon}!=oldbp_links:
  raise RuntimeError("NATIVE_CONNECTORS_CHANGED")
 byref=collections.defaultdict(list)
 for z in nexttexts:
  rr=source_ref(z)
  if rr in srcmap:byref[rr].append(z)
 if len(byref)!=147 or any(len(v)!=1 for v in byref.values()):
  raise RuntimeError("DESCRIPTION_LINKS_BROKEN")
 for sid,z,meaning,code,title in change_set:
  if unpack_body(byref[sid][0])!=meaning:raise RuntimeError("DESCRIPTION_TEXT_READBACK_MISMATCH")
 if MODE=="apply":
  errors=[]
  for sid,zs in byref.items():
   tt=txt(srcmap[sid]);dom=hist.get(hashlib.sha256(tt.encode()).hexdigest()) or ADD.get(added.get(tt))
   if unpack_body(zs[0])!=describe(tt,dom):errors.append(sid)
  if errors:raise RuntimeError("INCOMPLETE_DESCRIPTIONS_"+str(len(errors)))
 print("DESCRIPTION_READBACK_PASS","updated",len(change_set),"source_unchanged",True,
       "cards_unchanged",True,"native_links_unchanged",True,flush=True)
if __name__=="__main__":
 try:main()
 except Exception as e:print("DESCRIPTION_STOP",type(e).__name__,str(e));sys.exit(1)
