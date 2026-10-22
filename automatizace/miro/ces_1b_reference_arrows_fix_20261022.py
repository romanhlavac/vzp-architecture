#!/usr/bin/env python3
"""One-off native Miro REST v2 repair of 1B reference connectors (2026-10-22).
Target: ONLY the 7 connector IDs of the user-provided Process Modelling picture.
No business data printed; never rewire, move or delete anything.
"""
import os,json,time,urllib.request,urllib.parse,urllib.error
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
# (connector ID, target routing shape, expected caption)
TARGETS=[
 ("3458764688162124401","curved","Decides to"),
 ("3458764688162124402","straight","Invoked On"),
 ("3458764688162124403","straight","Produces an"),
 ("3458764688162124404","curved","Activates a"),
 ("3458764688162124406","curved","Issues a"),
 ("3458764688162124407","curved","observes"),
 ("3458764688162124408","curved","Results in one or more"),
]
STYLE={"strokeColor":"#000000","strokeWidth":"20","strokeStyle":"normal",
       "startStrokeCap":"none","endStrokeCap":"filled_triangle",
       "fontSize":"96","color":"#000000","textOrientation":"horizontal"}
def api(method,path,obj=None):
    data=None if obj is None else json.dumps(obj,ensure_ascii=False).encode()
    hd={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
    if data is not None:hd["Content-Type"]="application/json"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(ROOT+path,data=data,headers=hd,method=method),timeout=55) as res:
                body=res.read();return json.loads(body) if body else {}
        except urllib.error.HTTPError as ex:
            if method=="GET" and attempt<4 and ex.code in (429,500,502,503,504):
                time.sleep(min(15,2**attempt));continue
            raise RuntimeError("MIRO_HTTP_"+str(ex.code)+"_"+method) from None
def endpoint(z,key):return str((z.get(key) or {}).get("id") or "")
def label(z):return [str(v.get("content") or "") for v in (z.get("captions") or [])]
def read(id):return api("GET","connectors/"+id)
def preflight():
    state={}
    expected_src={
      "3458764688162124401":("3458764688162124379","3458764688162124376"),
      "3458764688162124402":("3458764688162124376","3458764688162124377"),
      "3458764688162124403":("3458764688162124377","3458764688162124378"),
      "3458764688162124404":("3458764688162124378","3458764688162124375"),
      "3458764688162124406":("3458764688162124375","3458764688162124376"),
      "3458764688162124407":("3458764688162124379","3458764688162124380"),
      "3458764688162124408":("3458764688162124378","3458764688162124380")
    }
    for id,shape,caption in TARGETS:
        z=read(id)
        if (endpoint(z,"startItem"),endpoint(z,"endItem"))!=expected_src[id]:
            raise RuntimeError("ENDPOINT_DRIFT_"+id)
        if label(z)!=[caption]:raise RuntimeError("CAPTION_DRIFT_"+id)
        if z.get("shape") not in ("curved","straight"):
            raise RuntimeError("SHAPE_DRIFT_"+id)
        state[id]=z
    print("REFERENCE_PREPARE_PASS",json.dumps({"connectors":len(state),"unchanged_semantics":True}),flush=True)
    return state
def main():
    before=preflight()
    changed=0
    for i,(id,shape,caption) in enumerate(TARGETS):
        z=before[id]
        st=dict(z.get("style") or {})
        st.update(STYLE)
        payload={"shape":shape,"style":st}
        api("PATCH","connectors/"+id,payload)
        fresh=read(id)
        if endpoint(fresh,"startItem")!=endpoint(z,"startItem") or endpoint(fresh,"endItem")!=endpoint(z,"endItem"):
            raise RuntimeError("SEMANTIC_ENDPOINT_CHANGED_"+id)
        if label(fresh)!=label(z):raise RuntimeError("SEMANTIC_CAPTION_CHANGED_"+id)
        if fresh.get("shape")!=shape:raise RuntimeError("ROUTE_SHAPE_READBACK_FAIL_"+id)
        style=fresh.get("style") or {}
        for k in ("strokeColor","strokeWidth","endStrokeCap","fontSize","color","textOrientation"):
            wanted=STYLE[k]
            got=style.get(k)
            if str(got).lower()!=str(wanted).lower() and not (k in ("strokeWidth","fontSize") and str(got).removesuffix(".0")==wanted):
                raise RuntimeError("STYLE_READBACK_FAIL_"+k+"_"+id)
        changed+=1
        print("REFERENCE_CONNECTOR_PASS",i+1,"of",len(TARGETS),"shape",shape,flush=True)
        time.sleep(.11)
    last=preflight()
    if any(last[id].get("shape")!=shape for id,shape,_ in TARGETS):
        raise RuntimeError("FINAL_ROUTE_DRIFT")
    print("REFERENCE_STYLES_ACCEPTANCE_PASS",json.dumps({
      "connectors":changed,"native_font_dp":96,"stroke_width_dp":20,
      "arrowheads":"filled_triangle","routing_shapes":{"straight":2,"curved":5},
      "semantic_ids_labels_endpoints":"PRESERVED","visual_acceptance":"OPEN"}),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("REFERENCE_STYLE_STOP",type(ex).__name__,str(ex),flush=True)
        raise SystemExit(1)
