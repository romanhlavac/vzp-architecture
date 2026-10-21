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
    for endpoint in ["docs/"+TARGET,"items/"+TARGET,"documents/"+TARGET]:
        try:
            status,obj=req("GET",endpoint)
            print("PROBE "+endpoint+" STATUS "+str(status)+" TYPE "+str(obj.get("type"))+" PARENT "+str((obj.get("parent") or {}).get("id"))+" TITLE_PRESENT "+str(TITLE in json.dumps(obj,ensure_ascii=False))+" KEYS "+str(list(obj)[:10]),flush=True)
        except Exception as ex:
            print("PROBE "+endpoint+" ERROR "+str(ex),flush=True)
    if MODE=="audit":
        print("MODE_AUDIT diagnostic only")
        return
    raise RuntimeError("NO_DELETE_UNLESS_FRESH_VERIFIED_PREFLIGHT")

if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL "+str(e),file=sys.stderr);sys.exit(2)
