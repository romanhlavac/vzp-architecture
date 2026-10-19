#!/usr/bin/env python3
"""Trim approved V14 Miro frame to its regrouped contents.  Read-only default."""
import os,sys,math,hashlib,json,collections
from ces1a_v14_integrate import call,pages,txt,x,y,width,height,oid,parent,TITLE,SOURCE_SHA,SHORT
MODE=os.getenv("V14_TRIM_MODE","audit")
if MODE not in ("audit","apply"):sys.exit("INVALID_MODE")
W,H=18000,13700
def main():
 frames=pages("items",{"type":"frame"})
 sr=[z for z in frames if hashlib.sha256(oid(z).encode()).hexdigest()==SOURCE_SHA]
 ds=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
 if len(sr)!=1 or len(ds)!=1:raise RuntimeError("FRAME_IDENTITY_DRIFT")
 d=ds[0];s=sr[0]
 data=pages("items",{"parent_item_id":oid(d)})
 sc=pages("items",{"parent_item_id":oid(s)})
 source_signature={(oid(z),txt(z),round(x(z),1),round(y(z),1)) for z in sc}
 counts=collections.Counter(z.get("type") for z in data)
 if counts["sticky_note"]!=147 or counts["text"]!=22:raise RuntimeError("TARGET_CONTENT_DRIFT")
 maxright=max(x(z)+width(z)/2 for z in data)
 maxbottom=max(y(z)+height(z)/2 for z in data)
 minleft=min(x(z)-width(z)/2 for z in data)
 mintop=min(y(z)-height(z)/2 for z in data)
 if maxright>W-60 or maxbottom>H-70 or minleft<30 or mintop<30:
  raise RuntimeError("TRIM_BOUNDS_NOT_SAFE")
 if any(txt(z).startswith(("EV","N")) and " · " in txt(z) for z in data if z.get("type")=="sticky_note"):
  raise RuntimeError("VISIBLE_PREFIXES_NOT_REMOVED")
 print("TRIM_PREFLIGHT_PASS","native_events",147,"texts",22,
       "bounds",tuple(round(q) for q in (minleft,mintop,maxright,maxbottom)),
       "frame_before",tuple(round(q) for q in (width(d),height(d))),
       "requested",(W,H),flush=True)
 if MODE=="audit":print("AUDIT_ONLY_NO_WRITES");return
 if abs(width(d)-W)>1 or abs(height(d)-H)>1:
  patch=call("PATCH","frames/"+oid(d),{"geometry":{"width":W,"height":H}})
  print("FRAME_PATCH_RESPONSE",tuple(round(q) for q in (width(patch),height(patch))),flush=True)
 # Fresh independent read-back after server-normalized geometry.
 after=pages("items",{"type":"frame"})
 target=[z for z in after if oid(z)==oid(d)]
 if len(target)!=1:raise RuntimeError("FRAME_MISSING_AFTER_PATCH")
 target=target[0]
 if abs(width(target)-W)>1 or abs(height(target)-H)>1:
  raise RuntimeError("FRAME_TRIM_UNAPPLIED")
 child=pages("items",{"parent_item_id":oid(d)})
 if {(oid(z),txt(z),round(x(z),1),round(y(z),1)) for z in child} != {(oid(z),txt(z),round(x(z),1),round(y(z),1)) for z in data}:
  raise RuntimeError("CHILD_CONTENT_OR_POSITION_CHANGED_AFTER_TRIM")
 source_after=pages("items",{"parent_item_id":oid(s)})
 if {(oid(z),txt(z),round(x(z),1),round(y(z),1)) for z in source_after}!=source_signature:
  raise RuntimeError("SOURCE_V13_CHANGED")
 print("FRAME_TRIM_READBACK_PASS","width",round(width(target)),"height",round(height(target)),
       "children",len(child),"protected_source_unchanged",True)
 print("VISUAL_RENDER_ACCEPTANCE_OPEN")
if __name__=="__main__":
 try:main()
 except Exception as e:print("FRAME_TRIM_STOP",type(e).__name__,str(e));sys.exit(1)
