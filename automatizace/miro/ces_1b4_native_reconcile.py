#!/usr/bin/env python3
"""Scoped native 1B.4 reconciliation; no business data/URLs/tokens in Git or logs."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import ces_demo_layout_1a_1b_refine_20261023 as baseline
api, page = baseline.api, baseline.page
MODE=os.getenv("RECONCILE_MODE","audit")
assert MODE in ("audit","repair","repair2")
M=baseline.FRAME_IDS["L2"]
def get(i): return api("GET","frames/"+i)
def closest(val,base,tol=3):return abs(val-base)<tol
def main():
  # This scope was discovered via a protected pre-write inventory, then re-read live.
  l2=get(M); parentid=str(l2.get("parent",{}).get("id","")); assert parentid,"PARENT_MISSING"
  parent=get(parentid)
  fs=page("items",{"type":"frame"})
  candidate=[f for f in fs if not (f.get("parent") or {}).get("id") and closest(f.get("geometry",{}).get("width",0),4280) and closest(f.get("geometry",{}).get("height",0),7400)]
  assert len(candidate)==1,"ORPHAN_SELECTION_AMBIGUOUS"
  orphan=candidate[0]
  old=(l2.get("position") or {})
  p=(parent.get("position") or {})
  bounds=parent.get("geometry") or {}
  # Distinct invariants: the already-known parent width and map height are
  # recorded as numeric geometry, not private content.
  assert closest(bounds.get("width",0),23800,10)
  assert closest((l2.get("geometry") or {}).get("height",0),7400,10)
  assert len(page("items",{"parent_item_id":orphan["id"]}))==0,"ORPHAN_NOT_EMPTY"
  print("AUDIT_PASSED",len(fs),"parent_width",round(bounds["width"]),"map_top",round(old.get("y",0)-(l2["geometry"]["height"]/2)),"orphan_unparented",flush=True)
  if MODE!="repair":return
  if MODE=="repair2":
    # After REST 400 on moving the ancestor, don't move it or retry.
    # Idempotent repair only of orphan parentage and existing map's local center.
    target={"parent":{"id":parentid},"position":{"x":14184+4280/2,"y":2798+7400/2,"origin":"center"}}
    api("PATCH","items/"+orphan["id"],target)
    o=api("GET","items/"+orphan["id"])
    assert str((o.get("parent") or {}).get("id"))==parentid,"NESTED_PARENT_FAIL"
    print("ORPHAN_PARENT_CONFIRMED",flush=True)
    api("PATCH","frames/"+M,{"position":{"x":18700+4600/2,"y":2798+7400/2,"origin":"center"}})
    m=get(M)
    assert abs(m["position"]["x"]-(18700+4600/2))<10 and abs(m["position"]["y"]-(2798+7400/2))<10,"MAP_PLACEMENT_FAIL"
    assert str((m.get("parent") or {}).get("id"))==parentid,"MAP_PARENT_FAIL"
    print("REPAIR2_CONFIRMED",flush=True)
    return
  # Only these three items may change. Positions are parent-local centers.
  px=p["x"]+2366
  patch=[("frames/"+parentid,{"position":{"x":px,"y":p["y"],"origin":"center"}}),
    ("items/"+orphan["id"],{"parent":{"id":parentid},"position":{"x":14184+4280/2,"y":2798+7400/2,"origin":"center"}}),
    ("frames/"+M,{"position":{"x":18700+4600/2,"y":2798+7400/2,"origin":"center"}})]
  for path,payload in patch:
    oldval=api("GET",path)
    api("PATCH",path,payload)
    newval=api("GET",path)
    assert newval["id"]==oldval["id"],"ID_DRIFT"
    print("STEP_CONFIRMED",path.split("/")[0],flush=True)
  o=api("GET","items/"+orphan["id"]); m=get(M); par=get(parentid)
  assert str((o.get("parent") or {}).get("id"))==parentid,"NESTED_PARENT_FAIL"
  assert str((m.get("parent") or {}).get("id"))==parentid,"MAP_PARENT_FAIL"
  assert closest(m["position"]["x"],18700+4600/2,10),"MAP_X_FAIL"
  assert closest(m["position"]["y"],2798+7400/2,10),"MAP_Y_FAIL"
  assert closest(par["position"]["x"],px,10),"PARENT_X_FAIL"
  print("REPAIR_CONFIRMED",flush=True)
if __name__=="__main__":main()
