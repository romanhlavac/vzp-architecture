#!/usr/bin/env python3
"""Move explicitly listed CES DEMO frames with Miro REST v2; dry-run default."""
import os,json,urllib.request,urllib.parse
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")+"/"
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
def api(verb,path,body=None):
    data=json.dumps(body).encode() if body else None
    hdr={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"}
    req=urllib.request.Request(BASE+path,method=verb,data=data,headers=hdr)
    with urllib.request.urlopen(req,timeout=50) as r: return json.load(r)
def main():
    fid="3458764687949068244"
    frame=api("GET","frames/"+fid)
    assert "Identifikace procesních scénářů" in frame["data"]["title"]
    print("READ_ONLY_PREFLIGHT",fid,frame["position"])
if __name__=="__main__":main()
