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
    print("PREFLIGHT exact id="+TARGET+" endpoint=docs",flush=True)
    st,item=req("GET","docs/"+TARGET)
    if st==404:
        print("TARGET_ABSENT no deletion required",flush=True)
        return
    if st!=200 or str(item.get("id",""))!=TARGET:
        raise RuntimeError("TARGET_ID_OR_STATUS_DRIFT")
    typ=str(item.get("type",""))
    parent=str((item.get("parent") or {}).get("id",""))
    if typ!="doc_format" or parent!=FRAME:
        raise RuntimeError("TARGET_TYPE_OR_PARENT_DRIFT")
    if TITLE not in json.dumps(item,ensure_ascii=False):
        raise RuntimeError("TARGET_DOC_TITLE_DRIFT")
    print("DOC_PREFLIGHT_PASS id="+TARGET+" type="+typ+" correct_parent=yes correct_title=yes",flush=True)
    if MODE=="audit":
        print("AUDIT_ONLY no write",flush=True)
        return
    d,_=req("DELETE","docs/"+TARGET)
    if d!=204:raise RuntimeError("DELETE_UNEXPECTED_HTTP_"+str(d))
    print("DELETE_204 id="+TARGET,flush=True)
    st,_=req("GET","docs/"+TARGET)
    if st!=404:raise RuntimeError("DELETE_VERIFY_NOT_404_"+str(st))
    print("DELETE_READBACK_PASS removed one exact redundant DL doc",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL "+str(e),file=sys.stderr);sys.exit(2)
