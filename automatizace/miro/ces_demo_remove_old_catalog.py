#!/usr/bin/env python3
"""Delete exactly one redundant CES DEMO native Miro Doc after canonical Sheets catalog reconciliation.
Default audit. Never deletes any frame, sticky, connector, new heuristic/source table or other doc.
"""
import os,json,sys,urllib.request,urllib.parse,urllib.error
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
MODE=os.environ.get("DEMO_OLD_DOC_MODE","audit")
assert MODE in ("audit","apply")
TARGET="3458764687803477373"
FRAME="3458764687757375873"
TITLE="Katalog business událostí"
def req(method,path):
    u=BASE+"/"+path
    r=urllib.request.Request(u,method=method,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=35) as z:
            b=z.read()
            return z.status,json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        if e.code==404:return 404,{}
        raise RuntimeError(method+" HTTP "+str(e.code)) from None
def main():
    print("PROBE_GET_ITEM",flush=True)
    st,item=req("GET","items/"+TARGET)
    if st==404:
        print("TARGET_ABSENT; no further deletion, idempotent completion")
        return
    if st!=200 or str(item.get("id",""))!=TARGET:raise RuntimeError("TARGET_ITEM_ID_DRIFT")
    typ=str(item.get("type",""))
    par=str((item.get("parent") or {}).get("id",""))
    if par!=FRAME or typ not in ("doc","document"):raise RuntimeError("PROTECTED_ITEM_PARENT_OR_TYPE_DRIFT")
    print("PROBE_GET_DOCS",flush=True)
    ds,detail=req("GET","docs/"+TARGET)
    if ds!=200:raise RuntimeError("DOC_DETAIL_UNREADABLE:"+str(ds))
    txt=json.dumps(detail,ensure_ascii=False)
    if TITLE not in txt:raise RuntimeError("DOC_TITLE_NOT_CONFIRMED")
    print("DOC_PRECHECK_PASS id="+TARGET+" type="+typ+" parent="+FRAME+" title_match=yes")
    if MODE=="audit":
        print("MODE_AUDIT no changes")
        return
    d,_=req("DELETE","docs/"+TARGET)
    if d!=204:raise RuntimeError("DELETE_NOT_204:"+str(d))
    post,_=req("GET","items/"+TARGET)
    if post!=404:raise RuntimeError("DELETE_READBACK_FAILED:"+str(post))
    print("DELETE_READBACK_PASS exact_redundant_doc_only")
if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL "+str(e),file=sys.stderr);sys.exit(2)
